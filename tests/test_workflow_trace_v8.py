"""Fresh synthetic proofs only; no historical trace is read or regraded."""

from __future__ import annotations

import copy
from pathlib import Path
import shlex
import unittest

from harnessmith.workflow_trace_v7 import normalize_events as normalize_v7
from harnessmith.workflow_trace_v8 import normalize_events
from tests import test_workflow_trace_v7 as fixtures
from tests.test_workflow_trace_v7 import ROOT, SPEC, TARGET, TEMPLATE, event

CONFIG = ".specify/extensions.yml"
PRINCIPLES = ".specify/memory/constitution.md"


class WorkflowTraceV8Tests(unittest.TestCase):
    # Reuse fixture construction, not old test methods or historical data.
    setUp = fixtures.WorkflowTraceV7Tests.setUp
    pin = fixtures.WorkflowTraceV7Tests.pin
    inventory = fixtures.WorkflowTraceV7Tests.inventory
    command = fixtures.WorkflowTraceV7Tests.command
    body = fixtures.WorkflowTraceV7Tests.body
    listing = fixtures.WorkflowTraceV7Tests.listing

    def normalize(self, items, normalizer=normalize_events, **kwargs):
        return fixtures.WorkflowTraceV7Tests.normalize(
            self, items, normalizer, **kwargs
        )

    def conditional(self, path=CONFIG, output="", **kwargs):
        self.manifest["pinned_absent_paths"] = [CONFIG]
        body = f"if [ -f {shlex.quote(path)} ]; then cat {shlex.quote(path)}; else test ! -e {shlex.quote(path)}; fi"
        return self.command(body, output, **{"id": "conditional", **kwargs})

    def read(self, path=SPEC, **kwargs):
        return self.command(
            "cat " + path,
            (self.workspace / path).read_text(),
            id="read-" + path,
            **kwargs,
        )

    def paired(self):
        left, right = self.read(SPEC), self.read(TARGET)
        return [left[0], right[0], left[1], right[1]]

    def proofs(self, result, field="absence_certificate"):
        return [
            fact
            for fact in result["events"] + result["diagnostics"]
            if field in fact
            and fact[field].get("instrumentation") == "codex-workflow-trace-v8"
        ]

    def write(self):
        item = {
            "id": "write",
            "type": "fileChange",
            "status": "completed",
            "changes": [
                {"path": TARGET, "kind": {"type": "update"}, "diff": "synthetic"}
            ],
        }
        return [
            event("item/started", item={**item, "status": "inProgress"}),
            event("item/completed", item=item),
        ]

    def test_absence_empty_and_explicit_null_stdout_have_distinct_evidence(self):
        for form in ("empty", "null"):
            with self.subTest(form=form):
                items = self.conditional()
                if form == "null":
                    items[1]["params"]["item"]["aggregatedOutput"] = None
                result = self.normalize(items)
                self.assertEqual([], result["issues"])
                fact = self.proofs(result)[0]
                self.assertTrue(fact["certified_absence"])
                self.assertEqual(CONFIG, fact["path"])
                self.assertEqual(
                    "text" if form == "empty" else form,
                    fact["absence_certificate"]["output_representation"],
                )

    def test_missing_output_field_is_not_evidence_of_empty_capture(self):
        items = self.conditional()
        del items[1]["params"]["item"]["aggregatedOutput"]
        result = self.normalize(items)
        self.assertEqual([], self.proofs(result))
        self.assertTrue(result["issues"])

    def test_present_conditional_proves_all_pinned_bytes(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPreserve intent.\n")
        result = self.normalize(self.conditional(PRINCIPLES, text))
        fact = self.proofs(result, "conditional_read_certificate")[0]
        self.assertEqual([], result["issues"])
        self.assertTrue(fact["read_before_write"])
        self.assertEqual(self.manifest["baseline"][PRINCIPLES], fact["read_sha256"])
        self.assertTrue(fact["read_coverage"]["complete"])

    def test_empty_present_file_and_alias_spelling_remain_outside_grammar(self):
        self.pin(PRINCIPLES, b"")
        result = self.normalize(self.conditional(PRINCIPLES, ""))
        self.assertEqual([], self.proofs(result, "conditional_read_certificate"))
        items = self.conditional()
        for raw in items:
            raw["params"]["item"]["command"] = raw["params"]["item"]["command"].replace(
                "cat " + CONFIG, "cat ./" + CONFIG
            )
        self.assertEqual([], self.proofs(self.normalize(items)))

    def test_proof_retains_exact_inherited_failures_without_mutating_inputs(self):
        items = self.conditional()
        old = self.normalize(items, normalize_v7)
        before = copy.deepcopy((items, self.manifest))
        result = self.normalize(items)
        proof = self.proofs(result)[0]["absence_certificate"]
        self.assertEqual(old["issues"], proof["superseded_inherited_issues"])
        self.assertEqual(old["events"], proof["superseded_inherited_facts"])
        self.assertEqual(old["command_records"], result["command_records"])
        self.assertEqual(before, (items, self.manifest))
        self.assertEqual(old, self.normalize(items, normalize_v7))
        self.assertEqual(
            (8, "codex-workflow-trace-v8", "codex-workflow-trace-v7"),
            tuple(
                result[k]
                for k in ("schema_version", "instrumentation", "base_normalizer")
            ),
        )

    def test_conditional_rejects_different_paths_or_unsafe_skipped_branch(self):
        base = f"if [ -f {CONFIG} ]; then cat {CONFIG}; else test ! -e {CONFIG}; fi"
        bodies = [
            base.replace("cat " + CONFIG, "cat " + SPEC),
            base.replace("test ! -e " + CONFIG, "test ! -e " + SPEC),
            base.replace("test ! -e", "test ! -f"),
            base.replace("cat " + CONFIG, "touch marker"),
            base.replace("cat " + CONFIG, "cat " + CONFIG + "; touch marker"),
            base + "; true",
            base + " 2>/dev/null",
            base + " || true",
            base.replace(CONFIG, '"$(pwd)/x"'),
            base.replace(CONFIG, '"$FILE"'),
            base.replace("test ! -e", "/usr/bin/test ! -e"),
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.manifest["pinned_absent_paths"] = [CONFIG]
                self.assertEqual(
                    [], self.proofs(self.normalize(self.command(body, "")))
                )

    def test_present_and_absent_mismatched_outputs_fail(self):
        for output in ("absent\n", "Permission denied\n", 0, False, [], {}):
            items = self.conditional()
            items[1]["params"]["item"]["aggregatedOutput"] = output
            self.assertEqual([], self.proofs(self.normalize(items)))
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        for output in (text[:-1], text + "noise", "", None):
            items = self.conditional(PRINCIPLES, text)
            items[1]["params"]["item"]["aggregatedOutput"] = output
            self.assertEqual(
                [], self.proofs(self.normalize(items), "conditional_read_certificate")
            )

    def test_failures_lifecycle_mismatch_and_wrong_scope_cannot_be_repaired(self):
        for field, value in (
            ("exitCode", 1),
            ("exitCode", False),
            ("status", "failed"),
            ("source", "untrusted"),
        ):
            items = self.conditional()
            items[1]["params"]["item"][field] = value
            result = self.normalize(items)
            self.assertEqual([], self.proofs(result))
            self.assertTrue(result["issues"])
        for field, value in (
            ("command", "true"),
            ("cwd", "/tmp"),
            ("source", "unifiedExecStartup"),
            ("status", "completed"),
        ):
            items = self.conditional()
            items[0]["params"]["item"][field] = value
            self.assertEqual([], self.proofs(self.normalize(items)))
        for variant in ("missing", "duplicate", "reversed", "scope"):
            items = self.conditional()
            if variant == "missing":
                items.pop()
            elif variant == "duplicate":
                items.insert(0, copy.deepcopy(items[0]))
            elif variant == "reversed":
                items.reverse()
            else:
                items[0]["params"]["threadId"] = "other"
            self.assertEqual([], self.proofs(self.normalize(items)))

    def test_inventory_and_actual_absence_are_required(self):
        for mutation in ("hash", "missing", "present", "directory", "symlink"):
            with self.subTest(mutation=mutation):
                items = self.conditional()
                original = copy.deepcopy(self.manifest)
                path = self.workspace / CONFIG
                if mutation == "hash":
                    self.manifest["baseline_inventory_sha256"] = "0" * 64
                elif mutation == "missing":
                    self.manifest["pinned_absent_paths"] = []
                elif mutation == "present":
                    path.write_text("changed")
                elif mutation == "directory":
                    path.mkdir()
                else:
                    path.symlink_to("nonexistent")
                self.assertEqual([], self.proofs(self.normalize(items)))
                if path.is_dir():
                    path.rmdir()
                elif path.exists() or path.is_symlink():
                    path.unlink()
                self.manifest = original

    def test_non_extension_absence_cannot_be_certified(self):
        items = self.conditional("absent.md")
        self.manifest["pinned_absent_paths"].append("absent.md")
        self.assertEqual([], self.proofs(self.normalize(items)))

    def test_symlink_present_path_and_conditional_parent_are_rejected(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        path = self.workspace / PRINCIPLES
        path.unlink()
        path.symlink_to(self.workspace / SPEC)
        self.assertEqual(
            [],
            self.proofs(
                self.normalize(self.conditional(PRINCIPLES, text)),
                "conditional_read_certificate",
            ),
        )
        parent = self.workspace / ".specify"
        moved = self.workspace / "real-specify"
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
        self.assertEqual([], self.proofs(self.normalize(self.conditional())))

    def test_scope_guard_preserves_known_read_and_rejects_only_relevant_foreign_operations(
        self,
    ):
        read, foreign = self.read(), self.command("touch unknown", "", id="foreign")
        for raw in foreign:
            raw["params"]["threadId"] = "other"
        result = self.normalize([read[0], *foreign, read[1]])
        guards = [fact for fact in result["events"] if fact.get("scope_guard_evidence")]
        self.assertEqual(1, len(guards))
        self.assertEqual(
            "read", guards[0]["scope_guard_evidence"]["inherited_facts"][0]["type"]
        )
        self.assertTrue(any(fact["type"] == "read" for fact in result["events"]))
        result = self.normalize(read + foreign)
        self.assertEqual([], result["issues"])
        passive = event(
            "item/completed",
            item={"id": "message", "type": "agentMessage", "text": "unrelated"},
        )
        passive["params"]["threadId"] = "other"
        self.assertEqual([], self.normalize([read[0], passive, read[1]])["issues"])

    def test_nonlogin_shell_quoted_absolute_paths_and_recorded_root(self):
        path = str(self.workspace / CONFIG)
        items = self.conditional(path)
        for item in items:
            item["params"]["item"]["command"] = "/bin/zsh -c " + shlex.quote(
                item["params"]["item"]["command"]
            )
        self.assertEqual(1, len(self.proofs(self.normalize(items))))
        for item in items:
            item["params"]["item"]["command"] = item["params"]["item"][
                "command"
            ].replace(" -c ", " -lc ")
        self.assertEqual([], self.proofs(self.normalize(items)))
        recorded = Path("/captured/isolated")
        items = self.conditional(str(recorded / CONFIG), cwd=str(recorded))
        self.assertEqual(
            1, len(self.proofs(self.normalize(items, recorded_workspace=recorded)))
        )

    def test_independent_overlap_retires_only_rejected_read(self):
        items = self.paired()
        old = self.normalize(items, normalize_v7)
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        proof = self.proofs(result, "read_only_attribution_certificate")[0][
            "read_only_attribution_certificate"
        ]
        self.assertEqual(["read-" + TARGET], proof["overlapping_read_only_item_ids"])
        self.assertEqual(old["issues"], proof["superseded_inherited_issues"])
        self.assertEqual({SPEC, TARGET}, {fact["path"] for fact in result["events"]})

    def test_reversed_completion_order_and_three_read_chain(self):
        pairs = [self.read(path) for path in (SPEC, TARGET, TEMPLATE)]
        for items in (
            [pairs[0][0], pairs[1][0], pairs[1][1], pairs[0][1]],
            [
                pairs[0][0],
                pairs[1][0],
                pairs[0][1],
                pairs[2][0],
                pairs[1][1],
                pairs[2][1],
            ],
        ):
            result = self.normalize(items)
            self.assertEqual([], result["issues"])
            self.assertTrue(self.proofs(result, "read_only_attribution_certificate"))

    def test_conditional_and_python_reads_can_be_independent_peers(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        conditional = self.conditional(PRINCIPLES, text)
        script = (
            "from pathlib import Path; p=Path("
            + repr(SPEC)
            + "); b=p.read_bytes(); print(repr(b)); print(b.decode())"
        )
        data = (self.workspace / SPEC).read_bytes()
        python = self.command(
            "python3 -c " + shlex.quote(script),
            repr(data) + "\n" + data.decode() + "\n",
            id="python",
        )
        result = self.normalize([python[0], conditional[0], python[1], conditional[1]])
        self.assertEqual([], result["issues"])
        self.assertEqual(
            1, len(self.proofs(result, "read_only_attribution_certificate"))
        )
        self.assertEqual(1, len(self.proofs(result, "conditional_read_certificate")))

    def test_unknown_failed_unfinished_or_mutating_peer_rejects_overlap(self):
        for mode in (
            "unknown",
            "failed",
            "unfinished",
            "mutating",
            "wrongscope",
            "truncated",
            "declared",
        ):
            left = self.read()
            right = self.read(TARGET)
            if mode == "unknown":
                right = self.command("touch marker", "", id="peer")
            elif mode == "failed":
                right[1]["params"]["item"].update(status="failed", exitCode=1)
            elif mode == "mutating":
                right = self.write()
            elif mode == "wrongscope":
                for event_ in right:
                    event_["params"]["threadId"] = "other"
            elif mode == "truncated":
                right[1]["params"]["item"]["aggregatedOutput"] = "partial"
            elif mode == "declared":
                right[1]["params"]["item"]["commandActions"] = [
                    {"type": "read", "path": TEMPLATE}
                ]
            items = [left[0], right[0], left[1]] + (
                [] if mode == "unfinished" else [right[1]]
            )
            with self.subTest(mode=mode):
                result = self.normalize(items)
                self.assertEqual(
                    [], self.proofs(result, "read_only_attribution_certificate")
                )
                self.assertTrue(result["issues"])

    def test_transitive_overlap_sees_later_mutation_before_long_peer_completes(self):
        left, right, third, write = (
            self.read(SPEC),
            self.read(TARGET),
            self.read(TEMPLATE),
            self.write(),
        )
        items = [
            left[0],
            right[0],
            left[1],
            third[0],
            right[1],
            write[0],
            write[1],
            third[1],
        ]
        result = self.normalize(items)
        self.assertEqual([], self.proofs(result, "read_only_attribution_certificate"))
        self.assertTrue(result["issues"])

    def test_conditional_then_discovery_recovers_transitively(self):
        result = self.normalize(
            self.conditional() + self.command("rg --files " + ROOT, self.listing())
        )
        self.assertEqual([], result["issues"])
        self.assertEqual(1, len(self.proofs(result)))
        proof = self.proofs(result, "terminal_discovery_certificate")[0][
            "terminal_discovery_certificate"
        ]
        self.assertEqual("literal-terminal-rg", proof["proof"])
        self.assertIn(
            "terminal discovery proof rejected:",
            proof["superseded_inherited_issues"][0]["detail"],
        )

    def test_discovery_cannot_overlap_even_proven_reads(self):
        read, discovery = (
            self.read(),
            self.command("rg --files " + ROOT, self.listing()),
        )
        result = self.normalize([read[0], discovery[0], discovery[1], read[1]])
        self.assertEqual([], self.proofs(result, "terminal_discovery_certificate"))
        self.assertTrue(result["issues"])

    def test_actual_failure_before_new_proof_is_never_cleared(self):
        failed = self.command("false", "", id="failed", exitCode=1, status="failed")
        items = (
            failed
            + self.conditional()
            + self.command("rg --files " + ROOT, self.listing())
        )
        old, result = self.normalize(items, normalize_v7), self.normalize(items)
        self.assertEqual(old["issues"], result["issues"])
        self.assertEqual([], self.proofs(result))
        self.assertEqual([], self.proofs(result, "terminal_discovery_certificate"))

    def test_absence_diagnostic_cannot_overlap_a_read_in_either_completion_order(self):
        read, absence = self.read(), self.conditional()
        for items in (
            [read[0], absence[0], read[1], absence[1]],
            [absence[0], read[0], absence[1], read[1]],
        ):
            result = self.normalize(items)
            self.assertEqual([], self.proofs(result))
            self.assertEqual(
                [], self.proofs(result, "read_only_attribution_certificate")
            )
            self.assertTrue(result["issues"])

    def test_scope_guard_is_not_hidden_by_an_earlier_known_write(self):
        foreign = self.command("touch unknown", "", id="foreign")
        for raw in foreign:
            raw["params"]["threadId"] = "other"
        items = self.write() + foreign + self.read(SPEC)
        result = self.normalize(items)
        self.assertTrue(
            any(fact.get("scope_guard_evidence") for fact in result["events"])
        )
        self.assertTrue(result["issues"])

    def test_read_dependency_repair_requires_completion_before_write_start(self):
        self.manifest["required_reads"] = [TARGET]
        data = (self.workspace / TARGET).read_text()
        self.manifest["baseline_target_hex"] = data.encode().hex()
        before, peer, write = self.read(TARGET), self.read(SPEC), self.write()
        final = self.command("cat " + TARGET, data, id="final")
        items = [before[0], peer[0], before[1], peer[1], *write, *final]
        old, result = self.normalize(items, normalize_v7), self.normalize(items)
        self.assertTrue(
            any(
                issue["detail"]
                == "required read did not complete before consuming action started"
                for issue in old["issues"]
            )
        )
        self.assertEqual([], result["issues"])
        fact = next(fact for fact in result["events"] if fact["type"] == "write")
        self.assertEqual(TARGET, fact["dependency_attribution_certificates"][0]["path"])
        late = [before[0], peer[0], before[1], write[0], peer[1], write[1], *final]
        result = self.normalize(late)
        self.assertTrue(result["issues"])
        self.assertFalse(
            any(
                fact.get("dependency_attribution_certificates")
                for fact in result["events"]
            )
        )

    def test_full_fresh_transitive_flow_preserves_final_read_and_raw_records(self):
        text = self.pin(PRINCIPLES, b"# Principles\nPinned.\n")
        self.manifest["required_reads"] = [TARGET, SPEC, PRINCIPLES]
        original = (self.workspace / TARGET).read_text()
        items = (
            self.conditional()
            + self.conditional(PRINCIPLES, text, id="principles")
            + self.command("rg --files " + ROOT, self.listing())
            + self.paired()
            + self.write()
            + self.command("cat " + TARGET, original, id="final")
        )
        old, result = self.normalize(items, normalize_v7), self.normalize(items)
        self.assertEqual([], result["issues"])
        self.assertEqual(old["command_records"], result["command_records"])
        self.assertTrue(any(fact.get("read_after_write") for fact in result["events"]))


if __name__ == "__main__":
    unittest.main()
