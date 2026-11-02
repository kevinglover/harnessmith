"""Fresh v11 fake-server cases; no provider calls or historical trace replays."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from harnessmith.workflow_runtime_v10 import CONFIG as FROZEN_CONFIG
from harnessmith.workflow_runtime_v11 import CONFIG, ORDER, collect_session, run_batch
from tests.test_workflow_runtime_v10 import fake_source as previous_fake_source


ROOT = Path(__file__).resolve().parents[1]
POST = "fresh-post-generation-extension-checkpoint"


def fake_source():
    """Build a new synthetic stream; shell strings are emitted, never executed."""
    source = previous_fake_source().replace("mock-codex-workflow-10", "mock-codex-workflow-11")
    start, end = source.index("def probe(path):"), source.index("def hook(name):")
    source = source[:start] + r'''def probe(path, post=False):
    body="if test -f "+path+"; then cat "+path+"; else printf 'ABSENT\\n'; fi"
    output=(workspace/path).read_text() if (workspace/path).is_file() else 'ABSENT\n'
    if (MODE=='pre-null' and not post and path=='.specify/extensions.yml') or (MODE=='post-null' and post):
        body='if [ -f '+path+' ]; then cat '+path+'; else test ! -e '+path+'; fi'
        output=None
    if (MODE=='pre-guarded' and not post and path=='.specify/extensions.yml') or (MODE=='post-guarded' and post):
        body='if [ -f '+path+' ]; then cat '+path+'; else test ! -e '+path+' && echo ABSENT; fi'
    if MODE=='wrapped': body='/bin/zsh -c '+shlex.quote(body)
    if post and MODE=='post-mixed':
        body='cat specs/001-invitations/spec.md; '+body
        output=(workspace/'specs/001-invitations/spec.md').read_text()+output
    if post and MODE=='post-noisy': output='unproven\n'+output
    failed=post and MODE=='post-failed'
    item({'type':'commandExecution','command':body,'cwd':str(workspace),
          'status':'failed' if failed else 'completed','exitCode':1 if failed else 0,
          'commandActions':[], 'aggregatedOutput':output})
def absence():
    probe('.specify/extensions.yml')
''' + source[end:]
    old = "    if MODE=='sequential':"
    assert source.count(old) == 1
    source = source.replace(old, "    if MODE!='concurrent':")
    old = "    if MODE not in ('missing-read', 'internal-append') or manifest['case']!='append':"
    assert source.count(old) == 1
    source = source.replace(old, "    if MODE=='post-before-readback': probe('.specify/extensions.yml',post=True)\n" + old)
    old = "    if MODE!='legacy-null': absence()"
    assert source.count(old) == 1
    source = source.replace(old, "    if MODE not in ('missing-post','before-only','claimed-post','post-before-readback','post-late'):\n        probe('.specify/extensions.yml',post=True)\n    if MODE=='claimed-post': output+=' I checked extension configuration after generation; it remained absent.'")
    old = "    item({'type':'agentMessage','phase':'commentary' if MODE=='missing-final' else 'final_answer','text':output})"
    assert source.count(old) == 1
    source = source.replace(old, old + "\n    if MODE=='post-late': probe('.specify/extensions.yml',post=True)")
    return source


class WorkflowRuntimeV11Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.auth = self.root / "auth.json"
        self.auth.write_text("{}")

    def run_fake(self, mode="good", timeout=10):
        executable = self.root / ("fake-" + mode)
        executable.write_text("#!" + sys.executable + "\nMODE=" + repr(mode) + "\n" + fake_source())
        executable.chmod(0o755)
        output = self.root / mode
        report = run_batch(ROOT, output, executable=executable, auth_file=self.auth,
                           enabled=True, timeout=timeout, evidence_kind="mock")
        return report, output / ORDER[0], executable

    @staticmethod
    def read(directory, name):
        return json.loads((directory / name).read_text())

    def checks(self, directory):
        return {c["name"]: c["passed"] for c in
                self.read(directory, "checks.json")["dimensions"]["workflow"]["checks"]}

    def assert_retained_single_result(self, report, directory):
        self.assertEqual((1, 1, 0), tuple(report[k] for k in
                         ("approved_session_count", "attempted_session_count", "retries")))
        self.assertEqual([], report["unattempted"])
        self.assertFalse(report["eligible_for_promotion"])
        for name in ("attempt.json", "before-inventory.json", "after-inventory.json",
                     "raw/events.jsonl", "raw/events.stdout", "raw/events.stderr",
                     "observation.json", "result.json"):
            self.assertTrue((directory / name).is_file(), name)
        self.assertEqual(1, len(list(directory.parent.glob("*/attempt.json"))))
        self.assertEqual(1, len(list(directory.parent.glob("*/result.json"))))
        self.assertFalse(list(directory.parent.rglob("auth.json")))

    def test_direct_if_test_proofs_and_fresh_postcheck_reach_one_fixed_slot(self):
        report, directory, executable = self.run_fake()
        self.assertEqual(("append-router-v8-instrument-v11",), ORDER)
        self.assertEqual(FROZEN_CONFIG, CONFIG)
        self.assertEqual(11, report["schema_version"])
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        self.assert_retained_single_result(report, directory)
        obs = self.read(directory, "observation.json")
        checks = self.read(directory, "checks.json")
        self.assertEqual((10, 11), (obs["schema_version"], checks["checker_version"]))
        self.assertEqual("offline-simulation", obs["evidence_kind"])
        self.assertEqual([], obs["issues"])
        absent = [d for d in obs["diagnostics"] if d.get("certified_absence")]
        self.assertEqual(2, len(absent))
        self.assertTrue(all(d["absence_certificate"]["proof"] == "literal-test-f-printf" for d in absent))
        self.assertEqual(1, len(absent[-1]["absence_certificate"]["accounted_native_appends"]))
        self.assertTrue(any(e.get("conditional_read_certificate", {}).get("proof") == "literal-test-f-printf"
                            for e in obs["events"]))
        self.assertTrue(self.checks(directory)[POST])
        self.assertFalse(checks["historical_results_regraded"])
        self.assertFalse(Path(obs["returned_configuration"]["testAuthHome"]).exists())
        env = self.read(directory.parent, "environment.json")
        self.assertEqual("codex-workflow-stdio-v11", env["instrumentation"])
        self.assertEqual(23, len(env["collector_files"]))
        for name, digest in env["collector_files"].items():
            data = (directory.parent / "instrument" / name).read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(data, (ROOT / "harnessmith" / name).read_bytes())
        manifest = self.read(directory, "manifest.json")
        self.assertEqual("router-v8", manifest["strategy"])
        for name in manifest["provenance"]["package"]:
            self.assertEqual((ROOT / "evaluations/variants/speckit-checklist-router-v8" / name).read_bytes(),
                             (directory / "workspace/.agents/skills/speckit-checklist" / name).read_bytes())
        self.assertEqual((ROOT / "evaluations/workflow-fidelity/prompts/append.md").read_bytes(),
                         (directory / "prompt.md").read_bytes())
        raw = [json.loads(s) for s in (directory / "raw/events.jsonl").read_text().splitlines()]
        for method in ("thread/start", "turn/start"):
            self.assertEqual(1, sum(r["direction"] == "send" and r["message"].get("method") == method for r in raw))
        with self.assertRaises(FileExistsError):
            collect_session(directory, executable=executable, auth_file=self.auth)
        with self.assertRaises(FileExistsError):
            run_batch(ROOT, directory.parent, executable=executable, auth_file=self.auth, enabled=True)

    def test_literal_nonlogin_wrappers_preserve_exact_present_and_absent_proofs(self):
        report, directory, _ = self.run_fake("wrapped")
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        obs = self.read(directory, "observation.json")
        records = [r for r in obs["command_records"] if r["raw_command"].startswith("/bin/zsh -c ")]
        self.assertEqual(3, len(records))
        self.assertTrue(self.checks(directory)[POST])

    def test_existing_safe_concurrent_reads_still_work_after_new_conditional(self):
        report, directory, _ = self.run_fake("concurrent")
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        self.assertTrue(self.checks(directory)[POST])

    def test_inherited_guarded_absence_and_null_precheck_keep_bounded_evidence(self):
        for mode in ("pre-guarded", "post-guarded", "pre-null"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertTrue(report["results"][0]["automated_checks_passed"], report)
                self.assertTrue(self.checks(directory)[POST])
                checks = self.read(directory, "checks.json")
                self.assertEqual(1 if mode == "pre-null" else 0,
                                 len(checks["command_backing_adapter"]["admissions"]))
                self.assertFalse(checks["command_backing_adapter"]["captured_observation_modified"])

    def test_missing_postcheck_cannot_be_supplied_by_snapshots_or_narration(self):
        for mode in ("missing-post", "before-only", "claimed-post"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                self.assertFalse(self.checks(directory)[POST])
                self.assertTrue(self.checks(directory)["append-preserves-prefix"])
                self.assertTrue(self.checks(directory)["separate-final-artifact-readback"])
                obs = self.read(directory, "observation.json")
                self.assertEqual(1, len([d for d in obs["diagnostics"] if d.get("certified_absence")]))
                self.assert_retained_single_result(report, directory)

    def test_postcheck_before_readback_or_after_final_report_never_passes(self):
        for mode in ("post-before-readback", "post-late"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                self.assertFalse(self.checks(directory)[POST])
                self.assert_retained_single_result(report, directory)

    def test_mixed_failed_noisy_or_null_postchecks_retain_failures(self):
        for mode in ("post-mixed", "post-failed", "post-noisy", "post-null"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                self.assertFalse(self.checks(directory)[POST])
                self.assert_retained_single_result(report, directory)
                if mode == "post-failed":
                    self.assertTrue(any(r["exit_code"] == 1 for r in self.read(directory, "observation.json")["command_records"]))

    def test_final_readback_and_git_claim_gates_remain_binding(self):
        for mode, criterion in (("missing-read", "separate-final-artifact-readback"),
                                ("unsupported-git", "recognized-git-comparison-claims-supported")):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                self.assertFalse(self.checks(directory)[criterion])
                self.assert_retained_single_result(report, directory)

    def test_provider_protocol_failures_stop_without_replacement(self):
        for mode in ("missing-usage", "wrong-model", "rerouted", "timeout"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode, timeout=0.3 if mode == "timeout" else 10)
                self.assertTrue(report["results"][0]["stop_batch"])
                self.assert_retained_single_result(report, directory)
                if mode == "wrong-model":
                    self.assertNotIn('"method": "turn/start"', (directory / "raw/events.jsonl").read_text())

    def test_instrumentation_exception_retains_failed_observation_with_new_schema(self):
        with mock.patch("harnessmith.workflow_runtime_v11.normalize_events", side_effect=ValueError("synthetic decoder failure")):
            report, directory, _ = self.run_fake()
        self.assertTrue(report["results"][0]["stop_batch"])
        self.assertEqual(10, self.read(directory, "observation.json")["schema_version"])
        self.assert_retained_single_result(report, directory)
        self.assertTrue((directory / "after/specs/001-invitations/checklists/security.md").is_file())

    def test_disabled_or_invalid_launch_never_prepares_or_spawns(self):
        output = self.root / "disabled"
        with mock.patch("harnessmith.workflow_runtime_v11.prepare_pilot") as prepare:
            with self.assertRaises(ValueError):
                run_batch(ROOT, output, executable="unused", auth_file=self.auth)
            for timeout in (0, 181):
                with self.assertRaises(ValueError):
                    run_batch(ROOT, output, executable="unused", auth_file=self.auth, enabled=True, timeout=timeout)
            prepare.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
