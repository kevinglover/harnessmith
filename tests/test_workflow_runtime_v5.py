"""Offline v5 collection through a local fake stdio server; no provider calls."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from harnessmith.workflow_runtime_v5 import ORDER, collect_session, run_batch
from tests.test_workflow_runtime_v4 import fake_source as v4_fake_source


ROOT = Path(__file__).resolve().parents[1]


def fake_source():
    source = v4_fake_source().replace("mock-codex-workflow-4", "mock-codex-workflow-5")
    marker = "    def write():"
    assert source.count(marker) == 1
    source = source.replace(marker,
        "    if MODE=='unsupported-error-story':\n"
        "        item({'type':'agentMessage','phase':'commentary',\n"
        "              'text':'The first adapter invocation returned “Unknown synthetic command” for my initially inferred ID.'})\n"
        + marker)
    source = source.replace(
        "    output=output.replace('4 new items', '**four** unchecked requirements-quality questions')",
        "    output=output.replace('4 new items', 'four item checklist' if MODE=='singular-count' else '**four** unchecked requirements-quality questions')",
    )
    native_write = (
        "    item({'type':'fileChange','status':'completed','changes':[{'path':str(target),\n"
        "          'kind':{'type':'update' if target.exists() else 'add'},'diff':content}]}, write)"
    )
    assert source.count(native_write) == 1
    source = source.replace(native_write,
        "    if MODE=='internal-append' and manifest['case']=='append':\n"
        "        import shlex\n"
        "        addition=content.encode()[len(base.encode()):]\n"
        "        script=('from pathlib import Path; p=Path('+repr(manifest['target'])+'); ' +\n"
        "                'old=p.read_bytes(); add='+repr(addition)+'; p.open(\"ab\").write(add); ' +\n"
        "                'new=p.read_bytes(); assert new == old + add; print(new.decode())')\n"
        "        item({'type':'commandExecution','command':'python3 -c '+shlex.quote(script),\n"
        "              'cwd':str(workspace),'status':'completed','exitCode':0,'commandActions':[],\n"
        "              'aggregatedOutput':content+chr(10)}, lambda:target.open('ab').write(addition))\n"
        "    else:\n" + "\n".join("    "+line for line in native_write.splitlines()))
    source = source.replace(
        "    command('cat '+manifest['target'],[manifest['target']])",
        "    if MODE!='internal-append' or manifest['case']!='append':\n"
        "        command('cat '+manifest['target'],[manifest['target']])",
    )
    return source


class WorkflowRuntimeV5Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.auth = self.root / "auth.json"
        self.auth.write_text("{}")

    def run_fake(self, mode="good", timeout=10):
        executable = self.root / ("fake-" + mode)
        executable.write_text(
            "#!" + sys.executable + "\nMODE=" + repr(mode) + "\n" + fake_source()
        )
        executable.chmod(0o755)
        output = self.root / mode
        report = run_batch(
            ROOT, output, executable=executable, auth_file=self.auth,
            enabled=True, timeout=timeout, evidence_kind="mock",
        )
        return report, output, executable

    def test_two_slots_use_new_parser_checker_and_pin_all_dependencies(self):
        report, output, executable = self.run_fake()
        self.assertEqual(["append-router-v5", "hooks-router-v5"], list(ORDER))
        self.assertEqual(list(ORDER), [r["session_id"] for r in report["results"]])
        self.assertEqual(5, report["schema_version"])
        self.assertEqual(2, report["approved_session_count"])
        self.assertEqual(0, report["retries"])
        self.assertEqual([], report["unattempted"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertTrue(all(r["automated_checks_passed"] for r in report["results"]), report)
        environment = json.loads((output / "environment.json").read_text())
        self.assertEqual("codex-workflow-stdio-v5", environment["instrumentation"])
        self.assertEqual("mock", environment["evidence_kind"])
        for name, digest in environment["collector_files"].items():
            data = (output / "instrument" / name).read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(data, (ROOT / "harnessmith" / name).read_bytes())
        self.assertIn("workflow_trace_v4.py", environment["collector_files"])
        self.assertIn("workflow_trace_v3.py", environment["collector_files"])
        self.assertIn("workflow_fidelity_v4.py", environment["collector_files"])
        self.assertIn("workflow_fidelity_v3.py", environment["collector_files"])
        for sid in ORDER:
            directory = output / sid
            observation = json.loads((directory / "observation.json").read_text())
            checks = json.loads((directory / "checks.json").read_text())
            self.assertEqual(4, observation["schema_version"])
            self.assertEqual(5, checks["checker_version"])
            self.assertFalse(checks["historical_results_regraded"])
            self.assertEqual("offline-simulation", observation["evidence_kind"])
            self.assertFalse(Path(observation["returned_configuration"]["testAuthHome"]).exists())
            raw = [json.loads(line) for line in (directory / "raw/events.jsonl").read_text().splitlines()]
            for method in ("thread/start", "turn/start"):
                self.assertEqual(1, sum(
                    r["direction"] == "send" and r["message"].get("method") == method
                    for r in raw
                ))
            self.assertTrue((directory / "before-inventory.json").exists())
            self.assertTrue((directory / "after-inventory.json").exists())
        with self.assertRaises(FileExistsError):
            collect_session(output / ORDER[0], executable=executable, auth_file=self.auth)
        self.assertFalse(list(output.rglob("auth.json")))

    def test_promised_post_and_failed_discovery_are_retained_without_replacement(self):
        for mode, failed_check in (
            ("promised-post", "hook-announcements"),
            ("failed-discovery", "successful-events"),
        ):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode)
                self.assertEqual(2, report["attempted_session_count"])
                self.assertEqual(0, report["retries"])
                self.assertEqual([], report["unattempted"])
                self.assertTrue(report["results"][0]["automated_checks_passed"])
                self.assertFalse(report["results"][1]["automated_checks_passed"])
                self.assertFalse(any(r["stop_batch"] for r in report["results"]))
                checks = json.loads((output / ORDER[1] / "checks.json").read_text())
                named = {c["name"]: c["passed"] for c in checks["dimensions"]["workflow"]["checks"]}
                self.assertFalse(named[failed_check])
                self.assertTrue(named["final-artifact-verification"])
                self.assertEqual(2, len(list(output.glob("*/result.json"))))

    def test_instrumentation_defect_stops_remaining_slot_and_retains_attempt(self):
        for mode in ("missing-usage", "wrong-model", "rerouted", "timeout"):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode, timeout=0.3 if mode == "timeout" else 10)
                self.assertEqual(1, report["attempted_session_count"])
                self.assertEqual(list(ORDER[1:]), report["unattempted"])
                self.assertEqual(0, report["retries"])
                first = output / ORDER[0]
                self.assertTrue((first / "raw/events.jsonl").is_file())
                self.assertTrue((first / "after-inventory.json").is_file())
                self.assertFalse((output / ORDER[1] / "attempt.json").exists())
                if mode == "wrong-model":
                    self.assertNotIn('"method": "turn/start"', (first / "raw/events.jsonl").read_text())

    def test_normalizer_exception_retains_schema_four_and_written_artifact(self):
        with mock.patch("harnessmith.workflow_runtime_v5.normalize_events", side_effect=ValueError("decoder failed")):
            report, output, _ = self.run_fake()
        self.assertEqual(1, report["attempted_session_count"])
        first = output / ORDER[0]
        self.assertTrue((first / "after/specs/001-invitations/checklists/security.md").exists())
        self.assertTrue((first / "raw/events.stdout").exists())
        observation = json.loads((first / "observation.json").read_text())
        self.assertEqual(4, observation["schema_version"])
        self.assertEqual("ValueError", report["results"][0]["collector_error"]["type"])

    def test_internal_append_readback_passes_through_collector_without_external_read(self):
        report, output, _ = self.run_fake("internal-append")
        self.assertTrue(all(r["automated_checks_passed"] for r in report["results"]), report)
        directory = output / ORDER[0]
        obs = json.loads((directory / "observation.json").read_text())
        self.assertTrue(any(e.get("read_after_write") for e in obs["events"]))
        self.assertTrue(any(e.get("write_mode") == "append" for e in obs["events"]))
        before = (directory / "before/specs/001-invitations/checklists/security.md").read_bytes()
        after = (directory / "after/specs/001-invitations/checklists/security.md").read_bytes()
        self.assertTrue(after.startswith(before))
        self.assertGreater(len(after), len(before))

    def test_singular_modifier_count_is_accepted_in_completed_report(self):
        report, output, _ = self.run_fake("singular-count")
        self.assertTrue(all(r["automated_checks_passed"] for r in report["results"]), report)
        obs = json.loads((output / ORDER[1] / "observation.json").read_text())
        self.assertIn("four item checklist", obs["final_output"])

    def test_unsupported_commentary_error_story_fails_without_replacement(self):
        report, output, _ = self.run_fake("unsupported-error-story")
        self.assertEqual(2, report["attempted_session_count"])
        self.assertEqual(0, report["retries"])
        self.assertFalse(any(r["automated_checks_passed"] for r in report["results"]))
        self.assertFalse(any(r["stop_batch"] for r in report["results"]))
        for sid in ORDER:
            obs = json.loads((output / sid / "observation.json").read_text())
            self.assertIn("Unknown synthetic command", " ".join(obs["commentary"]))
            checks = json.loads((output / sid / "checks.json").read_text())
            self.assertEqual("pass", checks["dimensions"]["content"]["automated_status"])
            self.assertEqual("fail", checks["dimensions"]["workflow"]["automated_status"])
            self.assertEqual("pending", checks["dimensions"]["workflow"]["review_status"])

    def test_disabled_and_invalid_timeout_never_prepare_or_spawn(self):
        output = self.root / "disabled"
        with mock.patch("harnessmith.workflow_runtime_v5.prepare_pilot") as prepare:
            with self.assertRaises(ValueError):
                run_batch(ROOT, output, executable="/unused", auth_file=self.auth)
            for timeout in (0, 181):
                with self.assertRaises(ValueError):
                    run_batch(ROOT, output, executable="/unused", auth_file=self.auth, enabled=True, timeout=timeout)
            prepare.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
