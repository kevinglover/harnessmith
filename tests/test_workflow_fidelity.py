"""Offline artifact/trace simulations only; never model-fidelity observations."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessmith.workflow_fidelity import (
    MARKERS,
    PACKAGE,
    SETUP,
    SETUP_COMMAND,
    check_workspace,
    main,
    prepare_pilot,
)


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    "Are authorization roles and workspace boundaries documented? [Completeness, Spec §FR-1]",
    "Is the invitation expiration interval quantified in requirements? [Clarity, Spec §FR-2]",
    "Are expired and reused invitation outcomes defined in requirements? [Coverage, Gap]",
    "Are invitation record retention requirements documented? [Completeness, Gap]",
]


class WorkflowFidelityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name).resolve() / "prepared"
        self.summary = prepare_pilot(ROOT, self.output)

    def good_observation(self, case="create", strategy="router"):
        directory = self.output / (case + "-" + strategy)
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        workspace = directory / "workspace"
        target = workspace / manifest["target"]
        events = [{"type": "read", "path": PACKAGE + "/SKILL.md"}]
        events.extend(
            {"type": "read", "path": PACKAGE + "/" + name}
            for name in manifest["expected_references"]
        )

        def hook(command):
            subprocess.run(
                [sys.executable, ".pilot/marker_hook.py", command],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            events.append(
                {
                    "type": "hook",
                    "command": command,
                    "status": "completed",
                    "exit_code": 0,
                }
            )

        if case == "hooks":
            events.append({"type": "read", "path": ".specify/extensions.yml"})
            hook("pilot-pre-marker")
        setup = subprocess.run(
            [str(workspace / SETUP), "--json", "--template", "checklist-template"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(setup.stdout)
        self.assertEqual(
            str(workspace / "specs/001-invitations"), payload["FEATURE_DIR"]
        )
        self.assertIn("Reviewer-owned", payload["TEMPLATE_CONTENT"])
        events.append(
            {
                "type": "setup",
                "command": SETUP_COMMAND,
                "status": "completed",
                "exit_code": 0,
            }
        )
        events.extend(
            {"type": "read", "path": name}
            for name in manifest["required_reads"]
            if name != ".specify/extensions.yml"
        )
        questions = QUESTIONS[1:] if case == "append" else QUESTIONS
        new_items = (
            "\n## Requirement Clarity\n\n"
            + "\n".join(
                "- [ ] CHK%03d %s" % (manifest["first_id"] + n, question)
                for n, question in enumerate(questions)
            )
            + "\n"
        )
        if case == "append":
            initial = target.read_text()
        else:
            initial = (
                "# Security Requirements Checklist\n\n"
                "**Purpose**: Security requirements review.\n**Created**: 2026-10-24\n\n"
                "**Ownership**: Reviewer-owned. `[x]` means reviewer approval of "
                "requirements quality, not implementation completion.\n\n"
                "## Notes\n\n`/speckit-implement` reads checklist state but does not modify markers.\n"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(initial + new_items)
        events.append({"type": "write", "path": manifest["target"]})
        if case == "hooks":
            hook("pilot-post-marker")
        text = (
            "%s %s; %d new items. Focus: security; depth: standard; "
            "actor/timing: reviewer during PR review."
            % ("Appended to" if case == "append" else "Created", target, len(questions))
        )
        if case == "hooks":
            text += (
                "\n## Extension Hooks\n**Automatic Pre-Hook**: Synthetic automatic pre\n"
                "Executing: `/pilot-pre-marker`\nEXECUTE_COMMAND: pilot-pre-marker\n"
                "**Optional Pre-Hook**: Synthetic optional pre\nCommand: `/pilot-optional-pre`\n"
                "Description: Optional marker\nPrompt: Run only if requested later.\n"
                "To execute: `/pilot-optional-pre`\n"
                "**Automatic Hook**: Synthetic automatic post\n"
                "Executing: `/pilot-post-marker`\nEXECUTE_COMMAND: pilot-post-marker\n"
                "**Optional Hook**: Synthetic optional post\nCommand: `/pilot-optional-post`\n"
                "Description: Optional marker\nPrompt: Run only if requested later.\n"
                "To execute: `/pilot-optional-post`\n"
            )
        observation = {
            "schema_version": 1,
            "evidence_kind": "offline-simulation",
            "completed": True,
            "model": "gpt-6-luna",
            "events": events,
            "output": text,
        }
        for event in events:
            event.setdefault("status", "completed")
            if event["type"] == "read":
                event["exit_code"] = 0
        return manifest_path, observation, target

    def assert_fails(self, manifest, observation, dimension=None):
        report = check_workspace(manifest, observation)
        self.assertFalse(report["automated_checks_passed"])
        if dimension:
            self.assertEqual(
                "fail", report["dimensions"][dimension]["automated_status"]
            )
        return report

    def test_preparation_is_six_fresh_hash_pinned_offline_sessions(self):
        self.assertEqual(6, self.summary["proposed_session_count"])
        self.assertEqual(0, self.summary["live_sessions_started"])
        self.assertEqual("pending", self.summary["model_fidelity"])
        self.assertEqual(
            [
                "create-canonical",
                "create-router",
                "append-router",
                "append-canonical",
                "hooks-canonical",
                "hooks-router",
            ],
            [s["id"] for s in self.summary["sessions"]],
        )
        for session in self.summary["sessions"]:
            manifest = json.loads((self.output / session["manifest"]).read_text())
            self.assertEqual("gpt-6-luna", manifest["model"])
            self.assertEqual("offline-preparation", manifest["evidence_kind"])
            self.assertTrue(manifest["provenance"]["source_sha256"])
            self.assertTrue(manifest["provenance"]["router_review_sha256"])
            self.assertEqual(
                {"checker.py", "rubric.md", "pilot.json"},
                set(manifest["provenance"]["instruments"]),
            )
            workspace = self.output / session["id"] / "workspace"
            self.assertFalse((workspace / "manifest.json").exists())
            self.assertFalse((workspace / MARKERS).exists())
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_all_six_good_simulations_pass_automation_only(self):
        for case in ("create", "append", "hooks"):
            for strategy in ("canonical", "router"):
                with self.subTest(case=case, strategy=strategy):
                    manifest, observation, _ = self.good_observation(case, strategy)
                    report = check_workspace(manifest, observation)
                    failures = [
                        check
                        for d in report["dimensions"].values()
                        for check in d.get("checks", [])
                        if not check["passed"]
                    ]
                    self.assertTrue(report["automated_checks_passed"], failures)
                    self.assertFalse(report["eligible_for_promotion"])
                    self.assertEqual("pending", report["model_fidelity"])
                    self.assertEqual(
                        "not-evaluated", report["dimensions"]["efficiency"]["status"]
                    )
                    self.assertEqual(
                        "pending", report["dimensions"]["content"]["review_status"]
                    )

    def test_append_prefix_and_existing_checkbox_states_are_byte_exact(self):
        manifest, observation, target = self.good_observation("append")
        good = target.read_bytes()
        for bad in (
            good.replace(b"[X]", b"[ ]"),
            good.replace(b"annotation:", b"annotation :"),
        ):
            target.write_bytes(bad)
            self.assert_fails(manifest, observation, "workflow")

    def test_checked_new_items_bad_ids_malformed_items_fail(self):
        manifest, observation, target = self.good_observation()
        good = target.read_text()
        for bad in (
            good.replace("- [ ]", "- [x]", 1),
            good.replace("CHK004", "CHK003"),
            good.replace("CHK001", "**CHK001**"),
            good.replace("[Completeness, Spec §FR-1]", "[Completeness, Spec §FR-1"),
            good + "- [ ] Malformed hidden checkbox\n",
            good + "1. [ ] CHK999 Hidden numbered checkbox? [Gap]\n",
        ):
            target.write_text(bad)
            self.assert_fails(manifest, observation, "formatting")

    def test_execution_test_and_omitted_topic_fail_content_screen(self):
        manifest, observation, target = self.good_observation()
        good = target.read_text()
        for bad in (
            good.replace(
                QUESTIONS[0], "Verify authorization works correctly? [Coverage, Gap]"
            ),
            good.replace("retention", "something unrelated"),
        ):
            target.write_text(bad)
            self.assert_fails(manifest, observation, "content")

    def test_modified_fixture_and_unexpected_file_fail(self):
        manifest, observation, target = self.good_observation()
        workspace = manifest.parent / "workspace"
        unrelated = workspace / "unexpected.txt"
        unrelated.write_text("not allowed")
        self.assert_fails(manifest, observation, "workflow")
        unrelated.unlink()
        (workspace / "specs/001-invitations/spec.md").write_text("changed")
        self.assert_fails(manifest, observation, "workflow")
        target.unlink()
        self.assert_fails(manifest, observation)

    def test_symlink_rejected_before_read(self):
        manifest, observation, _ = self.good_observation()
        (manifest.parent / "workspace/escape").symlink_to(ROOT / "skills")
        with self.assertRaisesRegex(ValueError, "symlink"):
            check_workspace(manifest, observation)

    def test_hook_markers_and_trace_are_both_required(self):
        manifest, observation, _ = self.good_observation("hooks")
        fake = copy.deepcopy(observation)
        fake["events"] = [e for e in fake["events"] if e["type"] != "hook"]
        self.assert_fails(manifest, fake, "workflow")
        (manifest.parent / "workspace" / MARKERS).unlink()
        self.assert_fails(manifest, observation, "workflow")

    def test_optional_disabled_and_conditional_hooks_never_execute(self):
        manifest, observation, _ = self.good_observation("hooks")
        for command in (
            "pilot-optional-pre",
            "pilot-disabled-post",
            "pilot-conditional-pre",
        ):
            fake = copy.deepcopy(observation)
            fake["events"].append(
                {
                    "type": "hook",
                    "command": command,
                    "status": "completed",
                    "exit_code": 0,
                }
            )
            self.assert_fails(manifest, fake, "workflow")

    def test_hook_order_failed_hook_and_stale_post_hash_fail(self):
        manifest, observation, target = self.good_observation("hooks")
        fake = copy.deepcopy(observation)
        post = fake["events"].pop()
        fake["events"].insert(0, post)
        self.assert_fails(manifest, fake, "workflow")
        fake = copy.deepcopy(observation)
        next(e for e in fake["events"] if e["type"] == "hook")["exit_code"] = 1
        self.assert_fails(manifest, fake, "workflow")
        target.write_text(target.read_text() + "After post-hook mutation\n")
        self.assert_fails(manifest, observation, "workflow")

    def test_reference_omission_extra_reference_and_late_reference_fail(self):
        manifest, observation, _ = self.good_observation()
        fake = copy.deepcopy(observation)
        reference = fake["events"].pop(1)
        self.assert_fails(manifest, fake, "reference_behavior")
        fake["events"].append(reference)
        self.assert_fails(manifest, fake, "reference_behavior")
        fake = copy.deepcopy(observation)
        fake["events"].append(
            {
                "type": "read",
                "path": PACKAGE + "/references/anti-examples-what-not-to-do.md",
                "status": "completed",
                "exit_code": 0,
            }
        )
        self.assert_fails(manifest, fake, "reference_behavior")

    def test_unknown_operation_and_wrong_setup_do_not_pass(self):
        manifest, observation, _ = self.good_observation()
        fake = copy.deepcopy(observation)
        fake["events"].append({"type": "unknown"})
        self.assert_fails(manifest, fake, "workflow")
        fake = copy.deepcopy(observation)
        next(e for e in fake["events"] if e["type"] == "setup")["command"] = (
            "real-project-hook"
        )
        self.assert_fails(manifest, fake, "workflow")

    def test_failed_read_or_write_is_not_successful_evidence(self):
        manifest, observation, _ = self.good_observation()
        for event_type in ("read", "write"):
            fake = copy.deepcopy(observation)
            event = next(e for e in fake["events"] if e["type"] == event_type)
            event["status"] = "failed"
            event["exit_code"] = 1
            self.assert_fails(manifest, fake, "workflow")
        fake = copy.deepcopy(observation)
        reference = fake["events"][1]
        reference["exit_code"] = 1
        self.assert_fails(manifest, fake, "reference_behavior")

    def test_append_target_and_context_must_be_read_before_write(self):
        manifest, observation, target = self.good_observation("append")
        relative = target.relative_to(manifest.parent / "workspace").as_posix()
        for path in (relative, "specs/001-invitations/spec.md"):
            fake = copy.deepcopy(observation)
            read = next(
                e
                for e in fake["events"]
                if e.get("path") == path and e["type"] == "read"
            )
            fake["events"].remove(read)
            self.assert_fails(manifest, fake, "workflow")
            fake["events"].append(read)
            self.assert_fails(manifest, fake, "workflow")

    def test_prepared_manifest_prompt_and_instrument_drift_are_rejected(self):
        manifest, observation, _ = self.good_observation()
        for path in (
            manifest,
            manifest.parent / "prompt.md",
            self.output / "instrument/rubric.md",
        ):
            before = path.read_bytes()
            path.write_bytes(before + b"\n")
            with self.assertRaises(ValueError):
                check_workspace(manifest, observation)
            path.write_bytes(before)

    def test_new_executable_artifact_and_unannounced_optional_hook_fail(self):
        manifest, observation, target = self.good_observation("hooks")
        target.chmod(0o755)
        self.assert_fails(manifest, observation, "workflow")
        target.chmod(0o644)
        fake = copy.deepcopy(observation)
        fake["output"] = fake["output"].replace("To execute: `/pilot-optional-pre`", "")
        self.assert_fails(manifest, fake, "workflow")

    def test_cli_checks_and_refuses_existing_reports(self):
        manifest, observation, _ = self.good_observation()
        observations = self.output / "observation.json"
        observations.write_text(json.dumps(observation))
        report = self.output / "report.json"
        self.assertEqual(
            0,
            main(["check", str(manifest), str(observations), "--output", str(report)]),
        )
        self.assertEqual(
            "offline-simulation", json.loads(report.read_text())["evidence_kind"]
        )
        with self.assertRaises(SystemExit):
            main(["check", str(manifest), str(observations), "--output", str(report)])

    def test_final_report_checks_count_operation_and_timing_outside_path(self):
        manifest, observation, _ = self.good_observation("append")
        for old, new in (
            ("3 new items", "13 new items"),
            ("Appended to", "Created"),
            ("PR review", "review"),
        ):
            fake = copy.deepcopy(observation)
            fake["output"] = fake["output"].replace(old, new)
            self.assert_fails(manifest, fake, "workflow")


if __name__ == "__main__":
    unittest.main()
