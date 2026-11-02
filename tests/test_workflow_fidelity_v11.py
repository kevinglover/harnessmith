"""Prospective post-generation checkpoint controls using fresh synthetic data."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith.workflow_fidelity_v11 import MODULES, check_workspace, prepare_pilot
from harnessmith.workflow_trace_v10 import normalize_events


ROOT = Path(__file__).resolve().parents[1]
TARGET = "specs/001-invitations/checklists/security.md"
EXTENSION = ".specify/extensions.yml"
SPEC = "specs/001-invitations/spec.md"
CONSTITUTION = ".specify/memory/constitution.md"
REFERENCE = v1.PACKAGE + "/references/project-generation.md"
SESSION = "append-router-v8-instrument-v11"
GATE = "fresh-post-generation-extension-checkpoint"


def conditional(path, kind="printf"):
    if kind == "printf":
        return "if test -f " + path + "; then cat " + path + "; else printf 'ABSENT\\n'; fi"
    suffix = " && echo ABSENT" if kind == "guarded" else ""
    return "if [ -f " + path + " ]; then cat " + path + "; else test ! -e " + path + suffix + "; fi"


class WorkflowFidelityV11Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "v11"
        self.summary = prepare_pilot(ROOT, self.output)
        self.directory = self.output / SESSION
        self.path = self.directory / "manifest.json"
        self.manifest_bytes = self.path.read_bytes()
        self.manifest = json.loads(self.path.read_text())
        self.workspace = self.directory / "workspace"
        self.target = self.workspace / TARGET

    @staticmethod
    def checks(report):
        return {c["name"]: c["passed"] for d in report["dimensions"].values() for c in d.get("checks", [])}

    def report(self, observation):
        return check_workspace(self.path, observation)

    def observation(self, mode="good", pre="printf", post="printf"):
        before = bytes.fromhex(self.manifest["baseline_target_hex"])
        questions = ["Is the expiration interval quantified? [Clarity, Gap]",
                     "Are expired and reused invitation outcomes defined? [Coverage, Gap]",
                     "Are invitation record retention requirements documented? [Completeness, Gap]"]
        self.target.write_bytes(before + ("\n## Requirement Clarity\n\n" + "\n".join(
            "- [ ] CHK%03d %s" % (i + 8, q) for i, q in enumerate(questions)) + "\n").encode())
        raw = []
        counter = 0

        def emit(method, value):
            raw.append({"method": method, "params": {"threadId": "t", "turnId": "u", "item": value}})

        def command(text, output, item_id=None):
            nonlocal counter
            counter += 1
            return {"id": item_id or "command-" + str(counter), "type": "commandExecution", "status": "completed",
                    "command": text, "cwd": str(self.workspace), "exitCode": 0,
                    "aggregatedOutput": output, "commandActions": []}

        def action(value):
            emit("item/started", {**value, "status": "inProgress"})
            emit("item/completed", value)

        action(command("cat " + REFERENCE, (self.workspace / REFERENCE).read_text()))
        action(command(conditional(EXTENSION, pre), None if pre == "null" else "ABSENT\n", "pre"))
        action(command(v1.SETUP_COMMAND, json.dumps({
            "FEATURE_DIR": str(self.workspace / "specs/001-invitations"), "AVAILABLE_DOCS": ["spec.md"],
            "TEMPLATE_CONTENT": (self.workspace / ".specify/templates/checklist-template.md").read_text(),
        }) + "\n"))
        action(command(conditional(CONSTITUTION), (self.workspace / CONSTITUTION).read_text()))
        action(command("cat " + SPEC, (self.workspace / SPEC).read_text()))
        action(command("cat " + TARGET, before.decode()))
        action(command("rg --files specs/001-invitations", TARGET + "\n" + SPEC + "\n"))
        probe = command(conditional(EXTENSION, post), None if post == "null" else "ABSENT\n", "post")
        if mode == "early-post":
            action(probe)
        action({"id": "write", "type": "fileChange", "status": "completed",
                "changes": [{"path": str(self.target), "kind": {"type": "update", "move_path": None}, "diff": "synthetic append"}]})
        if mode == "before-readback":
            action(probe)
        read = command("cat " + TARGET, self.target.read_text(), "readback")
        if mode == "overlap-readback":
            emit("item/started", {**read, "status": "inProgress"})
            action(probe)
            emit("item/completed", read)
        elif mode != "missing-readback":
            action(read)
        if mode not in {"before-only", "early-post", "before-readback", "late-post", "overlap-readback"}:
            action(probe)
        final = ("Appended to " + str(self.target) + " with three unchecked questions. "
                 "Focus: security; depth: standard; reviewer during PR review.")
        if mode == "unsupported-git":
            final += " One attempted comparison against Git history could not run because the workspace was not recognized as a Git repository."
        action({"id": "final", "type": "agentMessage", "status": "completed", "text": final, "phase": "final_answer"})
        if mode == "late-post":
            action(probe)
        raw.extend([{"method": "thread/tokenUsage/updated", "params": {"threadId": "t", "turnId": "u", "tokenUsage": {"total": {
            "inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 1,
            "reasoningOutputTokens": 0, "totalTokens": 11}}}},
            {"method": "turn/completed", "params": {"threadId": "t", "turnId": "u", "turn": {"id": "u", "status": "completed"}}}])
        result = normalize_events(raw, thread_id="t", turn_id="u", workspace=self.workspace,
                                  manifest=self.manifest, latency_ms=1)
        result["evidence_kind"] = "offline-simulation"
        return result

    @staticmethod
    def post(observation):
        return next(d for d in observation["diagnostics"] if d.get("raw_item_id") == "post")

    def test_fresh_separate_certified_postcheck_is_required_and_passes(self):
        observation = self.observation()
        self.assertEqual([], observation["issues"])
        original = copy.deepcopy(observation)
        report = self.report(observation)
        self.assertTrue(self.checks(report)[GATE])
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertFalse(report["eligible_for_promotion"])
        self.assertFalse(report["historical_results_regraded"])
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
        self.assertEqual(original, observation)

    def test_new_slot_pins_router_rubric_trace_and_original_input(self):
        self.assertEqual([SESSION], [s["id"] for s in self.summary["sessions"]])
        self.assertEqual((11, 11, 10, 1, 0), tuple(self.summary[k] for k in (
            "schema_version", "checker_version", "observation_schema_version", "proposed_session_count", "live_sessions_started")))
        self.assertEqual("router-v8", self.manifest["strategy"])
        self.assertEqual("1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45", self.manifest["provenance"]["source_sha256"])
        self.assertEqual((ROOT / "evaluations/workflow-fidelity/prompts/append.md").read_bytes(), (self.directory / "prompt.md").read_bytes())
        for name, source in MODULES.items():
            self.assertEqual((ROOT / source).read_bytes(), (self.output / "instrument" / name).read_bytes())
        for relative, digest in self.manifest["provenance"]["package"].items():
            self.assertEqual(digest, v1._sha((ROOT / "evaluations/variants/speckit-checklist-router-v8" / relative).read_bytes()))
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_prior_versions_are_rejected_without_regrade(self):
        observation = self.observation()
        for field, value in (("checker_version", 10), ("observation_schema_version", 9),
                             ("pilot_id", "opt-004-workflow-fidelity-v10")):
            manifest = copy.deepcopy(self.manifest)
            manifest[field] = value
            self.path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "newly prepared v11 bundle"):
                self.report(observation)
        self.path.write_bytes(self.manifest_bytes)
        for schema in (1, 8, 9, 11, None):
            observation["schema_version"] = schema
            with self.assertRaisesRegex(ValueError, "v10 observation schema"):
                self.report(observation)

    def test_dependency_and_copied_instrument_drift_fail(self):
        observation = self.observation()
        for name in ("checker-v10.py", "checker-v11.py", "trace-v9.py", "trace-v10.py", "rubric.md", "pilot.json"):
            manifest = copy.deepcopy(self.manifest)
            manifest["provenance"]["instruments"][name] = "0" * 64
            self.path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "dependency version differs"):
                self.report(observation)
        self.path.write_bytes(self.manifest_bytes)
        copied = self.output / "instrument/trace-v10.py"
        copied.write_bytes(copied.read_bytes() + b"\n# drift\n")
        with self.assertRaisesRegex(ValueError, "instrument changed"):
            self.report(observation)

    def test_before_only_snapshots_claims_early_late_and_overlapping_actions_fail(self):
        for mode in ("before-only", "early-post", "before-readback", "late-post", "overlap-readback", "missing-readback"):
            with self.subTest(mode=mode):
                observation = self.observation(mode)
                report = self.report(observation)
                self.assertFalse(self.checks(report)[GATE])
                self.assertFalse(report["automated_checks_passed"])
        observation = self.observation("before-only")
        observation["final_output"] += " Extension absence was checked after generation."
        self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_guarded_post_after_new_prefix_and_null_pre_compatibility(self):
        for pre, post in (("printf", "guarded"), ("guarded", "guarded"), ("null", "printf")):
            with self.subTest(pre=pre, post=post):
                observation = self.observation(pre=pre, post=post)
                report = self.report(observation)
                self.assertTrue(report["automated_checks_passed"], self.checks(report))
                self.assertEqual(int(pre == "null"), len(report["command_backing_adapter"]["admissions"]))
        observation = self.observation(post="null")
        self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_exact_certificate_identity_output_and_inventory_are_binding(self):
        good = self.observation()
        cases = {"proof": "literal-else-test", "instrumentation": "codex-workflow-trace-v8",
                 "path": "wrong.yml", "version": True, "output_representation": "null",
                 "absence_marker": "OTHER\n", "captured_output_sha256": "0" * 64,
                 "baseline_inventory_sha256": "0" * 64, "complete_command_coverage": False,
                 "stderr_stripped": True, "overlapping_read_only_item_ids": ["other"]}
        for field, value in cases.items():
            with self.subTest(field=field):
                observation = copy.deepcopy(good)
                self.post(observation)["absence_certificate"][field] = value
                self.assertFalse(self.checks(self.report(observation))[GATE])
        for field in ("absence_certificate", "certified_absence"):
            observation = copy.deepcopy(good)
            self.post(observation).pop(field)
            self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_duplicate_unbacked_failed_or_changed_record_cannot_supply_checkpoint(self):
        good = self.observation()
        for change in ("duplicate", "missing", "failed", "bool-exit", "wrong-command", "wrong-start",
                       "missing-output", "null-output", "noisy-output", "invalid-lifecycle"):
            with self.subTest(change=change):
                observation = copy.deepcopy(good)
                record = next(r for r in observation["command_records"] if r["raw_item_id"] == "post")
                if change == "duplicate":
                    observation["command_records"].append(copy.deepcopy(record))
                elif change == "missing":
                    observation["command_records"].remove(record)
                elif change == "failed":
                    record["exit_code"] = 1
                elif change == "bool-exit":
                    record["exit_code"] = False
                elif change == "wrong-command":
                    record["raw_command"] = "echo ABSENT"
                elif change == "wrong-start":
                    record["raw_start_index"] -= 1
                elif change == "missing-output":
                    record.pop("aggregated_output")
                elif change == "null-output":
                    record["aggregated_output"] = None
                elif change == "noisy-output":
                    record["aggregated_output"] += "warning\n"
                elif change == "invalid-lifecycle":
                    record["lifecycle_valid"] = False
                self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_native_append_and_readback_proof_must_match_observed_current_actions(self):
        good = self.observation()
        for field, value in (("raw_item_id", "earlier-write"), ("raw_start_index", 0),
                             ("raw_completion_index", 1), ("target", "wrong.md"),
                             ("before_sha256", "0" * 64), ("after_sha256", "0" * 64),
                             ("before_bytes", 0), ("after_bytes", 0), ("readback_item_ids", ["pre"])):
            with self.subTest(field=field):
                observation = copy.deepcopy(good)
                self.post(observation)["absence_certificate"]["accounted_native_appends"][0][field] = value
                self.assertFalse(self.checks(self.report(observation))[GATE])
        for field in ("superseded_inherited_facts", "superseded_inherited_issues"):
            observation = copy.deepcopy(good)
            self.post(observation)["absence_certificate"][field][0]["raw_item_id"] = "pre"
            self.assertFalse(self.checks(self.report(observation))[GATE])
        for field, key, value in (("superseded_inherited_facts", "type", "read"),
                                  ("superseded_inherited_facts", "reason", "unrelated"),
                                  ("superseded_inherited_facts", "status", "failed"),
                                  ("superseded_inherited_facts", "exit_code", False),
                                  ("superseded_inherited_facts", "raw_operation_index", 1),
                                  ("superseded_inherited_issues", "kind", "isolation"),
                                  ("superseded_inherited_issues", "detail", "unrelated")):
            observation = copy.deepcopy(good)
            self.post(observation)["absence_certificate"][field][0][key] = value
            self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_mixed_post_envelope_or_overlapping_unknown_action_fails(self):
        good = self.observation()
        observation = copy.deepcopy(good)
        post = self.post(observation)
        observation["events"].append({**post, "type": "read", "path": SPEC, "raw_operation_index": 1})
        self.assertFalse(self.checks(self.report(observation))[GATE])
        observation = copy.deepcopy(good)
        post = self.post(observation)
        observation["events"].append({**post, "type": "unknown", "path": "unknown", "raw_item_id": "other"})
        self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_stale_readback_new_mutation_and_wrong_final_boundary_fail(self):
        good = self.observation()
        for change in ("missing-read", "wrong-read-hash", "wrong-read-output", "duplicate-read-record", "later-write", "early-final"):
            with self.subTest(change=change):
                observation = copy.deepcopy(good)
                read = next(f for f in observation["events"] if f["raw_item_id"] == "readback")
                if change == "missing-read":
                    observation["events"].remove(read)
                elif change == "wrong-read-hash":
                    read["read_sha256"] = "0" * 64
                elif change == "wrong-read-output":
                    next(r for r in observation["command_records"] if r["raw_item_id"] == "readback")["aggregated_output"] = "stale bytes\n"
                elif change == "duplicate-read-record":
                    observation["command_records"].append(copy.deepcopy(next(r for r in observation["command_records"] if r["raw_item_id"] == "readback")))
                elif change == "later-write":
                    observation["events"].append({"type": "write", "path": TARGET, "raw_item_id": "new-write", "status": "completed", "raw_start_index": 2000, "raw_completion_index": 2001})
                elif change == "early-final":
                    observation["messages"][-1].update(raw_start_index=0, raw_completion_index=1)
                self.assertFalse(self.checks(self.report(observation))[GATE])

    def test_preservation_reference_separation_and_git_gates_remain_binding(self):
        observation = self.observation("unsupported-git")
        report = self.report(observation)
        self.assertTrue(self.checks(report)[GATE])
        self.assertFalse(self.checks(report)["recognized-git-comparison-claims-supported"])
        self.assertFalse(report["automated_checks_passed"])
        observation = self.observation()
        self.target.write_bytes(self.target.read_bytes().replace(b"[X]", b"[ ]", 1))
        report = self.report(observation)
        self.assertFalse(self.checks(report)["append-preserves-prefix"])
        self.assertFalse(self.checks(report)[GATE])
        for name in ("extension-check-isolated-from-other-operations", "context-reads-isolated-from-discovery-and-mutation",
                     "reference-before-project-actions", "separate-final-artifact-readback"):
            self.assertIn(name, self.checks(report))


if __name__ == "__main__":
    unittest.main()
