"""One-slot integration with synthetic observations and a local fake server."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from harnessmith.workflow_runtime_v6 import ORDER, collect_session, run_batch
from tests.test_workflow_runtime_v5 import fake_source as previous_fake_source


ROOT = Path(__file__).resolve().parents[1]


def fake_source():
    source = "import shlex\n" + previous_fake_source()

    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old
        source = source.replace(old, new)

    replace("mock-codex-workflow-5", "mock-codex-workflow-6")
    replace(
        "def hook(name):",
        '''def absence():
    if MODE=='read-only-python':
        script='from pathlib import Path; p=Path(".specify/extensions.yml"); print("EXISTS",p.exists()); print(p.read_text() if p.exists() else "")'
        item({'type':'commandExecution','command':'python3 -c '+shlex.quote(script),
              'cwd':str(workspace),'status':'completed','exitCode':0,'commandActions':[],
              'aggregatedOutput':'EXISTS False\\n\\n'})
    else:
        command('if [ -f .specify/extensions.yml ]; then cat .specify/extensions.yml; fi')
def hook(name):''',
    )
    replace(
        "    command('.specify/scripts/bash/check-prerequisites.sh --json --template checklist-template',",
        "    if MODE!='late-absence': absence()\n"
        "    command('.specify/scripts/bash/check-prerequisites.sh --json --template checklist-template',",
    )
    replace(
        "    paths=[p for p in manifest['required_reads'] if p!='.specify/extensions.yml']",
        "    if MODE=='late-absence': absence()\n"
        "    paths=[p for p in manifest['required_reads'] if p!='.specify/extensions.yml']",
    )
    replace(
        "    command(chr(10).join('cat '+p for p in paths),paths)",
        '''    if MODE=='read-only-python':
        cache=("python3: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead\\n"
               "python3: error: couldn't create cache file '/tmp/xcrun_db-AbC123' (errno=Operation not permitted)\\n")
        for path in paths:
            if path==manifest['target']:
                script=('from pathlib import Path; p=Path('+repr(path)+'); b=p.read_bytes(); '
                        'print("BYTES"); print(repr(b)); print("TEXT"); print(b.decode())')
                data=(workspace/path).read_bytes()
                output='BYTES\\n'+repr(data)+'\\nTEXT\\n'+data.decode()+'\\n'
            else:
                script=('from pathlib import Path; p=Path('+repr(path)+'); '
                        'print("EXISTS",p.exists()); print(p.read_text() if p.exists() else "")')
                output='EXISTS True\\n'+(workspace/path).read_text()+'\\n'
            item({'type':'commandExecution','command':'python3 -c '+shlex.quote(script),
                  'cwd':str(workspace),'status':'completed','exitCode':0,'commandActions':[],
                  'aggregatedOutput':cache+cache+output})
    else:
        command(chr(10).join('cat '+p for p in paths),paths)''',
    )
    replace(
        "    if MODE!='internal-append' or manifest['case']!='append':",
        "    if MODE not in ('missing-read', 'internal-append') or manifest['case']!='append':",
    )
    replace(
        "    item({'type':'agentMessage','phase':'commentary' if MODE=='missing-final' else 'final_answer','text':output})",
        "    output+=' The final file read shows the original checklist content, reviewer note, and checkbox states intact.'\n"
        "    if MODE=='unsupported-git':\n"
        "        output+=' One attempted comparison against Git history could not run because the workspace was not recognized as a Git repository.'\n"
        "    item({'type':'agentMessage','phase':'commentary' if MODE=='missing-final' else 'final_answer','text':output})",
    )
    return source


class WorkflowRuntimeV6Tests(unittest.TestCase):
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

    def test_one_append_slot_pins_new_and_inherited_dependencies(self):
        report, output, executable = self.run_fake()
        self.assertEqual(("append-router-v6",), ORDER)
        self.assertEqual(1, report["approved_session_count"])
        self.assertEqual(1, report["attempted_session_count"])
        self.assertEqual(6, report["schema_version"])
        self.assertEqual([], report["unattempted"])
        self.assertEqual(0, report["retries"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        env = json.loads((output / "environment.json").read_text())
        self.assertEqual("mock", env["evidence_kind"])
        self.assertEqual("codex-workflow-stdio-v6", env["instrumentation"])
        self.assertEqual(13, len(env["collector_files"]))
        for name, digest in env["collector_files"].items():
            data = (output / "instrument" / name).read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(data, (ROOT / "harnessmith" / name).read_bytes())
        directory = output / ORDER[0]
        obs = json.loads((directory / "observation.json").read_text())
        checks = json.loads((directory / "checks.json").read_text())
        self.assertEqual(5, obs["schema_version"])
        self.assertEqual(6, checks["checker_version"])
        self.assertFalse(checks["historical_results_regraded"])
        self.assertEqual("offline-simulation", obs["evidence_kind"])
        self.assertFalse(Path(obs["returned_configuration"]["testAuthHome"]).exists())
        raw = [json.loads(line) for line in (directory / "raw/events.jsonl").read_text().splitlines()]
        for method in ("thread/start", "turn/start"):
            self.assertEqual(1, sum(r["direction"] == "send" and r["message"].get("method") == method for r in raw))
        self.assertTrue((directory / "before-inventory.json").is_file())
        self.assertTrue((directory / "after-inventory.json").is_file())
        self.assertFalse(list(output.rglob("auth.json")))
        with self.assertRaises(FileExistsError):
            collect_session(directory, executable=executable, auth_file=self.auth)
        with self.assertRaises(FileExistsError):
            run_batch(ROOT, output, executable=executable, auth_file=self.auth, enabled=True, evidence_kind="mock")

    def test_synthetic_read_only_python_flows_through_real_parser_and_checker(self):
        report, output, _ = self.run_fake("read-only-python")
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        obs = json.loads((output / ORDER[0] / "observation.json").read_text())
        self.assertEqual([], obs["issues"])
        self.assertTrue(any(d.get("certified_absence") for d in obs["diagnostics"]))
        self.assertTrue(any("cache" in d.get("reason", "") for d in obs["diagnostics"]))

    def test_missing_final_read_is_not_supplied_by_claim_or_saved_artifact(self):
        report, output, _ = self.run_fake("missing-read")
        self.assertEqual(1, report["attempted_session_count"])
        self.assertFalse(report["results"][0]["automated_checks_passed"])
        self.assertFalse(report["results"][0]["stop_batch"])
        directory = output / ORDER[0]
        self.assertTrue((directory / "after/specs/001-invitations/checklists/security.md").exists())
        checks = json.loads((directory / "checks.json").read_text())
        by_name = {c["name"]: c["passed"] for c in checks["dimensions"]["workflow"]["checks"]}
        self.assertFalse(by_name["final-artifact-verification"])
        self.assertFalse(by_name["recognized-artifact-verification-claims-supported"])
        self.assertTrue(by_name["append-preserves-prefix"])

    def test_internal_readback_is_attributed_but_requires_separate_checkpoint(self):
        report, output, _ = self.run_fake("internal-append")
        self.assertFalse(report["results"][0]["automated_checks_passed"], report)
        obs = json.loads((output / ORDER[0] / "observation.json").read_text())
        self.assertTrue(any(e.get("read_after_write") for e in obs["events"]))
        self.assertTrue(any(e.get("write_mode") == "append" for e in obs["events"]))
        checks = json.loads((output / ORDER[0] / "checks.json").read_text())
        by_name = {c["name"]: c["passed"] for c in checks["dimensions"]["workflow"]["checks"]}
        self.assertTrue(by_name["final-artifact-verification"])
        self.assertTrue(by_name["recognized-artifact-verification-claims-supported"])
        self.assertEqual(["separate-final-artifact-readback"], [name for name, passed in by_name.items() if not passed])

    def test_unsupported_git_and_late_absence_fail_without_replacement(self):
        for mode, name in (
            ("unsupported-git", "recognized-git-comparison-claims-supported"),
            ("late-absence", "extension-config-before-setup"),
        ):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode)
                self.assertEqual(1, report["attempted_session_count"])
                self.assertEqual(0, report["retries"])
                self.assertEqual([], report["unattempted"])
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                self.assertFalse(report["results"][0]["stop_batch"])
                checks = json.loads((output / ORDER[0] / "checks.json").read_text())
                self.assertFalse(next(c["passed"] for c in checks["dimensions"]["workflow"]["checks"] if c["name"] == name))
                self.assertEqual(1, len(list(output.glob("*/attempt.json"))))

    def test_instrumentation_failures_keep_the_only_attempt(self):
        for mode in ("missing-usage", "wrong-model", "rerouted", "timeout"):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode, timeout=0.3 if mode == "timeout" else 10)
                self.assertEqual(1, report["attempted_session_count"])
                self.assertEqual(0, report["retries"])
                self.assertTrue(report["results"][0]["stop_batch"])
                directory = output / ORDER[0]
                self.assertTrue((directory / "raw/events.jsonl").exists())
                self.assertTrue((directory / "after-inventory.json").exists())
                self.assertEqual(1, len(list(output.glob("*/result.json"))))
                if mode == "wrong-model":
                    self.assertNotIn('"method": "turn/start"', (directory / "raw/events.jsonl").read_text())

    def test_normalizer_exception_retains_schema_five_and_artifact(self):
        with mock.patch("harnessmith.workflow_runtime_v6.normalize_events", side_effect=ValueError("decoder failed")):
            report, output, _ = self.run_fake()
        self.assertTrue(report["results"][0]["stop_batch"])
        directory = output / ORDER[0]
        self.assertTrue((directory / "after/specs/001-invitations/checklists/security.md").exists())
        self.assertEqual(5, json.loads((directory / "observation.json").read_text())["schema_version"])

    def test_disabled_and_invalid_timeout_do_not_prepare(self):
        output = self.root / "disabled"
        with mock.patch("harnessmith.workflow_runtime_v6.prepare_pilot") as prepare:
            with self.assertRaises(ValueError):
                run_batch(ROOT, output, executable="/unused", auth_file=self.auth)
            for timeout in (0, 181):
                with self.assertRaises(ValueError):
                    run_batch(ROOT, output, executable="/unused", auth_file=self.auth, enabled=True, timeout=timeout)
            prepare.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
