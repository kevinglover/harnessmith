"""Fresh checker-v8/schema-7 controls; no historical evidence or captured code is executed."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from harnessmith import workflow_fidelity as v1
from harnessmith.workflow_fidelity_v8 import MODULES, check_workspace, prepare_pilot
from harnessmith.workflow_trace_v7 import normalize_events


ROOT = Path(__file__).resolve().parents[1]
TARGET = "specs/001-invitations/checklists/security.md"
REFERENCE = v1.PACKAGE + "/references/project-generation.md"
SESSION = "append-router-v7-instrument-v8"
ABSENCE = "if [ -f .specify/extensions.yml ]; then cat .specify/extensions.yml; else printf 'NO_EXTENSIONS_FILE\\n'; fi"


class WorkflowFidelityV8Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve() / "v8"
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
        return {"schema_version": 7, "evidence_kind": "offline-simulation",
                "completed": True, "model": "gpt-6-luna", "events": events,
                "diagnostics": diagnostics, "messages": [self.message(final, 1000, "final_answer")],
                "command_records": records, "final_output": final, "commentary": []}

    @staticmethod
    def checks(report):
        return {c["name"]: c["passed"] for d in report["dimensions"].values() for c in d.get("checks", [])}

    def report(self, observation):
        return check_workspace(self.path, observation)

    def test_new_bundle_pins_new_router_and_all_new_and_inherited_instruments(self):
        self.assertEqual([SESSION], [s["id"] for s in self.summary["sessions"]])
        self.assertEqual((8, 8, 7, 1, 0), tuple(self.summary[key] for key in (
            "schema_version", "checker_version", "observation_schema_version", "proposed_session_count", "live_sessions_started")))
        self.assertEqual("router-v7", self.manifest["strategy"])
        self.assertEqual("not-applicable: authored router-v7 redesign", self.manifest["provenance"]["recipe_status"])
        self.assertEqual("1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45", self.manifest["provenance"]["source_sha256"])
        for name in ("checker-v7.py", "checker-v8.py", "trace-v6.py", "trace-v7.py"):
            self.assertIn(name, MODULES)
        for name, source in MODULES.items():
            self.assertEqual((ROOT / source).read_bytes(), (self.output / "instrument" / name).read_bytes())
        self.assertEqual((ROOT / "evaluations/workflow-fidelity/prompts/append.md").read_bytes(),
                         (self.directory / "prompt.md").read_bytes())
        for relative, digest in self.manifest["provenance"]["package"].items():
            self.assertEqual(digest, v1._sha((ROOT / "evaluations/variants/speckit-checklist-router-v7" / relative).read_bytes()))
        self.assertIn(".specify/extensions.yml", self.manifest["pinned_absent_paths"])
        with self.assertRaises(FileExistsError):
            prepare_pilot(ROOT, self.output)

    def test_automation_pass_keeps_manual_reviews_pending_and_promotion_blocked(self):
        observation = self.good()
        snapshot = copy.deepcopy(observation)
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertEqual((8, 8), (report["schema_version"], report["checker_version"]))
        self.assertEqual((4, 6), (report["topic_screen"]["version"], report["narrative_screen"]["version"]))
        self.assertFalse(report["historical_results_regraded"])
        self.assertFalse(report["eligible_for_promotion"])
        self.assertEqual("pending", report["narrative_screen"]["raw_review_status"])
        for dimension in ("content", "workflow"):
            self.assertEqual("pending", report["dimensions"][dimension]["review_status"])
        self.assertEqual(snapshot, observation)

    def test_multiple_known_context_reads_can_share_one_successful_envelope(self):
        observation = self.good()
        first = next(e for e in observation["events"] if e.get("path") == ".specify/memory/constitution.md")
        second = next(e for e in observation["events"] if e.get("path") == "specs/001-invitations/spec.md")
        old_id = second["raw_item_id"]
        for key in ("raw_item_id", "raw_start_index", "raw_completion_index"):
            second[key] = first[key]
        second["raw_operation_index"] = 1
        observation["command_records"] = [r for r in observation["command_records"] if r["raw_item_id"] != old_id]
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))

    def test_only_named_successful_passive_diagnostics_can_accompany_context_reads(self):
        good = self.good()
        for reason in ("literal output label", "corroborated read-only Python cache warning"):
            observation = copy.deepcopy(good)
            read = next(e for e in observation["events"] if e.get("path") == "specs/001-invitations/spec.md")
            companion = {**read, "type": "diagnostic", "reason": reason, "raw_operation_index": 1}
            companion.pop("path")
            observation["diagnostics"].append(companion)
            report = self.report(observation)
            self.assertTrue(report["automated_checks_passed"], (reason, self.checks(report)))
            companion["exit_code"] = 2
            self.assertFalse(self.checks(self.report(observation))[
                "context-reads-isolated-from-discovery-and-mutation"])

    def test_extension_envelope_allows_only_successful_corroborated_cache_noise(self):
        observation = self.good()
        companion = {**observation["diagnostics"][0], "reason": "corroborated read-only Python cache warning",
                     "raw_operation_index": 1}
        companion.pop("path")
        companion.pop("certified_absence")
        observation["diagnostics"].append(companion)
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        companion["status"] = "failed"
        self.assertFalse(self.checks(self.report(observation))[
            "extension-check-isolated-from-other-operations"])

    def test_successfully_attributed_discovery_still_fails_context_separation(self):
        observation = self.good()
        read = next(e for e in observation["events"] if e.get("path") == "specs/001-invitations/spec.md")
        observation["diagnostics"].append({**read, "type": "diagnostic", "reason": "file discovery",
            "path": "specs/001-invitations", "raw_operation_index": 1,
            "terminal_discovery_certificate": {"version": 1, "proof": "literal-terminal-rg"}})
        checks = self.checks(self.report(observation))
        self.assertFalse(checks["context-reads-isolated-from-discovery-and-mutation"])
        self.assertTrue(checks["extension-check-isolated-from-other-operations"])
        self.assertFalse(checks["discovery-isolated-from-other-operations"])

    def test_optional_and_template_reads_cannot_bypass_context_separation(self):
        good = self.good()
        for path in (".specify/templates/checklist-template.md", "specs/001-invitations/plan.md",
                     "specs/001-invitations/tasks.md", v1.PACKAGE + "/SKILL.md"):
            observation = copy.deepcopy(good)
            read = self.event("read", 85, path=path)
            observation["events"].append(read)
            observation["command_records"].append(self.record(85))
            observation["diagnostics"].append({**read, "type": "diagnostic", "path": "specs/001-invitations",
                                               "reason": "file discovery", "raw_operation_index": 1})
            checks = self.checks(self.report(observation))
            self.assertFalse(checks["context-reads-isolated-from-discovery-and-mutation"], path)
            self.assertFalse(checks["discovery-isolated-from-other-operations"], path)

    def test_discovery_alone_or_with_named_passive_diagnostics_is_allowed(self):
        good = self.good()
        for reason in ("file discovery", "directory discovery", "working-directory discovery"):
            observation = copy.deepcopy(good)
            fact = self.event("diagnostic", 85, path="specs/001-invitations", reason=reason)
            observation["diagnostics"].append(fact)
            observation["command_records"].append(self.record(85))
            self.assertTrue(self.report(observation)["automated_checks_passed"], reason)
            observation["diagnostics"].extend([
                {**fact, "reason": "literal output label", "raw_operation_index": 1},
                {**fact, "reason": "corroborated read-only Python cache warning", "raw_operation_index": 2},
            ])
            self.assertTrue(self.report(observation)["automated_checks_passed"], reason)

    def test_discovery_isolation_rejects_setup_hooks_writes_unknowns_and_other_diagnostics(self):
        good = self.good()
        for kind, reason in (("setup", ""), ("hook", ""), ("write", ""), ("unknown", ""),
                             ("diagnostic", "fixture absence"), ("diagnostic", "artifact directory creation")):
            observation = copy.deepcopy(good)
            fact = self.event("diagnostic", 85, path="specs/001-invitations", reason="file discovery")
            observation["diagnostics"].append(fact)
            observation["command_records"].append(self.record(85))
            companion = {**fact, "type": kind, "reason": reason, "path": TARGET,
                         "raw_operation_index": 1, "command": v1.SETUP_COMMAND}
            observation["diagnostics" if kind == "diagnostic" else "events"].append(companion)
            self.assertFalse(self.checks(self.report(observation))[
                "discovery-isolated-from-other-operations"], (kind, reason))

    def test_discovery_requires_unique_matching_successful_lifecycle(self):
        good = self.good()
        for change in ("failed", "unbacked", "wrong-boundary", "duplicate-record", "invalid-record"):
            observation = copy.deepcopy(good)
            fact = self.event("diagnostic", 85, path="specs/001-invitations", reason="file discovery")
            record = self.record(85)
            observation["diagnostics"].append(fact)
            if change != "unbacked":
                observation["command_records"].append(record)
            if change == "failed":
                fact.update(status="failed", exit_code=2)
            elif change == "wrong-boundary":
                fact["raw_completion_index"] += 1
            elif change == "duplicate-record":
                observation["command_records"].append(copy.deepcopy(record))
            elif change == "invalid-record":
                record["lifecycle_valid"] = False
            self.assertFalse(self.checks(self.report(observation))[
                "discovery-isolated-from-other-operations"], change)

    def test_extension_check_cannot_share_command_with_any_other_operation(self):
        good = self.good()
        for kind, reason in (("diagnostic", "file discovery"), ("diagnostic", "literal output label"),
                             ("read", ""), ("setup", ""), ("hook", ""), ("write", ""), ("unknown", "")):
            observation = copy.deepcopy(good)
            companion = {**observation["diagnostics"][0], "type": kind, "path": TARGET,
                         "raw_operation_index": 1, "reason": reason}
            observation["diagnostics" if kind == "diagnostic" else "events"].append(companion)
            checks = self.checks(self.report(observation))
            self.assertFalse(checks["extension-check-isolated-from-other-operations"], kind)

    def test_required_context_read_cannot_share_command_with_nonread_facts(self):
        good = self.good()
        for kind, reason in (("diagnostic", "fixture absence"), ("diagnostic", "file discovery"),
                             ("diagnostic", "artifact directory creation"), ("setup", ""),
                             ("hook", ""), ("write", ""), ("unknown", "")):
            observation = copy.deepcopy(good)
            read = next(e for e in observation["events"] if e.get("path") == "specs/001-invitations/spec.md")
            companion = {**read, "type": kind, "reason": reason, "path": ".specify/templates/checklist-template.md",
                         "raw_operation_index": 1}
            observation["diagnostics" if kind == "diagnostic" else "events"].append(companion)
            self.assertFalse(self.checks(self.report(observation))[
                "context-reads-isolated-from-discovery-and-mutation"], kind)

    def test_missing_failed_unbacked_and_ambiguous_context_reads_do_not_pass(self):
        good = self.good()
        for change in ("missing", "failed", "unbacked", "wrong-boundary", "duplicate-record",
                       "invalid-duplicate-record", "failed-record"):
            observation = copy.deepcopy(good)
            read = next(e for e in observation["events"] if e.get("path") == "specs/001-invitations/spec.md")
            record = next(r for r in observation["command_records"] if r["raw_item_id"] == read["raw_item_id"])
            if change == "missing":
                observation["events"].remove(read)
            elif change == "failed":
                read.update(status="failed", exit_code=2)
            elif change == "unbacked":
                observation["command_records"].remove(record)
            elif change == "wrong-boundary":
                read["raw_completion_index"] += 1
            elif change == "duplicate-record":
                observation["command_records"].append(copy.deepcopy(record))
            elif change == "invalid-duplicate-record":
                observation["command_records"].append({**record, "lifecycle_valid": False})
            else:
                record.update(status="failed", exit_code=2)
            self.assertFalse(self.checks(self.report(observation))[
                "context-reads-isolated-from-discovery-and-mutation"], change)

    def test_failed_or_duplicate_extension_attempt_is_not_repaired_by_later_success(self):
        good = self.good()
        for change in ("failed", "duplicate", "uncertified"):
            observation = copy.deepcopy(good)
            prior = copy.deepcopy(observation["diagnostics"][0])
            prior.update(raw_item_id="earlier-probe", raw_start_index=25, raw_completion_index=26)
            record = {**self.record(25), "raw_item_id": "earlier-probe"}
            if change == "failed":
                prior.update(status="failed", exit_code=2)
                record.update(status="failed", exit_code=2)
            elif change == "uncertified":
                prior["certified_absence"] = False
            else:
                observation["command_records"].append(copy.deepcopy(record))
            observation["diagnostics"].append(prior)
            observation["command_records"].append(record)
            self.assertFalse(self.checks(self.report(observation))[
                "extension-check-isolated-from-other-operations"], change)

    def test_prior_or_wrong_manifest_versions_are_rejected_without_regrading(self):
        observation = self.good()
        for field, value in (("checker_version", 7), ("observation_schema_version", 6),
                             ("pilot_id", "opt-004-workflow-fidelity-v7")):
            manifest = copy.deepcopy(self.manifest)
            manifest[field] = value
            self.path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "newly prepared v8 bundle"):
                self.report(observation)
        self.path.write_text(json.dumps(self.manifest))
        for schema in (1, 5, 6, 8, None):
            observation["schema_version"] = schema
            with self.assertRaisesRegex(ValueError, "v7 observation schema"):
                self.report(observation)

    def test_new_and_inherited_dependency_hashes_are_enforced(self):
        observation = self.good()
        for name in ("checker-v7.py", "checker-v8.py", "trace-v6.py", "trace-v7.py", "rubric.md", "pilot.json"):
            manifest = copy.deepcopy(self.manifest)
            manifest["provenance"]["instruments"][name] = "0" * 64
            self.path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "dependency version differs"):
                self.report(observation)

    def test_tampered_copied_instrument_and_prompt_are_rejected(self):
        observation = self.good()
        for path in (self.output / "instrument/trace-v7.py", self.directory / "prompt.md"):
            original = path.read_bytes()
            path.write_bytes(original + b"\n# changed\n")
            with self.assertRaisesRegex(ValueError, "instrument changed|prompt changed"):
                self.report(observation)
            path.write_bytes(original)

    def test_absence_still_requires_matching_successful_prior_certificate(self):
        good = self.good()
        for changes in ({"certified_absence": False}, {"raw_item_id": "unbacked"},
                        {"raw_completion_index": 40}, {"raw_start_index": 41, "raw_completion_index": 42},
                        {"path": ".git"}, {"exit_code": 1}, {"status": "failed"}):
            observation = copy.deepcopy(good)
            observation["diagnostics"][0].update(changes)
            report = self.report(observation)
            self.assertFalse(self.checks(report)["extension-config-before-setup"], changes)
            self.assertFalse(report["automated_checks_passed"])

    def test_separate_reference_and_setup_checkpoints_remain_hard_gates(self):
        good = self.good()
        observation = copy.deepcopy(good)
        observation["events"][1]["read_coverage"] = {"complete": False}
        self.assertFalse(self.checks(self.report(observation))["reference-before-project-actions"])
        observation = copy.deepcopy(good)
        observation["diagnostics"][0].update(raw_item_id="op-40", raw_start_index=40,
                                             raw_completion_index=41, raw_operation_index=0)
        observation["events"][2]["raw_operation_index"] = 1
        checks = self.checks(self.report(observation))
        self.assertFalse(checks["extension-config-before-setup"])
        self.assertFalse(checks["setup-isolated-from-file-reads"])

    def test_final_readback_and_unsupported_git_claims_remain_hard_gates(self):
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
        observation = copy.deepcopy(good)
        observation["events"][-1]["read_coverage"] = {"complete": False}
        self.assertFalse(self.checks(self.report(observation))["separate-final-artifact-readback"])

    def raw_observation(self, absence_command=ABSENCE, absence_output="NO_EXTENSIONS_FILE\n",
                        discovery="none"):
        observation = self.good()
        raw = []
        def event(method, item):
            return {"method": method, "params": {"threadId": "t", "turnId": "u", "item": item}}
        def item(value):
            value = {"id": str(len(raw)), "status": "completed", **value}
            raw.extend([event("item/started", {**value, "status": "inProgress"}),
                        event("item/completed", value)])
        def command(text, output):
            item({"type": "commandExecution", "command": text, "cwd": str(self.workspace),
                  "exitCode": 0, "aggregatedOutput": output, "commandActions": []})
        command("cat " + REFERENCE, (self.workspace / REFERENCE).read_text())
        command(absence_command, absence_output)
        command(v1.SETUP_COMMAND, json.dumps({
            "FEATURE_DIR": str(self.workspace / "specs/001-invitations"),
            "AVAILABLE_DOCS": ["spec.md"],
            "TEMPLATE_CONTENT": (self.workspace / ".specify/templates/checklist-template.md").read_text(),
        }) + "\n")
        for path in self.manifest["required_reads"]:
            data = bytes.fromhex(self.manifest["baseline_target_hex"]) if path == TARGET else (self.workspace / path).read_bytes()
            if path == "specs/001-invitations/spec.md" and discovery == "mixed":
                command("cat " + path + "; rg --files specs/001-invitations",
                        data.decode() + TARGET + "\nspecs/001-invitations/spec.md\n")
            else:
                command("cat " + path, data.decode())
        if discovery == "separate":
            command("rg --files specs/001-invitations", TARGET + "\nspecs/001-invitations/spec.md\n")
        elif discovery == "mixed-template":
            command("cat .specify/templates/checklist-template.md && rg --files --hidden specs/001-invitations",
                    (self.workspace / ".specify/templates/checklist-template.md").read_text()
                    + TARGET + "\nspecs/001-invitations/spec.md\n")
        item({"type": "fileChange", "changes": [{"path": TARGET, "kind": {"type": "update"}, "diff": "synthetic"}]})
        command("cat " + TARGET, self.target.read_text())
        item({"type": "agentMessage", "text": observation["final_output"], "phase": "final_answer"})
        raw.extend([{"method": "thread/tokenUsage/updated", "params": {"threadId": "t", "turnId": "u", "tokenUsage": {"total": {
            "inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 1,
            "reasoningOutputTokens": 0, "totalTokens": 11}}}},
            {"method": "turn/completed", "params": {"threadId": "t", "turnId": "u", "turn": {"id": "u", "status": "completed"}}}])
        result = normalize_events(raw, thread_id="t", turn_id="u", workspace=self.workspace,
                                  manifest=self.manifest, latency_ms=1)
        result["evidence_kind"] = "offline-simulation"
        return result

    def test_literal_else_printf_raw_certificate_integrates_with_separation_gates(self):
        observation = self.raw_observation()
        self.assertEqual(7, observation["schema_version"])
        self.assertEqual([], observation["issues"])
        certificates = [d for d in observation["diagnostics"] if d.get("certified_absence")]
        self.assertEqual([".specify/extensions.yml"], [d["path"] for d in certificates])
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))
        self.assertFalse(report["eligible_for_promotion"])

    def test_separate_successful_discovery_integrates_without_relaxing_gates(self):
        observation = self.raw_observation(discovery="separate")
        self.assertEqual([], observation["issues"])
        report = self.report(observation)
        self.assertTrue(report["automated_checks_passed"], self.checks(report))

    def test_new_parser_can_attribute_mixed_command_while_new_checker_rejects_workflow(self):
        observation = self.raw_observation(discovery="mixed")
        self.assertEqual([], observation["issues"])
        certificates = [d for d in observation["diagnostics"] if d.get("terminal_discovery_certificate")]
        self.assertEqual(1, len(certificates))
        self.assertTrue(any(e.get("type") == "read" and e["raw_item_id"] == certificates[0]["raw_item_id"]
                            for e in observation["events"]))
        report = self.report(observation)
        self.assertFalse(report["automated_checks_passed"])
        self.assertFalse(self.checks(report)["context-reads-isolated-from-discovery-and-mutation"])
        self.assertFalse(self.checks(report)["discovery-isolated-from-other-operations"])

    def test_inherited_template_read_and_discovery_grammar_cannot_bypass_new_boundaries(self):
        observation = self.raw_observation(discovery="mixed-template")
        self.assertEqual([], observation["issues"])
        self.assertTrue(any(e.get("path") == ".specify/templates/checklist-template.md"
                            for e in observation["events"]))
        report = self.report(observation)
        checks = self.checks(report)
        self.assertFalse(report["automated_checks_passed"])
        self.assertEqual({"context-reads-isolated-from-discovery-and-mutation",
                          "discovery-isolated-from-other-operations"},
                         {name for name, passed in checks.items() if not passed})

    def test_printing_label_alone_or_mismatched_stdout_cannot_pass_absence_gate(self):
        for command, output in (("printf 'NO_EXTENSIONS_FILE\\n'", "NO_EXTENSIONS_FILE\n"),
                                (ABSENCE, ""), (ABSENCE, "NO_EXTENSIONS_FILE\nextra\n")):
            observation = self.raw_observation(command, output)
            self.assertFalse(any(d.get("certified_absence") for d in observation["diagnostics"]))
            self.assertFalse(self.checks(self.report(observation))["extension-config-before-setup"])


if __name__ == "__main__":
    unittest.main()
