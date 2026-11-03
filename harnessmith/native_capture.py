"""O3 v1 durable offline capture. No qualified native transport or live launch.

The injected source/decoder seam is for synthetic qualification. Raw records
are committed before decoding; a decoder must never consult expected answers.
"""
from __future__ import annotations

from dataclasses import asdict
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import stat
import threading
import time

from .native_contract import integrity_findings, parse_trajectory, usage_totals

INSTRUMENTATION = "native-capture-v2"


def _locked(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return call


def _json(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _create(path, data):
    # Exclusive creation prevents an attempt or evidence blob being overwritten.
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    _sync_directory(path.parent)


class AttemptJournal:
    """Serialized journal in a new, controller-owned evidence directory.

    Directory must be outside the measured workspace. Never reopen an attempt
    for writing: recovery is read-only and a partial attempt consumes its slot.
    """

    def __init__(self, directory, manifest):
        self.lock = threading.RLock()
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=False, exist_ok=False)
        _sync_directory(self.directory.parent)
        (self.directory / "blobs").mkdir(mode=0o700)
        _sync_directory(self.directory)
        self.sequence = 0
        self.started = time.monotonic_ns()
        self.closed = False
        _create(self.directory / "journal.jsonl", b"")
        self.append("attempt.started", {"instrumentation": INSTRUMENTATION,
                                       "manifest_ref": self.blob(_json(manifest))})

    def elapsed_ms(self):
        return (time.monotonic_ns() - self.started) // 1_000_000

    @_locked
    def blob(self, data):
        if self.closed:
            raise RuntimeError("attempt is closed")
        if not isinstance(data, bytes):
            raise TypeError("capture requires bytes")
        digest = hashlib.sha256(data).hexdigest()
        path = self.directory / "blobs" / digest
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError("existing blob is corrupt")
        else:
            _create(path, data)
        return "blobs/" + digest

    @_locked
    def append(self, kind, data):
        if self.closed:
            raise RuntimeError("attempt is closed")
        record = dict(sequence=self.sequence, elapsed_ms=self.elapsed_ms(),
                      kind=kind, data=data)
        with (self.directory / "journal.jsonl").open("ab") as stream:
            stream.write(_json(record))
            stream.flush()
            os.fsync(stream.fileno())
        self.sequence += 1
        return record

    @_locked
    def raw(self, channel, payload):
        if channel not in {"send", "receive", "stderr", "controller"}:
            raise ValueError("unknown raw channel")
        reference = self.blob(payload)
        record = self.append("raw", {"channel": channel, "blob_ref": reference})
        return reference, record["elapsed_ms"]

    def snapshot(self, workspace, phase):
        """Retain bytes, modes, empty directories and links without following links.

        Requires a quiescent isolated workspace; this is not an OS-atomic snapshot.
        Special files and observable concurrent mutations fail closed.
        """
        root = Path(workspace)
        entries = {}

        def visit(path, relative):
            before = path.lstat()
            mode = stat.S_IMODE(before.st_mode)
            if stat.S_ISLNK(before.st_mode):
                entries[relative] = dict(kind="symlink", mode=mode,
                                         target=os.readlink(path))
            elif stat.S_ISDIR(before.st_mode):
                entries[relative] = dict(kind="directory", mode=mode)
                for child in sorted(path.iterdir()):
                    visit(child, child.name if relative == "." else relative + "/" + child.name)
            elif stat.S_ISREG(before.st_mode):
                # O_NOFOLLOW also rejects a link substituted since lstat.
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, "rb") as stream:
                    opened = os.fstat(stream.fileno())
                    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                        raise ValueError("workspace changed during snapshot")
                    reference = self.blob(stream.read())
                entries[relative] = dict(kind="file", mode=mode, blob_ref=reference)
            else:
                raise ValueError("unsupported workspace file: " + relative)
            after = path.lstat()
            if (before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                raise ValueError("workspace changed during snapshot")

        visit(root, ".")
        reference = self.blob(_json(entries))
        self.append("workspace.snapshot", {"phase": phase, "blob_ref": reference})
        return reference


def recover_attempt(directory):
    """Read intact journal prefix; report truncation/corruption, never repair it."""
    root = Path(directory)
    records: list[dict] = []
    findings: list[str] = []
    previous_ms = -1
    try:
        raw = (root / "journal.jsonl").read_bytes()
    except OSError as exc:
        raw = b""
        findings.append("journal unavailable: " + type(exc).__name__)
    for line in raw.splitlines(keepends=True):
        try:
            if not line.endswith(b"\n"):
                raise ValueError("torn journal tail")
            record = json.loads(line)
            if (set(record) != {"sequence", "elapsed_ms", "kind", "data"}
                    or not isinstance(record["data"], dict)
                    or not isinstance(record["kind"], str)
                    or type(record["sequence"]) is not int
                    or record["sequence"] != len(records)
                    or type(record["elapsed_ms"]) is not int
                    or record["elapsed_ms"] < previous_ms):
                raise ValueError("journal order/shape")
            previous_ms = record["elapsed_ms"]
            records.append(record)
        except (ValueError, TypeError, KeyError) as exc:
            findings.append(str(exc))
            break
    # Every retained blob is hashed, including snapshot contents and orphan blobs
    # from a crash between blob commit and journal commit.
    try:
        blobs = sorted((root / "blobs").iterdir())
    except OSError as exc:
        blobs = []
        findings.append("blob directory unavailable: " + type(exc).__name__)
    for path in blobs:
        if path.is_symlink() or not path.is_file():
            findings.append("invalid blob: " + path.name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != path.name:
            findings.append("corrupt blob: " + path.name)
    def check_references(data):
        for key, reference in data.items():
            if key.endswith("_ref"):
                if (not isinstance(reference, str) or len(reference) != 70
                        or not reference.startswith("blobs/")
                        or any(c not in "0123456789abcdef" for c in reference[6:])
                        or not (root / reference).is_file()):
                    findings.append("missing/invalid blob reference")
    for record in records:
        check_references(record["data"])
        if record["kind"] == "workspace.snapshot":
            reference = record["data"].get("blob_ref")
            # Never follow an unchecked reference out of the evidence root.
            if (isinstance(reference, str) and len(reference) == 70
                    and reference.startswith("blobs/")
                    and all(c in "0123456789abcdef" for c in reference[6:])
                    and (root / reference).is_file()):
                try:
                    entries = json.loads((root / reference).read_bytes())
                    for entry in entries.values():
                        check_references(entry)
                except (ValueError, TypeError, AttributeError):
                    findings.append("invalid workspace snapshot")
    terminal = records[-1] if records and records[-1]["kind"] == "attempt.finished" else None
    if terminal is None:
        findings.append("attempt has no terminal record")
    elif terminal["data"].get("status") not in ("complete", "incomplete", "interrupted"):
        findings.append("invalid terminal status")
    if not records or records[0]["kind"] != "attempt.started":
        findings.append("attempt has no start record")
    return dict(records=records, findings=findings,
                status=terminal["data"]["status"] if terminal and not findings else "incomplete")


def collect_mock_attempt(directory, workspace, manifest, source, decode, *, enabled=False):
    """Capture one synthetic attempt, with no retries or native launch capability.

    source(journal) yields (channel, bytes). It must capture outbound bytes via
    journal.raw before sending, and capture transport stderr as well. decode
    receives (bytes, blob_ref, elapsed_ms) only and returns event/usage lists.
    A receive-stream EOF completes capture, not a behavior gate. Exceptions are
    re-raised after partial retention. SIGKILL/disk failure require recovery.
    """
    if enabled is not True:
        raise RuntimeError("capture disabled")
    identity = manifest["trajectory"]
    if identity.get("mode") != "mock":
        raise ValueError("native adapter is not qualified")
    root = Path(workspace).resolve(strict=True)
    destination = Path(directory).resolve()
    if destination == root or root in destination.parents or destination in root.parents:
        raise ValueError("evidence and workspace must be separate")
    trace = dict(identity, capture_status="incomplete", capture_elapsed_ms=0,
                 events=[], usage=[])
    parse_trajectory(trace)  # Preflight before starting the source.
    journal = AttemptJournal(destination, manifest)
    failure = None
    try:
        journal.snapshot(root, "before")
        for channel, payload in source(journal):
            reference, elapsed = journal.raw(channel, payload)
            if channel != "receive":
                continue
            decoded = decode(payload, reference, elapsed)
            # Retain even invalid decoder output before attempting shape checks.
            decoded_ref = journal.blob(_json(decoded))
            journal.append("decoded", {"blob_ref": decoded_ref})
            if not isinstance(decoded, dict) or set(decoded) != {"events", "usage"}:
                raise ValueError("decoder must return events and usage")
            candidate = dict(trace, events=trace["events"] + decoded["events"],
                             usage=trace["usage"] + decoded["usage"])
            parse_trajectory(candidate)
            # Primary backing must be the just-committed raw record. Other
            # evidence references are adapter responsibilities, not inferred.
            for item in decoded["events"] + decoded["usage"]:
                if item["raw_ref"] != reference:
                    raise ValueError("decoder raw reference is not captured input")
            for event in decoded["events"]:
                if event["elapsed_ms"] != elapsed or event["origin"] != "mock":
                    raise ValueError("synthetic event clock/origin mismatch")
            trace = candidate
        trace["capture_status"] = "complete"
    except BaseException as exc:
        failure = exc
        trace["capture_status"] = "interrupted" if isinstance(exc, (KeyboardInterrupt, TimeoutError)) else "incomplete"
        journal.append("capture.error", {"type": type(exc).__name__, "message": str(exc)})
    finally:
        try:
            journal.snapshot(root, "after")
        except BaseException as exc:
            trace["capture_status"] = "incomplete"
            journal.append("snapshot.error", {"type": type(exc).__name__, "message": str(exc)})
            if failure is None:
                failure = exc
        trace["capture_elapsed_ms"] = journal.elapsed_ms()
        parsed = parse_trajectory(trace)
        findings = [asdict(item) for item in integrity_findings(parsed)]
        result = dict(instrumentation=INSTRUMENTATION, trajectory=trace,
                      findings=findings, usage_totals=usage_totals(parsed))
        result_ref = journal.blob(_json(result))
        journal.append("attempt.finished", {"status": trace["capture_status"],
                                             "result_ref": result_ref})
        journal.closed = True
    if failure is not None:
        raise failure
    return result
