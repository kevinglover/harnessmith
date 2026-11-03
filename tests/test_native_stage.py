from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

from harnessmith import native_capture, native_contract, native_stage, native_transport
from harnessmith.native_capture import recover_attempt
from harnessmith.native_stage import pin, run_mock_stage


class SyntheticObserver:
    """Test-only envelope; never a host-native normalizer."""
    def __init__(self, policy):
        self.usage = []

    def observe(self, direction, message, reference, elapsed):
        if direction == "send":
            return {"events": [], "usage": []}
        value = copy.deepcopy(message.get("fixture", {"events": [], "usage": []}))
        for event in value["events"]:
            event.update(raw_ref=reference, elapsed_ms=elapsed)
        for interval in value["usage"]:
            interval["raw_ref"] = reference
        return value

    def finish(self):
        return []


def fixture():
    def event(kind, identity, sequence, data, turn=None, cause=None):
        return dict(kind=kind, event_id=identity, sequence=sequence, elapsed_ms=0,
                    thread_id="thread", turn_id=turn, causal_event_id=cause,
                    origin="mock", raw_ref="placeholder", data=data)
    events = [event("thread.started", "thread", 0, {}),
        event("permission.snapshot", "permissions", 1, dict(policy_id="synthetic",
            allow_read=["workspace"], allow_write=[], network=False, approval_policy="never")),
        event("turn.started", "turn", 2, dict(turn_role="task", prompt_ref="synthetic"), "task"),
        event("turn.completed", "end", 3, dict(status="completed"), "task", "turn")]
    usage = [dict(interval_id="usage", thread_id="thread", meter_id="fixture",
        counter_epoch="fresh", basis="delta", baseline_reason="request_delta",
        work_ids=["turn"], raw_ref="placeholder", normalization_ref="synthetic-policy",
        unavailable_reason=None, baseline=None, final=dict(input_tokens=10,
        cached_input_tokens=0, cache_write_input_tokens=0, output_tokens=2, reasoning_output_tokens=0))]
    return dict(events=events, usage=usage)


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.policy = self.root / "policy.json"
        self.policy.write_text('{}')
        self.script = self.root / "server.py"
        self.write_server(fixture())
        self.destination = self.root / "stage"
        self.manifest = dict(schema_version=1, stage_id="offline", mode="mock",
            trajectory=dict(schema_version=1, target="codex", surface="synthetic",
                            host_version="test-only", mode="mock"),
            pins=[pin(native_stage.__file__, "stage"), pin(native_capture.__file__, "capture"),
                  pin(native_contract.__file__, "contract"), pin(native_transport.__file__, "transport"),
                  pin(__file__, "normalizer"), pin(sys.executable, "executable"),
                  pin(self.workspace, "fixture"), pin(self.script, "source"),
                  pin(self.policy, "policy"), pin(self.policy, "recipe"), pin(self.policy, "package")],
            attempts=[dict(id="first", workspace=str(self.workspace),
                command=[sys.executable, "-u", str(self.script)], env={},
                steps=[dict(send={"id": 1, "method": "test"}, until={"id": 1})])],
            ceilings=dict(attempts=1, threads=1, task_turns=1, deadline_seconds=2),
            normalization_policy={}, environment=dict(model="synthetic", effort="none",
                permissions={"synthetic": True}, resources={"concurrency": 1}, cache_policy="none"))

    def write_server(self, value):
        self.script.write_text("import sys,time\nsys.stdin.readline()\nprint(" +
            repr(json.dumps(dict(id=1, fixture=value))) + ", flush=True)\ntime.sleep(30)\n")

    def refresh(self):
        self.manifest["pins"] = [pin(p["path"], p["role"]) for p in self.manifest["pins"]]

    def run_stage(self):
        return run_mock_stage(self.destination, self.manifest, SyntheticObserver, enabled=True)

    def test_two_attempts_retained_before_advancing_and_no_reentry(self):
        second = copy.deepcopy(self.manifest["attempts"][0])
        second["id"] = "second"
        other = self.root / "other-workspace"
        other.mkdir()
        second["workspace"] = str(other)
        self.manifest["pins"].append(pin(other, "fixture"))
        self.manifest["attempts"].append(second)
        self.manifest["ceilings"].update(attempts=2, threads=2, task_turns=2)
        self.assertEqual("complete", self.run_stage()["status"])
        rows = recover_attempt(self.destination)["records"]
        self.assertEqual(["stage.slot_consumed", "stage.attempt_retained", "stage.slot_consumed", "stage.attempt_retained"],
                         [r["kind"] for r in rows if r["kind"].startswith("stage.")])
        with self.assertRaises(FileExistsError):
            self.run_stage()

    def test_disabled_and_native_fail_before_creating_evidence(self):
        with self.assertRaises(RuntimeError):
            run_mock_stage(self.destination, self.manifest, SyntheticObserver)
        self.manifest["mode"] = "native"
        with self.assertRaises(ValueError):
            self.run_stage()
        self.assertFalse(self.destination.exists())

    def test_drift_of_content_mode_missing_extra_file_is_rejected(self):
        for mutate in (lambda: (self.workspace / "extra").write_text("changed"),
                       lambda: self.script.chmod(0o700), lambda: self.policy.unlink()):
            with self.subTest(mutate=mutate):
                mutate()
                with self.assertRaises((ValueError, FileNotFoundError)):
                    self.run_stage()
                self.assertFalse(self.destination.exists())
                if not self.policy.exists():
                    self.policy.write_text('{}')
                self.refresh()

    def test_bad_counts_and_unpinned_instrument_fail_preflight(self):
        original = copy.deepcopy(self.manifest)
        for mutate in (lambda m: m["ceilings"].update(attempts=True),
                       lambda m: m["ceilings"].update(deadline_seconds=float('inf')),
                       lambda m: m.update(pins=[p for p in m["pins"] if p["role"] != "normalizer"])):
            self.manifest = copy.deepcopy(original)
            mutate(self.manifest)
            with self.assertRaises(ValueError):
                self.run_stage()
            self.assertFalse(self.destination.exists())

    def test_incomplete_usage_consumes_one_slot_and_stops_without_second(self):
        value = fixture()
        value["usage"] = []
        self.write_server(value)
        self.refresh()
        second = copy.deepcopy(self.manifest["attempts"][0])
        second["id"] = "second"
        other = self.root / "other-workspace"
        other.mkdir()
        second["workspace"] = str(other)
        self.manifest["pins"].append(pin(other, "fixture"))
        self.manifest["attempts"].append(second)
        self.manifest["ceilings"].update(attempts=2, threads=2, task_turns=2)
        with self.assertRaisesRegex(ValueError, "measurement incomplete"):
            self.run_stage()
        self.assertFalse((self.destination / "second").exists())
        self.assertTrue((self.destination / "first" / "journal.jsonl").exists())
        self.assertEqual("incomplete", recover_attempt(self.destination)["status"])

    def test_timeout_retains_slot_partial_attempt_and_process_cleanup(self):
        self.script.write_text("import time\ntime.sleep(30)\n")
        self.refresh()
        self.manifest["ceilings"]["deadline_seconds"] = .15
        with self.assertRaises(TimeoutError):
            self.run_stage()
        attempt = recover_attempt(self.destination / "first")
        self.assertEqual("interrupted", attempt["status"])
        self.assertTrue(any(r["kind"] == "transport.closed" for r in attempt["records"]))
        self.assertEqual("incomplete", recover_attempt(self.destination)["status"])

    def test_malformed_protocol_retained_and_stops(self):
        self.script.write_text("import os,time\nos.write(1,b'bad-json\\n')\ntime.sleep(30)\n")
        self.refresh()
        with self.assertRaises(ValueError):
            self.run_stage()
        rows = recover_attempt(self.destination / "first")["records"]
        self.assertTrue(any(r["kind"] == "transport.frame" for r in rows))
        self.assertEqual("incomplete", recover_attempt(self.destination)["status"])

    def test_observed_ceiling_violation_retains_offending_trace(self):
        value = fixture()
        value["events"].insert(1, dict(value["events"][0], event_id="other", thread_id="other", sequence=1))
        self.write_server(value)
        self.refresh()
        with self.assertRaisesRegex(ValueError, "observed stage count"):
            self.run_stage()
        rows = recover_attempt(self.destination / "first")["records"]
        result = json.loads((self.destination / "first" / rows[-1]["data"]["result_ref"]).read_bytes())
        self.assertEqual(5, len(result["trajectory"]["events"]))

    def test_previous_output_changes_do_not_invalidate_fresh_attempt_fixture(self):
        self.script.write_text("from pathlib import Path\n" + self.script.read_text().replace(
            "sys.stdin.readline()", "sys.stdin.readline(); Path('output').write_text('artifact')"))
        self.refresh()
        second = copy.deepcopy(self.manifest["attempts"][0])
        second["id"] = "second"
        other = self.root / "other"
        other.mkdir()
        second["workspace"] = str(other)
        self.manifest["pins"].append(pin(other, "fixture"))
        self.manifest["attempts"].append(second)
        self.manifest["ceilings"].update(attempts=2, threads=2, task_turns=2)
        self.assertEqual("complete", self.run_stage()["status"])
        self.assertEqual("artifact", (other / "output").read_text())

    def test_changed_normalization_policy_is_not_accepted_by_old_pin(self):
        self.manifest["normalization_policy"] = {"changed": True}
        with self.assertRaisesRegex(ValueError, "policy pin"):
            self.run_stage()
        self.assertFalse(self.destination.exists())

    def test_last_attempt_immutable_input_drift_stops_stage_after_retention(self):
        self.script.write_text("from pathlib import Path\n" + self.script.read_text().replace(
            "sys.stdin.readline()", "sys.stdin.readline(); Path(" + repr(str(self.policy)) + ").write_text('changed')"))
        self.refresh()
        with self.assertRaisesRegex(ValueError, "pinned input changed"):
            self.run_stage()
        rows = recover_attempt(self.destination)["records"]
        self.assertTrue(any(r["kind"] == "stage.attempt_retained" for r in rows))
        self.assertEqual("incomplete", recover_attempt(self.destination)["status"])

    def test_controller_crash_leaves_consumed_slot_without_replacement(self):
        self.script.write_text("import os,signal\nos.kill(os.getppid(),signal.SIGKILL)\nos._exit(0)\n")
        self.refresh()
        prepared = self.root / "manifest.json"
        prepared.write_text(json.dumps(self.manifest))
        command = """
import json,sys
from harnessmith.native_stage import run_mock_stage
from tests.test_native_stage import SyntheticObserver
run_mock_stage(sys.argv[1], json.load(open(sys.argv[2])), SyntheticObserver, enabled=True)
"""
        completed = subprocess.run([sys.executable, "-c", command, str(self.destination), str(prepared)],
                                   cwd=Path(__file__).resolve().parents[1], timeout=10, capture_output=True)
        self.assertEqual(-9, completed.returncode, completed.stderr.decode())
        recovered = recover_attempt(self.destination)
        self.assertEqual("incomplete", recovered["status"])
        self.assertEqual(1, sum(r["kind"] == "stage.slot_consumed" for r in recovered["records"]))
        self.assertEqual("incomplete", recover_attempt(self.destination / "first")["status"])

    def test_codex_observer_transport_keeps_permission_gap_open(self):
        import hashlib
        import shlex
        from harnessmith import codex_native_observer
        package = self.root / "package"
        package.mkdir()
        skill = package / "SKILL.md"
        skill.write_text("synthetic instructions\n")
        policy = dict(version=codex_native_observer.INSTRUMENTATION,
            accounting="fresh-cumulative-only", packages=[dict(root=str(skill), skill_id="synthetic",
                root_sha256=hashlib.sha256(skill.read_bytes()).hexdigest(),
                package_sha256=codex_native_observer.package_digest(package))])
        self.policy.write_text(json.dumps(policy))
        item = dict(type="commandExecution", id="command", command="cat " + shlex.quote(str(skill)),
                    status="inProgress", exitCode=None, aggregatedOutput=None)
        messages = [
            dict(id=2, result={"turn": {"id": "turn"}}),
            dict(method="turn/started", params=dict(threadId="thread", turn={"id": "turn"})),
            dict(method="item/started", params=dict(threadId="thread", turnId="turn", item=item)),
            dict(method="item/completed", params=dict(threadId="thread", turnId="turn",
                 item=dict(item, status="completed", exitCode=0, aggregatedOutput=skill.read_text()))),
            dict(method="thread/tokenUsage/updated", params=dict(threadId="thread", turnId="turn",
                 tokenUsage={"total": dict(inputTokens=10, cachedInputTokens=0, cacheWriteInputTokens=0,
                     outputTokens=2, reasoningOutputTokens=0), "last": {}})),
            dict(method="turn/completed", params=dict(threadId="thread", turn={"id": "turn", "status": "completed"})),
        ]
        initial = [dict(method="thread/started", params={"thread": {"id": "thread"}}),
                   dict(id=1, result={"thread": {"id": "thread"}})]
        self.script.write_text("import sys,time\nsys.stdin.readline()\n" +
            "\n".join("print(" + repr(json.dumps(m)) + ",flush=True)" for m in initial) +
            "\nsys.stdin.readline()\n" +
            "\n".join("print(" + repr(json.dumps(m)) + ",flush=True)" for m in messages) + "\ntime.sleep(30)\n")
        self.manifest["normalization_policy"] = policy
        self.manifest["pins"] = [p for p in self.manifest["pins"] if p["role"] not in {"normalizer", "package"}]
        self.manifest["pins"].extend([pin(codex_native_observer.__file__, "normalizer"), pin(package, "package")])
        self.manifest["attempts"][0]["steps"] = [
            dict(send={"id": 1, "method": "thread/start", "params": {}}, until={"id": 1}),
            dict(send={"id": 2, "method": "turn/start", "params": dict(threadId="thread",
                input=[dict(type="skill", name="synthetic", path=str(skill))])}, until={"method": "turn/completed"})]
        self.refresh()
        with self.assertRaisesRegex(ValueError, "measurement incomplete"):
            run_mock_stage(self.destination, self.manifest, codex_native_observer.CodexObserver, enabled=True)
        rows = recover_attempt(self.destination / "first")["records"]
        result = json.loads((self.destination / "first" / rows[-1]["data"]["result_ref"]).read_bytes())
        self.assertIn("invocation.observed", [e["kind"] for e in result["trajectory"]["events"]])
        self.assertEqual({"permission-missing"}, {f["code"] for f in result["findings"]})
        self.assertIsNone(result["usage_totals"])


if __name__ == "__main__":
    unittest.main()
