"""Synthetic offline regressions; these tests never launch a model session."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith.workflow_fidelity_v3 import (
    MODULES,
    _final_report,
    check_workspace,
    main,
    prepare_pilot,
)


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    "Are authorization roles and workspace boundaries specified in requirements? [Completeness, Spec §FR-1, Gap]",
    "Is the expiration interval quantified in requirements? [Clarity, Spec §FR-2, Gap]",
    "Are expired and reused invitation outcomes defined in requirements? [Coverage, Gap]",
    "Are invitation record retention requirements documented? [Completeness, Gap]",
]


class WorkflowFidelityV3Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name).resolve() / "v3"
        self.summary = prepare_pilot(ROOT, self.output)

    def good_observation(self, case="append"):
        directory = self.output / (case + "-router-v3")
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        workspace = directory / "workspace"
        target = workspace / manifest["target"]
        events = [
            {"type": "read", "path": v1.PACKAGE + "/SKILL.md"},
            {"type": "read", "path": v1.PACKAGE + "/references/project-generation.md"},
        ]

        def hook(command):
            subprocess.run(
                [sys.executable, ".pilot/marker_hook.py", command],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            events.append({"type": "hook", "command": command})

        if case == "hooks":
            events.append({"type": "read", "path": ".specify/extensions.yml"})
            hook("pilot-pre-marker")
        setup = subprocess.run(
            [str(workspace / v1.SETUP), "--json", "--template", "checklist-template"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Reviewer-owned", json.loads(setup.stdout)["TEMPLATE_CONTENT"])
        events.append({"type": "setup", "command": v1.SETUP_COMMAND})
        events.extend(
            {"type": "read", "path": path}
            for path in manifest["required_reads"]
            if path != ".specify/extensions.yml"
        )
        questions = QUESTIONS[1:] if case == "append" else QUESTIONS
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
        new_items = (
            "\n## Requirement Clarity\n\n"
            + "\n".join(
                "- [ ] CHK%03d %s" % (manifest["first_id"] + index, question)
                for index, question in enumerate(questions)
            )
            + "\n"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(initial + new_items)
        events.append({"type": "write", "path": manifest["target"]})
        events.append({
            "type": "read", "path": manifest["target"],
            "read_coverage": {"complete": True},
            "read_sha256": v1._sha(target.read_bytes()),
        })
        if case == "hooks":
            hook("pilot-post-marker")
        for index, event in enumerate(events):
            event.update(status="completed", exit_code=0,
                         raw_item_id="op-" + str(index), raw_operation_index=0,
                         raw_start_index=index * 10 + 10,
                         raw_completion_index=index * 10 + 11)
        final = (
            "%s %s with %s unchecked requirements-quality questions. "
            "Focus: security; depth: standard; reviewer during PR review."
            % ("Appended to" if case == "append" else "Created", target,
               "three" if case == "append" else "four")
        )
        messages = []
        if case == "hooks":
            for pre in (True, False):
                phase = "pre" if pre else "post"
                label = " Pre-Hook" if pre else " Hook"
                description = ("Record that generation has not begun." if pre
                               else "Record the generated checklist hash.")
                text = (
                    "## Extension Hooks\n\n**Automatic" + label + "**: Synthetic automatic " + phase + "\n"
                    "Description: " + description + "\n"
                    "Executing: `/pilot-" + phase + "-marker`\n"
                    "EXECUTE_COMMAND: pilot-" + phase + "-marker\n\n"
                    "**Optional" + label + "**: Synthetic optional " + phase + "\n"
                    "Command: `/pilot-optional-" + phase + "`\n"
                    "Description: Optional marker; offer this command but do not execute it.\n"
                    "Prompt: Run the optional " + phase + " marker only if requested later.\n"
                    "To execute: `/pilot-optional-" + phase + "`"
                )
                hook_event = next(e for e in events if e.get("command") == "pilot-" + phase + "-marker")
                messages.append({"text": text, "phase": "commentary", "status": "completed",
                                 "raw_item_id": "message-" + phase,
                                 "raw_start_index": hook_event["raw_start_index"] - 4,
                                 "raw_completion_index": hook_event["raw_start_index"] - 3})
        messages.append({"text": final, "phase": "final_answer", "status": "completed",
                         "raw_item_id": "final", "raw_start_index": 1000,
                         "raw_completion_index": 1001})
        return (manifest_path, {
            "schema_version": 3, "evidence_kind": "offline-simulation",
            "completed": True, "model": "gpt-6-luna", "events": events,
            "messages": messages, "final_output": final,
            "commentary": [m["text"] for m in messages if m["phase"] == "commentary"],
        }, target)

    def checks(self, manifest, observation):
        report = check_workspace(manifest, observation)
        return {
            check["name"]: check["passed"]
            for dimension in report["dimensions"].values()
            for check in dimension.get("checks", [])
        }

    def test_two_case_preparation_pins_old_and_new_instruments(self):
        self.assertEqual(2, self.summary["proposed_session_count"])
        self.assertEqual(0, self.summary["live_sessions_started"])
        self.assertEqual(
            ["append-router-v3", "hooks-router-v3"],
            [session["id"] for session in self.summary["sessions"]],
        )
        for session in self.summary["sessions"]:
            manifest = json.loads((self.output / session["manifest"]).read_text())
            self.assertEqual("gpt-6-luna", manifest["model"])
            self.assertEqual("low", manifest["reasoning_effort"])
            self.assertEqual(3, manifest["checker_version"])
            self.assertEqual(
                set(MODULES) | {"rubric.md", "pilot.json"},
                set(manifest["provenance"]["instruments"]),
            )
            self.assertEqual(
                "1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45",
                manifest["provenance"]["source_sha256"],
            )
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_good_simulations_pass_only_automation(self):
        for case in ("append", "hooks"):
            with self.subTest(case=case):
                manifest, observation, _ = self.good_observation(case)
                report = check_workspace(manifest, observation)
                self.assertTrue(
                    report["automated_checks_passed"],
                    self.checks(manifest, observation),
                )
                self.assertEqual(3, report["schema_version"])
                self.assertFalse(report["eligible_for_promotion"])
                self.assertFalse(report["historical_results_regraded"])
                self.assertEqual("pending", report["model_fidelity"])
                self.assertEqual(
                    "pending", report["dimensions"]["content"]["review_status"]
                )

    def test_final_counts_accept_words_bold_labels_and_adjectives(self):
        target = "/private/tmp/pilot-4/checklists/security.md"
        suffix = " Focus: security; standard depth; reviewer during PR review."
        for clause in (
            "Created %s with **four** unchecked requirements-quality questions.",
            "**Created** %s. **Items:** **4**.",
            "Created %s. New item count: four.",
            "Created %s with 4 new checklist items.",
            "Created %s. Questions: four.",
            "No policy values were invented. Created %s with four new items.",
        ):
            with self.subTest(clause=clause):
                self.assertTrue(
                    _final_report(clause % target + suffix, target, 4, False)
                )

    def test_final_counts_reject_path_digits_plans_negation_and_wrong_counts(self):
        target = "/private/tmp/4-items-created/checklists/security.md"
        suffix = " Focus: security; standard depth; reviewer during PR review."
        for clause in (
            "Created %s.",
            "I will create %s with four new items.",
            "I would have created %s with four new items.",
            "I have not created %s with four new items.",
            "Created %s with five new items.",
            "Created %s. I plan four new items.",
            "Created %s. Not four new items.",
            "Created %s with 14 new items.",
            "Created %s with 4 new items. Items: 5.",
            "I have not created %s. Created four new items elsewhere.",
            "I will create %s. Created /wrong/file. Four items.",
            "Created %s with four items. Appended four items.",
        ):
            with self.subTest(clause=clause):
                self.assertFalse(
                    _final_report(clause % target + suffix, target, 4, False)
                )
        self.assertFalse(
            _final_report(
                "Created " + target + ". Appended three items." + suffix,
                target,
                3,
                True,
            )
        )

    def test_report_and_gap_shape_checks_are_formatting_only(self):
        manifest, observation, _ = self.good_observation()
        report = check_workspace(manifest, observation)
        for dimension, values in report["dimensions"].items():
            names = {check["name"] for check in values.get("checks", [])}
            for name in ("final-report", "missing-policy-gap-markers-heuristic"):
                self.assertEqual(dimension == "formatting", name in names)

    def test_commentary_or_legacy_output_cannot_substitute_for_final(self):
        manifest, observation, _ = self.good_observation()
        for location in ("commentary", "output"):
            fake = copy.deepcopy(observation)
            fake[location] = fake.pop("final_output")
            self.assertFalse(self.checks(manifest, fake)["final-report"])
        observation["final_output"] = None
        self.assertFalse(self.checks(manifest, observation)["final-report"])

    def test_invalid_final_and_commentary_types_rejected(self):
        manifest, observation, _ = self.good_observation()
        for key, value in (("final_output", 4), ("commentary", [1])):
            fake = copy.deepcopy(observation)
            fake[key] = value
            with self.assertRaisesRegex(ValueError, "must be text"):
                check_workspace(manifest, fake)

    def test_single_item_combining_topics_cannot_hide_duplicated_topic(self):
        manifest, observation, target = self.good_observation("hooks")
        target.write_text(
            target.read_text()
            .replace(
                QUESTIONS[1],
                "Are expiration duration and expired/reused outcomes specified in requirements? [Clarity, Gap]",
            )
            .replace(QUESTIONS[2], QUESTIONS[0])
        )
        checks = self.checks(manifest, observation)
        self.assertTrue(checks["requested-coverage-heuristic"])
        self.assertFalse(checks["one-item-per-requested-topic-heuristic"])

    def test_gap_in_prose_or_source_citation_is_not_a_gap_marker(self):
        manifest, observation, target = self.good_observation()
        good = target.read_text()
        for replacement in (
            "[Clarity, Spec §FR-2]",
            "gap [Clarity, Spec §FR-2]",
            "[Clarity, Spec §FR-2, Gap",
        ):
            target.write_text(good.replace("[Clarity, Spec §FR-2, Gap]", replacement))
            self.assertFalse(
                self.checks(manifest, observation)[
                    "missing-policy-gap-markers-heuristic"
                ]
            )

    def test_topic_keywords_in_markers_do_not_supply_question_meaning(self):
        manifest, observation, target = self.good_observation()
        target.write_text(
            target.read_text().replace(
                QUESTIONS[-1],
                "Are requirements defined? [Completeness, Gap, retention]",
            )
        )
        self.assertFalse(
            self.checks(manifest, observation)["one-item-per-requested-topic-heuristic"]
        )

    def test_exact_ids_unchecked_states_and_prefix_invariants_remain(self):
        manifest, observation, target = self.good_observation()
        good = target.read_text()
        for bad, check in (
            (good.replace("CHK008", "CHK009"), "item-count-and-ids"),
            (good.replace("- [ ] CHK008", "- [x] CHK008"), "new-items-unchecked"),
            (good.replace("[X]", "[ ]"), "append-preserves-prefix"),
            (good + "- [ ] Hidden malformed item?\n", "no-malformed-items"),
        ):
            target.write_text(bad)
            self.assertFalse(self.checks(manifest, observation)[check])

    def test_claims_cannot_replace_constitution_reads_or_hook_actions(self):
        for case in ("append", "hooks"):
            manifest, observation, _ = self.good_observation(case)
            fake = copy.deepcopy(observation)
            fake["events"] = [
                event
                for event in fake["events"]
                if event.get("path") != ".specify/memory/constitution.md"
            ]
            fake["commentary"] = "I read the constitution."
            self.assertFalse(self.checks(manifest, fake)["required-context-reads"])
            if case == "hooks":
                fake = copy.deepcopy(observation)
                fake["events"] = [
                    event for event in fake["events"] if event["type"] != "hook"
                ]
                self.assertFalse(self.checks(manifest, fake)["automatic-hook-order"])

    def test_hook_offers_order_and_marker_hash_remain_strict(self):
        manifest, observation, target = self.good_observation("hooks")
        fake = copy.deepcopy(observation)
        fake["messages"] = [m for m in fake["messages"] if m["phase"] == "final_answer"]
        fake["commentary"] = "Automatic and optional hooks were offered and handled."
        self.assertFalse(self.checks(manifest, fake)["hook-announcements"])
        fake = copy.deepcopy(observation)
        post = fake["events"].pop()
        fake["events"].insert(0, post)
        self.assertFalse(self.checks(manifest, fake)["automatic-hook-order"])
        fake = copy.deepcopy(observation)
        fake["events"].append(
            {
                "type": "hook",
                "command": "pilot-optional-pre",
                "status": "completed",
                "exit_code": 0,
            }
        )
        self.assertFalse(self.checks(manifest, fake)["automatic-hook-order"])
        target.write_text(target.read_text() + "\n")
        self.assertFalse(self.checks(manifest, observation)["hook-marker-artifacts"])

    def test_pinned_dependency_copy_and_manifest_cannot_change(self):
        manifest, observation, _ = self.good_observation()
        instrument = self.output / "instrument/trace-v2.py"
        instrument.write_text(instrument.read_text() + "\n# changed\n")
        with self.assertRaisesRegex(ValueError, "instrument changed"):
            check_workspace(manifest, observation)

    def test_v1_bundle_identity_is_rejected(self):
        manifest, observation, _ = self.good_observation()
        value = json.loads(manifest.read_text())
        value.pop("checker_version")
        manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "newly prepared v3 bundle"):
            check_workspace(manifest, observation)

    def test_absence_provenance_pins_exact_baseline(self):
        path, _, _ = self.good_observation()
        manifest = json.loads(path.read_text())
        self.assertEqual(["specs/001-invitations/plan.md", "specs/001-invitations/tasks.md"],
                         manifest["pinned_absent_paths"])
        self.assertEqual(v1._sha(json.dumps(manifest["baseline"], sort_keys=True,
                                           separators=(",", ":")).encode()),
                         manifest["baseline_inventory_sha256"])

    def test_actual_hook_blocks_require_fields_and_normalized_commands(self):
        path, good, _ = self.good_observation("hooks")
        for old, replacement in (
            ("EXECUTE_COMMAND: pilot-pre-marker", "I will execute pilot-pre-marker"),
            ("EXECUTE_COMMAND: pilot-pre-marker", "EXECUTE_COMMAND: pilot.pre.marker"),
            ("Executing: `/pilot-pre-marker`", "Executing: `/wrong-command`"),
            ("To execute: `/pilot-optional-pre`", "I offered pilot-optional-pre"),
            ("Prompt: Run the optional pre marker only if requested later.", "Prompt: Later."),
            ("Description: Record that generation has not begun.", ""),
            ("To execute: `/pilot-optional-pre`", "To execute: `/pilot-optional-pre`\nTo execute: `/wrong`"),
            ("**Optional Pre-Hook**: Synthetic optional pre", "I will show an Optional Pre-Hook"),
        ):
            with self.subTest(replacement=replacement):
                observation = copy.deepcopy(good)
                observation["messages"][0]["text"] = observation["messages"][0]["text"].replace(old, replacement)
                self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_quoted_examples_future_plans_and_negated_blocks_do_not_count(self):
        path, good, _ = self.good_observation("hooks")
        for prefix, suffix in (
            ("I will render this later; here is an example:\n```text\n", "\n```"),
            ("The reference contains this sample:\n```text\n", "\n```"),
            ("I am not executing the following hook:\n", ""),
            ("I may execute this hook later:\n", ""),
            ("Example:\n", ""),
            ("Description: I will only show this example later.\n", ""),
            ("", "\nPrompt: I am not actually executing this hook."),
        ):
            with self.subTest(prefix=prefix):
                observation = copy.deepcopy(good)
                observation["messages"][0]["text"] = prefix + observation["messages"][0]["text"] + suffix
                self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_markdown_indented_code_is_not_an_action_announcement(self):
        path, good, _ = self.good_observation("hooks")
        for indentation in ("    ", "     ", "        ", "\t", "  \t "):
            with self.subTest(indentation=repr(indentation)):
                observation = copy.deepcopy(good)
                observation["messages"][0]["text"] = "\n".join(
                    indentation + line for line in observation["messages"][0]["text"].splitlines()
                )
                self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_hook_claims_deltas_and_final_only_blocks_do_not_pass(self):
        path, good, _ = self.good_observation("hooks")
        for mode in ("no-messages", "incomplete", "no-start", "final-only", "claims"):
            with self.subTest(mode=mode):
                observation = copy.deepcopy(good)
                if mode == "no-messages":
                    observation["messages"] = []
                elif mode == "incomplete":
                    observation["messages"][0]["status"] = "inProgress"
                elif mode == "no-start":
                    observation["messages"][0]["raw_start_index"] = None
                elif mode == "final-only":
                    observation["messages"][0]["phase"] = "final_answer"
                else:
                    observation["messages"][0]["text"] = "Automatic and optional hooks were offered and handled."
                self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_hook_blocks_must_follow_config_and_precede_action_in_same_phase(self):
        path, good, _ = self.good_observation("hooks")
        config = next(e for e in good["events"] if e.get("path") == ".specify/extensions.yml")
        write = next(e for e in good["events"] if e["type"] == "write")
        pre = next(e for e in good["events"] if e.get("command") == "pilot-pre-marker")
        post = next(e for e in good["events"] if e.get("command") == "pilot-post-marker")
        for message_index, start, finish in (
            (0, config["raw_start_index"] - 3, config["raw_start_index"] - 2),
            (0, pre["raw_start_index"] - 2, pre["raw_completion_index"] + 1),
            (0, 900, 901),
            (1, write["raw_start_index"] - 3, write["raw_start_index"] - 2),
            (1, post["raw_completion_index"] + 1, post["raw_completion_index"] + 2),
        ):
            with self.subTest(message_index=message_index, start=start):
                observation = copy.deepcopy(good)
                observation["messages"][message_index].update(raw_start_index=start, raw_completion_index=finish)
                self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_final_verification_needs_full_final_hash_after_writes_before_report(self):
        path, good, _ = self.good_observation()
        read_index = len(good["events"]) - 1
        write = good["events"][read_index - 1]
        for replacement in (
            {"read_sha256": "0" * 64},
            {"read_coverage": {"complete": False}},
            {"raw_start_index": write["raw_start_index"] - 2,
             "raw_completion_index": write["raw_start_index"] - 1},
            {"raw_start_index": 1002, "raw_completion_index": 1003},
            {"status": "failed"},
            {"raw_completion_index": None},
        ):
            with self.subTest(replacement=replacement):
                observation = copy.deepcopy(good)
                observation["events"][read_index].update(replacement)
                self.assertFalse(self.checks(path, observation)["final-artifact-verification"])

    def test_post_offers_cannot_precede_verification_even_after_write(self):
        path, observation, _ = self.good_observation("hooks")
        write = next(e for e in observation["events"] if e["type"] == "write")
        observation["messages"][1].update(raw_start_index=write["raw_completion_index"] + 1,
                                          raw_completion_index=write["raw_completion_index"] + 2)
        self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_final_report_must_follow_completed_post_hook(self):
        path, good, _ = self.good_observation("hooks")
        verification = next(e for e in good["events"] if e.get("read_sha256"))
        post = next(e for e in good["events"] if e.get("command") == "pilot-post-marker")
        for start, finish in (
            (verification["raw_completion_index"] + 1, verification["raw_completion_index"] + 2),
            (post["raw_start_index"], post["raw_completion_index"] + 1),
            (post["raw_completion_index"], post["raw_completion_index"] + 1),
        ):
            with self.subTest(start=start):
                observation = copy.deepcopy(good)
                observation["messages"][-1].update(raw_start_index=start, raw_completion_index=finish)
                checks = self.checks(path, observation)
                self.assertTrue(checks["final-artifact-verification"])
                self.assertTrue(checks["hook-announcements"])
                self.assertFalse(checks["final-report-after-hooks"])
                self.assertFalse(check_workspace(path, observation)["automated_checks_passed"])

    def test_a_recovered_failed_write_is_never_forgiven(self):
        path, observation, _ = self.good_observation("hooks")
        write_index = next(i for i, e in enumerate(observation["events"]) if e["type"] == "write")
        observation["events"].insert(write_index, {
            "type": "unknown", "status": "failed", "exit_code": 0,
            "reason": "zsh: can't create temp file for here document: operation not permitted",
        })
        checks = self.checks(path, observation)
        self.assertFalse(checks["classified-events"])
        self.assertFalse(checks["successful-events"])
        self.assertTrue(checks["hook-marker-artifacts"])

    def test_v2_bundle_and_observation_identities_are_rejected(self):
        path, observation, _ = self.good_observation()
        observation["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "unsupported v3 observation"):
            check_workspace(path, observation)
        manifest = json.loads(path.read_text())
        manifest["checker_version"] = 2
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "newly prepared v3 bundle"):
            check_workspace(path, observation)

    def test_cli_reports_exclusively_without_model_calls(self):
        manifest, observation, _ = self.good_observation()
        observation_path = self.output / "simulation.json"
        observation_path.write_text(json.dumps(observation))
        report_path = self.output / "simulation-report.json"
        args = [
            "check",
            str(manifest),
            str(observation_path),
            "--output",
            str(report_path),
        ]
        self.assertEqual(0, main(args))
        self.assertEqual(
            "offline-simulation", json.loads(report_path.read_text())["evidence_kind"]
        )
        with self.assertRaises(SystemExit):
            main(args)


if __name__ == "__main__":
    unittest.main()
