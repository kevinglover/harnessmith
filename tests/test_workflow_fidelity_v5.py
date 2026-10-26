"""Fresh synthetic v5 controls only; no historical regrades or live sessions."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith import workflow_fidelity_v3 as v3
from harnessmith.workflow_fidelity_v5 import (
    MODULES, _execution_error_claims, _final_report, check_workspace, main,
    prepare_pilot,
)


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    "Are authorization roles and workspace boundaries specified? [Completeness, Gap]",
    "Is the expiration interval quantified? [Clarity, Gap]",
    "Are expired and reused invitation outcomes defined? [Coverage, Gap]",
    "Are invitation record retention requirements documented? [Completeness, Gap]",
]
CACHE_NOISE = (
    "python3: warning: confstr() failed with code 5: couldn't get path of "
    "DARWIN_USER_TEMP_DIR; using /tmp instead\n"
    "python3: error: couldn't create cache file '/tmp/xcrun_db-AbC123' "
    "(errno=Operation not permitted)\n"
)


class WorkflowFidelityV5Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "v5"
        self.summary = prepare_pilot(ROOT, self.output)

    def good(self, case="append"):
        directory = self.output / (case + "-router-v5")
        path = directory / "manifest.json"
        manifest = json.loads(path.read_text())
        target = directory / "workspace" / manifest["target"]
        before = bytes.fromhex(manifest["baseline_target_hex"]).decode()
        initial = before or (
            "# Security Requirements Checklist\n\n**Purpose**: Security requirements review.\n"
            "**Created**: 2026-10-25\n\n**Ownership**: Reviewer-owned. `[x]` means "
            "reviewer approval of requirements quality, not implementation completion.\n\n"
            "## Notes\n\n`/speckit-implement` reads checklist state but does not modify markers.\n"
        )
        questions = QUESTIONS[1:] if case == "append" else QUESTIONS
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(initial + "\n## Requirement Clarity\n\n" + "\n".join(
            "- [ ] CHK%03d %s" % (manifest["first_id"] + i, q) for i, q in enumerate(questions)) + "\n")
        events = [{"type": "read", "path": v1.PACKAGE + "/SKILL.md"},
                  {"type": "read", "path": v1.PACKAGE + "/references/project-generation.md"}]
        if case == "hooks":
            events += [{"type": "read", "path": ".specify/extensions.yml"},
                       {"type": "hook", "command": "pilot-pre-marker"}]
        events += [{"type": "setup", "command": v1.SETUP_COMMAND}]
        events += [{"type": "read", "path": p} for p in manifest["required_reads"] if p != ".specify/extensions.yml"]
        events += [{"type": "write", "path": manifest["target"]},
                   {"type": "read", "path": manifest["target"], "read_coverage": {"complete": True},
                    "read_sha256": v1._sha(target.read_bytes())}]
        if case == "hooks":
            events += [{"type": "hook", "command": "pilot-post-marker"}]
            markers = [
                {"command": "pilot-pre-marker", "target_exists": False, "target_sha256": None},
                {"command": "pilot-post-marker", "target_exists": True, "target_sha256": v1._sha(target.read_bytes())},
            ]
            (directory / "workspace" / v1.MARKERS).write_text("\n".join(json.dumps(m) for m in markers) + "\n")
        for i, event in enumerate(events):
            event.update(status="completed", exit_code=0, raw_item_id="op-" + str(i),
                         raw_operation_index=0, raw_start_index=10 * i + 10, raw_completion_index=10 * i + 11)
        messages = []
        if case == "hooks":
            for pre in (True, False):
                phase = "pre" if pre else "post"
                text = "\n\n".join("\n".join([heading] + fields)
                                   for heading, fields in [v3._hook_fields(pre, optional) for optional in (False, True)])
                event = next(e for e in events if e.get("command") == "pilot-" + phase + "-marker")
                messages.append(self.message(text, "message-" + phase, event["raw_start_index"] - 4))
        final = ("Appended to" if before else "Created") + " " + str(target) + " with " + str(manifest["new_items"]) + " unchecked questions. Focus: security; depth: standard; reviewer during PR review."
        messages.append(self.message(final, "final", 1000, "final_answer"))
        return path, {"schema_version": 4, "evidence_kind": "offline-simulation",
                      "completed": True, "model": "gpt-6-luna", "events": events,
                      "messages": messages, "final_output": final, "command_records": [],
                      "commentary": [m["text"] for m in messages if m["phase"] == "commentary"]}, target

    @staticmethod
    def message(text, item_id="claim", index=500, phase="commentary"):
        return {"text": text, "raw_item_id": item_id, "raw_start_index": index,
                "raw_completion_index": index + 1, "status": "completed", "phase": phase}

    @staticmethod
    def record(output, command="python3 .pilot/marker_hook.py inferred-id", exit_code=1, index=300):
        return {"raw_item_id": "execution", "raw_start_index": index,
                "raw_completion_index": index + 1, "status": "completed", "exit_code": exit_code,
                "raw_command": command, "aggregated_output": output, "lifecycle_valid": True}

    def checks(self, path, observation):
        report = check_workspace(path, observation)
        return {c["name"]: c["passed"] for d in report["dimensions"].values() for c in d.get("checks", [])}

    def test_preparation_has_actual_dependencies_and_new_version_identity(self):
        self.assertEqual(["append-router-v5", "hooks-router-v5"], [s["id"] for s in self.summary["sessions"]])
        self.assertEqual(0, self.summary["live_sessions_started"])
        self.assertEqual(4, self.summary["observation_schema_version"])
        self.assertEqual(5, self.summary["schema_version"])
        self.assertIn("checker-v4.py", MODULES)
        self.assertIn("trace-v4.py", MODULES)
        for session in self.summary["sessions"]:
            manifest = json.loads((self.output / session["manifest"]).read_text())
            self.assertEqual(5, manifest["checker_version"])
            self.assertEqual("router-v5", manifest["strategy"])
            self.assertEqual(set(MODULES) | {"rubric.md", "pilot.json"}, set(manifest["provenance"]["instruments"]))
            self.assertEqual("1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45", manifest["provenance"]["source_sha256"])
            for name, source in MODULES.items():
                self.assertEqual((ROOT / source).read_bytes(), (self.output / "instrument" / name).read_bytes())
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_good_cases_pass_automation_with_all_manual_reviews_pending(self):
        for case in ("append", "hooks"):
            with self.subTest(case=case):
                path, observation, _ = self.good(case)
                report = check_workspace(path, observation)
                self.assertTrue(report["automated_checks_passed"], self.checks(path, observation))
                self.assertEqual(5, report["schema_version"])
                self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
                self.assertEqual("pending", report["dimensions"]["workflow"]["review_status"])
                self.assertEqual("pending", report["dimensions"]["content"]["review_status"])
                self.assertFalse(report["eligible_for_promotion"])
                self.assertFalse(report["historical_results_regraded"])

    def test_singular_modifier_is_bounded_and_all_counts_remain_consistent(self):
        target = "/tmp/security.md"
        suffix = " Focus: security; depth: standard; reviewer during PR review."
        for count in ("four item checklist", "four-item checklist", "4-item checklist", "four question checklist", "four items", "item count: four"):
            with self.subTest(count=count):
                self.assertTrue(_final_report("Created " + target + " with " + count + "." + suffix, target, 4, False))
        for report in (
            "Created " + target + " with three item checklist.",
            "Created " + target + " with five-item checklist.",
            "Created " + target + ". I plan to add four item checklist.",
            "I will create " + target + " with four-item checklist.",
            "I did not create " + target + " with four item checklist.",
            "Created " + target + ". Not four item checklist.",
            "Created " + target + " with four-item checklist. Added three items.",
            "Created " + target + " with four items. Created five-item checklist.",
            "Appended " + target + " with four-item checklist.",
            "Created " + target + " with four item report.",
        ):
            with self.subTest(report=report):
                self.assertFalse(_final_report(report + suffix, target, 4, False))

    def test_invented_or_duplicate_pre_blocks_fail_even_with_correct_later_blocks(self):
        path, good, _ = self.good("hooks")
        for extra in (
            "Automatic Pre-Hook: specify-context\nDescription: Invented context.\nExecuting: /specify-context\nEXECUTE_COMMAND: specify-context",
            "Optional Pre-Hook: speckit-audit\nCommand: /speckit-audit\nTo execute: /speckit-audit",
            "- Automatic Pre-Hook: invented\n  Description: Invented hook.\n  Executing: /invented\n  EXECUTE_COMMAND: invented",
            "+ **Optional Pre-Hook**: invented\n  Command: /invented",
            "1. Automatic Pre-Hook: invented\n  Executing: /invented",
            good["messages"][0]["text"],
        ):
            with self.subTest(extra=extra):
                observation = copy.deepcopy(good)
                observation["messages"].insert(0, self.message(extra, "invented", 1))
                checks = self.checks(path, observation)
                self.assertFalse(checks["configured-pre-hook-blocks-only"])
                self.assertFalse(checks["hook-announcements"])
                self.assertFalse(check_workspace(path, observation)["automated_checks_passed"])

    def test_quoted_and_fenced_bullet_pre_blocks_are_not_emitted_blocks(self):
        path, good, _ = self.good("hooks")
        invented = "- Automatic Pre-Hook: invented\n  Executing: /invented"
        for text in ("\n".join("> " + line for line in invented.splitlines()),
                     "```text\n" + invented + "\n```",
                     "\n".join("    " + line for line in invented.splitlines())):
            observation = copy.deepcopy(good)
            observation["messages"].insert(0, self.message(text, "example", 1))
            self.assertTrue(self.checks(path, observation)["configured-pre-hook-blocks-only"])
            self.assertTrue(self.checks(path, observation)["hook-announcements"])

    def test_exact_fields_and_pre_timing_are_still_required(self):
        path, good, _ = self.good("hooks")
        for field in ("pilot-pre-marker", "Record that generation has not begun.", "pilot-optional-pre", "Run the optional pre marker only if requested later."):
            observation = copy.deepcopy(good)
            observation["messages"][0]["text"] = observation["messages"][0]["text"].replace(field, "invented")
            self.assertFalse(self.checks(path, observation)["hook-announcements"])
        for index in (1, 200):
            observation = copy.deepcopy(good)
            observation["messages"][0].update(raw_start_index=index, raw_completion_index=index + 1)
            self.assertFalse(self.checks(path, observation)["hook-announcements"])

    def test_unsupported_error_story_is_screened_in_commentary_and_final(self):
        path, good, _ = self.good()
        story = "The first adapter invocation returned “Unknown synthetic command” for my initially inferred ID."
        for phase in ("commentary", "final_answer"):
            observation = copy.deepcopy(good)
            observation["messages"].insert(0, self.message(story, phase=phase))
            report = check_workspace(path, observation)
            self.assertFalse(self.checks(path, observation)["recognized-execution-error-claims-supported"])
            claim = report["narrative_screen"]["execution_error_claims"][0]
            self.assertEqual("unverified", claim["status"])
            self.assertEqual(phase, claim["phase"])
            self.assertEqual([], claim["support_item_ids"])

    def test_matching_earlier_return_supports_claim_without_erasing_failed_action(self):
        path, observation, _ = self.good()
        observation["messages"].insert(0, self.message("The Python setup command failed with SyntaxError."))
        observation["command_records"] = [self.record("SyntaxError: invalid syntax\n", "python3 " + v1.SETUP, exit_code=0)]
        observation["events"].append({"type": "unknown", "status": "failed", "exit_code": 0, "failure_output": True})
        checks = self.checks(path, observation)
        self.assertTrue(checks["recognized-execution-error-claims-supported"])
        self.assertFalse(checks["successful-events"])
        self.assertFalse(checks["classified-events"])
        self.assertFalse(check_workspace(path, observation)["automated_checks_passed"])
        claim = check_workspace(path, observation)["narrative_screen"]["execution_error_claims"][0]
        self.assertEqual(["execution"], claim["support_item_ids"])

    def test_support_requires_matching_payload_subject_and_completed_prior_lifecycle(self):
        story = "The first adapter invocation returned Unknown synthetic command."
        good = {"messages": [self.message(story)], "command_records": [self.record("Unknown synthetic command: inferred-id")]}
        self.assertEqual("supported", _execution_error_claims(good)[0]["status"])
        for changes in (
            {"aggregated_output": "SyntaxError: invalid syntax"},
            {"raw_command": "python3 unrelated.py"},
            {"raw_completion_index": 500},
            {"raw_start_index": 600, "raw_completion_index": 601},
            {"status": "inProgress"}, {"raw_start_index": None},
            {"lifecycle_valid": False}, {"lifecycle_valid": None},
        ):
            observation = copy.deepcopy(good)
            observation["command_records"][0].update(changes)
            self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"], changes)

    def test_subject_names_in_output_arguments_paths_or_compounds_do_not_prove_invocation(self):
        for story, diagnostic, commands in (
            ("The adapter invocation returned Unknown synthetic command.", "Unknown synthetic command", (
                "printf 'marker_hook.py Unknown synthetic command\\n'", "cat .pilot/marker_hook.py",
                "python3 unrelated.py .pilot/marker_hook.py", "false && python3 .pilot/marker_hook.py bad-id || true")),
            ("The setup command failed with SyntaxError.", "SyntaxError", (
                "printf 'check-prerequisites.sh SyntaxError\\n'", "cat " + v1.SETUP,
                "python3 -c 'print(\"check-prerequisites.sh SyntaxError\")'",
                "false && python3 " + v1.SETUP + " || true")),
            ("The Python command returned SyntaxError.", "SyntaxError", ("printf 'python3 SyntaxError'", "cat python3")),
        ):
            for command in commands:
                with self.subTest(story=story, command=command):
                    observation = {"messages": [self.message(story)],
                                   "command_records": [self.record(diagnostic, command, 1)]}
                    self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"])

    def test_past_assertion_survives_expected_qualification_or_future_recovery(self):
        for text in (
            "The adapter invocation returned Unknown synthetic command as expected.",
            "The expected adapter invocation returned Unknown synthetic command.",
            "The adapter invocation returned Unknown synthetic command and I will recover.",
        ):
            observation = {"messages": [self.message(text)], "command_records": []}
            self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"], text)
            observation["command_records"] = [self.record("Unknown synthetic command")]
            self.assertEqual("supported", _execution_error_claims(observation)[0]["status"], text)
        for text in (
            "I expect that the adapter invocation returned Unknown synthetic command.",
            "The adapter invocation would have returned Unknown synthetic command.",
            "The adapter invocation returned Unknown synthetic command if it was executed.",
            "For example, the adapter invocation returned Unknown synthetic command.",
        ):
            self.assertEqual([], _execution_error_claims({"messages": [self.message(text)]}), text)

    def test_cache_diagnostic_can_be_supported_but_success_is_not_setup_failure(self):
        record = self.record(CACHE_NOISE + '{"FEATURE_DIR":"specs/001-invitations"}', "sh " + v1.SETUP, 0)
        observation = {"command_records": [record], "messages": [self.message("The setup command returned a cache diagnostic.")]}
        self.assertEqual("supported", _execution_error_claims(observation)[0]["status"])
        for verb in ("failed", "FAILED"):
            observation["messages"][0]["text"] = "The setup command " + verb + " with a cache diagnostic."
            self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"])
        observation["messages"][0]["text"] = "The script returned no SyntaxError."
        self.assertEqual([], _execution_error_claims(observation))

    def test_unsent_deltas_and_nonassertions_cannot_become_claims_or_review_pass(self):
        path, good, _ = self.good()
        text = "The adapter invocation returned Unknown synthetic command."
        for wrapper in (lambda s: '"' + s + '"', lambda s: "> " + s,
                        lambda s: "```text\n" + s + "\n```", lambda s: "    " + s,
                        lambda s: "If " + s, lambda s: "For example, " + s,
                        lambda s: s.replace("returned", "never returned"),
                        lambda s: s.replace("returned", "returned no"),
                        lambda s: s.replace("The adapter", "No adapter"),
                        lambda s: s.replace("returned", "would have returned")):
            observation = copy.deepcopy(good)
            observation["messages"].insert(0, self.message(wrapper(text)))
            report = check_workspace(path, observation)
            self.assertEqual([], report["narrative_screen"]["execution_error_claims"])
            self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
            self.assertEqual("pending", report["dimensions"]["workflow"]["review_status"])
            self.assertFalse(report["eligible_for_promotion"])
        observation = copy.deepcopy(good)
        observation["commentary"].append(text)
        observation["messages"].append({**self.message(text), "status": "inProgress"})
        self.assertEqual([], check_workspace(path, observation)["narrative_screen"]["execution_error_claims"])

    def test_literal_execution_needs_an_earlier_record_not_just_a_promise(self):
        observation = {"messages": [self.message("I invoked `/pilot-pre-marker`." )], "command_records": []}
        self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"])
        observation["command_records"] = [self.record("", "python3 .pilot/marker_hook.py pilot-pre-marker", 0)]
        self.assertEqual("supported", _execution_error_claims(observation)[0]["status"])
        observation["messages"][0]["text"] = "I will invoke `/pilot-pre-marker`."
        self.assertEqual([], _execution_error_claims(observation))

    def test_execution_quotes_suffixes_and_success_claims_are_not_evidence(self):
        observation = {"messages": [self.message('The example says "I invoked `/pilot-pre-marker`."')],
                       "command_records": [self.record("", "python3 .pilot/marker_hook.py pilot-pre-marker", 0)]}
        self.assertEqual([], _execution_error_claims(observation))
        observation["messages"][0]["text"] = '"I invoked `/pilot-pre-marker`."'
        self.assertEqual([], _execution_error_claims(observation))
        observation["messages"][0]["text"] = "I invoked `/pilot-pre-marker`."
        observation["command_records"][0]["raw_command"] += "-different"
        self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"])
        observation["command_records"] = [self.record("Unknown synthetic command", "python3 .pilot/marker_hook.py pilot-pre-marker", 1)]
        observation["messages"][0]["text"] = "I successfully invoked `/pilot-pre-marker`."
        self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"])
        observation["messages"][0]["text"] = "I ran `false`."
        for command in ("printf 'false'", "cat false", "true && false", "python3 -c 'print(\"false\")'"):
            observation["command_records"] = [self.record("false", command, 0)]
            self.assertEqual("unverified", _execution_error_claims(observation)[0]["status"], command)
        observation["command_records"] = [self.record("", "/bin/sh -c 'false'", 1)]
        self.assertEqual("supported", _execution_error_claims(observation)[0]["status"])

    def test_failed_actions_and_missing_context_are_never_waived(self):
        path, good, _ = self.good("hooks")
        for change in ("missing-constitution", "failed-command", "masked-failure"):
            observation = copy.deepcopy(good)
            if change == "missing-constitution":
                observation["events"] = [e for e in observation["events"] if e.get("path") != ".specify/memory/constitution.md"]
            else:
                observation["events"].append({"type": "unknown", "status": "failed", "exit_code": 1 if change == "failed-command" else 0})
            self.assertFalse(check_workspace(path, observation)["automated_checks_passed"])
            checks = self.checks(path, observation)
            if change == "missing-constitution":
                self.assertFalse(checks["required-context-reads"])
                self.assertFalse(checks["context-before-write"])
            else:
                self.assertFalse(checks["successful-events"])

    def test_old_identity_schema_and_changed_instruments_are_rejected(self):
        path, observation, _ = self.good()
        observation["schema_version"] = 3
        with self.assertRaisesRegex(ValueError, "unsupported v4 observation"):
            check_workspace(path, observation)
        observation["schema_version"] = 4
        manifest = json.loads(path.read_text())
        manifest["checker_version"] = 4
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "newly prepared v5 bundle"):
            check_workspace(path, observation)
        manifest["checker_version"] = 5
        manifest["provenance"]["instruments"]["trace-v4.py"] = "0" * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "dependency version differs"):
            check_workspace(path, observation)

    def test_cli_writes_new_report_and_refuses_overwrite(self):
        path, observation, _ = self.good()
        observation_path, report_path = self.output / "observation.json", self.output / "report.json"
        observation_path.write_text(json.dumps(observation))
        argv = ["check", str(path), str(observation_path), "--output", str(report_path)]
        self.assertEqual(0, main(argv))
        with self.assertRaises(SystemExit):
            main(argv)


if __name__ == "__main__":
    unittest.main()
