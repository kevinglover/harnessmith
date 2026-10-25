"""Two-case stdio simulation through the real v2 normalizer and checker.

The executable is a local fake server. No Codex/provider process is launched.
"""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from harnessmith.workflow_runtime_v2 import ORDER, collect_session, run_batch
from tests.test_workflow_runtime import FAKE_SERVER as FROZEN_FAKE_SERVER


ROOT = Path(__file__).resolve().parents[1]


def fake_source():
    """Adapt the retained v1 fake without changing its source or its tests."""
    source = FROZEN_FAKE_SERVER.replace("mock-codex-workflow-1", "mock-codex-workflow-2")
    source = source.replace(
        "'status':'completed','exitCode':0,'source':'agent',",
        "'status':'completed','exitCode':0,'source':'agent',"
        "'aggregatedOutput':''.join((workspace/p).read_text() for p in reads),",
    )
    source = source.replace(
        "    for path in manifest['required_reads']:\n"
        "        if path!='.specify/extensions.yml': command('cat '+path,[path])",
        "    paths=[p for p in manifest['required_reads'] if p!='.specify/extensions.yml']\n"
        "    if MODE=='missing-constitution': paths=[p for p in paths if 'constitution' not in p]\n"
        "    command(chr(10).join('cat '+p for p in paths),paths)",
    )
    source = source.replace("[Completeness, Spec §FR-1]", "[Completeness, Spec §FR-1, Gap]")
    source = source.replace("[Clarity, Spec §FR-2]", "[Clarity, Spec §FR-2, Gap]")
    source = source.replace(
        "def hook(name):\n",
        '''def hook(name):
    pre=name=='pilot-pre-marker'
    automatic='Automatic Pre-Hook' if pre else 'Automatic Hook'
    optional='Optional Pre-Hook' if pre else 'Optional Hook'
    optional_id='pilot-optional-pre' if pre else 'pilot-optional-post'
    announcement=('## Extension Hooks\\n\\n**'+automatic+'**: Synthetic automatic\\n'
                  'Executing: `/'+name+'`\\nEXECUTE_COMMAND: '+name+'\\n\\n'
                  '**'+optional+'**: Synthetic optional\\nCommand: `/'+optional_id+'`\\n'
                  'Description: Optional local marker.\\nPrompt: Run only if requested.\\n'
                  'To execute: `/'+optional_id+'`')
    item({'type':'agentMessage','phase':'commentary','text':announcement})
''',
    )
    source = source.replace(
        "    if MODE=='unknown': command('echo diagnostic')",
        "    if MODE=='unknown': command(\"python3 -c 'print(123)'\")",
    )
    source = source.replace(
        "    if manifest['case']=='hooks':\n"
        "        output+=' Automatic Pre-Hook Automatic Hook EXECUTE_COMMAND: pilot-pre-marker EXECUTE_COMMAND: pilot-post-marker Optional Pre-Hook Optional Hook To execute: `/pilot-optional-pre` To execute: `/pilot-optional-post`'\n",
        "",
    )
    source = source.replace(
        "    item({'type':'agentMessage','text':output})",
        "    output=output.replace('3 new items', '**three** new unchecked requirements-quality questions')\n"
        "    output=output.replace('4 new items', '**four** unchecked requirements-quality questions')\n"
        "    item({'type':'agentMessage','phase':'commentary' if MODE=='missing-final' else 'final_answer','text':output})",
    )
    return source


