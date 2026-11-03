"""Fresh synthetic guarded-echo traces; no historical results or command execution."""

from __future__ import annotations

import copy
import shlex
import unittest
from unittest.mock import patch

from harnessmith.workflow_trace_v8 import normalize_events as normalize_v8
from harnessmith.workflow_trace_v9 import normalize_events
from tests import test_workflow_trace_v8 as fixtures
from tests.test_workflow_trace_v7 import ROOT, SPEC, TARGET, event
from tests.test_workflow_trace_v8 import CONFIG, PRINCIPLES


class WorkflowTraceV9Tests(unittest.TestCase):
    setUp = fixtures.WorkflowTraceV8Tests.setUp
    pin = fixtures.WorkflowTraceV8Tests.pin
    inventory = fixtures.WorkflowTraceV8Tests.inventory
    command = fixtures.WorkflowTraceV8Tests.command
    body = fixtures.WorkflowTraceV8Tests.body
    listing = fixtures.WorkflowTraceV8Tests.listing
    read = fixtures.WorkflowTraceV8Tests.read
    write = fixtures.WorkflowTraceV8Tests.write

    def normalize(self, items, normalizer=normalize_events, **kwargs):
        return fixtures.WorkflowTraceV8Tests.normalize(self, items, normalizer, **kwargs)

    def conditional(self, path=CONFIG, output="ABSENT\n", **kwargs):
        self.manifest["pinned_absent_paths"] = [CONFIG]
        return self.command(self.guarded(path), output, **{"id": "conditional", **kwargs})

    @staticmethod
    def guarded(path=CONFIG):
        word = shlex.quote(path)
        return f"if [ -f {word} ]; then cat {word}; else test ! -e {word} && echo ABSENT; fi"

    def proofs(self, result, field="absence_certificate"):
        return [fact for fact in result["events"] + result["diagnostics"]
                if fact.get(field, {}).get("instrumentation") == "codex-workflow-trace-v9"]

    def assertRejected(self, items, field="absence_certificate", **kwargs):
        result = self.normalize(items, **kwargs)
        self.assertEqual([], self.proofs(result, field))
        self.assertTrue(result["issues"])
        return result

    def appended(self):
        before = (self.workspace / TARGET).read_text()
        after = before + "- [ ] CHK002 New question?\n"
        items = self.conditional(id="pre") + self.write()
        (self.workspace / TARGET).write_text(after)
        items += self.command("cat " + TARGET, after, id="readback")
        items += self.conditional(id="post")
        return items

    def test_absence_certifies_exact_guarded_marker_and_retains_inherited_failure(self):
        items = self.conditional()
        initial = copy.deepcopy((items, self.manifest))
        old = self.normalize(items, normalize_v8)
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        fact = self.proofs(result)[0]
        proof = fact["absence_certificate"]
        self.assertTrue(fact["certified_absence"])
        self.assertEqual("literal-else-test-echo", proof["proof"])
        self.assertEqual("ABSENT\n", proof["absence_marker"])
        self.assertEqual(old["issues"], proof["superseded_inherited_issues"])
        self.assertEqual(old["events"], proof["superseded_inherited_facts"])
        self.assertEqual(old["command_records"], result["command_records"])
        self.assertEqual(initial, (items, self.manifest))
        self.assertEqual(old, self.normalize(items, normalize_v8))
        self.assertEqual((9, "codex-workflow-trace-v9", "codex-workflow-trace-v8"), tuple(
            result[key] for key in ("schema_version", "instrumentation", "base_normalizer")))

    def test_present_branch_reads_exact_pinned_bytes_and_parses_unused_else(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPreserve intent.\n")
        result = self.normalize(self.conditional(PRINCIPLES, text))
        self.assertEqual([], result["issues"])
        fact = self.proofs(result, "conditional_read_certificate")[0]
        self.assertEqual(self.manifest["baseline"][PRINCIPLES], fact["read_sha256"])
        self.assertTrue(fact["read_coverage"]["complete"])
        self.assertTrue(fact["read_before_write"])
        bad = self.guarded(PRINCIPLES).replace("echo ABSENT", "touch marker")
        self.assertRejected(self.command(bad, text), "conditional_read_certificate")

    def test_three_repaired_checkpoints_and_downstream_discovery_are_correlated(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPreserve intent.\n")
        items = self.conditional(id="pre") + self.conditional(PRINCIPLES, text, id="principles")
        items += self.command("rg --files " + ROOT, self.listing(), id="discovery")
        before = (self.workspace / TARGET).read_text()
        items += self.command("cat " + TARGET, before, id="before") + self.write()
        after = before + "- [ ] CHK002 New question?\n"
        (self.workspace / TARGET).write_text(after)
        items += self.command("cat " + TARGET, after, id="after") + self.conditional(id="post")
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        self.assertEqual(2, len(self.proofs(result)))
        self.assertEqual(1, len(self.proofs(result, "conditional_read_certificate")))
        discovery = self.proofs(result, "terminal_discovery_certificate")[0]
        self.assertFalse(discovery["certifies_absence"])
        self.assertFalse(discovery["certifies_file_contents"])
        self.assertFalse(discovery["terminal_discovery_certificate"]["workflow_separation_implied"])
        self.assertIn("terminal discovery proof rejected", discovery["terminal_discovery_certificate"]["superseded_inherited_issues"][0]["detail"])

    def test_postappend_certificate_records_exact_native_append_and_readback(self):
        result = self.normalize(self.appended())
        self.assertEqual([], result["issues"])
        proof = self.proofs(result)[1]["absence_certificate"]
        append = proof["accounted_native_appends"][0]
        self.assertEqual("write", append["raw_item_id"])
        self.assertEqual(["readback"], append["readback_item_ids"])
        self.assertGreater(append["after_bytes"], append["before_bytes"])
        self.assertTrue(any(fact["type"] == "write" for fact in result["events"]))

    def test_observed_absolute_native_path_and_explicit_null_move_are_supported(self):
        items = self.appended()
        for raw in items[2:4]:
            raw["params"]["item"]["changes"] = [{"path": str(self.workspace / TARGET),
                                                  "kind": {"type": "update", "move_path": None},
                                                  "diff": "synthetic append"}]
        self.assertEqual(2, len(self.proofs(self.normalize(items))))

    def test_postappend_rejects_mode_changes_and_symlink_aliases(self):
        for path in (SPEC, TARGET):
            items = self.appended()
            (self.workspace / path).chmod(0o755)
            self.assertNotIn("post", [fact["raw_item_id"] for fact in self.proofs(self.normalize(items))])
            (self.workspace / path).chmod(0o644)
            (self.workspace / TARGET).write_bytes(bytes.fromhex(self.manifest["baseline_target_hex"]))
        items = self.appended()
        alias = self.workspace / "linked"
        alias.symlink_to(self.workspace / TARGET)
        self.assertNotIn("post", [fact["raw_item_id"] for fact in self.proofs(self.normalize(items))])

    def test_native_append_cannot_overlap_a_prior_operation(self):
        items = self.appended()
        read = self.read()
        items[2:4] = [read[0], items[2], items[3], read[1]]
        result = self.normalize(items)
        self.assertNotIn("post", [fact["raw_item_id"] for fact in self.proofs(result)])

    def test_recovered_guarded_prefix_enables_only_inherited_read_concurrency(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        left, right = self.read(SPEC), self.read(TARGET)
        items = self.conditional(PRINCIPLES, text) + [left[0], right[0], left[1], right[1]]
        old = self.normalize(items, normalize_v8)
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        proof = self.proofs(result, "read_only_attribution_certificate")[0]["read_only_attribution_certificate"]
        self.assertEqual(["read-" + TARGET], proof["overlapping_read_only_item_ids"])
        self.assertTrue(any(issue["detail"] == "exact read overlaps an uncompleted operation"
                            for issue in proof["superseded_inherited_issues"]))
        self.assertEqual(old["command_records"], result["command_records"])
        mutation = self.command("touch unknown", "", id="unknown")
        result = self.normalize(self.conditional(PRINCIPLES, text)
                                + [left[0], right[0], mutation[0], left[1], mutation[1], right[1]])
        self.assertEqual([], self.proofs(result, "read_only_attribution_certificate"))

    def test_mixed_discovery_recovers_attribution_without_implying_separation(self):
        items = self.conditional() + self.command(self.body(), self.spec + self.template + self.listing())
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        proof = self.proofs(result, "terminal_discovery_certificate")[0]["terminal_discovery_certificate"]
        self.assertFalse(proof["workflow_separation_implied"])
        self.assertEqual(2, len(proof["prefix_reads"]))
        self.assertEqual(2, len(proof["superseded_inherited_issues"]))

    def test_unrelated_item_issue_or_fact_cannot_be_silently_erased(self):
        items = self.conditional()
        old = self.normalize(items, normalize_v8)
        for field, entry in (("issues", {"kind": "fidelity", "detail": "unrelated", "raw_item_id": "conditional",
                                          "raw_start_index": 0, "raw_completion_index": 1}),
                             ("events", {**old["events"][0], "reason": "unrelated"})):
            altered = copy.deepcopy(old)
            altered[field].append(entry)
            with patch("harnessmith.workflow_trace_v9.normalize_v8", return_value=altered):
                result = self.normalize(items)
            self.assertEqual([], self.proofs(result))
            self.assertIn(entry, result[field])

    def test_non_extension_absence_and_foreign_passive_scope(self):
        items = self.conditional("missing.md")
        self.manifest["pinned_absent_paths"].append("missing.md")
        self.assertRejected(items)
        items = self.conditional()
        passive = event("item/completed", item={"id": "message", "type": "agentMessage", "text": "unrelated"})
        passive["params"]["threadId"] = "foreign"
        result = self.normalize([items[0], passive, items[1]])
        self.assertEqual(1, len(self.proofs(result)))

    def test_same_path_quotes_absolute_paths_and_nonlogin_shell(self):
        for path in (CONFIG, str(self.workspace / CONFIG)):
            items = self.conditional(path)
            for raw in items:
                raw["params"]["item"]["command"] = "/bin/zsh -c " + shlex.quote(raw["params"]["item"]["command"])
            self.assertEqual(1, len(self.proofs(self.normalize(items))))
        recorded = self.workspace.parent / "recorded"
        items = self.conditional(str(recorded / CONFIG), cwd=str(recorded))
        self.assertEqual(1, len(self.proofs(self.normalize(items, recorded_workspace=recorded))))

    def test_wrong_paths_connectors_marker_extra_operations_and_unsafe_branches(self):
        base = self.guarded()
        variants = [
            base.replace("cat " + CONFIG, "cat " + SPEC),
            base.replace("test ! -e " + CONFIG, "test ! -e " + SPEC),
            base.replace("test ! -e", "test ! -f"), base.replace("&&", ";"),
            base.replace("&&", "||"), base.replace("&&", "&"),
            base.replace("&& echo ABSENT", "&& echo ABSENT && true"),
            base.replace("echo ABSENT", "echo -n ABSENT"),
            base.replace("echo ABSENT", "echo ABSENT extra"),
            base.replace("echo ABSENT", "echo absent"),
            base.replace("echo ABSENT", "printf ABSENT"),
            base.replace("echo ABSENT", "/bin/echo ABSENT"),
            base.replace("cat " + CONFIG, "touch marker"),
            base.replace("cat " + CONFIG, "cat " + CONFIG + "; touch marker"),
            base.replace(CONFIG, '"$PATH"'), base.replace(CONFIG, '"$(pwd)/absent"'),
            base + "; true", base + " 2>/dev/null", base + " || true",
            base.replace(CONFIG, "./" + CONFIG),
        ]
        self.manifest["pinned_absent_paths"] = [CONFIG]
        for body in variants:
            with self.subTest(body=body):
                self.assertRejected(self.command(body, "ABSENT\n"))

    def test_wrong_noisy_missing_and_null_marker_output(self):
        for output in ("ABSENT", "ABSENT\r\n", "absent\n", "noise\nABSENT\n", "ABSENT\nnoise", "", None, 0, False, [], {}):
            items = self.conditional()
            items[1]["params"]["item"]["aggregatedOutput"] = output
            self.assertRejected(items)
        items = self.conditional()
        del items[1]["params"]["item"]["aggregatedOutput"]
        self.assertRejected(items)

    def test_present_wrong_empty_and_failed_output(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        for output in (text[:-1], text + "noise", "ABSENT\n", "", None):
            items = self.conditional(PRINCIPLES, text)
            items[1]["params"]["item"]["aggregatedOutput"] = output
            self.assertRejected(items, "conditional_read_certificate")
        self.pin(PRINCIPLES, b"")
        self.assertRejected(self.conditional(PRINCIPLES, ""), "conditional_read_certificate")
        text = self.pin(PRINCIPLES, b"Permission denied\n")
        self.assertRejected(self.conditional(PRINCIPLES, text), "conditional_read_certificate")

    def test_failed_commands_mismatched_lifecycle_and_scope_remain_failed(self):
        for field, value in (("exitCode", 1), ("exitCode", False), ("status", "failed"), ("source", "unknown")):
            items = self.conditional()
            items[1]["params"]["item"][field] = value
            self.assertRejected(items)
        for variant in ("missing", "duplicate", "reversed", "scope", "command", "cwd", "source", "login"):
            items = self.conditional()
            if variant == "missing":
                items.pop()
            elif variant == "duplicate":
                items.insert(0, copy.deepcopy(items[0]))
            elif variant == "reversed":
                items.reverse()
            elif variant == "scope":
                items[0]["params"]["threadId"] = "foreign"
            elif variant == "login":
                for raw in items:
                    raw["params"]["item"]["command"] = "/bin/zsh -lc " + shlex.quote(raw["params"]["item"]["command"])
            else:
                items[0]["params"]["item"][variant] = "different"
            self.assertRejected(items)

    def test_pins_absence_present_files_directories_and_symlinks(self):
        for variant in ("hash", "unpinned", "present", "directory", "symlink"):
            items, original = self.conditional(), copy.deepcopy(self.manifest)
            path = self.workspace / CONFIG
            if variant == "hash":
                self.manifest["baseline_inventory_sha256"] = "0" * 64
            elif variant == "unpinned":
                self.manifest["pinned_absent_paths"] = []
            elif variant == "present":
                path.write_text("changed")
            elif variant == "directory":
                path.mkdir()
            else:
                path.symlink_to("nonexistent")
            self.assertRejected(items)
            if path.is_dir():
                path.rmdir()
            elif path.exists() or path.is_symlink():
                path.unlink()
            self.manifest = original
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        path = self.workspace / PRINCIPLES
        path.unlink()
        path.symlink_to(self.workspace / SPEC)
        self.assertRejected(self.conditional(PRINCIPLES, text), "conditional_read_certificate")

    def test_foreign_prior_unknown_mutation_and_overlap_cannot_be_repaired(self):
        for prefix in (self.command("touch marker", "", id="unknown"), self.write()):
            self.assertRejected(prefix + self.conditional())
        foreign = self.read()
        for raw in foreign:
            raw["params"]["threadId"] = "foreign"
        self.assertRejected(foreign + self.conditional())
        read, probe = self.read(), self.conditional()
        self.assertRejected([read[0], probe[0], read[1], probe[1]])
        self.assertRejected([probe[0], read[0], probe[1], read[1]])

    def test_postappend_requires_complete_unique_native_update_and_separate_readback(self):
        for variant in ("extra", "add", "move", "unknownkey", "mismatch", "failed", "missing", "no-readback", "two-writes", "nonprefix", "changed-spec"):
            with self.subTest(variant=variant):
                before = bytes.fromhex(self.manifest["baseline_target_hex"])
                (self.workspace / TARGET).write_bytes(before)
                items = self.appended()
                if variant == "extra":
                    for raw in items[2:4]:
                        raw["params"]["item"]["changes"] = raw["params"]["item"]["changes"] + [{"path": SPEC, "kind": {"type": "update"}, "diff": "extra"}]
                elif variant in {"add", "move", "unknownkey"}:
                    for raw in items[2:4]:
                        change = copy.deepcopy(raw["params"]["item"]["changes"][0])
                        if variant == "add":
                            change["kind"] = {"type": "add"}
                        elif variant == "move":
                            change["kind"]["movePath"] = SPEC
                        else:
                            change["extra"] = "unknown"
                        raw["params"]["item"]["changes"] = [change]
                elif variant == "mismatch":
                    items[2]["params"]["item"]["changes"] = []
                elif variant == "failed":
                    items[3]["params"]["item"]["status"] = "failed"
                elif variant == "missing":
                    items.pop(2)
                elif variant == "no-readback":
                    del items[4:6]
                elif variant == "two-writes":
                    extra = self.write()
                    for raw in extra:
                        raw["params"]["item"]["id"] = "write-again"
                    items[4:4] = extra
                elif variant == "nonprefix":
                    (self.workspace / TARGET).write_text("replaced\n")
                else:
                    (self.workspace / SPEC).write_text("changed\n")
                result = self.normalize(items)
                self.assertNotIn("post", [fact["raw_item_id"] for fact in self.proofs(result)])
                (self.workspace / SPEC).write_text(self.spec)

    def test_inherited_null_absence_certificates_remain_v8_unchanged(self):
        items = fixtures.WorkflowTraceV8Tests.conditional(self)
        items[1]["params"]["item"]["aggregatedOutput"] = None
        old, result = self.normalize(items, normalize_v8), self.normalize(items)
        self.assertEqual(old["diagnostics"], result["diagnostics"])
        self.assertEqual([], result["issues"])
        self.assertEqual("codex-workflow-trace-v8", result["diagnostics"][0]["absence_certificate"]["instrumentation"])

    def test_downstream_discovery_does_not_hide_wrong_output_or_unknown_prefix(self):
        for discovery in (self.command("rg --files " + ROOT, "invented.md\n", id="discovery"),
                          self.command("rg --files " + ROOT + "; true", self.listing(), id="discovery")):
            result = self.normalize(self.conditional() + discovery)
            self.assertEqual([], self.proofs(result, "terminal_discovery_certificate"))
            self.assertTrue(result["issues"])
        result = self.normalize(self.conditional() + self.command("touch unknown", "", id="unknown")
                                + self.command("rg --files " + ROOT, self.listing(), id="discovery"))
        self.assertEqual([], self.proofs(result, "terminal_discovery_certificate"))


if __name__ == "__main__":
    unittest.main()
