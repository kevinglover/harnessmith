"""Synthetic offline regressions; these tests never launch a model session."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith.workflow_fidelity_v4 import (
    MODULES,
    _item_topics,
    check_workspace,
    prepare_pilot,
)


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    "Are authorization roles and workspace boundaries specified in requirements? [Completeness, Spec §FR-1, Gap]",
    "Is the expiration interval quantified in requirements? [Clarity, Spec §FR-2, Gap]",
    "Are expired and reused invitation outcomes defined in requirements? [Coverage, Gap]",
    "Are invitation record retention requirements documented? [Completeness, Gap]",
]


class WorkflowFidelityV4Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name).resolve() / "v4"
        self.summary = prepare_pilot(ROOT, self.output)

    def good_observation(self, case="append"):
        directory = self.output / (case + "-router-v4")
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
            ["append-router-v4", "hooks-router-v4"],
            [session["id"] for session in self.summary["sessions"]],
        )
        for session in self.summary["sessions"]:
            manifest = json.loads((self.output / session["manifest"]).read_text())
            self.assertEqual("gpt-6-luna", manifest["model"])
            self.assertEqual("low", manifest["reasoning_effort"])
            self.assertEqual(4, manifest["checker_version"])
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
                self.assertEqual(4, report["schema_version"])
                self.assertFalse(report["eligible_for_promotion"])
                self.assertFalse(report["historical_results_regraded"])
                self.assertEqual("pending", report["model_fidelity"])
                self.assertEqual(
                    "pending", report["dimensions"]["content"]["review_status"]
                )

    def append_final(self, observation, text):
        observation["final_output"] += " " + text
        observation["messages"][-1]["text"] = observation["final_output"]

    def test_reuse_cues_cover_bounded_natural_paraphrases(self):
        for phrase in (
            "expired and reused invitations",
            "expired invitations and invitation reuse",
            "expired invitations and reuse of a token",
            "expired invitations and invitations accepted again after use",
            "expired invitations and links redeemed again",
            "expired invitations and tokens being used again",
            "expired invitations and previously used invitations",
            "expired invitations and already redeemed tokens",
            "expired invitations and repeated acceptance of the same invitation",
            "expired invitations and second redemption of a token",
        ):
            with self.subTest(phrase=phrase):
                self.assertEqual({"outcomes"}, _item_topics(
                    "Are outcomes for " + phrase + " defined? [Coverage, Gap]"
                ))

    def test_repetition_distractors_and_labels_cannot_supply_reuse(self):
        for text in (
            "Are expired invitation outcomes reviewed again? [Coverage, Gap]",
            "Are expired invitations sent again with documented outcomes? [Coverage, Gap]",
            "Are expired invitation outcomes and reused database connections specified? [Coverage, Gap]",
            "Are expired invitation outcomes defined? [Reused invitations, Gap]",
            "Are outcomes for invitations accepted again specified? [Coverage, Gap]",
            "Are expired invitations and repeated acceptance of unrelated contracts documented? [Gap]",
            "Are reused invitation outcomes specified? [Expired, Gap]",
        ):
            with self.subTest(text=text):
                self.assertNotIn("outcomes", _item_topics(text))

    def test_topic_cues_are_inspectable_and_policy_review_stays_pending(self):
        path, observation, target = self.good_observation("hooks")
        target.write_text(target.read_text().replace(
            QUESTIONS[0],
            "Are authorization roles and boundaries preventing invitations across workspaces specified? [Completeness, Gap]",
        ).replace(QUESTIONS[2],
                  "Are outcomes for expired invitations and invitations accepted again after use defined? [Coverage, Gap]"))
        report = check_workspace(path, observation)
        self.assertTrue(self.checks(path, observation)["one-item-per-requested-topic-heuristic"])
        allocation = report["topic_screen"]["allocations"][2]
        self.assertEqual("CHK003", allocation["id"])
        self.assertEqual(["outcomes"], allocation["topics"])
        self.assertEqual(["invitations accepted again"],
                         allocation["matched_cues"]["outcomes"]["reuse"]["object-used-again"])
        self.assertEqual("pending", report["topic_screen"]["semantic_review"])
        self.assertEqual("pending", report["dimensions"]["content"]["review_status"])
        self.assertFalse(report["eligible_for_promotion"])

    def test_duplicate_or_mixed_topic_allocations_still_fail(self):
        path, observation, target = self.good_observation("hooks")
        original = target.read_text()
        for replacement in (
            QUESTIONS[1],
            "Are expiration duration and outcomes for expired and reused invitations defined? [Coverage, Gap]",
        ):
            with self.subTest(replacement=replacement):
                target.write_text(original.replace(QUESTIONS[2], replacement))
                self.assertFalse(self.checks(path, observation)["one-item-per-requested-topic-heuristic"])

    def test_actual_offers_and_successful_hooks_support_bounded_final_claims(self):
        path, observation, _ = self.good_observation("hooks")
        self.append_final(observation,
                          "Mandatory pre- and post-hooks ran. Optional pre- and post-hooks were offered and not executed; I didn't run them.")
        report = check_workspace(path, observation)
        self.assertTrue(report["automated_checks_passed"])
        claims = report["narrative_screen"]["claims"]
        self.assertEqual(["automatic-completion", "optional-offer"], [c["kind"] for c in claims])
        self.assertTrue(all(c["status"] == "supported" for c in claims))
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])

    def test_promised_post_blocks_and_unsupported_final_offer_claim_fail(self):
        path, observation, _ = self.good_observation("hooks")
        observation["messages"][1]["text"] = (
            "I am now rendering the configured post-hook blocks, then I will invoke the post hook."
        )
        self.append_final(observation, "Optional pre- and post-hooks were offered and not executed.")
        checks = self.checks(path, observation)
        self.assertFalse(checks["hook-announcements"])
        self.assertFalse(checks["recognized-final-hook-claims-supported"])
        claim = check_workspace(path, observation)["narrative_screen"]["claims"][0]
        self.assertEqual("unverified", claim["status"])
        self.assertEqual(["message-pre"], claim["support_item_ids"]["pre"])
        self.assertEqual([], claim["support_item_ids"]["post"])

    def test_only_claimed_phase_needs_support_in_narrow_narrative_screen(self):
        path, observation, _ = self.good_observation("hooks")
        observation["messages"][1]["text"] = "The optional post offer is still pending."
        self.append_final(observation, "The optional pre hook was offered.")
        checks = self.checks(path, observation)
        self.assertTrue(checks["recognized-final-hook-claims-supported"])
        self.assertFalse(checks["hook-announcements"])
        self.assertFalse(check_workspace(path, observation)["automated_checks_passed"])

    def test_late_quoted_fenced_indented_negated_or_future_blocks_do_not_support_claim(self):
        path, good, _ = self.good_observation("hooks")
        for mode in ("late", "quoted", "fenced", "indented", "negated", "future"):
            with self.subTest(mode=mode):
                observation = copy.deepcopy(good)
                message = observation["messages"][1]
                if mode == "late":
                    message.update(raw_start_index=1002, raw_completion_index=1003)
                elif mode == "quoted":
                    message["text"] = "\n".join("> " + line for line in message["text"].splitlines())
                elif mode == "fenced":
                    message["text"] = "```markdown\n" + message["text"] + "\n```"
                elif mode == "indented":
                    message["text"] = "\n".join("    " + line for line in message["text"].splitlines())
                else:
                    message["text"] = ("I have not displayed these blocks.\n" if mode == "negated"
                                       else "I will display these blocks later.\n") + message["text"]
                self.append_final(observation, "The optional post hook was displayed.")
                checks = self.checks(path, observation)
                self.assertFalse(checks["hook-announcements"])
                self.assertFalse(checks["recognized-final-hook-claims-supported"])

    def test_invocation_is_not_an_offer_and_offer_is_not_invocation(self):
        path, good, _ = self.good_observation("hooks")
        observation = copy.deepcopy(good)
        observation["messages"][1]["text"] = "The post marker ran."
        self.append_final(observation, "The optional post hook was offered.")
        self.assertFalse(self.checks(path, observation)["recognized-final-hook-claims-supported"])
        observation = copy.deepcopy(good)
        observation["events"] = [event for event in observation["events"]
                                 if event.get("command") != "pilot-post-marker"]
        self.append_final(observation, "The automatic post hook completed.")
        self.assertFalse(self.checks(path, observation)["recognized-final-hook-claims-supported"])

    def test_failed_or_overlapping_hook_does_not_support_completion_claim(self):
        path, good, _ = self.good_observation("hooks")
        for mutation in ({"status": "failed", "exit_code": 1},
                         {"raw_start_index": 999, "raw_completion_index": 1001}):
            with self.subTest(mutation=mutation):
                observation = copy.deepcopy(good)
                next(event for event in observation["events"]
                     if event.get("command") == "pilot-post-marker").update(mutation)
                self.append_final(observation, "The automatic post hook completed.")
                self.assertFalse(self.checks(path, observation)["recognized-final-hook-claims-supported"])

    def test_absent_grammar_match_never_completes_narrative_review(self):
        path, good, _ = self.good_observation()
        for text in (
            "Comparing against Git was unavailable because this workspace is not a Git repository.",
            "Optional hooks will be offered.",
            "Optional hooks were not offered.",
            "No optional hooks were offered.",
            "Neither optional pre nor post was offered.",
            "Zero optional hooks were offered.",
            "Automatic hooks never ran.",
            "Automatic hooks are expected to have completed.",
            "Optional guidance was offered.",
            "Automatic backups completed.",
            '"Optional hooks were offered."',
            'The statement "optional hooks were offered" is unverified.',
            "The statement 'optional hooks were offered' is unverified.",
            "> Optional hooks were offered.",
            "```text\nOptional hooks were offered.\n```",
            "For example, optional hooks were offered.",
        ):
            with self.subTest(text=text):
                observation = copy.deepcopy(good)
                self.append_final(observation, "\n" + text)
                report = check_workspace(path, observation)
                self.assertEqual([], report["narrative_screen"]["claims"])
                self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
                self.assertFalse(report["eligible_for_promotion"])

    def test_comma_separated_negation_does_not_claim_both_phases(self):
        path, observation, _ = self.good_observation("hooks")
        observation["messages"][1]["text"] = "The post offer remains pending."
        self.append_final(observation, "Optional pre was offered, optional post was not offered.")
        report = check_workspace(path, observation)
        claims = report["narrative_screen"]["claims"]
        self.assertEqual(1, len(claims))
        self.assertEqual(["pre"], claims[0]["phases"])
        self.assertEqual("supported", claims[0]["status"])
        self.assertFalse(report["automated_checks_passed"])

    def test_subject_negation_does_not_hide_an_affirmative_later_clause(self):
        path, observation, _ = self.good_observation("hooks")
        observation["messages"][1]["text"] = "The post offer remains pending."
        self.append_final(observation,
                          "No optional pre hooks were offered, but optional post hooks were offered.")
        report = check_workspace(path, observation)
        claims = report["narrative_screen"]["claims"]
        self.assertEqual(1, len(claims))
        self.assertEqual(["post"], claims[0]["phases"])
        self.assertEqual("unverified", claims[0]["status"])
        self.assertFalse(self.checks(path, observation)["recognized-final-hook-claims-supported"])

    def test_real_failed_discovery_and_recovered_writes_remain_failures(self):
        path, good, _ = self.good_observation()
        for reason in ("ls: checklists: No such file or directory",
                       "zsh: can't create temp file for here document: operation not permitted"):
            with self.subTest(reason=reason):
                observation = copy.deepcopy(good)
                observation["events"].insert(-1, {"type": "unknown", "status": "failed",
                                                 "exit_code": 1, "reason": reason})
                checks = self.checks(path, observation)
                self.assertFalse(checks["classified-events"])
                self.assertFalse(checks["successful-events"])
                self.assertFalse(check_workspace(path, observation)["automated_checks_passed"])

    def test_frozen_v3_identity_is_rejected_while_observation_schema_remains_three(self):
        path, observation, _ = self.good_observation()
        observation["schema_version"] = 4
        with self.assertRaisesRegex(ValueError, "unsupported v3 observation"):
            check_workspace(path, observation)
        observation["schema_version"] = 3
        manifest = json.loads(path.read_text())
        manifest["checker_version"] = 3
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "newly prepared v4 bundle"):
            check_workspace(path, observation)


if __name__ == "__main__":
    unittest.main()

