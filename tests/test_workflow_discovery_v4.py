"""Harmless local discovery controls for router v4 using the frozen parser."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from harnessmith.workflow_trace_v3 import normalize_events
from tests.test_workflow_trace_v3 import end_events, lifecycle


class WorkflowDiscoveryV4Tests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("rg"), "local discovery control requires rg")
    def test_existing_feature_inventory_handles_absent_empty_and_populated_checklists(self):
        for state in ("absent", "empty", "populated"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary).resolve()
                feature = "specs/001-invitations"
                target = feature + "/checklists/security.md"
                spec = workspace / feature / "spec.md"
                spec.parent.mkdir(parents=True)
                spec.write_text("# Synthetic requirements\n")
                if state != "absent":
                    (workspace / target).parent.mkdir()
                if state == "populated":
                    (workspace / target).write_text("- [X] CHK007 Existing reviewer state\n")

                def inventory():
                    return {p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in workspace.rglob("*") if p.is_file()}

                before = inventory()
                result = subprocess.run(
                    [shutil.which("rg"), "--files", feature],
                    cwd=workspace, capture_output=True, text=True, check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                paths = result.stdout.splitlines()
                self.assertIn(feature + "/spec.md", paths)
                self.assertEqual(state == "populated", target in paths)
                self.assertEqual(before, inventory())
                events = lifecycle({
                    "id": "discovery", "type": "commandExecution",
                    "command": "rg --files " + feature, "cwd": str(workspace),
                    "status": "completed", "exitCode": result.returncode,
                    "aggregatedOutput": result.stdout, "commandActions": [],
                }) + end_events()
                observation = normalize_events(
                    events, thread_id="thread", turn_id="turn", workspace=workspace,
                    manifest={"model": "gpt-6-luna", "target": target, "baseline": before,
                              "required_reads": [feature + "/spec.md"]},
                    latency_ms=0,
                )
                self.assertEqual([], observation["issues"])
                self.assertFalse(any(e["type"] == "unknown" for e in observation["events"]))
                self.assertTrue(any(d.get("reason") == "file discovery" for d in observation["diagnostics"]))


if __name__ == "__main__":
    unittest.main()
