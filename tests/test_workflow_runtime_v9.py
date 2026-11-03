"""New v9 collector integration with fresh synthetic local stdio events only."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from harnessmith.workflow_runtime_v8 import CONFIG as FROZEN_CONFIG
from harnessmith.workflow_runtime_v9 import CONFIG, ORDER, collect_session, run_batch
from tests.test_workflow_runtime_v8 import fake_source as previous_fake_source


ROOT = Path(__file__).resolve().parents[1]


def fake_source():
    source = previous_fake_source().replace("mock-codex-workflow-8", "mock-codex-workflow-9")
    start, end = source.index("def absence():"), source.index("def hook(name):")
    source = source[:start] + r'''def probe(path):
    body='if [ -f '+path+' ]; then cat '+path+'; else test ! -e '+path+'; fi'
    output=(workspace/path).read_text() if (workspace/path).is_file() else None
    if path=='.specify/extensions.yml':
        if MODE=='wrong-absence-path': body=body.replace('! -e '+path, '! -e wrong.yml')
        if MODE=='noisy-absence': output='not proof\n'
        if MODE=='mutating-absence': body=body.replace('else test', 'else touch not-executed; test')
    item({'type':'commandExecution','command':body,'cwd':str(workspace),
          'status':'completed','exitCode':0,'commandActions':[], 'aggregatedOutput':output})
def absence():
    probe('.specify/extensions.yml')
''' + source[end:]
    start = source.index("    if MODE=='read-only-python':", source.index("    paths="))
    end = source.index("    questions=[", start)
    source = source[:start] + r'''    probe('.specify/memory/constitution.md')
    paths=[p for p in paths if p!='.specify/memory/constitution.md']
    listing=''.join(p+'\n' for p in sorted(manifest['baseline']) if p.startswith('specs/001-invitations/'))
    body='rg --files specs/001-invitations'
    if MODE=='mixed-discovery':
        body=chr(10).join('cat '+p for p in paths)+chr(10)+body
        listing=''.join((workspace/p).read_text() for p in paths)+listing
    item({'type':'commandExecution','command':body,'cwd':str(workspace),
          'status':'completed','exitCode':0,'commandActions':[], 'aggregatedOutput':listing})
    pending=None
    if MODE=='sequential':
        for path in paths: command('cat '+path,[path])
    elif MODE!='mixed-discovery':
        peer=[]
        for path in paths:
            seq+=1
            value={'id':str(seq),'type':'commandExecution','command':'cat '+path,
                   'cwd':str(workspace),'status':'completed','exitCode':0,
                   'commandActions':[], 'aggregatedOutput':(workspace/path).read_text()}
            peer.append(value)
        if MODE=='unknown-overlap': peer[1]['command']='touch not-executed'
        if MODE=='failed-overlap': peer[1].update(status='failed',exitCode=1)
        if MODE=='truncated-overlap': peer[1]['aggregatedOutput']=peer[1]['aggregatedOutput'][:10]
        for value in peer: event('item/started',item={**value,'status':'inProgress'})
        event('item/completed',item=peer[0])
        if MODE=='consume-before-read-completion': pending=peer[1]
        elif MODE!='unfinished-overlap': event('item/completed',item=peer[1])
''' + source[end:]
    old = "    if MODE not in ('missing-read', 'internal-append') or manifest['case']!='append':"
    assert source.count(old) == 1
    source = source.replace(old, "    if pending is not None: event('item/completed',item=pending)\n" + old)
    return source


class WorkflowRuntimeV9Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.auth = self.root / "auth.json"
        self.auth.write_text("{}")

    def run_fake(self, mode="good"):
        executable = self.root / ("fake-" + mode)
        executable.write_text("#!" + sys.executable + "\nMODE=" + repr(mode) + "\n" + fake_source())
        executable.chmod(0o755)
        output = self.root / mode
        report = run_batch(ROOT, output, executable=executable, auth_file=self.auth,
                           enabled=True, timeout=10, evidence_kind="mock")
        directory = output / ORDER[0]
        return report, directory, executable

    @staticmethod
    def read(directory, name):
        return json.loads((directory / name).read_text())

    def test_new_proofs_flow_through_single_slot_with_unchanged_router_and_permissions(self):
        report, directory, executable = self.run_fake()
        self.assertEqual(("append-router-v7-instrument-v9",), ORDER)
        self.assertEqual(FROZEN_CONFIG, CONFIG)
        self.assertEqual((9, 1, 1, 0), tuple(report[k] for k in (
            "schema_version", "approved_session_count", "attempted_session_count", "retries")))
        self.assertEqual([], report["unattempted"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)
        obs = self.read(directory, "observation.json")
        checks = self.read(directory, "checks.json")
        self.assertEqual((8, 9), (obs["schema_version"], checks["checker_version"]))
        self.assertEqual("offline-simulation", obs["evidence_kind"])
        self.assertEqual([], obs["issues"])
        self.assertTrue(any(d.get("certified_absence") for d in obs["diagnostics"]))
        self.assertTrue(any(d.get("terminal_discovery_certificate") for d in obs["diagnostics"]))
        self.assertFalse(checks["historical_results_regraded"])
        env = self.read(directory.parent, "environment.json")
        self.assertEqual("codex-workflow-stdio-v9", env["instrumentation"])
        self.assertEqual(19, len(env["collector_files"]))
        for name, digest in env["collector_files"].items():
            data = (directory.parent / "instrument" / name).read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(data, (ROOT / "harnessmith" / name).read_bytes())
        manifest = self.read(directory, "manifest.json")
        self.assertEqual("router-v7", manifest["strategy"])
        for name in manifest["provenance"]["package"]:
            self.assertEqual((ROOT / "evaluations/variants/speckit-checklist-router-v7" / name).read_bytes(),
                             (directory / "workspace/.agents/skills/speckit-checklist" / name).read_bytes())
        self.assertEqual((ROOT / "evaluations/workflow-fidelity/prompts/append.md").read_bytes(),
                         (directory / "prompt.md").read_bytes())
        raw = [json.loads(s) for s in (directory / "raw/events.jsonl").read_text().splitlines()]
        for method in ("thread/start", "turn/start"):
            self.assertEqual(1, sum(r["direction"] == "send" and r["message"].get("method") == method for r in raw))
        self.assertFalse(Path(obs["returned_configuration"]["testAuthHome"]).exists())
        self.assertFalse(list(directory.parent.rglob("auth.json")))
        with self.assertRaises(FileExistsError):
            collect_session(directory, executable=executable, auth_file=self.auth)
        with self.assertRaises(FileExistsError):
            run_batch(ROOT, directory.parent, executable=executable, auth_file=self.auth, enabled=True)

    def test_sequential_read_choice_still_passes_without_requiring_concurrency(self):
        report, _, _ = self.run_fake("sequential")
        self.assertTrue(report["results"][0]["automated_checks_passed"], report)

    def test_unsupported_or_ambiguous_absence_retains_failed_result(self):
        for mode in ("wrong-absence-path", "noisy-absence", "mutating-absence"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                obs = self.read(directory, "observation.json")
                self.assertFalse(any(d.get("certified_absence") for d in obs["diagnostics"]))
                self.assertTrue((directory / "after-inventory.json").is_file())
                self.assertEqual(0, report["retries"])

    def test_unsafe_incomplete_failed_or_consumed_early_overlaps_never_pass(self):
        for mode in ("unknown-overlap", "failed-overlap", "truncated-overlap",
                     "unfinished-overlap", "consume-before-read-completion"):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                self.assertTrue(self.read(directory, "observation.json")["issues"])
                self.assertEqual((1, 0), (report["attempted_session_count"], report["retries"]))
                for path in ("raw/events.jsonl", "after-inventory.json", "result.json"):
                    self.assertTrue((directory / path).is_file(), path)

    def test_attribution_does_not_relax_discovery_command_boundaries(self):
        report, directory, _ = self.run_fake("mixed-discovery")
        obs = self.read(directory, "observation.json")
        self.assertEqual([], obs["issues"])
        self.assertFalse(report["results"][0]["automated_checks_passed"])
        checks = self.read(directory, "checks.json")
        failed = [c["name"] for c in checks["dimensions"]["workflow"]["checks"] if not c["passed"]]
        self.assertEqual(["context-reads-isolated-from-discovery-and-mutation",
                          "discovery-isolated-from-other-operations"], failed)

    def test_final_readback_and_git_claim_gates_remain_binding(self):
        for mode, criterion in (("missing-read", "separate-final-artifact-readback"),
                                ("unsupported-git", "recognized-git-comparison-claims-supported")):
            with self.subTest(mode=mode):
                report, directory, _ = self.run_fake(mode)
                self.assertFalse(report["results"][0]["automated_checks_passed"])
                checks = self.read(directory, "checks.json")
                self.assertFalse(next(c["passed"] for c in checks["dimensions"]["workflow"]["checks"] if c["name"] == criterion))

    def test_instrumentation_exception_retains_only_attempt_and_new_schema(self):
        with mock.patch("harnessmith.workflow_runtime_v9.normalize_events", side_effect=ValueError("synthetic decoder failure")):
            report, directory, _ = self.run_fake()
        self.assertTrue(report["results"][0]["stop_batch"])
        self.assertEqual((1, 0), (report["attempted_session_count"], report["retries"]))
        self.assertEqual(8, self.read(directory, "observation.json")["schema_version"])
        self.assertTrue((directory / "after/specs/001-invitations/checklists/security.md").is_file())

    def test_disabled_or_invalid_launch_never_prepares_or_spawns(self):
        output = self.root / "disabled"
        with mock.patch("harnessmith.workflow_runtime_v9.prepare_pilot") as prepare:
            with self.assertRaises(ValueError):
                run_batch(ROOT, output, executable="unused", auth_file=self.auth)
            for timeout in (0, 181):
                with self.assertRaises(ValueError):
                    run_batch(ROOT, output, executable="unused", auth_file=self.auth, enabled=True, timeout=timeout)
            prepare.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
