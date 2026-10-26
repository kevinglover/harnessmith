"""Fresh synthetic v7 collector regressions; only a local fake stdio server."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from harnessmith.workflow_runtime_v6 import CONFIG as FROZEN_CONFIG
from harnessmith.workflow_runtime_v7 import CONFIG, ORDER, collect_session, run_batch
from tests.test_workflow_runtime_v6 import fake_source as previous_fake_source


ROOT = Path(__file__).resolve().parents[1]


def fake_source():
    source = previous_fake_source().replace("mock-codex-workflow-6", "mock-codex-workflow-7")
    old = "        command('if [ -f .specify/extensions.yml ]; then cat .specify/extensions.yml; fi')"
    assert source.count(old) == 1
    replacement = r'''        body="if [ -f .specify/extensions.yml ]; then cat .specify/extensions.yml; else printf 'NO_EXTENSIONS_FILE\\n'; fi"
        output='NO_EXTENSIONS_FILE\n'
        if MODE=='absence-label-only': body="printf 'NO_EXTENSIONS_FILE\\n'"
        if MODE=='absence-side-effect': body=body.replace('then cat', 'then touch injected; cat')
        if MODE=='absence-wrong-output': output='SOMETHING_ELSE\n'
        if MODE=='absence-noisy': output='warning: unexpected output\n'+output
        item({'type':'commandExecution','command':body,'cwd':str(workspace),
              'status':'completed','exitCode':0,'commandActions':[], 'aggregatedOutput':output})'''
    return source.replace(old, replacement)


class WorkflowRuntimeV7Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.auth = self.root / "auth.json"
        self.auth.write_text("{}")

    def run_fake(self, mode="good", timeout=10):
        executable = self.root / ("fake-" + mode)
        executable.write_text("#!" + sys.executable + "\nMODE=" + repr(mode) + "\n" + fake_source())
        executable.chmod(0o755)
        output = self.root / mode
        report = run_batch(ROOT, output, executable=executable, auth_file=self.auth,
                           enabled=True, timeout=timeout, evidence_kind="mock")
        return report, output, executable

    def test_else_printf_reaches_new_checker_with_unchanged_package_and_limits(self):
        report, output, executable = self.run_fake()
        self.assertEqual(("append-router-v6-instrument-v7",), ORDER)
        self.assertEqual(FROZEN_CONFIG, CONFIG)
        self.assertEqual(7, report["schema_version"])
        self.assertEqual(1, report["approved_session_count"])
        self.assertEqual(1, report["attempted_session_count"])
        self.assertEqual([], report["unattempted"])
        self.assertEqual(0, report["retries"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        env = json.loads((output / "environment.json").read_text())
        self.assertEqual("mock", env["evidence_kind"])
        self.assertEqual("codex-workflow-stdio-v7", env["instrumentation"])
        self.assertEqual(15, len(env["collector_files"]))
        for name, digest in env["collector_files"].items():
            data = (output / "instrument" / name).read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(data, (ROOT / "harnessmith" / name).read_bytes())
        directory = output / ORDER[0]
        manifest = json.loads((directory / "manifest.json").read_text())
        self.assertEqual("router-v6", manifest["strategy"])
        self.assertEqual((ROOT / "evaluations/workflow-fidelity/prompts/append.md").read_bytes(),
                         (directory / "prompt.md").read_bytes())
        package = directory / "workspace/.agents/skills/speckit-checklist"
        for path in manifest["provenance"]["package"]:
            self.assertEqual((ROOT / "evaluations/variants/speckit-checklist-router-v6" / path).read_bytes(),
                             (package / path).read_bytes())
        obs = json.loads((directory / "observation.json").read_text())
        checks = json.loads((directory / "checks.json").read_text())
        self.assertEqual(6, obs["schema_version"])
        self.assertEqual(7, checks["checker_version"])
        self.assertFalse(checks["historical_results_regraded"])
        self.assertEqual("offline-simulation", obs["evidence_kind"])
        self.assertEqual([], obs["issues"])
        self.assertTrue(any(d.get("certified_absence") for d in obs["diagnostics"]))
        self.assertFalse(Path(obs["returned_configuration"]["testAuthHome"]).exists())
        raw = [json.loads(line) for line in (directory / "raw/events.jsonl").read_text().splitlines()]
        for method in ("thread/start", "turn/start"):
            self.assertEqual(1, sum(r["direction"] == "send" and r["message"].get("method") == method for r in raw))
        for path in ("before-inventory.json", "after-inventory.json", "raw/events.stdout", "raw/events.stderr"):
            self.assertTrue((directory / path).is_file(), path)
        self.assertFalse(list(output.rglob("auth.json")))
        with self.assertRaises(FileExistsError):
            collect_session(directory, executable=executable, auth_file=self.auth)
        with self.assertRaises(FileExistsError):
            run_batch(ROOT, output, executable=executable, auth_file=self.auth, enabled=True, evidence_kind="mock")

    def test_false_or_late_absence_never_clears_checkpoint_and_result_is_retained(self):
        for mode in ("absence-label-only", "absence-side-effect", "absence-wrong-output", "absence-noisy", "late-absence"):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode)
                self.assertEqual(1, report["attempted_session_count"])
                self.assertEqual(0, report["retries"])
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                directory = output / ORDER[0]
                obs = json.loads((directory / "observation.json").read_text())
                self.assertFalse(any(d.get("certified_absence") for d in obs["diagnostics"]))
                checks = json.loads((directory / "checks.json").read_text())
                self.assertFalse(next(c["passed"] for c in checks["dimensions"]["workflow"]["checks"]
                                      if c["name"] == "extension-config-before-setup"))
                self.assertTrue((directory / "after-inventory.json").is_file())
                self.assertTrue((directory / "raw/events.jsonl").is_file())
                self.assertEqual(1, len(list(output.glob("*/result.json"))))

    def test_certificate_does_not_waive_final_read_or_unsupported_git_claims(self):
        for mode, name in (("missing-read", "separate-final-artifact-readback"),
                           ("unsupported-git", "recognized-git-comparison-claims-supported")):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                obs = json.loads((output / ORDER[0] / "observation.json").read_text())
                self.assertTrue(any(d.get("certified_absence") for d in obs["diagnostics"]))
                checks = json.loads((output / ORDER[0] / "checks.json").read_text())
                self.assertFalse(next(c["passed"] for c in checks["dimensions"]["workflow"]["checks"] if c["name"] == name))

    def test_instrumentation_failure_keeps_the_single_attempt(self):
        report, output, _ = self.run_fake("missing-usage")
        self.assertEqual(1, report["attempted_session_count"])
        self.assertEqual(0, report["retries"])
        self.assertTrue(report["results"][0]["stop_batch"])
        directory = output / ORDER[0]
        self.assertTrue((directory / "raw/events.jsonl").is_file())
        self.assertTrue((directory / "after-inventory.json").is_file())
        self.assertEqual(1, len(list(output.glob("*/result.json"))))

    def test_normalizer_exception_retains_schema_six_and_artifact(self):
        with mock.patch("harnessmith.workflow_runtime_v7.normalize_events", side_effect=ValueError("decoder failed")):
            report, output, _ = self.run_fake()
        self.assertTrue(report["results"][0]["stop_batch"])
        directory = output / ORDER[0]
        self.assertTrue((directory / "after/specs/001-invitations/checklists/security.md").exists())
        self.assertEqual(6, json.loads((directory / "observation.json").read_text())["schema_version"])

    def test_disabled_and_invalid_timeout_do_not_prepare_or_spawn(self):
        output = self.root / "disabled"
        with mock.patch("harnessmith.workflow_runtime_v7.prepare_pilot") as prepare:
            with self.assertRaises(ValueError):
                run_batch(ROOT, output, executable="/unused", auth_file=self.auth)
            for timeout in (0, 181):
                with self.assertRaises(ValueError):
                    run_batch(ROOT, output, executable="/unused", auth_file=self.auth, enabled=True, timeout=timeout)
            prepare.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
