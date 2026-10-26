"""Fresh synthetic terminal discovery traces; captured text is never executed."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from harnessmith.workflow_trace_v6 import normalize_events as normalize_v6
from harnessmith.workflow_trace_v7 import normalize_events

ROOT = "specs/001-invitations"
SPEC = ROOT + "/spec.md"
TARGET = ROOT + "/checklists/security.md"
TEMPLATE = ".specify/templates/checklist-template.md"


def event(method, **params):
    return {"method": method, "params": {"threadId": "t", "turnId": "u", **params}}


class WorkflowTraceV7Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve() / "workspace"
        self.workspace.mkdir()
        self.manifest = {"model": "gpt-6-luna", "target": TARGET, "baseline": {}}
        self.spec = self.pin(SPEC, b"# Invitations\nExpiry is unspecified.\n")
        self.template = self.pin(TEMPLATE, b"# Checklist\nUse questions.\n")
        self.pin(TARGET, b"# Security\n- [x] CHK001 Existing.\n")
        self.manifest["baseline_target_hex"] = (self.workspace / TARGET).read_bytes().hex()

    def pin(self, path, data):
        destination = self.workspace / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        self.manifest["baseline"][path] = hashlib.sha256(data).hexdigest()
        self.inventory()
        return data.decode()

    def inventory(self):
        self.manifest["baseline_inventory_sha256"] = hashlib.sha256(json.dumps(
            self.manifest["baseline"], sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest()

    def body(self, separator="\n", root=ROOT):
        return separator.join(("cat " + SPEC, "cat " + TEMPLATE, "rg --files " + root))

    def listing(self, root=ROOT):
        return root.rstrip("/") + "/spec.md\n" + root.rstrip("/") + "/checklists/security.md\n"

    def command(self, command=None, output=None, **overrides):
        item = {"id": "discovery", "type": "commandExecution", "status": "completed",
                "command": command or self.body(), "cwd": str(self.workspace), "exitCode": 0,
                "aggregatedOutput": self.spec + self.template + self.listing() if output is None else output,
                "commandActions": [], **overrides}
        return [event("item/started", item={**item, "status": "inProgress"}),
                event("item/completed", item=item)]

    def normalize(self, items, normalizer=normalize_events, **kwargs):
        stream = items + [event("thread/tokenUsage/updated", tokenUsage={"total": {
            "inputTokens": 10, "cachedInputTokens": 0, "outputTokens": 1,
            "reasoningOutputTokens": 0, "totalTokens": 11}}),
            event("turn/completed", turn={"id": "u", "status": "completed"})]
        return normalizer(stream, thread_id="t", turn_id="u", workspace=self.workspace,
                          manifest=self.manifest, latency_ms=1, **kwargs)

    def certificates(self, result):
        return [fact for fact in result["diagnostics"] if fact.get("terminal_discovery_certificate")]

    def assertRejected(self, items, **kwargs):
        result = self.normalize(items, **kwargs)
        self.assertEqual([], self.certificates(result))
        self.assertTrue(result["issues"])
        return result

    def test_exact_newline_terminal_retires_only_artificial_failure(self):
        items = self.command()
        raw_before, manifest_before = copy.deepcopy(items), copy.deepcopy(self.manifest)
        old = self.normalize(items, normalize_v6)
        self.assertEqual(["individual statement success unproven", "failed or incomplete operation"],
                         [issue["detail"] for issue in old["issues"]])
        result = self.normalize(items)
        self.assertEqual([], result["issues"])
        self.assertEqual(7, result["schema_version"])
        self.assertEqual("codex-workflow-trace-v7", result["instrumentation"])
        self.assertEqual("codex-workflow-trace-v6", result["base_normalizer"])
        self.assertEqual([SPEC, TEMPLATE], [fact["path"] for fact in result["events"]])
        self.assertEqual(old["events"][:2], result["events"])
        diagnostic = self.certificates(result)[0]
        self.assertEqual((0, 1, 2), (diagnostic["raw_start_index"], diagnostic["raw_completion_index"],
                                     diagnostic["raw_operation_index"]))
        proof = diagnostic["terminal_discovery_certificate"]
        self.assertEqual("literal-terminal-rg", proof["proof"])
        self.assertEqual([SPEC, TEMPLATE], proof["prefix_reads"])
        self.assertEqual(self.manifest["baseline_inventory_sha256"], proof["baseline_inventory_sha256"])
        self.assertEqual(hashlib.sha256(items[1]["params"]["item"]["aggregatedOutput"].encode()).hexdigest(),
                         proof["captured_output_sha256"])
        self.assertTrue(proof["complete_command_coverage"])
        self.assertTrue(proof["terminal_exit_attributable"])
        self.assertFalse(proof["stderr_stripped"])
        self.assertFalse(proof["workflow_separation_implied"])
        self.assertEqual(old["issues"], proof["superseded_inherited_issues"])
        self.assertEqual("unknown", proof["inherited_attribution"]["type"])
        self.assertFalse(diagnostic["certifies_file_contents"])
        self.assertFalse(diagnostic["certifies_absence"])
        self.assertEqual(raw_before, items)
        self.assertEqual(manifest_before, self.manifest)
        self.assertEqual(old, self.normalize(items, normalize_v6))
        self.assertEqual(old["command_records"], result["command_records"])

    def test_semicolon_and_and_chains_have_same_exact_proof(self):
        for separator in ("; ", " && ", "\n", ";\n"):
            with self.subTest(separator=separator):
                result = self.normalize(self.command(self.body(separator)))
                self.assertEqual([], result["issues"])
                self.assertEqual(1, len(self.certificates(result)))

    def test_standalone_is_certified_without_read_prefix(self):
        result = self.normalize(self.command("rg --files " + ROOT, self.listing()))
        self.assertEqual([], result["events"])
        self.assertEqual([], result["issues"])
        self.assertEqual([], self.certificates(result)[0]["terminal_discovery_certificate"]["prefix_reads"])

    def test_returned_path_order_is_not_assumed(self):
        reverse = TARGET + "\n" + SPEC + "\n"
        result = self.normalize(self.command(output=self.spec + self.template + reverse))
        self.assertEqual([], result["issues"])
        self.assertEqual(sorted([SPEC, TARGET]), self.certificates(result)[0]["terminal_discovery_certificate"]["discovered_paths"])

    def test_quoted_absolute_recorded_paths_and_nonlogin_shell_are_supported(self):
        absolute = str(self.workspace / ROOT)
        result = self.normalize(self.command(self.body(root=shlex.quote(absolute)),
                                            self.spec + self.template + self.listing(absolute)))
        self.assertEqual(1, len(self.certificates(result)))
        command = "/bin/zsh -c " + shlex.quote(self.body(root='"' + ROOT + '"'))
        self.assertEqual(1, len(self.certificates(self.normalize(self.command(command)))))
        recorded = Path("/recorded/isolated/workspace")
        root = str(recorded / ROOT)
        result = self.normalize(self.command(self.body(root=shlex.quote(root)),
                                            self.spec + self.template + self.listing(root), cwd=str(recorded)),
                                recorded_workspace=recorded)
        self.assertEqual(1, len(self.certificates(result)))
        self.assertIn(root, result["command_records"][0]["raw_command"])

    def test_scoped_relative_cwd_is_supported(self):
        result = self.normalize(self.command("rg --files 001-invitations", self.listing("001-invitations"),
                                            cwd=str(self.workspace / "specs")))
        self.assertEqual(1, len(self.certificates(result)))

    def test_exact_pinned_target_prefix_remains_valid_before_later_write(self):
        before = (self.workspace / TARGET).read_text()
        write = {"id": "edit", "type": "fileChange", "status": "completed", "changes": [
            {"path": TARGET, "kind": {"type": "update"}, "diff": "synthetic append"}]}
        items = self.command("cat " + TARGET + "\nrg --files " + ROOT, before + self.listing())
        items += [event("item/started", item={**write, "status": "inProgress"}), event("item/completed", item=write)]
        (self.workspace / TARGET).write_text(before + "- [ ] CHK002 New.\n")
        result = self.normalize(items)
        self.assertEqual(1, len(self.certificates(result)))
        self.assertEqual("write", result["events"][-1]["type"])

    def test_hidden_pinned_members_are_not_added_to_visible_listing(self):
        self.pin(ROOT + "/.review", b"Hidden review\n")
        self.pin(ROOT + "/.hidden/note", b"Hidden directory\n")
        self.assertEqual(1, len(self.certificates(self.normalize(self.command()))))

    def test_missing_wrong_partial_duplicate_and_extra_path_output_rejected(self):
        for listing in ("", SPEC + "\n", TARGET + "\n", self.listing() + SPEC + "\n",
                        "specs/other/spec.md\n" + TARGET + "\n", self.listing() + "/tmp/outside\n",
                        self.listing().rstrip("\n"), self.listing().replace("\n", "\r\n")):
            with self.subTest(listing=listing):
                self.assertRejected(self.command(output=self.spec + self.template + listing))

    def test_bad_standalone_output_is_new_failing_event_not_inherited_success(self):
        items = self.command("rg --files " + ROOT, "invented.md\n")
        old = self.normalize(items, normalize_v6)
        self.assertEqual([], old["issues"])
        result = self.assertRejected(items)
        self.assertIn("terminal discovery proof rejected", result["events"][0]["reason"])
        self.assertEqual(old["command_records"], result["command_records"])

    def test_and_chain_hardening_retains_existing_read_facts(self):
        items = self.command(self.body(" && "), self.spec + self.template + "invented.md\n")
        old = self.normalize(items, normalize_v6)
        result = self.assertRejected(items)
        self.assertEqual(old["events"], result["events"][:2])

    def test_read_output_prefix_must_be_exact_and_ordered(self):
        for output in ("extra\n" + self.spec + self.template + self.listing(),
                       self.template + self.spec + self.listing(), self.spec + self.listing(),
                       self.spec + "noise\n" + self.template + self.listing()):
            with self.subTest(output=output):
                self.assertRejected(self.command(output=output))

    def test_pinned_content_hash_and_nonempty_reads_are_required(self):
        (self.workspace / SPEC).write_text("changed\n")
        self.assertRejected(self.command())
        self.pin(SPEC, b"")
        self.assertRejected(self.command(output=self.template + self.listing()))

    def test_inventory_hash_and_file_membership_are_required(self):
        original = copy.deepcopy(self.manifest)
        for update in ({"baseline_inventory_sha256": "wrong"}, {"baseline": {}},
                       {"baseline": {SPEC: self.manifest["baseline"][SPEC]}}):
            with self.subTest(update=update):
                self.manifest = {**original, **update}
                if "baseline" in update:
                    self.inventory()
                self.assertRejected(self.command())
        self.manifest = original
        del self.manifest["baseline_inventory_sha256"]
        self.assertRejected(self.command())

    def test_invalid_inventory_hash_values_cannot_pin_discovery_membership(self):
        for value in ("not-a-hash", 42, None):
            with self.subTest(value=value):
                self.manifest["baseline"][TARGET] = value
                self.inventory()
                self.assertRejected(self.command())

    def test_unpinned_added_or_deleted_files_reject_discovery(self):
        extra = self.workspace / ROOT / "extra.md"
        extra.write_text("extra\n")
        self.assertRejected(self.command())
        extra.unlink()
        (self.workspace / TARGET).unlink()
        self.assertRejected(self.command())

    def test_missing_file_hidden_and_unscoped_roots_reject(self):
        for root in ("specs/missing", SPEC, ".", ".specify", "specs/../specs/001-invitations"):
            with self.subTest(root=root):
                self.assertRejected(self.command(self.body(root=root)))

    def test_symlink_root_descendant_and_prefix_paths_reject(self):
        link = self.workspace / "linked"
        link.symlink_to(self.workspace / ROOT, target_is_directory=True)
        self.assertRejected(self.command(self.body(root="linked")))
        link.unlink()
        link = self.workspace / ROOT / "link"
        link.symlink_to("missing")
        self.assertRejected(self.command())
        link.unlink()
        target = self.workspace / SPEC
        target.unlink()
        target.symlink_to(self.workspace / TEMPLATE)
        self.assertRejected(self.command())

    def test_outside_root_cwd_and_read_paths_reject(self):
        self.assertRejected(self.command(self.body(root="/tmp/outside")))
        self.assertRejected(self.command(cwd="/tmp"))
        self.assertRejected(self.command("cat /tmp/input\nrg --files " + ROOT))

    def test_dynamic_paths_and_output_producers_never_gain_certificate(self):
        for command in ("cat " + SPEC + "\nprintf '%s' " + shlex.quote(self.template) + "\nrg --files " + ROOT,
                        "printf " + shlex.quote(self.spec + self.template) + "\nrg --files " + ROOT,
                        "cat \"$SPEC\"\nrg --files " + ROOT,
                        "cat " + SPEC + "\nrg --files $(pwd)",
                        "touch hidden\nrg --files " + ROOT):
            with self.subTest(command=command):
                result = self.normalize(self.command(command))
                self.assertEqual([], self.certificates(result))

    def test_redirection_pipeline_fallback_and_masked_failure_are_not_repaired(self):
        for command in (self.body() + " | sort", self.body() + " 2>/dev/null",
                        self.body() + " || true", self.body() + "; true",
                        "false; " + self.body(), self.body() + " &",
                        "cat " + SPEC + "; rm hidden; rg --files " + ROOT):
            with self.subTest(command=command):
                self.assertRejected(self.command(command))

    def test_nonzero_status_failure_output_and_noninteger_exit_reject(self):
        for overrides in ({"exitCode": 1}, {"exitCode": 2}, {"exitCode": False},
                          {"exitCode": "0"}, {"status": "failed"}):
            with self.subTest(overrides=overrides):
                self.assertRejected(self.command(**overrides))
        for error in ("Permission denied\n", "SyntaxError: invalid\n", "rg: missing: No such file or directory\n"):
            self.assertRejected(self.command(output=self.spec + self.template + self.listing() + error))

    def test_absence_conditional_compound_failure_remains_unchanged(self):
        body = ("if [ -f .specify/extensions.yml ]; then cat .specify/extensions.yml; "
                "else printf 'ABSENT\\n'; fi\nrg --files --hidden .specify .pilot 2>/dev/null")
        items = self.command(body, "ABSENT\n.specify/templates/checklist-template.md\n", exitCode=2)
        old = self.normalize(items, normalize_v6)
        result = self.normalize(items)
        self.assertEqual(old["events"], result["events"])
        self.assertEqual(old["issues"], result["issues"])
        self.assertEqual([], self.certificates(result))

    def test_bad_source_actions_and_wrappers_reject(self):
        for overrides in ({"source": "untrusted"}, {"commandActions": None},
                          {"commandActions": [{"type": "read", "path": TARGET}]}):
            with self.subTest(overrides=overrides):
                self.assertRejected(self.command(**overrides))
        for command in ("/bin/zsh -lc " + shlex.quote(self.body()),
                        "/bin/zsh -ic " + shlex.quote(self.body()),
                        "/bin/sh -c " + shlex.quote(self.body()) + " extra"):
            result = self.normalize(self.command(command))
            self.assertEqual([], self.certificates(result))

    def test_unsupported_discovery_flags_and_roots_do_not_gain_new_proof(self):
        for command in ("rg --files --hidden " + ROOT, "rg --files " + ROOT + " .specify",
                        "rg --files -g '*.md' " + ROOT, "rg --files", "/usr/bin/rg --files " + ROOT):
            with self.subTest(command=command):
                items = self.command(command, self.listing())
                old = self.normalize(items, normalize_v6)
                result = self.normalize(items)
                self.assertEqual([], self.certificates(result))
                self.assertEqual(old["events"], result["events"])
                self.assertEqual(old["diagnostics"], result["diagnostics"])
                self.assertEqual(old["issues"], result["issues"])

    def test_incomplete_duplicate_reversed_and_mismatched_lifecycles_reject(self):
        original = self.command()
        for items in ([original[0]], [original[1]], original[::-1],
                      [original[0], original[0], original[1]], original + [original[1]]):
            with self.subTest(items=items):
                self.assertRejected(items)
        for field, value in (("command", "rg --files " + ROOT), ("cwd", "/tmp"),
                             ("type", "fileChange"), ("source", "untrusted"), ("status", "completed")):
            items = copy.deepcopy(original)
            items[0]["params"]["item"][field] = value
            with self.subTest(field=field):
                self.assertRejected(items)

    def test_unknown_mutating_overlapping_and_cross_scope_prefixes_reject(self):
        for prefix in (self.command("touch hidden", "", id="prior"),
                       self.command("false", "", id="prior", exitCode=1)):
            self.assertRejected(prefix + self.command())
        write = {"id": "edit", "type": "fileChange", "status": "completed", "changes": [
            {"path": TARGET, "kind": {"type": "update"}, "diff": "synthetic"}]}
        self.assertRejected([event("item/started", item={**write, "status": "inProgress"}),
                             event("item/completed", item=write)] + self.command())
        prior = self.command("cat " + SPEC, self.spec, id="prior")
        self.assertRejected(prior[:1] + self.command() + prior[1:])
        self.assertRejected(prior[:1] + self.command())
        prior[0]["params"]["threadId"] = "other"
        self.assertRejected(prior + self.command())

    def test_safe_read_only_prefix_is_allowed(self):
        prior = self.command("cat " + SPEC, self.spec, id="prior")
        result = self.normalize(prior + self.command())
        self.assertEqual([], result["issues"])
        self.assertEqual(1, len(self.certificates(result)))

    def test_unrelated_later_failure_issues_and_raw_records_are_retained(self):
        later = self.command("false", "", id="later", exitCode=1)
        items = self.command() + later
        old = self.normalize(items, normalize_v6)
        result = self.normalize(items)
        self.assertEqual(1, len(self.certificates(result)))
        self.assertEqual([issue for issue in old["issues"] if issue.get("raw_item_id") == "later"],
                         result["issues"])
        self.assertEqual(old["command_records"], result["command_records"])
        self.assertEqual([fact for fact in old["events"] if fact.get("raw_item_id") == "later"],
                         [fact for fact in result["events"] if fact.get("raw_item_id") == "later"])

    def test_same_item_declared_mismatch_issue_is_never_cleared(self):
        items = self.command(commandActions=[{"type": "read", "path": TARGET}])
        old = self.normalize(items, normalize_v6)
        result = self.assertRejected(items)
        self.assertEqual(old["events"], result["events"])
        self.assertEqual(old["issues"], result["issues"])


if __name__ == "__main__":
    unittest.main()