class WorkflowRuntimeV2Tests(unittest.TestCase):
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

    def test_two_sessions_use_v2_trace_and_checker_with_retained_provenance(self):
        report, output, executable = self.run_fake()
        self.assertEqual(["append-router-v2", "hooks-router-v2"], list(ORDER))
        self.assertEqual(list(ORDER), [r["session_id"] for r in report["results"]])
        self.assertEqual(2, report["approved_session_count"])
        self.assertEqual(0, report["retries"])
        self.assertEqual([], report["unattempted"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertTrue(all(r["automated_checks_passed"] for r in report["results"]), report)
        environment = json.loads((output / "environment.json").read_text())
        self.assertEqual("codex-workflow-stdio-v2", environment["instrumentation"])
        self.assertEqual("mock", environment["evidence_kind"])
        for name, digest in environment["collector_files"].items():
            data = (output / "instrument" / name).read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(data, (ROOT / "harnessmith" / name).read_bytes())
        for session in ORDER:
            directory = output / session
            observation = json.loads((directory / "observation.json").read_text())
            checks = json.loads((directory / "checks.json").read_text())
            self.assertEqual(2, observation["schema_version"])
            self.assertEqual(2, checks["checker_version"])
            self.assertFalse(checks["historical_results_regraded"])
            self.assertEqual("offline-simulation", observation["evidence_kind"])
            self.assertIn("requirements-quality questions", observation["final_output"])
            self.assertNotIn("Extension Hooks", observation["final_output"])
            self.assertTrue(any(
                e.get("success_evidence") == "pinned input bytes in ordered stdout"
                for e in observation["events"]
            ))
            self.assertFalse(Path(observation["returned_configuration"]["testAuthHome"]).exists())
            raw = [json.loads(line) for line in (directory / "raw/events.jsonl").read_text().splitlines()]
            self.assertEqual(1, sum(
                r["direction"] == "send" and r["message"].get("method") == "turn/start"
                for r in raw
            ))
            self.assertTrue((directory / "before-inventory.json").exists())
            self.assertTrue((directory / "after-inventory.json").exists())
        with self.assertRaises(FileExistsError):
            collect_session(output / ORDER[0], executable=executable, auth_file=self.auth)
        self.assertFalse(list(output.rglob("auth.json")))

    def test_context_and_unknown_operation_failures_retain_both_without_retries(self):
        for mode in ("missing-constitution", "unknown", "missing-final"):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode)
                self.assertEqual(2, report["attempted_session_count"])
                self.assertFalse(any(r["automated_checks_passed"] for r in report["results"]))
                self.assertFalse(any(r["stop_batch"] for r in report["results"]))
                self.assertEqual(2, len(list(output.glob("*/result.json"))))
                self.assertEqual(0, report["retries"])

    def test_instrumentation_failure_retains_artifacts_and_stops_second_slot(self):
        for mode in ("missing-usage", "wrong-model", "rerouted", "timeout"):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(mode, timeout=0.3 if mode == "timeout" else 10)
                self.assertEqual(1, report["attempted_session_count"])
                self.assertEqual(list(ORDER[1:]), report["unattempted"])
                first = output / ORDER[0]
                self.assertTrue((first / "raw/events.jsonl").is_file())
                self.assertTrue((first / "after-inventory.json").is_file())
                self.assertFalse((output / ORDER[1] / "attempt.json").exists())
                if mode == "wrong-model":
                    self.assertNotIn('"method": "turn/start"', (first / "raw/events.jsonl").read_text())

    def test_normalizer_exception_retains_schema_two_fallback_and_written_bytes(self):
        with mock.patch("harnessmith.workflow_runtime_v2.normalize_events", side_effect=ValueError("decoder failed")):
            report, output, _ = self.run_fake()
        self.assertEqual(1, report["attempted_session_count"])
        first = output / ORDER[0]
        self.assertTrue((first / "after/specs/001-invitations/checklists/security.md").exists())
        observation = json.loads((first / "observation.json").read_text())
        self.assertEqual(2, observation["schema_version"])
        self.assertEqual("", observation["final_output"])
        self.assertEqual("ValueError", report["results"][0]["collector_error"]["type"])

    def test_disabled_and_invalid_timeout_never_prepare_or_spawn(self):
        output = self.root / "disabled"
        with mock.patch("harnessmith.workflow_runtime_v2.prepare_pilot") as prepare:
            with self.assertRaises(ValueError):
                run_batch(ROOT, output, executable="/unused", auth_file=self.auth)
            for timeout in (0, 181):
                with self.assertRaises(ValueError):
                    run_batch(ROOT, output, executable="/unused", auth_file=self.auth, enabled=True, timeout=timeout)
            prepare.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
