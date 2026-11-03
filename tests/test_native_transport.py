from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import time
import unittest

from harnessmith.native_capture import AttemptJournal, recover_attempt
from harnessmith.native_transport import StdioCapture


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = AttemptJournal(self.root / "attempt", {"mode": "mock"})

    def start(self, script, **options):
        return StdioCapture(self.journal, [sys.executable, "-u", "-c", script],
                            cwd=self.root, env={}, timeout=options.pop("timeout", 3), **options)

    def rows(self):
        return recover_attempt(self.journal.directory)["records"]

    def test_bidirectional_exact_chunks_and_concurrent_stderr(self):
        with self.start("import os,sys; os.write(2,b'diagnostic\\xff'); print(sys.stdin.readline().strip())") as client:
            sent = client.send({"id": 1, "method": "test"})
            self.assertEqual({"id": 1, "method": "test"}, client.receive().message())
        self.assertEqual({"id": 1, "method": "test"}, sent.message())
        raw = [r for r in self.rows() if r["kind"] == "raw"]
        stderr = b"".join((self.journal.directory / r["data"]["blob_ref"]).read_bytes()
                          for r in raw if r["data"]["channel"] == "stderr")
        self.assertEqual(b"diagnostic\xff", stderr)
        sequences = [r["sequence"] for r in self.rows()]
        self.assertEqual(list(range(len(sequences))), sequences)

    def test_readers_capture_while_consumer_is_idle(self):
        with self.start("import os,time; os.write(1,b'{\"id\":1}\\n'); os.write(2,b'retained'); time.sleep(2)") as client:
            until = time.monotonic() + 1
            while not any(r["kind"] == "transport.frame" for r in self.rows()) and time.monotonic() < until:
                time.sleep(.01)
            self.assertTrue(any(r["kind"] == "transport.frame" for r in self.rows()))
            self.assertEqual(1, client.receive().message()["id"])

    def test_malformed_frame_is_retained_before_parse(self):
        with self.start("import os,time; os.write(1,b'\\xffbad\\n'); time.sleep(2)") as client:
            frame = client.receive()
            self.assertEqual(b"\xffbad\n", (self.journal.directory / frame.raw_ref).read_bytes())
            with self.assertRaises(ValueError):
                frame.message()

    def test_timeout_kills_owned_process_group(self):
        client = self.start("import time; time.sleep(30)", timeout=.15)
        with self.assertRaises(TimeoutError):
            with client:
                client.receive()
        self.assertIsNotNone(client.process.returncode)
        self.assertTrue(all(not r.is_alive() for r in client.readers))

    def test_startup_failure_is_retained(self):
        with self.assertRaises(FileNotFoundError):
            StdioCapture(self.journal, ["/missing/executable"], cwd=self.root, env={}, timeout=1)
        self.assertEqual("transport.start_failed", self.rows()[-1]["kind"])

    def test_partial_frame_and_non_object_are_errors(self):
        with self.assertRaises(ValueError):
            with self.start("import os; os.write(1,b'{\"id\":1}')") as client:
                client.receive()
        self.assertTrue(any(r["kind"] == "transport.truncated" for r in self.rows()))

    def test_no_newline_stream_is_bounded_but_retained(self):
        with self.assertRaises(ValueError):
            with self.start("import os,time; os.write(1,b'x'*1024); time.sleep(2)", max_frame_bytes=32) as client:
                client.receive()
        raw = [r for r in self.rows() if r["kind"] == "raw"]
        self.assertEqual(b"x" * 1024, (self.journal.directory / raw[0]["data"]["blob_ref"]).read_bytes())

    def test_pending_overflow_fails_instead_of_dropping_evidence(self):
        import queue
        with self.assertRaises(queue.Full):
            with self.start("import os,time; os.write(1,b'{}\\n'*20); time.sleep(2)", max_pending_frames=1) as client:
                until = time.monotonic() + 1
                while client.errors.empty() and time.monotonic() < until:
                    time.sleep(.01)
                client.receive()

    def test_closed_stdout_with_surviving_child_is_cleaned_up(self):
        script = """
import os,time
if os.fork() == 0:
    time.sleep(30)
else:
    print('{}', flush=True)
    os._exit(0)
"""
        with self.start(script) as client:
            self.assertEqual({}, client.receive().message())
        self.assertTrue(all(not r.is_alive() for r in client.readers))

    def test_rejected_outbound_intent_is_retained_but_not_sent(self):
        def reject(frame):
            self.assertTrue((self.journal.directory / frame.raw_ref).exists())
            raise ValueError("unqualified request")
        with self.start("import sys,time; sys.stdin.readline(); print('received',flush=True); time.sleep(30)") as client:
            with self.assertRaisesRegex(ValueError, "unqualified"):
                client.send({"id": 1, "method": "unsafe"}, before_write=reject)
        self.assertFalse(any(r["kind"] == "transport.sent" for r in self.rows()))
        self.assertTrue(any(r["kind"] == "raw" and r["data"]["channel"] == "send" for r in self.rows()))


if __name__ == "__main__":
    unittest.main()
