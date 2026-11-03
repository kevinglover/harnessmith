from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from harnessmith.workflow_fidelity import PACKAGE, SETUP, SETUP_COMMAND
from harnessmith.workflow_trace_v2 import normalize_events

TARGET = "specs/001-invitations/checklists/security.md"
SPEC = "specs/001-invitations/spec.md"
CONSTITUTION = ".specify/memory/constitution.md"
TEMPLATE = ".specify/templates/checklist-template.md"
CACHE_NOISE = (
    "python3: warning: confstr() failed with code 5: couldn't get path of "
    "DARWIN_USER_TEMP_DIR; using /tmp instead\n"
    "python3: error: couldn't create cache file '/tmp/xcrun_db-AbC123' "
    "(errno=Operation not permitted)\n"
)


def event(method, **params):
    return {
        "method": method,
        "params": {"threadId": "thread", "turnId": "turn", **params},
    }


def lifecycle(item):
    return [
        event("item/started", item={**item, "status": "inProgress"}),
        event("item/completed", item=item),
    ]


def end_events():
    return [
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
        event("turn/completed", turn={"id": "turn", "status": "completed"}),
    ]


class WorkflowTraceV2Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name).resolve() / "workspace"
        self.workspace.mkdir()
        self.manifest = {
            "model": "gpt-6-luna",
            "target": TARGET,
            "baseline": {},
            "required_reads": [SPEC, CONSTITUTION],
        }
        self.contents = {}
        self.pin(
            SPEC, "# Synthetic spec\n\nFR1: owners invite.\nFR2: expiry unspecified.\n"
        )
        self.pin(CONSTITUTION, "# Synthetic principles\nReviewer owns checks.\n")
        self.pin(TEMPLATE, "# Checklist\n\n## Requirements\n")
        self.pin(SETUP, "#!/bin/sh\n# frozen adapter\n")

    def pin(self, path, text):
        target = self.workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        self.manifest["baseline"][path] = hashlib.sha256(text.encode()).hexdigest()
        self.contents[path] = text

    def command(self, text, **overrides):
        return lifecycle(
            {
                "id": "command",
                "type": "commandExecution",
                "command": text,
                "cwd": str(self.workspace),
                "status": "completed",
                "exitCode": 0,
                "commandActions": [],
                **overrides,
            }
        )

    def normalize(self, events, **overrides):
        return normalize_events(
            events + end_events(),
            thread_id="thread",
            turn_id="turn",
            workspace=self.workspace,
            manifest=self.manifest,
            latency_ms=12,
            **overrides,
        )

    def unknown(self, result):
        return [entry for entry in result["events"] if entry["type"] == "unknown"]

    def test_bounded_and_discovery_labels_and_reads(self):
        command = (
            "cat "
            + SPEC
            + " && printf '\\n--- FILES ---\\n' && rg --files -g 'spec.md' -g 'constitution*' .specify specs"
        )
        result = self.normalize(
            self.command(
                command,
                aggregatedOutput=self.contents[SPEC]
                + "\n--- FILES ---\n"
                + SPEC
                + "\n",
            )
        )
        self.assertEqual([], result["issues"])
        self.assertEqual([SPEC], [e["path"] for e in result["events"]])
        self.assertEqual(
            ["literal output label", "file discovery"],
            [e["reason"] for e in result["diagnostics"]],
        )
        self.assertEqual(
            ("command", 0, 1, 0),
            tuple(
                result["events"][0][k]
                for k in (
                    "raw_item_id",
                    "raw_start_index",
                    "raw_completion_index",
                    "raw_operation_index",
                )
            ),
        )

    def test_newline_and_semicolon_reads_need_ordered_pinned_stdout(self):
        for separator in ("\n", "; "):
            with self.subTest(separator=separator):
                result = self.normalize(
                    self.command(
                        "cat " + CONSTITUTION + separator + "cat " + SPEC,
                        aggregatedOutput=self.contents[CONSTITUTION]
                        + self.contents[SPEC],
                    )
                )
                self.assertEqual([], result["issues"])
                self.assertEqual(
                    [CONSTITUTION, SPEC], [e["path"] for e in result["events"]]
                )
                self.assertTrue(
                    all(
                        "pinned input" in e["success_evidence"]
                        for e in result["events"]
                    )
                )

    def test_inverted_partial_or_claimed_stdout_cannot_certify_all_reads(self):
        for output in (
            self.contents[SPEC] + self.contents[CONSTITUTION],
            self.contents[CONSTITUTION][:10],
            "I read both files",
            "",
        ):
            with self.subTest(output=output):
                result = self.normalize(
                    self.command(
                        "cat " + CONSTITUTION + "\ncat " + SPEC, aggregatedOutput=output
                    )
                )
                self.assertTrue(self.unknown(result))

    def test_hash_mismatch_blocks_stdout_attribution(self):
        (self.workspace / CONSTITUTION).write_text("changed after capture\n")
        result = self.normalize(
            self.command(
                "cat " + CONSTITUTION + "\ncat " + SPEC,
                aggregatedOutput=self.contents[CONSTITUTION] + self.contents[SPEC],
            )
        )
        self.assertTrue(
            any("hash mismatch" in e.get("reason", "") for e in self.unknown(result))
        )

    def test_unpinned_bytes_and_empty_files_do_not_establish_read(self):
        for path, content in (("untracked.md", "untracked\n"), ("empty.md", "")):
            self.pin(path, content)
            if path == "untracked.md":
                del self.manifest["baseline"][path]
            result = self.normalize(
                self.command(
                    "cat " + path + "\ncat " + SPEC,
                    aggregatedOutput=content + self.contents[SPEC],
                )
            )
            self.assertTrue(self.unknown(result))

    def test_sed_partial_mandatory_read_is_never_full_context(self):
        result = self.normalize(
            self.command(
                "sed -n '1,2p' " + SPEC + "\ncat " + CONSTITUTION,
                aggregatedOutput="# Synthetic spec\n\n" + self.contents[CONSTITUTION],
            )
        )
        self.assertTrue(self.unknown(result))
        reference = PACKAGE + "/references/project-generation.md"
        self.pin(reference, "first\nsecond\nthird\n")
        for path in (reference, CONSTITUTION, SPEC):
            truncated = self.normalize(self.command("sed -n '1p' " + path))
            self.assertTrue(self.unknown(truncated))
            full = self.normalize(self.command("sed -n '1,999p' " + path))
            self.assertEqual([], full["issues"])
            self.assertTrue(full["events"][0]["read_coverage"]["complete"])

    def test_present_fixture_if_read_is_observed_not_assumed(self):
        command = f"if [ -f {CONSTITUTION} ]; then cat {CONSTITUTION}; fi"
        good = self.normalize(
            self.command(command, aggregatedOutput=self.contents[CONSTITUTION])
        )
        self.assertEqual([], good["issues"])
        self.assertEqual(CONSTITUTION, good["events"][0]["path"])
        missing = self.normalize(self.command(command, aggregatedOutput=""))
        self.assertTrue(self.unknown(missing))

    def test_absent_extension_branch_then_setup_json(self):
        command = (
            "if [ -f .specify/extensions.yml ]; then cat .specify/extensions.yml; else printf '%s\\n' 'NO_EXTENSIONS'; fi\n"
            + SETUP_COMMAND
        )
        output = (
            "NO_EXTENSIONS\n"
            + json.dumps(
                {
                    "FEATURE_DIR": str(self.workspace / "specs/001-invitations"),
                    "AVAILABLE_DOCS": ["spec.md"],
                    "TEMPLATE_CONTENT": self.contents[TEMPLATE],
                }
            )
            + "\n"
        )
        result = self.normalize(self.command(command, aggregatedOutput=output))
        self.assertEqual([], result["issues"])
        self.assertEqual(["setup"], [e["type"] for e in result["events"]])
        self.assertEqual("fixture absence", result["diagnostics"][0]["reason"])
        corrupted = self.normalize(
            self.command(
                command, aggregatedOutput=output.replace("AVAILABLE_DOCS", "invented")
            )
        )
        self.assertTrue(self.unknown(corrupted))

    def test_absence_branch_cannot_hide_malicious_or_unrelated_reads(self):
        commands = [
            "if [ -f absent ]; then python3 -c 'print(1)'; else printf 'NO\\n'; fi",
            f"if [ -f absent ]; then cat {SPEC}; else printf 'NO\\n'; fi",
            "if [ -f absent ]; then cat absent; else rm " + SPEC + "; fi",
        ]
        for command in commands:
            result = self.normalize(self.command(command, aggregatedOutput="NO\n"))
            self.assertTrue(self.unknown(result))
            self.assertFalse(any(e["type"] == "read" for e in result["events"]))

    def test_missing_directory_branch_and_setup_noise_are_bounded(self):
        command = f"cat {CONSTITUTION}\nif [ -d specs/001-invitations/checklists ]; then rg --files specs/001-invitations/checklists; else printf 'NO_CHECKLIST_DIR\\n'; fi"
        result = self.normalize(
            self.command(
                command,
                aggregatedOutput=self.contents[CONSTITUTION] + "NO_CHECKLIST_DIR\n",
            )
        )
        self.assertEqual([], result["issues"])
        self.assertEqual("fixture absence", result["diagnostics"][0]["reason"])

    def test_exact_runtime_cache_warning_requires_pinned_setup_json(self):
        output = (
            json.dumps(
                {
                    "FEATURE_DIR": str(self.workspace / "specs/001-invitations"),
                    "AVAILABLE_DOCS": ["spec.md"],
                    "TEMPLATE_CONTENT": self.contents[TEMPLATE],
                }
            )
            + "\n"
        )
        result = self.normalize(
            self.command(SETUP_COMMAND, aggregatedOutput=CACHE_NOISE * 2 + output)
        )
        self.assertEqual([], result["issues"])
        self.assertEqual(["setup"], [e["type"] for e in result["events"]])
        self.assertEqual(
            CACHE_NOISE * 2, result["diagnostics"][0]["raw_warning_output"]
        )
        for broken in (
            CACHE_NOISE,
            CACHE_NOISE + output[:30],
            CACHE_NOISE + output.replace("spec.md", "fake.md"),
            CACHE_NOISE + output + "permission denied\n",
        ):
            with self.subTest(broken=broken):
                invalid = self.normalize(
                    self.command(SETUP_COMMAND, aggregatedOutput=broken)
                )
                self.assertTrue(self.unknown(invalid))
                self.assertTrue(
                    any(e["status"] == "failed" for e in self.unknown(invalid))
                )
        (self.workspace / SETUP).write_text("untrusted adapter\n")
        unpinned = self.normalize(
            self.command(SETUP_COMMAND, aggregatedOutput=CACHE_NOISE + output)
        )
        self.assertTrue(self.unknown(unpinned))

    def test_exact_runtime_cache_warning_requires_pinned_hook_json(self):
        self.pin(".pilot/marker_hook.py", "# synthetic hook\n")
        pre_json = (
            json.dumps(
                {
                    "command": "pilot-pre-marker",
                    "target_exists": False,
                    "target_sha256": None,
                }
            )
            + "\n"
        )
        pre = self.normalize(
            self.command(
                "python3 .pilot/marker_hook.py pilot-pre-marker",
                aggregatedOutput=CACHE_NOISE + pre_json,
            )
        )
        self.assertEqual([], pre["issues"])
        self.assertEqual("hook", pre["events"][0]["type"])
        for output in (
            CACHE_NOISE,
            CACHE_NOISE + pre_json.replace("pre-marker", "optional-pre"),
            CACHE_NOISE + pre_json + "permission denied\n",
        ):
            invalid = self.normalize(
                self.command(
                    "python3 .pilot/marker_hook.py pilot-pre-marker",
                    aggregatedOutput=output,
                )
            )
            self.assertTrue(self.unknown(invalid))
        self.pin(TARGET, "created artifact\n")
        post_json = (
            json.dumps(
                {
                    "command": "pilot-post-marker",
                    "target_exists": True,
                    "target_sha256": self.manifest["baseline"][TARGET],
                }
            )
            + "\n"
        )
        post = self.normalize(
            self.command(
                "python3 .pilot/marker_hook.py pilot-post-marker",
                aggregatedOutput=CACHE_NOISE + post_json,
            )
        )
        self.assertEqual([], post["issues"])
        invalid = self.normalize(
            self.command(
                "python3 .pilot/marker_hook.py pilot-post-marker",
                aggregatedOutput=CACHE_NOISE
                + post_json.replace(self.manifest["baseline"][TARGET], "0" * 64),
            )
        )
        self.assertTrue(self.unknown(invalid))

    def test_runtime_noise_not_ignored_for_other_commands_or_failure_exit(self):
        for command in ("cat " + SPEC, "pwd"):
            result = self.normalize(
                self.command(
                    command, aggregatedOutput=CACHE_NOISE + self.contents[SPEC]
                )
            )
            self.assertTrue(self.unknown(result))
            self.assertFalse(
                any(
                    "corroborated" in e.get("reason", "") for e in result["diagnostics"]
                )
            )
        output = (
            json.dumps(
                {
                    "FEATURE_DIR": str(self.workspace / "specs/001-invitations"),
                    "AVAILABLE_DOCS": ["spec.md"],
                    "TEMPLATE_CONTENT": self.contents[TEMPLATE],
                }
            )
            + "\n"
        )
        result = self.normalize(
            self.command(
                SETUP_COMMAND, exitCode=1, aggregatedOutput=CACHE_NOISE + output
            )
        )
        self.assertTrue(self.unknown(result))

    def test_tested_path_escape_isolation_even_if_missing(self):
        result = self.normalize(
            self.command("if [ -f ../outside ]; then cat ../outside; fi")
        )
        self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))

    def test_pipes_dynamic_producers_redirection_and_fallbacks_rejected(self):
        commands = [
            f"cat {SPEC} | sort",
            f"cat {SPEC} || true",
            f"cat {SPEC}\npython3 -c 'print(1)'",
            f"cat {SPEC} 2>/dev/null",
            f"cat $(pwd)/{SPEC}",
            "cat $HOME/private",
            "rg --files -g '*.md' ..",
            "rg --files -g '../*.md' .",
            "cat *.md",
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.normalize(
                    self.command(command, aggregatedOutput=self.contents[SPEC])
                )
                self.assertTrue(self.unknown(result))
                self.assertFalse(any(e["type"] == "read" for e in result["events"]))

    def test_qualified_tools_and_comments_cannot_spoof_reads(self):
        for command in (
            f"cat {SPEC} # {CONSTITUTION}",
            f"cat {SPEC}\n.pilot/printf '{self.contents[SPEC]}'",
            ".pilot/rg --files .",
            ".pilot/echo ok",
        ):
            with self.subTest(command=command):
                result = self.normalize(
                    self.command(command, aggregatedOutput=self.contents[SPEC])
                )
                self.assertTrue(self.unknown(result))
                self.assertFalse(any(e["type"] == "read" for e in result["events"]))

    def test_terminal_discovery_pipeline_keeps_prefix_reads_and_unknown_exit(self):
        reference = PACKAGE + "/references/project-generation.md"
        self.pin(reference, "required generation guidance\n")
        command = (
            "cat "
            + reference
            + " && printf '\\n--- FILES ---\\n' && rg --files .specify .agents | sort"
        )
        output = self.contents[reference] + "\n--- FILES ---\n" + reference + "\n"
        result = self.normalize(self.command(command, aggregatedOutput=output))
        self.assertEqual(
            [reference], [e["path"] for e in result["events"] if e["type"] == "read"]
        )
        self.assertTrue(
            any(
                "producer exit is unavailable" in e.get("reason", "")
                for e in self.unknown(result)
            )
        )
        failure = self.normalize(
            self.command(
                command, aggregatedOutput=output + "rg: .specify: permission denied\n"
            )
        )
        self.assertTrue(any(e["status"] == "failed" for e in self.unknown(failure)))
        self.assertEqual(
            [reference], [e["path"] for e in failure["events"] if e["type"] == "read"]
        )
        for suffix in (
            "rg --files .. | sort",
            "rg --files . | .pilot/sort",
            "cat " + SPEC + " | sort",
        ):
            invalid = self.normalize(
                self.command(
                    "cat " + reference + " && " + suffix, aggregatedOutput=output
                )
            )
            self.assertFalse(any(e["type"] == "read" for e in invalid["events"]))

    def test_mandatory_reads_must_finish_before_consumers_start(self):
        reference = PACKAGE + "/references/project-generation.md"
        self.pin(reference, "required workflow\n")
        self.manifest["expected_references"] = ["references/project-generation.md"]
        self.pin(".specify/extensions.yml", "hooks: []\n")
        patch = lifecycle(
            {
                "id": "write",
                "type": "fileChange",
                "status": "completed",
                "changes": [
                    {"kind": {"type": "add"}, "path": TARGET, "diff": "+content"}
                ],
            }
        )
        pairs = [
            (SPEC, patch),
            (reference, self.command(SETUP_COMMAND, id="setup")),
            (
                ".specify/extensions.yml",
                self.command(
                    "python3 .pilot/marker_hook.py pilot-pre-marker", id="hook"
                ),
            ),
        ]
        for path, consumer in pairs:
            with self.subTest(path=path):
                read = self.command("cat " + path, id="read")
                overlap = self.normalize([read[0], consumer[0], read[1], consumer[1]])
                self.assertTrue(
                    any(e.get("dependency_path") == path for e in self.unknown(overlap))
                )
                awaited = self.normalize(read + consumer)
                self.assertFalse(
                    any(e.get("dependency_path") == path for e in self.unknown(awaited))
                )
                reread = self.command("cat " + path, id="reread")
                extra = self.normalize(read + consumer + reread)
                self.assertFalse(
                    any(e.get("dependency_path") == path for e in self.unknown(extra))
                )

    def test_aggregate_zero_does_not_hide_denied_heredoc_or_failed_ls(self):
        commands = [
            f"cat > {TARGET} <<'EOF'\nbody\nEOF\ncat {TARGET}",
            f"python3 - <<'PY'\nprint(1)\nPY\ntail {TARGET}",
        ]
        for command in commands:
            result = self.normalize(
                self.command(
                    command,
                    aggregatedOutput="zsh:2: can't create temp file for here document: operation not permitted\n",
                )
            )
            self.assertTrue(any(e["status"] == "failed" for e in self.unknown(result)))
            self.assertFalse(any(e["type"] == "write" for e in result["events"]))
        result = self.normalize(
            self.command(
                "ls -la absent\ncat " + SPEC,
                aggregatedOutput="ls: absent: No such file or directory\n"
                + self.contents[SPEC],
            )
        )
        self.assertTrue(any(e["status"] == "failed" for e in self.unknown(result)))

    def test_actual_failure_exit_retained_even_with_matching_stdout(self):
        result = self.normalize(
            self.command(
                "cat " + SPEC, exitCode=1, aggregatedOutput=self.contents[SPEC]
            )
        )
        self.assertTrue(
            any(
                i["detail"] == "failed or incomplete operation"
                for i in result["issues"]
            )
        )
        self.assertEqual(1, result["events"][0]["exit_code"])

    def test_append_initial_read_uses_pinned_before_bytes_not_final_target(self):
        self.pin(TARGET, "- [X] CHK007 Existing reviewer state\n")
        self.manifest["baseline_target_hex"] = self.contents[TARGET].encode().hex()
        (self.workspace / TARGET).write_text(
            self.contents[TARGET] + "- [ ] CHK008 New\n"
        )
        result = self.normalize(
            self.command(
                "cat " + TARGET + "\ncat " + SPEC,
                aggregatedOutput=self.contents[TARGET] + self.contents[SPEC],
            )
        )
        self.assertEqual([], result["issues"])
        self.assertEqual(TARGET, result["events"][0]["path"])
        self.manifest["baseline_target_hex"] = b"forged before".hex()
        invalid = self.normalize(
            self.command(
                "cat " + TARGET + "\ncat " + SPEC,
                aggregatedOutput="forged before" + self.contents[SPEC],
            )
        )
        self.assertTrue(self.unknown(invalid))

    def test_relocated_absolute_paths_map_only_under_recorded_root(self):
        original = Path("/recorded/pilot/workspace")
        result = self.normalize(
            self.command(
                "cat " + str(original / SPEC) + "\ncat " + str(original / CONSTITUTION),
                cwd=str(original),
                aggregatedOutput=self.contents[SPEC] + self.contents[CONSTITUTION],
            ),
            recorded_workspace=original,
        )
        self.assertEqual([], result["issues"])
        self.assertEqual([SPEC, CONSTITUTION], [e["path"] for e in result["events"]])
        outside = self.normalize(
            self.command("cat /recorded/other/spec.md", cwd=str(original)),
            recorded_workspace=original,
        )
        self.assertTrue(any(i["kind"] == "isolation" for i in outside["issues"]))
        traversal = self.normalize(
            self.command("cat /recorded/pilot/workspace/../secret", cwd=str(original)),
            recorded_workspace=original,
        )
        self.assertTrue(any(i["kind"] == "isolation" for i in traversal["issues"]))

    def test_symlink_cannot_escape_during_replay(self):
        (self.workspace / "escape").symlink_to(self.workspace.parent)
        result = self.normalize(self.command("cat escape/private"))
        self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))

    def test_final_answer_phase_separated_from_commentary_and_partial(self):
        events = lifecycle(
            {
                "id": "comment",
                "type": "agentMessage",
                "phase": "commentary",
                "text": "I will create four items",
            }
        )
        events += lifecycle(
            {
                "id": "final",
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "Created two items",
            }
        )
        events += [
            event("item/agentMessage/delta", itemId="partial", delta="three items")
        ]
        result = self.normalize(events)
        self.assertEqual("Created two items", result["final_output"])
        self.assertEqual(["I will create four items"], result["commentary"])
        self.assertIn("three items", result["output"])
        for phase in (None, "finalAnswer", "commentary"):
            missing = self.normalize(
                lifecycle(
                    {
                        "id": "x",
                        "type": "agentMessage",
                        "phase": phase,
                        "text": "Created four items",
                    }
                )
            )
            self.assertIsNone(missing["final_output"])

    def test_missing_lifecycle_reroute_unknown_items_and_overlap_retained(self):
        missing = self.normalize(self.command("cat " + SPEC)[1:])
        self.assertFalse(missing["instrumentation_valid"])
        rerouted = self.normalize([event("model/rerouted", toModel="other")])
        self.assertFalse(rerouted["instrumentation_valid"])
        unknown = self.normalize(
            lifecycle({"id": "mcp", "type": "mcpToolCall", "status": "completed"})
        )
        self.assertTrue(self.unknown(unknown))
        pre = self.command("python3 .pilot/marker_hook.py pilot-pre-marker", id="pre")
        setup = self.command(SETUP_COMMAND, id="setup")
        overlap = self.normalize([pre[0], setup[0], pre[1], setup[1]])
        self.assertTrue(any("overlap" in i["detail"] for i in overlap["issues"]))

    def test_reference_must_finish_before_project_context_read_starts(self):
        reference = ".agents/skills/speckit-checklist/references/project-generation.md"
        self.pin(reference, "Read this guidance before project actions.\n")
        self.manifest["expected_references"] = ["references/project-generation.md"]
        guidance = self.command("cat " + reference, id="guidance")
        context = self.command("cat " + SPEC, id="context")
        overlapping = self.normalize(
            [guidance[0], context[0], guidance[1], context[1]]
        )
        self.assertTrue(any(
            entry.get("dependency_path") == reference
            for entry in self.unknown(overlapping)
        ))
        sequenced = self.normalize(guidance + context)
        self.assertEqual([], sequenced["issues"])
        same_item = self.normalize(self.command("cat " + reference + " && cat " + SPEC))
        self.assertEqual([], same_item["issues"])

    def test_wrapper_keeps_raw_command_and_actions_cannot_invent_read(self):
        body = "cat " + SPEC + "\ncat " + CONSTITUTION
        command = "/bin/zsh -c " + shlex.quote(body)
        result = self.normalize(
            self.command(
                command,
                aggregatedOutput=self.contents[SPEC] + self.contents[CONSTITUTION],
                commandActions=[{"type": "read", "path": "invented.md"}],
            )
        )
        self.assertTrue(self.unknown(result))
        self.assertEqual(command, result["events"][0]["raw_command"])


if __name__ == "__main__":
    unittest.main()
