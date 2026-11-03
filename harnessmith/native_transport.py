"""Versioned POSIX stdio capture for O3; no host or permission qualification.

Readers commit exact stream chunks independently of the protocol consumer.
Frames are also committed before JSON parsing. There is no implicit environment,
credential lookup, shell, retry, or provider selection.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import queue
import selectors
import signal
import subprocess
import threading
import time

INSTRUMENTATION = "native-stdio-v1"


@dataclass(frozen=True)
class Frame:
    payload: bytes
    raw_ref: str
    elapsed_ms: int

    def message(self):
        value = json.loads(self.payload)
        if not isinstance(value, dict):
            raise ValueError("protocol frame must be an object")
        return value


class StdioCapture:
    """Continuously retain both streams, with a whole-process deadline.

    Queue and frame bounds fail capture rather than silently dropping evidence.
    On close the owned process group is killed, including descendants whose
    leader has exited. This is cleanup, not an OS sandbox.
    """

    def __init__(self, journal, command, *, cwd, env, timeout,
                 max_frame_bytes=4 * 1024 * 1024, max_pending_frames=1024):
        if (not command or not all(isinstance(x, str) and x for x in command)
                or not os.path.isabs(command[0]) or not isinstance(env, dict)
                or timeout <= 0 or max_frame_bytes < 1 or max_pending_frames < 1):
            raise ValueError("invalid transport configuration")
        self.journal = journal
        self.deadline = time.monotonic() + timeout
        self.max_frame_bytes = max_frame_bytes
        self.frames: queue.Queue[Frame] = queue.Queue(maxsize=max_pending_frames)
        self.errors: queue.Queue[BaseException] = queue.Queue()
        self.readers = []
        self.process = None
        self.closed = False
        self.stdout_done = threading.Event()
        journal.append("transport.starting", dict(instrumentation=INSTRUMENTATION,
                       command=list(command), cwd=str(cwd), env_keys=sorted(env)))
        try:
            self.process = subprocess.Popen(command, cwd=cwd, env=dict(env),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True, bufsize=0)
            journal.append("transport.started", {"pid": self.process.pid})
            assert self.process.stdin is not None
            os.set_blocking(self.process.stdin.fileno(), False)
            for channel, pipe in (("receive", self.process.stdout), ("stderr", self.process.stderr)):
                reader = threading.Thread(target=self._read, args=(channel, pipe), daemon=True)
                self.readers.append(reader)
                reader.start()
        except BaseException as exc:
            self.close()
            journal.append("transport.start_failed", {"error": type(exc).__name__, "message": str(exc)})
            raise

    def _frame(self, payload):
        reference = self.journal.blob(payload)
        record = self.journal.append("transport.frame", {"blob_ref": reference})
        self.frames.put_nowait(Frame(payload, reference, record["elapsed_ms"]))

    def _read(self, channel, pipe):
        pending = b""
        try:
            while True:
                chunk = os.read(pipe.fileno(), 65536)
                if not chunk:
                    break
                self.journal.raw(channel, chunk)
                if channel == "receive":
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        if len(line) + 1 > self.max_frame_bytes:
                            raise ValueError("protocol frame exceeds bound")
                        self._frame(line + b"\n")
                    if len(pending) > self.max_frame_bytes:
                        raise ValueError("protocol frame exceeds bound")
            if pending:
                # Its exact bytes already exist in raw chunks. A partial frame
                # must not be parsed as a valid terminal protocol message.
                self.journal.append("transport.truncated", {"blob_ref": self.journal.blob(pending)})
                raise ValueError("unterminated protocol frame")
        except BaseException as exc:
            self.errors.put(exc)
        finally:
            if channel == "receive":
                self.stdout_done.set()
            pipe.close()

    def _check(self):
        if not self.errors.empty():
            raise self.errors.get_nowait()
        if time.monotonic() >= self.deadline:
            raise TimeoutError("whole-trajectory transport deadline exceeded")
        if self.closed:
            raise RuntimeError("transport closed")

    def send(self, message, *, before_write=None):
        self._check()
        payload = (json.dumps(message, allow_nan=False) + "\n").encode()
        if len(payload) > self.max_frame_bytes:
            raise ValueError("outbound frame exceeds bound")
        reference, elapsed = self.journal.raw("send", payload)
        frame = Frame(payload, reference, elapsed)
        if before_write is not None:
            before_write(frame)
        # Persist intent before touching the pipe; a later failure does not
        # promote this record to successful receipt or execution.
        offset = 0
        assert self.process is not None and self.process.stdin is not None
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while offset < len(payload):
                self._check()
                if not selector.select(min(.05, max(0, self.deadline - time.monotonic()))):
                    continue
                try:
                    offset += os.write(self.process.stdin.fileno(), payload[offset:])
                except BlockingIOError:
                    continue
        self.journal.append("transport.sent", {"blob_ref": reference})
        return frame

    def receive(self):
        while True:
            self._check()
            try:
                return self.frames.get(timeout=min(.05, max(0, self.deadline - time.monotonic())))
            except queue.Empty:
                if self.stdout_done.is_set():
                    self._check()
                    raise EOFError("host stdout closed before requested boundary")

    def close(self):
        if self.closed:
            return
        self.closed = True
        process = self.process
        if process is None:
            return
        cleanup_error = None
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as exc:
            cleanup_error = exc
        if process.stdin is not None:
            process.stdin.close()
        process.wait(timeout=5)
        for reader in self.readers:
            reader.join(timeout=5)
        if any(reader.is_alive() for reader in self.readers):
            raise RuntimeError("stream reader did not terminate")
        self.journal.append("transport.closed", {"returncode": process.returncode})
        if cleanup_error is not None:
            self.journal.append("transport.cleanup_error", {
                "error": type(cleanup_error).__name__, "message": str(cleanup_error)})
            raise cleanup_error
        if not self.errors.empty():
            raise self.errors.get_nowait()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        try:
            self.close()
        except BaseException as exc:
            if kind is None:
                raise
            # Preserve the primary exception and retain the cleanup failure.
            self.journal.append("transport.cleanup_failed", {
                "primary_error": kind.__name__, "cleanup_error": type(exc).__name__,
                "message": str(exc)})
        return False
