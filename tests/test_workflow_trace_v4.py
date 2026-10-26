"""Synthetic-only schema-4 parser regressions; no historical trace regrading."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from harnessmith.workflow_fidelity import PACKAGE, SETUP, SETUP_COMMAND
from harnessmith.workflow_trace_v3 import normalize_events as normalize_v3
from harnessmith.workflow_trace_v4 import normalize_events


TARGET = "specs/001-invitations/checklists/security.md"
REFERENCE = PACKAGE + "/references/generation.md"
CONFIG = ".specify/extensions.yml"
CONSTITUTION = ".specify/memory/constitution.md"
TEMPLATE = ".specify/templates/checklist-template.md"
CACHE = (
    "python3: warning: confstr() failed with code 5: couldn't get path of "
    "DARWIN_USER_TEMP_DIR; using /tmp instead\n"
    "python3: error: couldn't create cache file '/tmp/xcrun_db-AbC123' "
    "(errno=Operation not permitted)\n"
)


def event(method, **params):
    return {"method": method, "params": {"threadId": "t", "turnId": "u", **params}}


class WorkflowTraceV4Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name).resolve() / "workspace"
        self.workspace.mkdir()
        self.manifest = {
            "model": "gpt-6-luna",
            "target": TARGET,
            "baseline": {},
            "required_reads": [CONSTITUTION],
        }
        self.before = (
            b"# Review\n- [x] CHK001 First\n- [X] CHK002 Second\n<!-- reviewer -->\n"
        )
        self.addition = b"- [ ] CHK003 Are expiry requirements stated? [Gap]\n"
        self.pin(TARGET, self.before)
        self.manifest["baseline_target_hex"] = self.before.hex()
        self.reference = self.pin(REFERENCE, b"# Generation\nQuestion requirements.\n")
        self.config = self.pin(CONFIG, b"hooks:\n  pre: pilot-pre-marker\n")
        self.pin(CONSTITUTION, b"# Principles\nReview requirements.\n")
        self.pin(TEMPLATE, b"# Checklist\n")
        self.pin(SETUP, b"#!/bin/sh\n# synthetic shell adapter\n")

    def pin(self, path, payload):
        destination = self.workspace / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        self.manifest["baseline"][path] = hashlib.sha256(payload).hexdigest()
        return payload.decode("utf-8")

    def script(self, path=TARGET):
        return (
            f"from pathlib import Path; p=Path({path!r}); old=p.read_bytes(); "
            f"add={self.addition!r}; p.open('ab').write(add); "
            "new=p.read_bytes(); assert new == old + add; print(new.decode())"
        )

    def command(self, command, output="", **overrides):
        item = {
            "id": "command",
            "type": "commandExecution",
            "status": "completed",
            "command": command,
            "cwd": str(self.workspace),
            "exitCode": 0,
            "aggregatedOutput": output,
            "commandActions": [],
            **overrides,
        }
        return [
            event("item/started", item={**item, "status": "inProgress"}),
            event("item/completed", item=item),
        ]

    def append(self, script=None, output=None, **overrides):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        return self.command(
            "python3 -c " + shlex.quote(script or self.script()),
            after.decode() + "\n" if output is None else output,
            **overrides,
        )

    def normalize(self, events, **kwargs):
        tail = [
            event(
                "thread/tokenUsage/updated",
                tokenUsage={
                    "total": {
                        "inputTokens": 100,
                        "cachedInputTokens": 20,
                        "outputTokens": 10,
                        "reasoningOutputTokens": 3,
                        "totalTokens": 110,
                    }
                },
            ),
            event("turn/completed", turn={"id": "u", "status": "completed"}),
        ]
        return normalize_events(
            events + tail,
            thread_id="t",
            turn_id="u",
            workspace=self.workspace,
            manifest=self.manifest,
            latency_ms=1,
            **kwargs,
        )

    def unknowns(self, result):
        return [item for item in result["events"] if item["type"] == "unknown"]

    def reads(self, result):
        return [item for item in result["events"] if item["type"] == "read"]

    def test_internal_literal_append_has_before_write_and_final_read(self):
        result = self.normalize(self.append())
        self.assertEqual(4, result["schema_version"])
        self.assertEqual([], result["issues"])
        before, write, after = result["events"]
        self.assertEqual(
            ["read", "write", "read"], [e["type"] for e in result["events"]]
        )
        self.assertEqual(
            [0, 1, 2], [e["raw_operation_index"] for e in result["events"]]
        )
        self.assertEqual(hashlib.sha256(self.before).hexdigest(), before["read_sha256"])
        self.assertEqual("append", write["write_mode"])
        self.assertEqual(
            hashlib.sha256(self.before + self.addition).hexdigest(),
            after["read_sha256"],
        )
        self.assertTrue(after["read_after_write"])
        self.assertTrue(after["read_coverage"]["complete"])
        self.assertEqual(0, before["raw_start_index"])
        self.assertEqual(1, after["raw_completion_index"])

    def test_names_unicode_and_cache_warning_remain_bounded(self):
        self.addition = "- [ ] CHK003 Is café policy specified? [Gap]\n".encode()
        script = self.script().replace("old", "original").replace("new", "updated")
        result = self.normalize(
            self.append(script, CACHE + (self.before + self.addition).decode() + "\n")
        )
        self.assertEqual([], result["issues"])
        self.assertEqual(CACHE, result["diagnostics"][0]["raw_warning_output"])

    def test_missing_read_assert_or_print_is_never_certified(self):
        for fragment in (
            "old=p.read_bytes(); ",
            "new=p.read_bytes(); ",
            "assert new == old + add; ",
            "; print(new.decode())",
        ):
            with self.subTest(fragment=fragment):
                result = self.normalize(
                    self.append(self.script().replace(fragment, ""))
                )
                self.assertTrue(self.unknowns(result))
                self.assertFalse(self.reads(result))

    def test_dynamic_or_altered_ast_never_executes(self):
        sentinel = self.workspace / "must-not-exist"
        scripts = [
            self.script().replace(repr(self.addition), "input().encode()"),
            self.script().replace(repr(self.addition), "b'a' + b'b'"),
            self.script().replace("'ab'", "'wb'"),
            self.script().replace("new == old + add", "new.startswith(old)"),
            self.script().replace("new.decode()", "old.decode()"),
            self.script().replace("from pathlib import Path", "from evil import Path"),
            self.script().replace("p=Path", "print=Path"),
            self.script().replace("new=p.read_bytes()", "new=old + add"),
            self.script() + f"; Path({str(sentinel)!r}).touch()",
        ]
        for script in scripts:
            with self.subTest(script=script):
                result = self.normalize(self.append(script))
                self.assertTrue(self.unknowns(result))
                self.assertFalse(any(e["type"] == "write" for e in result["events"]))
        self.assertFalse(sentinel.exists())

    def test_altered_prefix_unpinned_baseline_and_mismatched_hash_fail(self):
        events = self.append()
        (self.workspace / TARGET).write_bytes(b"altered\n" + self.addition)
        self.assertTrue(self.unknowns(self.normalize(events)))
        for value in (None, b"forged".hex(), "not-hex"):
            with self.subTest(value=value):
                events = self.append()
                self.manifest["baseline_target_hex"] = value
                self.assertTrue(self.unknowns(self.normalize(events)))

    def test_partial_extra_denied_and_nonzero_append_output_fail(self):
        full = (self.before + self.addition).decode() + "\n"
        for output in (
            "",
            full[:12],
            full[:-1],
            "label\n" + full,
            full + "Permission denied\n",
            CACHE.replace("code 5", "code 6") + full,
        ):
            with self.subTest(output=output):
                self.assertTrue(
                    self.unknowns(self.normalize(self.append(output=output)))
                )
        for overrides in ({"exitCode": 1}, {"status": "failed"}, {"exitCode": False}):
            self.assertTrue(self.unknowns(self.normalize(self.append(**overrides))))

    def test_append_requires_matching_complete_lifecycle(self):
        events = self.append()
        self.assertFalse(self.reads(self.normalize(events[1:])))
        self.assertFalse(self.reads(self.normalize(events[:1])))
        events[0]["params"]["item"]["command"] = "cat different"
        result = self.normalize(events)
        self.assertFalse(self.reads(result))
        self.assertFalse(result["command_records"][0]["lifecycle_valid"])
        self.assertFalse(result["instrumentation_valid"])
        events = self.append()
        events[0]["params"]["item"]["status"] = "failed"
        self.assertFalse(self.reads(self.normalize(events)))

    def test_wrong_target_outside_and_symlink_append_are_rejected(self):
        for path in ("different.md", "../escape.md", "/tmp/escape.md"):
            self.assertTrue(
                self.unknowns(self.normalize(self.append(self.script(path))))
            )
        (self.workspace / "alias.md").symlink_to(self.workspace / TARGET)
        result = self.normalize(self.append(self.script("alias.md")))
        self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))
        (self.workspace / "outside").symlink_to(self.workspace.parent)
        self.assertTrue(
            self.unknowns(self.normalize(self.append(self.script("outside/escape"))))
        )

    def test_declared_read_cannot_disagree_with_append(self):
        result = self.normalize(
            self.append(commandActions=[{"type": "read", "path": CONFIG}])
        )
        self.assertTrue(self.unknowns(result))
        self.assertFalse(self.reads(result))

    def test_append_cannot_be_masked_or_followed_by_spoofed_output(self):
        for suffix in (" || true", "; cat " + TARGET, " && cat " + TARGET):
            events = self.append()
            for notification in events:
                notification["params"]["item"]["command"] += suffix
            self.assertTrue(self.unknowns(self.normalize(events)))

    def test_relocated_literal_append_retains_original_command(self):
        root = Path("/recorded/synthetic/workspace")
        events = self.append(self.script(str(root / TARGET)), cwd=str(root))
        result = self.normalize(events, recorded_workspace=root)
        self.assertEqual([], result["issues"])
        self.assertIn(str(root), result["events"][0]["raw_command"])

    def test_nonzero_discovery_retains_proven_reference_and_envelope_failure(self):
        command = (
            f"cat {REFERENCE} && printf '\\nFILES\\n' && rg --files -g '.specify/**'"
        )
        result = self.normalize(
            self.command(command, self.reference + "\nFILES\n", exitCode=1)
        )
        read = self.reads(result)[0]
        self.assertEqual(REFERENCE, read["path"])
        self.assertEqual(0, read["exit_code"])
        self.assertEqual(1, read["envelope_exit_code"])
        self.assertTrue(read["constituent_success"])
        self.assertEqual(
            hashlib.sha256(self.reference.encode()).hexdigest(), read["read_sha256"]
        )
        self.assertTrue(
            any(
                e["status"] == "failed" and e["exit_code"] == 1
                for e in self.unknowns(result)
            )
        )
        self.assertTrue(result["issues"])
        self.assertEqual(1, result["command_records"][0]["exit_code"])

    def test_nonzero_malformed_cat_retains_exact_config_and_failure(self):
        command = f"cat {CONFIG} && cat {SETUP} --json --template checklist-template"
        output = (
            self.config + "cat: illegal option -- -\nusage: cat [-benstuv] [file ...]\n"
        )
        result = self.normalize(self.command(command, output, exitCode=1))
        self.assertEqual([CONFIG], [e["path"] for e in self.reads(result)])
        self.assertEqual(0, self.reads(result)[0]["exit_code"])
        self.assertTrue(any(e["status"] == "failed" for e in self.unknowns(result)))

    def test_failed_envelope_status_can_retain_proven_completed_read(self):
        command = f"cat {REFERENCE} && printf 'FILES\\n' && rg --files"
        for status in ("completed", "failed"):
            result = self.normalize(
                self.command(
                    command, self.reference + "FILES\n", status=status, exitCode=1
                )
            )
            self.assertEqual("completed", self.reads(result)[0]["status"])
            self.assertEqual(0, self.reads(result)[0]["exit_code"])
            self.assertTrue(any(e["status"] == "failed" for e in self.unknowns(result)))
            self.assertEqual(status, result["command_records"][0]["status"])
        for status in ("inProgress", "interrupted", "declined"):
            result = self.normalize(
                self.command(
                    command, self.reference + "FILES\n", status=status, exitCode=1
                )
            )
            self.assertFalse(
                any(e.get("constituent_success") for e in self.reads(result))
            )

    def test_constituent_read_requires_start_evidence_and_survives_recovery_as_failure(
        self,
    ):
        failed = self.command(
            f"cat {REFERENCE} && rg --files",
            self.reference,
            id="failed",
            status="failed",
            exitCode=1,
        )
        self.assertFalse(
            any(
                e.get("constituent_success")
                for e in self.reads(self.normalize(failed[1:]))
            )
        )
        result = self.normalize(
            failed + self.command("cat " + CONFIG, self.config, id="recovery")
        )
        self.assertTrue(any(e.get("constituent_success") for e in self.reads(result)))
        self.assertTrue(
            any(
                e["status"] == "failed" and e["raw_item_id"] == "failed"
                for e in self.unknowns(result)
            )
        )

    def test_constituent_reads_cannot_use_unpinned_or_changed_input(self):
        command = f"cat {REFERENCE} && rg --files"
        (self.workspace / REFERENCE).write_text("changed\n")
        result = self.normalize(self.command(command, self.reference, exitCode=1))
        self.assertFalse(any(e.get("constituent_success") for e in self.reads(result)))
        self.manifest["baseline"].pop(REFERENCE)
        result = self.normalize(self.command(command, "changed\n", exitCode=1))
        self.assertFalse(any(e.get("constituent_success") for e in self.reads(result)))

    def test_constituent_proof_rejects_partial_wrong_order_or_unbounded_producers(self):
        good = f"cat {REFERENCE} && printf 'label\\n' && rg --files"
        for command, output in (
            (good, self.reference[:8] + "label\n"),
            (good, "label\n" + self.reference),
            (good, self.reference + "label\nextra\n"),
            (f"cat {REFERENCE} && python3 -c 'print(1)'", self.reference),
            (
                f"cat {REFERENCE} || printf %s {shlex.quote(self.reference)}",
                self.reference,
            ),
            (f"cat {REFERENCE} && rg --files --follow", self.reference),
        ):
            with self.subTest(command=command, output=output):
                result = self.normalize(self.command(command, output, exitCode=1))
                self.assertFalse(
                    any(e.get("constituent_success") for e in self.reads(result))
                )
                self.assertTrue(result["issues"])

    def test_constituent_paths_and_declared_reads_must_match(self):
        (self.workspace / "alias.md").symlink_to(self.workspace / REFERENCE)
        for command in (
            "cat alias.md && rg --files",
            f"cat {REFERENCE} && rg --files ../outside",
        ):
            result = self.normalize(self.command(command, self.reference, exitCode=1))
            self.assertFalse(
                any(e.get("constituent_success") for e in self.reads(result))
            )
            self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))
        result = self.normalize(
            self.command(
                f"cat {REFERENCE} && rg --files",
                self.reference,
                exitCode=1,
                commandActions=[{"type": "read", "path": CONFIG}],
            )
        )
        self.assertFalse(any(e.get("constituent_success") for e in self.reads(result)))

    def test_masked_python_shell_failure_never_invents_constitution_or_erases_error(
        self,
    ):
        bad = (
            f"python3 {SETUP} --json --template checklist-template && "
            f"cat {CONSTITUTION} || true; cat {TEMPLATE}"
        )
        events = self.command(
            bad, "SyntaxError: invalid syntax\n# Checklist\n", id="bad"
        )
        events += self.command(SETUP_COMMAND, "", id="recovery")
        result = self.normalize(events)
        self.assertFalse(any(e.get("path") == CONSTITUTION for e in self.reads(result)))
        self.assertTrue(
            any(
                e["status"] == "failed" and e["raw_item_id"] == "bad"
                for e in self.unknowns(result)
            )
        )
        self.assertTrue(
            any(
                e["type"] == "setup" and e["raw_item_id"] == "recovery"
                for e in result["events"]
            )
        )
        self.assertEqual(
            "SyntaxError: invalid syntax\n# Checklist\n",
            result["command_records"][0]["aggregated_output"],
        )

    def test_hidden_discovery_is_diagnostic_never_read_or_absence_proof(self):
        for hidden in (False, True):
            command = (
                "rg --files " + ("--hidden " if hidden else "") + "-g '.specify/**'"
            )
            result = self.normalize(self.command(command, CONFIG + "\n"))
            self.assertEqual([], result["events"])
            diagnostic = result["diagnostics"][0]
            self.assertEqual(hidden, diagnostic["include_hidden"])
            self.assertFalse(diagnostic["certifies_file_contents"])
            self.assertFalse(diagnostic["certifies_absence"])
            self.assertEqual(not hidden, diagnostic["hidden_patterns_without_hidden"])
        failed = self.normalize(self.command("rg --files --hidden", "", exitCode=1))
        self.assertTrue(any(e["status"] == "failed" for e in self.unknowns(failed)))

    def test_hidden_discovery_rejects_expansion_follow_links_and_outside_paths(self):
        for command in (
            "rg --files --hidden --follow",
            "rg --files --hidden ../outside",
            "rg --files --hidden -g '../*'",
            "rg --files --hidden -g '.specify/**' | cat",
            "rg --files --hidden $PWD",
            "rg --files --hidden --hidden",
        ):
            self.assertTrue(self.unknowns(self.normalize(self.command(command))))

    def test_v3_module_and_input_objects_are_not_mutated(self):
        events = self.append()
        copied = copy.deepcopy(events)
        manifest = copy.deepcopy(self.manifest)
        result = self.normalize(events)
        self.assertEqual(copied, events)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual("codex-workflow-trace-v4", result["instrumentation"])
        old = normalize_v3(
            events,
            thread_id="t",
            turn_id="u",
            workspace=self.workspace,
            manifest=self.manifest,
            latency_ms=1,
        )
        self.assertEqual(3, old["schema_version"])
        self.assertFalse(any(e["type"] == "write" for e in old["events"]))

    def test_unchanged_v3_literal_replacement_still_uses_separate_cat(self):
        payload = "# Replacement\n"
        (self.workspace / TARGET).write_text(payload)
        script = (
            f"from pathlib import Path; p=Path({TARGET!r}); p.write_text({payload!r})"
        )
        result = self.normalize(
            self.command(
                "python3 -c " + shlex.quote(script) + " && cat " + TARGET, payload
            )
        )
        self.assertEqual([], result["issues"])
        self.assertEqual(["write", "read"], [e["type"] for e in result["events"]])

    def test_unchanged_v3_literal_heredoc_still_classifies(self):
        result = self.normalize(
            self.command(f"cat >> {TARGET} <<'EOF'\n# Added\nEOF\n")
        )
        self.assertEqual([], result["issues"])
        self.assertEqual(["write"], [e["type"] for e in result["events"]])

    def test_heredoc_retains_constituent_errors_despite_zero_exit(self):
        for error in ("SyntaxError", "IndentationError", "AssertionError"):
            result = self.normalize(
                self.command(
                    f"cat >> {TARGET} <<'EOF'\n# Added\nEOF\n",
                    error + ": invalid captured execution\n",
                )
            )
            self.assertTrue(any(e["type"] == "write" for e in result["events"]))
            self.assertTrue(any(e["status"] == "failed" for e in self.unknowns(result)))
            self.assertTrue(result["issues"])

    def test_corroborated_cache_warning_does_not_mask_another_failure(self):
        payload = (
            json.dumps(
                {
                    "FEATURE_DIR": str(self.workspace / "specs/001-invitations"),
                    "AVAILABLE_DOCS": ["spec.md"],
                    "TEMPLATE_CONTENT": "# Checklist\n",
                }
            )
            + "\n"
        )
        clean = self.normalize(self.command(SETUP_COMMAND, CACHE + payload))
        self.assertEqual([], clean["issues"])
        for error in ("SyntaxError", "IndentationError", "AssertionError"):
            result = self.normalize(
                self.command(
                    SETUP_COMMAND,
                    CACHE + payload + error + ": extra failure\n",
                )
            )
            self.assertTrue(
                any(
                    "cache warning" in e.get("reason", "")
                    for e in result["diagnostics"]
                )
            )
            self.assertTrue(any(e["status"] == "failed" for e in self.unknowns(result)))
            self.assertTrue(result["issues"])


if __name__ == "__main__":
    unittest.main()
