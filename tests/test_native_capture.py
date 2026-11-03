from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessmith.native_capture import AttemptJournal, collect_mock_attempt, recover_attempt


def manifest():
    return {"trajectory": dict(schema_version=1, trajectory_id="mock-attempt",
        target="codex", surface="synthetic", host_version="test-only", mode="mock")}


def decode(payload, reference, elapsed):
    value = json.loads(payload)
    for item in value["events"] + value["usage"]:
        item["raw_ref"] = reference
    for item in value["events"]:
        item["elapsed_ms"] = elapsed
    return value


def records():
    def event(kind, identifier, data, turn=None, cause=None):
        return dict(kind=kind, event_id=identifier, sequence=0, elapsed_ms=0,
                    thread_id="thread", turn_id=turn, causal_event_id=cause,
                    origin="mock", raw_ref="placeholder", data=data)
    events = [event("thread.started", "thread", {}),
              event("permission.snapshot", "permissions", dict(policy_id="mock",
                    allow_read=["workspace"], allow_write=["workspace"],
                    network=False, approval_policy="never")),
              event("turn.started", "start", dict(turn_role="task", prompt_ref="synthetic-prompt"), "turn"),
              event("turn.completed", "end", dict(status="completed"), "turn", "start")]
    for index, item in enumerate(events):
        item["sequence"] = index
    usage = [dict(interval_id="usage", thread_id="thread", meter_id="mock",
                  counter_epoch="fresh", basis="delta", baseline_reason="request_delta",
                  work_ids=["start"], raw_ref="placeholder", normalization_ref="synthetic-policy",
                  unavailable_reason=None, baseline=None, final=dict(input_tokens=10,
                  cached_input_tokens=2, cache_write_input_tokens=0,
                  output_tokens=3, reasoning_output_tokens=1))]
    return {"events": events, "usage": usage}


class NativeCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "target").write_bytes(b"original\n")
        self.destination = self.root / "attempt"

    def collect(self, source, decoder=decode, **options):
        return collect_mock_attempt(self.destination, self.workspace, manifest(),
                                    source, decoder, enabled=True, **options)

    def result(self):
        recovered = recover_attempt(self.destination)
        ref = recovered["records"][-1]["data"]["result_ref"]
        return json.loads((self.destination / ref).read_bytes())

    def test_disabled_and_native_fail_before_source_or_directory(self):
        def source(journal):
            self.fail("source must not run")
        with self.assertRaises(RuntimeError):
            collect_mock_attempt(self.destination, self.workspace, manifest(), source, decode)
        value = manifest()
        value["trajectory"]["mode"] = "native"
        with self.assertRaises(ValueError):
            collect_mock_attempt(self.destination, self.workspace, value, source, decode, enabled=True)
        self.assertFalse(self.destination.exists())

    def test_raw_is_durable_before_decoder_and_complete_usage(self):
        payload = json.dumps(records()).encode()
        def decoder(raw, reference, elapsed):
            self.assertEqual(payload, (self.destination / reference).read_bytes())
            recovered = recover_attempt(self.destination)
            self.assertEqual("raw", recovered["records"][-1]["kind"])
            return decode(raw, reference, elapsed)
        result = self.collect(lambda j: iter([("receive", payload)]), decoder)
        self.assertEqual([], result["findings"])
        self.assertEqual(10, result["usage_totals"]["input_tokens"])
        self.assertEqual("complete", recover_attempt(self.destination)["status"])

    def test_malformed_raw_bytes_and_stderr_survive_parse_failure(self):
        payload = b"\xffnot-json\r\n"
        with self.assertRaises(ValueError):
            self.collect(lambda j: iter([("stderr", b"diagnostic\n"), ("receive", payload)]))
        recovered = recover_attempt(self.destination)
        raw = [r for r in recovered["records"] if r["kind"] == "raw"]
        self.assertEqual(2, len(raw))
        self.assertEqual(payload, (self.destination / raw[-1]["data"]["blob_ref"]).read_bytes())
        self.assertEqual("incomplete", recovered["status"])
        self.assertIsNone(self.result()["usage_totals"])

    def test_partial_events_and_after_state_survive_timeout_interrupt_and_exception(self):
        for error in (TimeoutError, KeyboardInterrupt, RuntimeError):
            with self.subTest(error=error):
                self.destination = self.root / error.__name__
                def source(journal):
                    value = records()
                    value["events"] = value["events"][:3]
                    value["usage"] = []
                    yield "receive", json.dumps(value).encode()
                    (self.workspace / "target").write_bytes(b"partial edit\n")
                    raise error("injected")
                with self.assertRaises(error):
                    self.collect(source)
                result = self.result()
                self.assertEqual(3, len(result["trajectory"]["events"]))
                self.assertIsNone(result["usage_totals"])
                snapshots = [r for r in recover_attempt(self.destination)["records"]
                             if r["kind"] == "workspace.snapshot"]
                self.assertEqual(["before", "after"], [r["data"]["phase"] for r in snapshots])

    def test_snapshot_retains_bytes_modes_links_and_empty_directories(self):
        (self.workspace / "empty").mkdir()
        (self.workspace / "link").symlink_to("/does/not/exist")
        (self.workspace / "target").chmod(0o751)
        self.collect(lambda j: iter([]))
        record = next(r for r in recover_attempt(self.destination)["records"]
                      if r["kind"] == "workspace.snapshot")
        snapshot = json.loads((self.destination / record["data"]["blob_ref"]).read_bytes())
        self.assertEqual(0o751, snapshot["target"]["mode"])
        self.assertEqual("/does/not/exist", snapshot["link"]["target"])
        self.assertEqual("directory", snapshot["empty"]["kind"])
        self.assertEqual(b"original\n", (self.destination / snapshot["target"]["blob_ref"]).read_bytes())

    def test_bad_backing_and_native_origin_do_not_enter_typed_trace(self):
        for field, value in (("raw_ref", "invented"), ("origin", "native"), ("elapsed_ms", -1)):
            self.destination = self.root / field
            def bad_decoder(payload, reference, elapsed):
                result = decode(payload, reference, elapsed)
                result["events"][0][field] = value
                return result
            with self.assertRaises(ValueError):
                self.collect(lambda j: iter([("receive", json.dumps(records()).encode())]), bad_decoder)
            self.assertEqual([], self.result()["trajectory"]["events"])
            self.assertTrue(any(r["kind"] == "decoded" for r in recover_attempt(self.destination)["records"]))

    def test_unknown_usage_and_bad_lifecycle_prevent_totals(self):
        for mutation in (lambda v: v["usage"][0]["final"].update(cache_write_input_tokens=None),
                         lambda v: v["events"][-1].update(causal_event_id="missing")):
            value = records()
            mutation(value)
            self.destination = self.root / ("case" + str(len(list(self.root.iterdir()))))
            result = self.collect(lambda j: iter([("receive", json.dumps(value).encode())]))
            self.assertTrue(result["findings"])
            self.assertIsNone(result["usage_totals"])

    def test_attempt_cannot_be_reused_or_nested_in_workspace(self):
        self.collect(lambda j: iter([]))
        with self.assertRaises(FileExistsError):
            self.collect(lambda j: self.fail("no retry"))
        self.destination = self.workspace / "evidence"
        with self.assertRaises(ValueError):
            self.collect(lambda j: self.fail("must not launch"))

    def test_process_exit_retains_consumed_attempt_and_exact_raw(self):
        script = """
import os, sys
from harnessmith.native_capture import AttemptJournal
j = AttemptJournal(sys.argv[1], {'mode': 'mock'})
j.raw('receive', b'partial raw\\xff')
os._exit(17)
"""
        completed = subprocess.run([sys.executable, "-c", script, str(self.destination)], check=False)
        self.assertEqual(17, completed.returncode)
        recovered = recover_attempt(self.destination)
        self.assertEqual("incomplete", recovered["status"])
        self.assertEqual(b"partial raw\xff", (self.destination / recovered["records"][-1]["data"]["blob_ref"]).read_bytes())

    def test_recovery_reports_torn_tail_and_corruption_without_rewriting(self):
        journal = AttemptJournal(self.destination, manifest())
        reference, _ = journal.raw("receive", b"raw")
        path = self.destination / "journal.jsonl"
        with path.open("ab") as stream:
            stream.write(b'{"torn":')
        (self.destination / reference).write_bytes(b"corrupt")
        before = path.read_bytes()
        recovered = recover_attempt(self.destination)
        self.assertEqual(before, path.read_bytes())
        self.assertTrue(any("torn" in f for f in recovered["findings"]))
        self.assertTrue(any("corrupt" in f for f in recovered["findings"]))

    def test_special_file_snapshot_failure_is_retained_without_source(self):
        os.mkfifo(self.workspace / "pipe")
        with self.assertRaises(ValueError):
            self.collect(lambda j: self.fail("source must not run"))
        self.assertEqual("incomplete", self.result()["trajectory"]["capture_status"])

    def test_missing_snapshot_content_invalidates_recovery(self):
        self.collect(lambda j: iter([]))
        record = next(r for r in recover_attempt(self.destination)["records"]
                      if r["kind"] == "workspace.snapshot")
        snapshot = json.loads((self.destination / record["data"]["blob_ref"]).read_bytes())
        (self.destination / snapshot["target"]["blob_ref"]).unlink()
        recovered = recover_attempt(self.destination)
        self.assertEqual("incomplete", recovered["status"])
        self.assertIn("missing/invalid blob reference", recovered["findings"])


if __name__ == "__main__":
    unittest.main()
