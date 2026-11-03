"""New synthetic v6 controls only; no old observations or captured code runs."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith.workflow_fidelity_v6 import (
    MODULES, _artifact_claims, _extension_checks, _git_claims, check_workspace,
    _separate_final_readback, main, prepare_pilot,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = "specs/001-invitations/checklists/security.md"
READ_STORY = "The final file read shows the existing content and checkbox states intact."
GIT_STORY = ("One attempted comparison against Git history could not run because "
             "the workspace was not recognized as a Git repository.")


class WorkflowFidelityV6Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "v6"
        self.summary = prepare_pilot(ROOT, self.output)

    @staticmethod
    def message(text, index=500, phase="commentary"):
        return {"text": text, "raw_item_id": "message-" + str(index),
                "raw_start_index": index, "raw_completion_index": index + 1,
                "status": "completed", "phase": phase}

    @staticmethod
    def record(index=300, command=None, output="", exit_code=0):
        return {"raw_item_id": "op-" + str(index), "raw_start_index": index,
                "raw_completion_index": index + 1, "status": "completed",
                "exit_code": exit_code, "raw_command": command or "cat " + TARGET,
                "aggregated_output": output, "lifecycle_valid": True, "cwd_relative": "."}

    def event(self, kind, index, **fields):
        record = self.record(index)
        return {"type": kind, **{key: record[key] for key in (
            "raw_item_id", "raw_start_index", "raw_completion_index", "status", "exit_code")},
            "raw_operation_index": 0, **fields}

    def good(self):
        directory = self.output / "append-router-v6"
        path = directory / "manifest.json"
        manifest = json.loads(path.read_text())
        target = directory / "workspace" / TARGET
        before = bytes.fromhex(manifest["baseline_target_hex"])
        questions = ["Is the expiration interval quantified? [Clarity, Gap]",
                     "Are expired and reused invitation outcomes defined? [Coverage, Gap]",
                     "Are invitation record retention requirements documented? [Completeness, Gap]"]
        target.write_bytes(before + ("\n## Requirement Clarity\n\n" + "\n".join(
            "- [ ] CHK%03d %s" % (i + 8, q) for i, q in enumerate(questions)) + "\n").encode())
        events = [self.event("read", 10, path=v1.PACKAGE + "/SKILL.md"),
                  self.event("read", 20, path=v1.PACKAGE + "/references/project-generation.md"),
                  self.event("setup", 40, command=v1.SETUP_COMMAND)]
        reference_path = v1.PACKAGE + "/references/project-generation.md"
        events[1].update(read_coverage={"complete": True}, read_sha256=manifest["baseline"][reference_path])
        events += [self.event("read", i * 10 + 50, path=name) for i, name in enumerate(manifest["required_reads"])]
        events += [self.event("write", 100, path=TARGET),
                   self.event("read", 110, path=TARGET, read_coverage={"complete": True},
                              read_sha256=v1._sha(target.read_bytes()))]
        diagnostics = [self.event("diagnostic", 30, path=".specify/extensions.yml",
                                 certified_absence=True, reason="fixture absence")]
        records = [self.record(e["raw_start_index"]) for e in events + diagnostics if e["type"] != "write"]
        final = ("Appended to " + str(target) + " with three unchecked questions. "
                 "Focus: security; depth: standard; reviewer during PR review.")
        observation = {"schema_version": 5, "evidence_kind": "offline-simulation",
                       "completed": True, "model": "gpt-6-luna", "events": events,
                       "diagnostics": diagnostics, "messages": [self.message(final, 1000, "final_answer")],
                       "command_records": records, "final_output": final, "commentary": []}
        return path, manifest, observation, target

    @staticmethod
    def checks(report):
        return {c["name"]: c["passed"] for d in report["dimensions"].values() for c in d.get("checks", [])}

    def claim_observation(self, text, record=None, phase="commentary"):
        return {"messages": [self.message(text, phase=phase)],
                "command_records": [record] if record else []}

    def test_preparation_pins_one_append_slot_new_and_inherited_sources_and_absence(self):
        self.assertEqual(["append-router-v6"], [s["id"] for s in self.summary["sessions"]])
        self.assertEqual((6, 6, 5, 1, 0), tuple(self.summary[key] for key in (
            "schema_version", "checker_version", "observation_schema_version", "proposed_session_count", "live_sessions_started")))
        path, manifest, _, _ = self.good()
        self.assertIn(".specify/extensions.yml", manifest["pinned_absent_paths"])
        self.assertNotIn(".specify/extensions.yml", manifest["baseline"])
        self.assertIn("checker-v5.py", MODULES)
        self.assertIn("trace-v4.py", MODULES)
        self.assertIn("trace-v5.py", MODULES)
        for name, source in MODULES.items():
            self.assertEqual((ROOT / source).read_bytes(), (self.output / "instrument" / name).read_bytes())
        self.assertEqual("1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45", manifest["provenance"]["source_sha256"])
        self.assertTrue(path.exists())
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_good_case_passes_automation_only_manual_review_stays_pending(self):
        path, _, observation, _ = self.good()
        report = check_workspace(path, observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertEqual(6, report["schema_version"])
        self.assertFalse(report["historical_results_regraded"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
        self.assertEqual("pending", report["dimensions"]["workflow"]["review_status"])
        self.assertEqual("pending", report["dimensions"]["content"]["review_status"])

    def test_pinned_absence_requires_exact_successful_matching_lifecycle_before_setup(self):
        _, manifest, good, _ = self.good()
        for change in ({"raw_start_index": 41, "raw_completion_index": 42},
                       {"raw_completion_index": 40}, {"status": "failed"},
                       {"exit_code": 1}, {"certified_absence": False},
                       {"path": ".git"}, {"reason": "inferred absence"},
                       {"raw_item_id": "unmatched"}):
            observation = copy.deepcopy(good)
            observation["diagnostics"][0].update(change)
            self.assertFalse(_extension_checks(manifest, observation)[0]["passed"], change)
        for missing in ("diagnostics", "command_records"):
            observation = copy.deepcopy(good)
            observation.pop(missing)
            self.assertFalse(_extension_checks(manifest, observation)[0]["passed"], missing)
        manifest["pinned_absent_paths"].remove(".specify/extensions.yml")
        self.assertFalse(_extension_checks(manifest, good)[0]["passed"])

    def test_existing_extension_requires_full_baseline_hash_read_not_absence(self):
        _, manifest, observation, _ = self.good()
        manifest["baseline"][".specify/extensions.yml"] = "f" * 64
        self.assertFalse(_extension_checks(manifest, observation)[0]["passed"])
        read = self.event("read", 30, path=".specify/extensions.yml",
                          read_coverage={"complete": True}, read_sha256="f" * 64)
        observation["events"].append(read)
        self.assertTrue(_extension_checks(manifest, observation)[0]["passed"])
        for changes in ({"read_sha256": "a" * 64}, {"read_coverage": {"complete": False}},
                        {"read_coverage": {}}, {"exit_code": 1}, {"raw_start_index": 45, "raw_completion_index": 46}):
            bad = copy.deepcopy(observation)
            bad["events"][-1].update(changes)
            self.assertFalse(_extension_checks(manifest, bad)[0]["passed"], changes)

    def test_same_envelope_discovery_before_setup_operation_is_still_not_prior(self):
        _, manifest, observation, _ = self.good()
        observation["diagnostics"][0].update(raw_item_id="op-40", raw_start_index=40,
                                             raw_completion_index=41, raw_operation_index=0)
        observation["events"][2]["raw_operation_index"] = 1
        checks = _extension_checks(manifest, observation)
        self.assertFalse(checks[0]["passed"])
        self.assertFalse(checks[1]["passed"])

    def test_setup_must_not_share_envelope_with_any_file_read(self):
        _, manifest, observation, _ = self.good()
        read = observation["events"][1]
        read.update(raw_item_id="op-40", raw_start_index=40, raw_completion_index=41,
                    raw_operation_index=0)
        observation["events"][2]["raw_operation_index"] = 1
        self.assertTrue(_extension_checks(manifest, observation)[0]["passed"])
        self.assertFalse(_extension_checks(manifest, observation)[1]["passed"])

    def test_reference_checkpoint_requires_full_prior_separate_command_for_all_project_actions(self):
        path, _, good, _ = self.good()
        for changes in ({"read_coverage": {"complete": False}}, {"read_sha256": "0" * 64},
                        {"raw_item_id": "unmatched"}):
            observation = copy.deepcopy(good)
            observation["events"][1].update(changes)
            self.assertFalse(self.checks(check_workspace(path, observation))["reference-before-project-actions"], changes)
        for location in ("context", "absence"):
            observation = copy.deepcopy(good)
            consumer = observation["events"][3] if location == "context" else observation["diagnostics"][0]
            consumer.update(raw_item_id="op-20", raw_start_index=20, raw_completion_index=21,
                            raw_operation_index=1)
            self.assertFalse(self.checks(check_workspace(path, observation))["reference-before-project-actions"], location)

    def test_unsupported_final_read_assertion_fails_commentary_and_final(self):
        path, manifest, good, target = self.good()
        for phase in ("commentary", "final_answer"):
            observation = copy.deepcopy(good)
            observation["events"] = [e for e in observation["events"] if e["raw_start_index"] != 110]
            observation["messages"].insert(0, self.message(READ_STORY, phase=phase))
            claims = _artifact_claims(manifest, observation, target.read_bytes())
            self.assertEqual("unverified", claims[0]["status"])
            report = check_workspace(path, observation)
            self.assertFalse(self.checks(report)["recognized-artifact-verification-claims-supported"])
            self.assertFalse(self.checks(report)["final-artifact-verification"])
            self.assertFalse(report["automated_checks_passed"])

    def test_supported_verification_requires_complete_current_afterwrite_prior_read(self):
        _, manifest, good, target = self.good()
        good["messages"].insert(0, self.message(READ_STORY))
        self.assertEqual("supported", _artifact_claims(manifest, good, target.read_bytes())[0]["status"])
        for changes in ({"read_coverage": {"complete": False}}, {"read_sha256": "0" * 64},
                        {"raw_start_index": 90, "raw_completion_index": 91},
                        {"raw_start_index": 600, "raw_completion_index": 601},
                        {"status": "inProgress"}, {"raw_item_id": "unbacked"},
                        {"path": ".specify/memory/constitution.md"}):
            observation = copy.deepcopy(good)
            observation["events"][-1].update(changes)
            self.assertEqual("unverified", _artifact_claims(manifest, observation, target.read_bytes())[0]["status"], changes)
        observation = copy.deepcopy(good)
        observation["events"].append(self.event("write", 120, path=TARGET))
        self.assertEqual("unverified", _artifact_claims(manifest, observation, target.read_bytes())[0]["status"])
        observation = copy.deepcopy(good)
        observation["command_records"][-2]["lifecycle_valid"] = False
        self.assertEqual("unverified", _artifact_claims(manifest, observation, target.read_bytes())[0]["status"])

    def test_bounded_read_grammar_and_prefix_claim_need_actual_preservation(self):
        _, manifest, observation, target = self.good()
        for text in (READ_STORY, "I reread the final file.", "I verified the final checklist.",
                     "I checked the original content.", "Final readback confirmed the result."):
            observation["messages"] = [self.message(text)]
            self.assertEqual("supported", _artifact_claims(manifest, observation, target.read_bytes())[0]["status"], text)
        observation["messages"] = [self.message(READ_STORY)]
        changed = b"replacement"
        observation["events"][-1]["read_sha256"] = v1._sha(changed)
        self.assertEqual("unverified", _artifact_claims(manifest, observation, changed)[0]["status"])

    def test_ordered_internal_append_readback_supports_claim_but_later_write_invalidates(self):
        _, manifest, observation, target = self.good()
        observation["messages"].insert(0, self.message(READ_STORY))
        write, read = observation["events"][-2:]
        write.update(raw_item_id="op-110", raw_start_index=110, raw_completion_index=111,
                     raw_operation_index=1)
        read["raw_operation_index"] = 2
        self.assertEqual("supported", _artifact_claims(manifest, observation, target.read_bytes())[0]["status"])
        self.assertFalse(_separate_final_readback(manifest, observation, target.read_bytes())["passed"])
        observation["events"].append(self.event("write", 120, path=TARGET))
        self.assertEqual("unverified", _artifact_claims(manifest, observation, target.read_bytes())[0]["status"])

    def test_separate_final_readback_requires_distinct_full_prior_completed_command(self):
        path, manifest, good, target = self.good()
        for changes in ({"read_coverage": {"complete": False}}, {"read_sha256": "0" * 64},
                        {"raw_start_index": 90, "raw_completion_index": 91},
                        {"raw_start_index": 1100, "raw_completion_index": 1101},
                        {"status": "inProgress"}, {"raw_item_id": "unbacked"}):
            observation = copy.deepcopy(good)
            observation["events"][-1].update(changes)
            self.assertFalse(_separate_final_readback(manifest, observation, target.read_bytes())["passed"], changes)
        observation = copy.deepcopy(good)
        write, read = observation["events"][-2:]
        write.update(raw_item_id="op-110", raw_start_index=110, raw_completion_index=111,
                     raw_operation_index=1)
        read["raw_operation_index"] = 2
        self.assertFalse(self.checks(check_workspace(path, observation))["separate-final-artifact-readback"])
        self.assertTrue(self.checks(check_workspace(path, observation))["final-artifact-verification"])
        observation["events"].append(self.event("read", 120, path=TARGET,
                                              read_coverage={"complete": True}, read_sha256=v1._sha(target.read_bytes())))
        observation["command_records"].append(self.record(120))
        self.assertTrue(self.checks(check_workspace(path, observation))["separate-final-artifact-readback"])

    def test_read_quoted_negated_planned_hypothetical_fenced_and_unsent_not_claims(self):
        _, manifest, good, target = self.good()
        for text in ('"' + READ_STORY + '"', "> " + READ_STORY,
                     "```text\n" + READ_STORY + "\n```", "    " + READ_STORY,
                     "If " + READ_STORY, "For example, " + READ_STORY,
                     "The final file read never shows the content intact.",
                     "I did not read the final file.", "I will read the final file.",
                     "I would have verified the final file."):
            observation = copy.deepcopy(good)
            observation["messages"] = [self.message(text)]
            self.assertEqual([], _artifact_claims(manifest, observation, target.read_bytes()), text)
        good["messages"] = [{**self.message(READ_STORY), "status": "inProgress"}]
        self.assertEqual([], _artifact_claims(manifest, good, target.read_bytes()))

    def test_unsupported_git_history_error_fails_both_completed_phases(self):
        path, manifest, observation, _ = self.good()
        for phase in ("commentary", "final_answer"):
            observation["messages"].insert(0, self.message(GIT_STORY, phase=phase))
            claims = _git_claims(manifest, observation)
            self.assertEqual("unverified", claims[0]["status"])
            report = check_workspace(path, observation)
            self.assertFalse(self.checks(report)["recognized-git-comparison-claims-supported"])
            self.assertFalse(report["automated_checks_passed"])

    def test_real_earlier_git_diff_failure_supports_only_corroborated_error(self):
        manifest = {"target": TARGET}
        record = self.record(command="git diff HEAD -- " + TARGET,
                             output="fatal: not a git repository (or any of the parent directories): .git\n", exit_code=128)
        observation = self.claim_observation(GIT_STORY, record)
        self.assertEqual("supported", _git_claims(manifest, observation)[0]["status"])
        for changes in ({"exit_code": 0}, {"aggregated_output": "fatal: ambiguous argument 'HEAD'"},
                        {"aggregated_output": "The workspace is not a Git repository."},
                        {"raw_start_index": 600, "raw_completion_index": 601},
                        {"raw_completion_index": 500}, {"status": "inProgress"},
                        {"lifecycle_valid": False}, {"raw_start_index": None},
                        {"raw_item_id": None}, {"raw_item_id": ""},
                        {"cwd_relative": None}, {"cwd_relative": "specs"}):
            bad = copy.deepcopy(observation)
            bad["command_records"][0].update(changes)
            self.assertEqual("unverified", _git_claims(manifest, bad)[0]["status"], changes)

    def test_git_mentions_unrelated_status_and_dynamic_or_masked_commands_cannot_support(self):
        output = "fatal: not a git repository (or any of the parent directories): .git"
        for command in ("git status", "git rev-parse --is-inside-work-tree", "cat .git/config",
                        "printf 'git diff HEAD -- " + TARGET + "'", "git diff HEAD -- other.md",
                        "false && git diff HEAD -- " + TARGET, "git diff HEAD -- " + TARGET + " || true",
                        "python3 -c 'print(\"git diff\")'"):
            observation = self.claim_observation(GIT_STORY, self.record(command=command, output=output, exit_code=128))
            self.assertEqual("unverified", _git_claims({"target": TARGET}, observation)[0]["status"], command)

    def test_successful_git_comparison_needs_relevant_successful_return(self):
        for command, output in (("git diff HEAD -- " + TARGET, ""),
                                ("git diff HEAD -- " + TARGET, "diff --git a/security.md b/security.md\n")):
            record = self.record(command=command, output=output)
            for text in ("I compared the file against Git history.", "I ran a Git comparison.",
                         "Git comparison completed."):
                observation = self.claim_observation(text, record)
                self.assertEqual("supported", _git_claims({"target": TARGET}, observation)[0]["status"], (text, command))
        for output, exit_code in (("fatal: not a git repository", 0), ("garbage", 0), ("", 1)):
            record = self.record(command="git diff HEAD -- " + TARGET, output=output, exit_code=exit_code)
            observation = self.claim_observation("Git comparison completed.", record)
            self.assertEqual("unverified", _git_claims({"target": TARGET}, observation)[0]["status"])

    def test_git_claimed_no_differences_requires_empty_diff_not_show_or_changed_output(self):
        story = "Git diff showed no differences."
        for command, output, expected in (("git diff HEAD -- " + TARGET, "", "supported"),
                                          ("git diff HEAD -- " + TARGET, "diff --git a/a b/a\n", "unverified"),
                                          ("git show HEAD:" + TARGET, "content", "unverified")):
            observation = self.claim_observation(story, self.record(command=command, output=output))
            self.assertEqual(expected, _git_claims({"target": TARGET}, observation)[0]["status"])

    def test_git_follow_on_result_in_same_sentence_remains_part_of_claim(self):
        for text in ("The Git comparison succeeded, and it showed no differences.",
                     "Git comparison completed, but it showed no differences.",
                     'Git comparison completed, and it showed "no differences".'):
            observation = self.claim_observation(text, self.record(
                command="git diff HEAD -- " + TARGET, output="diff --git a/a b/a\n"))
            self.assertEqual("unverified", _git_claims({"target": TARGET}, observation)[0]["status"], text)
        observation = self.claim_observation("Git comparison succeeded, and it showed changes.", self.record(
            command="git diff HEAD -- " + TARGET, output=""))
        self.assertEqual("unverified", _git_claims({"target": TARGET}, observation)[0]["status"])

    def test_git_quoted_negated_future_hypothetical_fenced_and_unsent_not_claims(self):
        for text in ('"' + GIT_STORY + '"', "> " + GIT_STORY,
                     "```text\n" + GIT_STORY + "\n```", "    " + GIT_STORY,
                     "If " + GIT_STORY, "For example, " + GIT_STORY,
                     "I did not compare the file against Git history.",
                     "I never ran a Git comparison.", "I will run a Git comparison.",
                     "I would have compared the file against Git history.",
                     "Git comparison never failed because it was not a Git repository."):
            self.assertEqual([], _git_claims({"target": TARGET}, self.claim_observation(text)), text)
        observation = self.claim_observation(GIT_STORY)
        observation["messages"][0]["status"] = "inProgress"
        self.assertEqual([], _git_claims({"target": TARGET}, observation))

    def test_existing_failure_and_error_screens_remain_independent(self):
        path, _, observation, _ = self.good()
        observation["messages"].insert(0, self.message("The adapter invocation returned Unknown synthetic command."))
        observation["events"].append({"type": "unknown", "status": "failed", "exit_code": 1})
        report = check_workspace(path, observation)
        checks = self.checks(report)
        self.assertFalse(checks["recognized-execution-error-claims-supported"])
        self.assertFalse(checks["successful-events"])
        self.assertFalse(checks["classified-events"])
        self.assertFalse(report["automated_checks_passed"])

    def test_rejects_prior_bundle_observation_and_drifted_dependencies(self):
        path, manifest, observation, _ = self.good()
        for version in (1, 3, 4):
            with self.assertRaisesRegex(ValueError, "observation schema"):
                check_workspace(path, {**observation, "schema_version": version})
        manifest["checker_version"] = 5
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "newly prepared v6"):
            check_workspace(path, observation)
        manifest["checker_version"] = 6
        manifest["provenance"]["instruments"]["trace-v5.py"] = "0" * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "dependency version differs"):
            check_workspace(path, observation)

    def test_cli_retains_new_report_and_refuses_overwrite(self):
        path, _, observation, _ = self.good()
        observation_path, report_path = self.output / "observation.json", self.output / "report.json"
        observation_path.write_text(json.dumps(observation))
        argv = ["check", str(path), str(observation_path), "--output", str(report_path)]
        self.assertEqual(0, main(argv))
        with self.assertRaises(SystemExit):
            main(argv)


if __name__ == "__main__":
    unittest.main()
