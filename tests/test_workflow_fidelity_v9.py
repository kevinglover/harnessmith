"""Fresh schema-8 checker controls; commands are data, never executed."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith.workflow_fidelity_v9 import MODULES, check_workspace, prepare_pilot
from harnessmith.workflow_trace_v8 import normalize_events


ROOT = Path(__file__).resolve().parents[1]
TARGET = "specs/001-invitations/checklists/security.md"
SPEC = "specs/001-invitations/spec.md"
CONSTITUTION = ".specify/memory/constitution.md"
REFERENCE = v1.PACKAGE + "/references/project-generation.md"
SESSION = "append-router-v7-instrument-v9"


def conditional(path):
    return "if [ -f " + path + " ]; then cat " + path + "; else test ! -e " + path + "; fi"


class WorkflowFidelityV9Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "v9"
        self.summary = prepare_pilot(ROOT, self.output)
        self.directory = self.output / SESSION
        self.path = self.directory / "manifest.json"
        self.manifest = json.loads(self.path.read_text())
        self.workspace = self.directory / "workspace"
        self.target = self.workspace / TARGET

    @staticmethod
    def message(text, index=500, phase="commentary"):
        return {"text": text, "raw_item_id": "message-" + str(index),
                "raw_start_index": index, "raw_completion_index": index + 1,
                "status": "completed", "phase": phase}

    @staticmethod
    def record(index=300):
        return {"raw_item_id": "op-" + str(index), "raw_start_index": index,
                "raw_completion_index": index + 1, "status": "completed",
                "exit_code": 0, "raw_command": "cat " + TARGET,
                "aggregated_output": "", "lifecycle_valid": True, "cwd_relative": "."}

    def event(self, kind, index, **fields):
        record = self.record(index)
        return {"type": kind, **{key: record[key] for key in (
            "raw_item_id", "raw_start_index", "raw_completion_index", "status", "exit_code")},
            "raw_operation_index": 0, **fields}

    def good(self):
        before = bytes.fromhex(self.manifest["baseline_target_hex"])
        questions = ["Is the expiration interval quantified? [Clarity, Gap]",
                     "Are expired and reused invitation outcomes defined? [Coverage, Gap]",
                     "Are invitation record retention requirements documented? [Completeness, Gap]"]
        self.target.write_bytes(before + ("\n## Requirement Clarity\n\n" + "\n".join(
            "- [ ] CHK%03d %s" % (i + 8, q) for i, q in enumerate(questions)) + "\n").encode())
        events = [self.event("read", 10, path=v1.PACKAGE + "/SKILL.md"),
                  self.event("read", 20, path=REFERENCE, read_coverage={"complete": True},
                             read_sha256=self.manifest["baseline"][REFERENCE]),
                  self.event("setup", 40, command=v1.SETUP_COMMAND)]
        events += [self.event("read", i * 10 + 50, path=name)
                   for i, name in enumerate(self.manifest["required_reads"])]
        events += [self.event("write", 100, path=TARGET),
                   self.event("read", 110, path=TARGET, read_coverage={"complete": True},
                              read_sha256=v1._sha(self.target.read_bytes()))]
        diagnostics = [self.event("diagnostic", 30, path=".specify/extensions.yml",
                                 certified_absence=True, reason="fixture absence")]
        records = [self.record(e["raw_start_index"]) for e in events + diagnostics if e["type"] != "write"]
        final = ("Appended to " + str(self.target) + " with three unchecked questions. "
                 "Focus: security; depth: standard; reviewer during PR review.")
        return {"schema_version": 8, "evidence_kind": "offline-simulation",
                "completed": True, "model": "gpt-6-luna", "events": events,
                "diagnostics": diagnostics, "messages": [self.message(final, 1000, "final_answer")],
                "command_records": records, "final_output": final, "commentary": []}

    @staticmethod
    def checks(report):
        return {c["name"]: c["passed"] for d in report["dimensions"].values() for c in d.get("checks", [])}

    def report(self, observation):
        return check_workspace(self.path, observation)

    def test_new_bundle_pins_unchanged_router_prompt_and_new_dependency_chain(self):
        self.assertEqual([SESSION], [s["id"] for s in self.summary["sessions"]])
        self.assertEqual((9, 9, 8, 1, 0), tuple(self.summary[key] for key in (
            "schema_version", "checker_version", "observation_schema_version", "proposed_session_count", "live_sessions_started")))
        self.assertEqual("router-v7", self.manifest["strategy"])
        self.assertEqual("not-applicable: authored router-v7 redesign", self.manifest["provenance"]["recipe_status"])
        self.assertEqual("1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45", self.manifest["provenance"]["source_sha256"])
        for name in ("checker-v8.py", "checker-v9.py", "trace-v7.py", "trace-v8.py"):
            self.assertIn(name, MODULES)
        for name, source in MODULES.items():
            self.assertEqual((ROOT / source).read_bytes(), (self.output / "instrument" / name).read_bytes())
        self.assertEqual((ROOT / "evaluations/workflow-fidelity/prompts/append.md").read_bytes(),
                         (self.directory / "prompt.md").read_bytes())
        for relative, digest in self.manifest["provenance"]["package"].items():
            self.assertEqual(digest, v1._sha((ROOT / "evaluations/variants/speckit-checklist-router-v7" / relative).read_bytes()))
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_gates_and_pending_reviews_remain_binding(self):
        observation = self.good()
        before = copy.deepcopy(observation)
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertEqual((9, 9), (report["schema_version"], report["checker_version"]))
        self.assertEqual((4, 6), (report["topic_screen"]["version"], report["narrative_screen"]["version"]))
        self.assertFalse(report["historical_results_regraded"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
        for dimension in ("content", "workflow"):
            self.assertEqual("pending", report["dimensions"][dimension]["review_status"])
        self.assertEqual(before, observation)
        for name in ("extension-check-isolated-from-other-operations",
                     "context-reads-isolated-from-discovery-and-mutation",
                     "discovery-isolated-from-other-operations", "context-before-write",
                     "separate-final-artifact-readback", "recognized-git-comparison-claims-supported"):
            self.assertIn(name, self.checks(report))

    def test_prior_manifest_and_observation_versions_cannot_be_regraded(self):
        observation = self.good()
        for field, value in (("checker_version", 8), ("observation_schema_version", 7),
                             ("pilot_id", "opt-004-workflow-fidelity-v8")):
            manifest = copy.deepcopy(self.manifest)
            manifest[field] = value
            self.path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "newly prepared v9 bundle"):
                self.report(observation)
        self.path.write_text(json.dumps(self.manifest))
        for schema in (1, 6, 7, 9, None):
            observation["schema_version"] = schema
            with self.assertRaisesRegex(ValueError, "v8 observation schema"):
                self.report(observation)

    def test_new_and_inherited_dependency_drift_fails(self):
        observation = self.good()
        for name in ("checker-v8.py", "checker-v9.py", "trace-v7.py", "trace-v8.py", "rubric.md", "pilot.json"):
            manifest = copy.deepcopy(self.manifest)
            manifest["provenance"]["instruments"][name] = "0" * 64
            self.path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "dependency version differs"):
                self.report(observation)

    def test_copied_new_instrument_and_original_prompt_tampering_fails(self):
        observation = self.good()
        for path in (self.output / "instrument/trace-v8.py", self.directory / "prompt.md"):
            original = path.read_bytes()
            path.write_bytes(original + b"\n# changed\n")
            with self.assertRaisesRegex(ValueError, "instrument changed|prompt changed"):
                self.report(observation)
            path.write_bytes(original)

    def test_final_read_and_unsupported_git_claims_remain_hard_failures(self):
        good = self.good()
        for claim, name in (("The final file read shows the existing content and checkbox states intact.",
                             "recognized-artifact-verification-claims-supported"),
                            ("One attempted comparison against Git history could not run because the workspace was not recognized as a Git repository.",
                             "recognized-git-comparison-claims-supported")):
            observation = copy.deepcopy(good)
            if "file read" in claim:
                observation["events"] = [e for e in observation["events"] if e["raw_start_index"] != 110]
            observation["messages"].insert(0, self.message(claim))
            report = self.report(observation)
            self.assertFalse(self.checks(report)[name])
            self.assertFalse(report["automated_checks_passed"])

    def test_command_separation_does_not_accept_new_certificate_as_a_waiver(self):
        good = self.good()
        for path, expected in ((".specify/extensions.yml", "extension-check-isolated-from-other-operations"),
                               (SPEC, "context-reads-isolated-from-discovery-and-mutation")):
            observation = copy.deepcopy(good)
            fact = next(e for e in observation["events"] + observation["diagnostics"] if e.get("path") == path)
            observation["diagnostics"].append({**fact, "type": "diagnostic", "reason": "file discovery",
                "path": "specs/001-invitations", "raw_operation_index": 1,
                "terminal_discovery_certificate": {"proof": "literal-terminal-rg"}})
            report = self.report(observation)
            self.assertFalse(self.checks(report)[expected])
            self.assertFalse(self.checks(report)["discovery-isolated-from-other-operations"])
            self.assertFalse(report["automated_checks_passed"])

    def raw_observation(self, mode="good", absence_output="", constitution_output=None):
        observation = self.good()
        raw = []
        counter = 0

        def emit(method, value):
            raw.append({"method": method, "params": {"threadId": "t", "turnId": "u", "item": value}})

        def command(text, output, exit_code=0):
            nonlocal counter
            counter += 1
            return {"id": "command-" + str(counter), "type": "commandExecution", "status": "completed",
                    "command": text, "cwd": str(self.workspace), "exitCode": exit_code,
                    "aggregatedOutput": output, "commandActions": []}

        def start(value):
            emit("item/started", {**value, "status": "inProgress"})

        def finish(value):
            emit("item/completed", value)

        def action(value):
            start(value)
            finish(value)

        reference = command("cat " + REFERENCE, (self.workspace / REFERENCE).read_text())
        absence = command(conditional(".specify/extensions.yml"), absence_output)
        if mode == "missing-absence-output":
            absence.pop("aggregatedOutput")
        if mode == "reference-overlap":
            start(reference)
            action(absence)
            finish(reference)
        elif mode == "reference-read-overlap":
            start(reference)
            action(command("cat " + CONSTITUTION, (self.workspace / CONSTITUTION).read_text()))
            finish(reference)
            action(absence)
        else:
            action(reference)
            action(absence)
        action(command(v1.SETUP_COMMAND, json.dumps({
            "FEATURE_DIR": str(self.workspace / "specs/001-invitations"), "AVAILABLE_DOCS": ["spec.md"],
            "TEMPLATE_CONTENT": (self.workspace / ".specify/templates/checklist-template.md").read_text(),
        }) + "\n"))
        constitution = (self.workspace / CONSTITUTION).read_text() if constitution_output is None else constitution_output
        action(command(conditional(CONSTITUTION), constitution))
        spec = command("cat " + SPEC, (self.workspace / SPEC).read_text())
        target = command("cat " + TARGET, bytes.fromhex(self.manifest["baseline_target_hex"]).decode())
        listing = TARGET + "\n" + SPEC + "\n"
        discovery = command("rg --files specs/001-invitations", listing)
        write = {"id": "write", "type": "fileChange", "status": "completed",
                 "changes": [{"path": TARGET, "kind": {"type": "update"}, "diff": "synthetic append"}]}
        if mode == "mixed-discovery":
            action(target)
            action(command("cat " + SPEC + "; rg --files specs/001-invitations", spec["aggregatedOutput"] + listing))
        elif mode == "sequential":
            action(spec)
            action(target)
            action(discovery)
        else:
            start(spec)
            start(target)
            if mode == "read-failure":
                spec["exitCode"] = 1
            elif mode == "truncated-read":
                spec["aggregatedOutput"] = spec["aggregatedOutput"][:-1]
            if mode == "unknown-overlap":
                action(command("unrecognized-tool --probe", ""))
            if mode == "discovery-overlap":
                action(discovery)
            finish(target)
            if mode == "write-before-read-completes":
                action(write)
            finish(spec)
            if mode != "discovery-overlap":
                action(discovery)
        if mode != "write-before-read-completes":
            action(write)
        action(command("cat " + TARGET, self.target.read_text()))
        action({"id": "final", "type": "agentMessage", "status": "completed",
                "text": observation["final_output"], "phase": "final_answer"})
        raw.extend([{"method": "thread/tokenUsage/updated", "params": {"threadId": "t", "turnId": "u", "tokenUsage": {"total": {
            "inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 1,
            "reasoningOutputTokens": 0, "totalTokens": 11}}}},
            {"method": "turn/completed", "params": {"threadId": "t", "turnId": "u", "turn": {"id": "u", "status": "completed"}}}])
        result = normalize_events(raw, thread_id="t", turn_id="u", workspace=self.workspace,
                                  manifest=self.manifest, latency_ms=1)
        result["evidence_kind"] = "offline-simulation"
        return result

    def test_exact_else_test_present_and_absent_branches_integrate_without_gate_changes(self):
        observation = self.raw_observation("sequential")
        self.assertEqual(8, observation["schema_version"])
        self.assertEqual([], observation["issues"])
        absent = [d for d in observation["diagnostics"] if d.get("certified_absence")]
        self.assertEqual([".specify/extensions.yml"], [d["path"] for d in absent])
        self.assertEqual("literal-else-test", absent[0]["absence_certificate"]["proof"])
        present = next(e for e in observation["events"] if e.get("path") == CONSTITUTION)
        self.assertEqual("literal-else-test", present["conditional_read_certificate"]["proof"])
        self.assertTrue(present["read_coverage"]["complete"])
        self.assertEqual(self.manifest["baseline"][CONSTITUTION], present["read_sha256"])
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertFalse(report["eligible_for_promotion"])

    def test_explicit_null_absence_uses_a_reported_copy_without_rewriting_evidence(self):
        observation = self.raw_observation("sequential", absence_output=None)
        before = copy.deepcopy(observation)
        self.assertEqual([], observation["issues"])
        certificate = next(d for d in observation["diagnostics"] if d.get("certified_absence"))
        self.assertEqual("null", certificate["absence_certificate"]["output_representation"])
        record = next(r for r in observation["command_records"] if r["raw_item_id"] == certificate["raw_item_id"])
        self.assertIsNone(record["aggregated_output"])
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        adapter = report["command_backing_adapter"]
        self.assertFalse(adapter["captured_observation_modified"])
        self.assertEqual([certificate["raw_item_id"]], [a["raw_item_id"] for a in adapter["admissions"]])
        self.assertEqual(before, observation)
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])

    def test_null_backing_needs_unique_matching_successful_exact_new_absence_proof(self):
        good = self.raw_observation("sequential", absence_output=None)
        for change in ("old-instrument", "missing-proof", "wrong-hash", "wrong-inventory", "missing-output",
                       "wrong-representation", "incomplete-coverage", "failed", "invalid-lifecycle", "wrong-boundary",
                       "duplicate-record", "companion-read", "missing-record-output"):
            with self.subTest(change=change):
                observation = copy.deepcopy(good)
                fact = next(d for d in observation["diagnostics"] if d.get("certified_absence"))
                record = next(r for r in observation["command_records"] if r["raw_item_id"] == fact["raw_item_id"])
                proof = fact["absence_certificate"]
                if change == "old-instrument":
                    proof["instrumentation"] = "codex-workflow-trace-v7"
                elif change == "missing-proof":
                    fact.pop("absence_certificate")
                elif change == "wrong-hash":
                    proof["captured_output_sha256"] = "0" * 64
                elif change == "wrong-inventory":
                    proof["baseline_inventory_sha256"] = "0" * 64
                elif change == "missing-output":
                    proof["output_representation"] = "missing"
                elif change == "wrong-representation":
                    proof["output_representation"] = "text"
                elif change == "incomplete-coverage":
                    proof["complete_command_coverage"] = False
                elif change == "failed":
                    record["exit_code"] = 2
                elif change == "invalid-lifecycle":
                    record["lifecycle_valid"] = False
                elif change == "wrong-boundary":
                    record["raw_completion_index"] += 1
                elif change == "duplicate-record":
                    observation["command_records"].append(copy.deepcopy(record))
                elif change == "companion-read":
                    observation["events"].append({**fact, "type": "read", "path": SPEC, "raw_operation_index": 1})
                elif change == "missing-record-output":
                    record.pop("aggregated_output")
                report = self.report(observation)
                self.assertEqual([], report["command_backing_adapter"]["admissions"])
                self.assertFalse(self.checks(report)["extension-config-before-setup"])
                self.assertFalse(self.checks(report)["extension-check-isolated-from-other-operations"])

    def test_missing_absence_output_and_null_present_read_are_not_empty_successes(self):
        observation = self.raw_observation("missing-absence-output")
        self.assertFalse(any(d.get("certified_absence") for d in observation["diagnostics"]))
        self.assertFalse(self.report(observation)["automated_checks_passed"])
        observation = self.raw_observation("sequential", absence_output=None)
        read = next(e for e in observation["events"] if e.get("path") == CONSTITUTION)
        record = next(r for r in observation["command_records"] if r["raw_item_id"] == read["raw_item_id"])
        record["aggregated_output"] = None
        report = self.report(observation)
        self.assertFalse(self.checks(report)["context-reads-isolated-from-discovery-and-mutation"])
        self.assertNotIn(read["raw_item_id"], [a["raw_item_id"] for a in report["command_backing_adapter"]["admissions"]])

    def test_independent_overlapping_reads_complete_before_discovery_and_write(self):
        observation = self.raw_observation()
        self.assertEqual([], observation["issues"])
        reads = [e for e in observation["events"] if e.get("path") in {SPEC, TARGET}
                 and e.get("read_before_write")]
        self.assertEqual({SPEC, TARGET}, {e["path"] for e in reads})
        self.assertTrue(any(e.get("read_only_attribution_certificate") for e in reads))
        discovery = [d for d in observation["diagnostics"] if d.get("terminal_discovery_certificate")]
        self.assertEqual(1, len(discovery))
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])

    def test_new_attribution_does_not_waive_mixed_read_discovery_boundaries(self):
        observation = self.raw_observation("mixed-discovery")
        self.assertEqual([], observation["issues"])
        self.assertTrue(any(d.get("terminal_discovery_certificate") for d in observation["diagnostics"]))
        report = self.report(observation)
        self.assertFalse(report["automated_checks_passed"])
        self.assertFalse(self.checks(report)["context-reads-isolated-from-discovery-and-mutation"])
        self.assertFalse(self.checks(report)["discovery-isolated-from-other-operations"])

    def test_unknown_failed_partial_or_mutating_overlap_cannot_pass(self):
        for mode in ("unknown-overlap", "read-failure", "truncated-read", "write-before-read-completes"):
            with self.subTest(mode=mode):
                observation = self.raw_observation(mode)
                self.assertTrue(observation["issues"])
                report = self.report(observation)
                self.assertFalse(report["automated_checks_passed"], mode)
                self.assertTrue(any(not self.checks(report)[name] for name in (
                    "classified-events", "successful-events", "required-context-reads", "context-before-write")), mode)

    def test_open_reads_cannot_certify_discovery_and_reference_must_finish_first(self):
        observation = self.raw_observation("discovery-overlap")
        self.assertFalse(any(d.get("terminal_discovery_certificate") for d in observation["diagnostics"]))
        self.assertFalse(self.report(observation)["automated_checks_passed"])
        observation = self.raw_observation("reference-overlap")
        self.assertTrue(any(e.get("type") == "unknown" for e in observation["events"]))
        report = self.report(observation)
        self.assertFalse(self.checks(report)["reference-before-project-actions"])
        self.assertFalse(report["automated_checks_passed"])
        observation = self.raw_observation("reference-read-overlap")
        reference = next(e for e in observation["events"] if e.get("path") == REFERENCE)
        early = [e for e in observation["events"] if e.get("type") == "read" and e.get("path") == CONSTITUTION
                 and e["raw_start_index"] < reference["raw_completion_index"]]
        self.assertEqual(1, len(early))
        self.assertTrue(early[0]["read_coverage"]["complete"])
        self.assertFalse(self.checks(self.report(observation))["reference-before-project-actions"])

    def test_unknown_reference_boundary_is_conservative_without_penalizing_later_unknowns(self):
        good = self.good()
        for position in ("before", "overlap", "missing-lifecycle", "after"):
            with self.subTest(position=position):
                observation = copy.deepcopy(good)
                index = {"before": 5, "overlap": 20, "missing-lifecycle": 90, "after": 90}[position]
                unknown = self.event("unknown", index, reason="unsupported synthetic command")
                if position == "missing-lifecycle":
                    unknown.pop("raw_start_index")
                    unknown.pop("raw_completion_index")
                observation["events"].append(unknown)
                report = self.report(observation)
                checks = self.checks(report)
                self.assertEqual(position == "after", checks["reference-before-project-actions"])
                self.assertFalse(checks["classified-events"])
                self.assertFalse(report["automated_checks_passed"])

    def test_else_test_output_mismatch_never_establishes_checkpoint(self):
        observation = self.raw_observation("sequential", absence_output="unproven absence\n")
        self.assertFalse(any(d.get("certified_absence") for d in observation["diagnostics"]))
        checks = self.checks(self.report(observation))
        self.assertFalse(checks["extension-config-before-setup"])
        self.assertFalse(checks["extension-check-isolated-from-other-operations"])
        observation = self.raw_observation("sequential", constitution_output="")
        checks = self.checks(self.report(observation))
        self.assertFalse(checks["required-context-reads"])
        self.assertFalse(checks["context-before-write"])


if __name__ == "__main__":
    unittest.main()
