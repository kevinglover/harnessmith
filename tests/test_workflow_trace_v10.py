"""Fresh synthetic if-test/printf proofs; no historical command replay/regrade."""

from __future__ import annotations

import copy
from pathlib import Path
import shlex
import unittest
from unittest.mock import patch

from harnessmith.workflow_trace_v9 import normalize_events as normalize_v9
from harnessmith.workflow_trace_v10 import normalize_events
from tests.test_workflow_trace_v7 import ROOT, SPEC, TARGET
from tests.test_workflow_trace_v8 import CONFIG, PRINCIPLES
from tests import test_workflow_trace_v9 as fixtures


class WorkflowTraceV10Tests(unittest.TestCase):
    setUp = fixtures.WorkflowTraceV9Tests.setUp
    pin = fixtures.WorkflowTraceV9Tests.pin
    inventory = fixtures.WorkflowTraceV9Tests.inventory
    command = fixtures.WorkflowTraceV9Tests.command
    body = fixtures.WorkflowTraceV9Tests.body
    listing = fixtures.WorkflowTraceV9Tests.listing
    read = fixtures.WorkflowTraceV9Tests.read
    write = fixtures.WorkflowTraceV9Tests.write
    appended = fixtures.WorkflowTraceV9Tests.appended

    def normalize(self, items, normalizer=normalize_events, **kwargs):
        return fixtures.WorkflowTraceV9Tests.normalize(self, items, normalizer, **kwargs)

    @staticmethod
    def conditional_body(path=CONFIG):
        word = shlex.quote(path)
        return f"if test -f {word}; then cat {word}; else printf 'ABSENT\\n'; fi"

    def conditional(self, path=CONFIG, output="ABSENT\n", **kwargs):
        self.manifest["pinned_absent_paths"] = [CONFIG]
        return self.command(self.conditional_body(path), output,
                            **{"id": "conditional", **kwargs})

    def proofs(self, result, field="absence_certificate"):
        return [fact for fact in result["events"] + result["diagnostics"]
                if fact.get(field, {}).get("instrumentation") == "codex-workflow-trace-v10"]

    def reject(self, items, field="absence_certificate", **kwargs):
        result = self.normalize(items, **kwargs)
        self.assertEqual([], self.proofs(result, field))
        self.assertTrue(result["issues"])
        return result

    def test_exact_absence_preserves_raw_inherited_failures_and_version_identity(self):
        items = self.conditional()
        before = copy.deepcopy((items, self.manifest))
        old, result = self.normalize(items, normalize_v9), self.normalize(items)
        self.assertEqual([], result["issues"])
        proof = self.proofs(result)[0]["absence_certificate"]
        self.assertEqual("literal-test-f-printf", proof["proof"])
        self.assertEqual("ABSENT\n", proof["absence_marker"])
        self.assertEqual("text", proof["output_representation"])
        self.assertTrue(proof["complete_command_coverage"])
        self.assertFalse(proof["stderr_stripped"])
        self.assertEqual(old["issues"], proof["superseded_inherited_issues"])
        self.assertEqual(old["events"], proof["superseded_inherited_facts"])
        self.assertEqual(old["command_records"], result["command_records"])
        self.assertEqual(before, (items, self.manifest))
        self.assertEqual(old, self.normalize(items, normalize_v9))
        self.assertEqual((10, "codex-workflow-trace-v10", "codex-workflow-trace-v9"), tuple(
            result[key] for key in ("schema_version", "instrumentation", "base_normalizer")))

    def test_present_full_pinned_bytes_and_unsafe_unused_branch(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPreserve intent.\n")
        result = self.normalize(self.conditional(PRINCIPLES, text))
        self.assertEqual([], result["issues"])
        fact = self.proofs(result, "conditional_read_certificate")[0]
        self.assertEqual(self.manifest["baseline"][PRINCIPLES], fact["read_sha256"])
        self.assertTrue(fact["read_coverage"]["complete"])
        self.assertTrue(fact["read_before_write"])
        body = self.conditional_body(PRINCIPLES).replace("printf 'ABSENT\\n'", "touch marker")
        self.reject(self.command(body, text), "conditional_read_certificate")

    def test_direct_single_quoted_and_double_quoted_nonlogin_wrappers(self):
        body = self.conditional_body()
        variants = [body, "/bin/zsh -c " + shlex.quote(body),
                    '/bin/zsh -c "' + body + '"',
                    '/bin/zsh -c "' + body.replace("\\", "\\\\") + '"']
        self.manifest["pinned_absent_paths"] = [CONFIG]
        for command in variants:
            with self.subTest(command=command):
                result = self.normalize(self.command(command, "ABSENT\n"))
                self.assertEqual([], result["issues"])
                self.assertEqual(command, self.proofs(result)[0]["raw_command"])

    def test_quoted_space_and_apostrophe_paths_and_recorded_workspace(self):
        name = "notes/reviewer's principles.md"
        text = self.pin(name, b"# Pinned\nLiteral path.\n")
        body = self.conditional_body(name)
        result = self.normalize(self.command('/bin/zsh -c ' + shlex.quote(body), text))
        self.assertEqual(1, len(self.proofs(result, "conditional_read_certificate")))
        recorded = Path("/recorded/isolated/workspace")
        items = self.conditional(str(recorded / CONFIG), cwd=str(recorded))
        self.assertEqual(1, len(self.proofs(self.normalize(items, recorded_workspace=recorded))))

    def test_bad_wrapping_expansions_and_backslash_semantics(self):
        self.manifest["pinned_absent_paths"] = [CONFIG]
        body = self.conditional_body()
        for command in (
            "/bin/zsh -lc " + shlex.quote(body),
            "/bin/zsh -ic " + shlex.quote(body),
            "/bin/zsh -c " + shlex.quote(body) + " extra",
            "/bin/zsh -c " + shlex.quote(body) + "; true",
            '/bin/zsh -c "' + body.replace(CONFIG, "'$FILE'") + '"',
            '/bin/zsh -c "' + body.replace(CONFIG, "'$(pwd)/file'") + '"',
            '/bin/zsh -c "' + body.replace(CONFIG, "'`pwd`/file'") + '"',
            '/bin/zsh -c "' + body.replace("\\", "\\\\\\\\") + '"',
            "/bin/zsh -c " + shlex.quote(body.replace("\\", "\\\\")),
            "/bin/zsh -c '" + body + "'",
        ):
            with self.subTest(command=command):
                self.reject(self.command(command, "ABSENT\n"))

    def test_bad_paths_format_and_mixed_commands_are_not_new_proofs(self):
        self.manifest["pinned_absent_paths"] = [CONFIG]
        body = self.conditional_body()
        variants = [body.replace("cat " + CONFIG, "cat " + SPEC),
                    body.replace("test -f", "test -e"),
                    body.replace("test -f", "/usr/bin/test -f"),
                    body.replace("printf 'ABSENT\\n'", "printf '%s\\n' ABSENT"),
                    body.replace("printf 'ABSENT\\n'", "printf 'ABSENT'"),
                    body.replace("printf 'ABSENT\\n'", "printf 'ABSENT\\n' extra"),
                    body.replace("printf 'ABSENT\\n'", "/usr/bin/printf 'ABSENT\\n'"),
                    body.replace("printf 'ABSENT\\n'", "echo ABSENT"),
                    body.replace("cat " + CONFIG, "touch marker"),
                    body.replace("cat " + CONFIG, "cat " + CONFIG + "; touch marker"),
                    body.replace("printf 'ABSENT\\n'", "printf 'ABSENT\\n'; touch marker"),
                    body.replace(CONFIG, "./" + CONFIG), body.replace(CONFIG, "$FILE"),
                    body + "; true", body + " || true", body + " 2>/dev/null"]
        for command in variants:
            with self.subTest(command=command):
                self.reject(self.command(command, "ABSENT\n"))

    def test_wrong_missing_null_and_noisy_outputs_fail(self):
        for output in (None, "", "ABSENT", "ABSENT\r\n", "absent\n", "noise\nABSENT\n",
                       "ABSENT\nnoise", 0, False, [], {}):
            items = self.conditional()
            items[1]["params"]["item"]["aggregatedOutput"] = output
            self.reject(items)
        items = self.conditional()
        del items[1]["params"]["item"]["aggregatedOutput"]
        self.reject(items)
        text = self.pin(PRINCIPLES, b"# Pinned\n")
        for output in (text[:-1], text + "noise", "ABSENT\n", "", None):
            items = self.conditional(PRINCIPLES, text)
            items[1]["params"]["item"]["aggregatedOutput"] = output
            self.reject(items, "conditional_read_certificate")
        self.pin(PRINCIPLES, b"")
        self.reject(self.conditional(PRINCIPLES, ""), "conditional_read_certificate")

    def test_lifecycle_failures_and_wrong_scope_remain_binding(self):
        for field, value in (("exitCode", 1), ("exitCode", False), ("status", "failed"),
                             ("command", "true"), ("cwd", "/tmp"), ("source", "unknown")):
            items = self.conditional()
            items[1]["params"]["item"][field] = value
            self.reject(items)
        for variant in ("missing", "duplicate", "reversed", "thread", "turn"):
            items = self.conditional()
            if variant == "missing":
                items.pop()
            elif variant == "duplicate":
                items.insert(0, copy.deepcopy(items[0]))
            elif variant == "reversed":
                items.reverse()
            else:
                items[0]["params"][variant + "Id"] = "foreign"
            self.reject(items)

    def test_pinned_absence_inventory_present_file_directory_and_symlinks(self):
        for variant in ("hash", "unpinned", "file", "directory", "symlink"):
            items = self.conditional()
            before = copy.deepcopy(self.manifest)
            path = self.workspace / CONFIG
            if variant == "hash":
                self.manifest["baseline_inventory_sha256"] = "0" * 64
            elif variant == "unpinned":
                self.manifest["pinned_absent_paths"] = []
            elif variant == "file":
                path.write_text("present")
            elif variant == "directory":
                path.mkdir()
            else:
                path.symlink_to("nonexistent")
            self.reject(items)
            if path.is_dir():
                path.rmdir()
            elif path.exists() or path.is_symlink():
                path.unlink()
            self.manifest = before
        items = self.conditional("missing.md")
        self.manifest["pinned_absent_paths"].append("missing.md")
        self.reject(items)

    def test_present_symlink_and_changed_pin_are_rejected(self):
        text = self.pin(PRINCIPLES, b"# Pinned\n")
        path = self.workspace / PRINCIPLES
        path.write_text("changed")
        self.reject(self.conditional(PRINCIPLES, text), "conditional_read_certificate")
        path.unlink()
        path.symlink_to(self.workspace / SPEC)
        self.reject(self.conditional(PRINCIPLES, text), "conditional_read_certificate")
        parent = self.workspace / ".specify"
        moved = self.workspace / "real-specify"
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
        self.reject(self.conditional())

    def test_unknown_mutation_and_overlapping_actions_block_new_proofs(self):
        self.reject(self.command("touch marker", "", id="unknown") + self.conditional())
        self.reject(self.write() + self.conditional())
        read, probe = self.read(), self.conditional()
        self.reject([read[0], probe[0], read[1], probe[1]])
        self.reject([probe[0], read[0], probe[1], read[1]])
        foreign = self.read()
        for raw in foreign:
            raw["params"]["threadId"] = "foreign"
        self.reject(foreign + probe)

    def test_postappend_probe_records_native_append_and_full_readback(self):
        items = self.appended()
        for raw in items[2:4]:
            raw["params"]["item"]["changes"] = [{"path": str(self.workspace / TARGET),
                "kind": {"type": "update", "move_path": None}, "diff": "synthetic append"}]
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        self.assertEqual(2, len(self.proofs(result)))
        accounted = self.proofs(result)[1]["absence_certificate"]["accounted_native_appends"]
        self.assertEqual("write", accounted[0]["raw_item_id"])
        self.assertEqual(["readback"], accounted[0]["readback_item_ids"])
        self.assertGreater(accounted[0]["after_bytes"], accounted[0]["before_bytes"])

    def test_postappend_without_readback_or_changed_modes_inventory_prefix_fails(self):
        before = bytes.fromhex(self.manifest["baseline_target_hex"])
        for variant in ("no-readback", "wrong-readback", "prefix", "spec", "mode", "extra", "native-overlap", "wrong-target"):
            (self.workspace / TARGET).write_bytes(before)
            items = self.appended()
            if variant == "no-readback":
                del items[4:6]
            elif variant == "wrong-readback":
                items[5]["params"]["item"]["aggregatedOutput"] = "partial"
            elif variant == "prefix":
                (self.workspace / TARGET).write_text("replacement")
            elif variant == "spec":
                (self.workspace / SPEC).write_text("changed")
            elif variant == "mode":
                (self.workspace / TARGET).chmod(0o755)
            elif variant == "extra":
                (self.workspace / "extra").write_text("extra")
            elif variant == "native-overlap":
                read = self.read()
                items[2:4] = [read[0], items[2], items[3], read[1]]
            else:
                for raw in items[2:4]:
                    raw["params"]["item"]["changes"] = [{"path": SPEC, "kind": {"type": "update"}, "diff": "wrong"}]
            result = self.normalize(items)
            self.assertNotIn("post", [fact["raw_item_id"] for fact in self.proofs(result)])
            (self.workspace / SPEC).write_text(self.spec)
            (self.workspace / TARGET).chmod(0o644)
            if (self.workspace / "extra").exists():
                (self.workspace / "extra").unlink()

    def test_downstream_discovery_attribution_does_not_imply_command_separation(self):
        text = self.pin(PRINCIPLES, b"# Pinned\n")
        for command, output in (("rg --files " + ROOT, self.listing()),
                                (self.body(), self.spec + self.template + self.listing())):
            result = self.normalize(self.conditional(id="pre")
                + self.conditional(PRINCIPLES, text, id="principles")
                + self.command(command, output, id="discovery"))
            self.assertEqual([], result["issues"])
            proof = self.proofs(result, "terminal_discovery_certificate")[0]["terminal_discovery_certificate"]
            self.assertFalse(proof["workflow_separation_implied"])
            self.assertTrue(proof["superseded_inherited_issues"])
        result = self.normalize(self.conditional()
                                + self.command("rg --files " + ROOT, "invented.md\n", id="discovery"))
        self.assertEqual([], self.proofs(result, "terminal_discovery_certificate"))
        self.assertTrue(result["issues"])

    def test_existing_read_concurrency_can_recover_after_new_conditional(self):
        text = self.pin(PRINCIPLES, b"# Pinned\n")
        left, right = self.read(SPEC), self.read(TARGET)
        result = self.normalize(self.conditional(PRINCIPLES, text)
                                + [left[0], right[0], left[1], right[1]])
        self.assertEqual([], result["issues"])
        proof = self.proofs(result, "read_only_attribution_certificate")[0]["read_only_attribution_certificate"]
        self.assertEqual(["read-" + TARGET], proof["overlapping_read_only_item_ids"])
        self.assertEqual("exact read overlaps an uncompleted operation", proof["superseded_inherited_issues"][0]["detail"])

    def test_exact_dependency_repair_retains_shadow_failure_and_requires_early_read(self):
        text = self.pin(PRINCIPLES, b"# Pinned\n")
        self.manifest["required_reads"] = [PRINCIPLES]
        items = self.conditional(PRINCIPLES, text) + self.write()
        items += self.command("cat " + PRINCIPLES, text, id="late-read")
        old, result = self.normalize(items, normalize_v9), self.normalize(items)
        self.assertTrue(any(issue.get("consumer_item_id") == "write" for issue in old["issues"]))
        write = next(fact for fact in result["events"] if fact["type"] == "write")
        proof = write["dependency_attribution_certificates"][0]
        self.assertEqual("codex-workflow-trace-v10", proof["instrumentation"])
        self.assertEqual(["conditional"], proof["read_item_ids"])
        self.assertEqual("write", proof["superseded_inherited_issues"][0]["consumer_item_id"])
        self.assertEqual("unknown", proof["superseded_inherited_facts"][0]["type"])
        self.assertEqual([], result["issues"])
        late = self.write() + self.conditional(PRINCIPLES, text)
        self.reject(late, "conditional_read_certificate")

    def test_new_proof_rejects_unsafe_outer_wrapper_in_preceding_read(self):
        # The outer double quotes would expand $FILE despite the apparent inner
        # single-quoted literal; no captured command is executed by this test.
        text = self.pin("$FILE", b"Pinned literal-dollar filename.\n")
        prior = self.command('/bin/zsh -c "cat \'$FILE\'"', text, id="prior")
        self.reject(prior + self.conditional())

    def test_mixed_guarded_postcheck_recovered_without_editing_existing_proofs(self):
        items = self.appended()
        for raw in items[-2:]:
            raw["params"]["item"]["command"] = fixtures.WorkflowTraceV9Tests.guarded()
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        self.assertEqual("literal-else-test-echo", self.proofs(result)[1]["absence_certificate"]["proof"])
        items = self.command(fixtures.WorkflowTraceV9Tests.guarded(), "ABSENT\n")
        old, result = self.normalize(items, normalize_v9), self.normalize(items)
        self.assertEqual(old["diagnostics"], result["diagnostics"])
        self.assertEqual([], self.proofs(result))

    def test_unrelated_fact_or_issue_cannot_be_erased(self):
        items = self.conditional()
        old = self.normalize(items, normalize_v9)
        for field, entry in (("issues", {"kind": "fidelity", "detail": "unrelated", "raw_item_id": "conditional",
                                          "raw_start_index": 0, "raw_completion_index": 1}),
                             ("events", {**old["events"][0], "reason": "unrelated"})):
            inherited = copy.deepcopy(old)
            inherited[field].append(entry)
            with patch("harnessmith.workflow_trace_v10.normalize_v9", return_value=inherited):
                result = self.normalize(items)
            self.assertEqual([], self.proofs(result))
            self.assertIn(entry, result[field])


if __name__ == "__main__":
    unittest.main()
