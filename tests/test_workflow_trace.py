from __future__ import annotations

import copy
from pathlib import Path
import shlex
import tempfile
import unittest

from harnessmith.workflow_fidelity import SETUP_COMMAND
from harnessmith.workflow_trace import normalize_events


TARGET = "specs/001-invitations/checklists/security.md"


def event(method, **params):
    return {
        "method": method,
        "params": {"threadId": "thread", "turnId": "turn", **params},
    }


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


def lifecycle(item):
    started = {**item, "status": "inProgress"}
    return [event("item/started", item=started), event("item/completed", item=item)]


class WorkflowTraceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name).resolve() / "workspace"
        self.workspace.mkdir()
        self.manifest = {"model": "gpt-6-luna", "target": TARGET, "case": "hooks"}

    def normalize(self, events, **overrides):
        arguments = dict(
            thread_id="thread",
            turn_id="turn",
            workspace=self.workspace,
            manifest=self.manifest,
            latency_ms=17,
        )
        arguments.update(overrides)
        return normalize_events(events, **arguments)

    def command(self, command, *, identifier="command", actions=None, **overrides):
        item = {
            "id": identifier,
            "type": "commandExecution",
            "command": command,
            "cwd": str(self.workspace),
            "status": "completed",
            "exitCode": 0,
            "commandActions": [] if actions is None else actions,
            **overrides,
        }
        return lifecycle(item)

    def change(self, kind=None, path=TARGET, *, identifier="patch", **overrides):
        item = {
            "id": identifier,
            "type": "fileChange",
            "status": "completed",
            "changes": [
                {"kind": kind or {"type": "add"}, "path": path, "diff": "+fixture"}
            ],
            **overrides,
        }
        return lifecycle(item)

    def test_chained_read_setup_and_hook_with_wrapper_preserve_mapping(self):
        command = (
            "cat .specify/extensions.yml && python3 .pilot/marker_hook.py pilot-pre-marker && bash "
            + SETUP_COMMAND
            + " && sed -n '1,240p' specs/001-invitations/spec.md"
        )
        wrapped = "/bin/zsh -lc " + shlex.quote(command)
        events = self.command(
            wrapped,
            actions=[
                {"type": "read", "path": ".specify/extensions.yml"},
                {"type": "unknown", "command": command},
                {
                    "type": "read",
                    "path": str(self.workspace / "specs/001-invitations/spec.md"),
                },
            ],
        )
        result = self.normalize(events + end_events())
        self.assertTrue(result["instrumentation_valid"])
        self.assertEqual([], result["issues"])
        self.assertEqual(
            ["read", "hook", "setup", "read"], [e["type"] for e in result["events"]]
        )
        self.assertEqual("pilot-pre-marker", result["events"][1]["command"])
        self.assertEqual(SETUP_COMMAND, result["events"][2]["command"])
        for index, normalized in enumerate(result["events"]):
            self.assertEqual(
                ("command", 0, 1, index),
                (
                    normalized["raw_item_id"],
                    normalized["raw_start_index"],
                    normalized["raw_completion_index"],
                    normalized["raw_operation_index"],
                ),
            )

    def test_last_thread_total_is_measured_once_and_other_threads_ignored(self):
        earlier = copy.deepcopy(end_events()[0])
        earlier["params"]["tokenUsage"]["total"].update(inputTokens=50, totalTokens=60)
        other = copy.deepcopy(earlier)
        other["params"]["threadId"] = "other"
        result = self.normalize([earlier] + end_events() + [other])
        self.assertEqual(100, result["usage"]["inputTokens"])
        self.assertEqual(20, result["usage"]["cachedInputTokens"])
        self.assertEqual(17, result["usage"]["latency_ms"])
        self.assertEqual(1, result["usage"]["raw_event_index"])

    def test_stdout_or_agent_claims_never_synthesize_reads(self):
        events = self.command(
            "pwd", aggregatedOutput="Read .specify/memory/constitution.md"
        )
        events += lifecycle(
            {"id": "answer", "type": "agentMessage", "text": "I read the feature spec."}
        )
        result = self.normalize(events + end_events())
        self.assertEqual([], result["events"])
        self.assertEqual(
            "working-directory discovery", result["diagnostics"][0]["reason"]
        )
        self.assertIn("I read", result["output"])

    def test_file_add_update_are_writes_delete_move_and_outside_are_retained(self):
        for kind in ({"type": "add"}, {"type": "update", "move_path": None}):
            result = self.normalize(self.change(kind=kind) + end_events())
            self.assertEqual("write", result["events"][0]["type"])
            self.assertEqual(TARGET, result["events"][0]["path"])
        for kind in (
            {"type": "delete"},
            {"type": "update", "move_path": "another.md"},
            {"type": "future"},
        ):
            result = self.normalize(self.change(kind=kind) + end_events())
            self.assertEqual("unknown", result["events"][0]["type"])
            self.assertTrue(result["instrumentation_valid"])
            self.assertTrue(any(i["kind"] == "fidelity" for i in result["issues"]))
        outside = self.normalize(self.change(path="../outside.md") + end_events())
        self.assertTrue(any(i["kind"] == "isolation" for i in outside["issues"]))

    def test_literal_heredoc_write_and_directory_audit_record(self):
        for redirect in (f"> {TARGET} <<'EOF'", f"<<'EOF' >> {TARGET}"):
            command = f"mkdir -p specs/001-invitations/checklists && cat {redirect}\n# Check author's $literal\nEOF\n"
            result = self.normalize(self.command(command) + end_events())
            self.assertEqual([], result["issues"])
            self.assertEqual(["write"], [e["type"] for e in result["events"]])
            self.assertEqual(
                ["command"], result["diagnostics"][0]["associated_write_item_ids"]
            )
            self.assertEqual(TARGET, result["events"][0]["path"])

    def test_directory_creation_without_artifact_is_not_hidden(self):
        result = self.normalize(
            self.command("mkdir -p specs/001-invitations/checklists") + end_events()
        )
        self.assertEqual("unknown", result["events"][0]["type"])
        self.assertEqual(
            "artifact directory creation", result["diagnostics"][0]["reason"]
        )

    def test_unknown_shell_forms_are_retained_and_never_executed(self):
        commands = [
            "cat spec.md; cat missing.md",
            "cat spec.md\ncat other.md",
            "cat spec.md | head -5",
            "cat $(whoami)",
            "cat spec.md > other.md",
            "python3 -c 'print(1)'",
            "rm spec.md",
            "mkdir -p outside",
            "cat > " + TARGET + " <<EOF\n$(id)\nEOF\n",
            "cat > " + TARGET + " <<'EOF'\ncontent\nEOF\npwd",
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.normalize(self.command(command) + end_events())
                self.assertEqual(["unknown"], [e["type"] for e in result["events"]])
                self.assertTrue(result["instrumentation_valid"])

    def test_declared_read_must_match_deterministic_command(self):
        result = self.normalize(
            self.command("cat one.md", actions=[{"type": "read", "path": "two.md"}])
            + end_events()
        )
        self.assertEqual("unknown", result["events"][0]["type"])
        self.assertIn("disagrees", result["events"][0]["reason"])

    def test_paths_normalize_from_cwd_and_reject_symlink_escape(self):
        nested = self.workspace / "specs"
        nested.mkdir()
        result = self.normalize(
            self.command("cat feature.md", cwd=str(nested)) + end_events()
        )
        self.assertEqual("specs/feature.md", result["events"][0]["path"])
        (self.workspace / "escape").symlink_to(self.workspace.parent)
        for command, cwd in (
            ("cat escape/private.md", str(self.workspace)),
            ("pwd", str(self.workspace.parent)),
        ):
            result = self.normalize(self.command(command, cwd=cwd) + end_events())
            self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))

    def test_failed_commands_and_patches_cannot_be_neutral(self):
        for events in (
            self.command("ls -la", exitCode=1),
            self.command("cat spec.md", status="failed", exitCode=1),
            self.change(status="failed"),
        ):
            result = self.normalize(events + end_events())
            self.assertEqual(1, len(result["events"]))
            self.assertTrue(any(i["kind"] == "fidelity" for i in result["issues"]))

    def test_unknown_items_and_missing_lifecycle_are_not_dropped(self):
        events = lifecycle({"id": "mcp", "type": "mcpToolCall", "status": "completed"})
        result = self.normalize(events + end_events())
        self.assertEqual("mcpToolCall", result["events"][0]["raw_item_type"])
        for events in (self.command("pwd")[1:], self.command("cat spec.md")[:1]):
            result = self.normalize(events + end_events())
            self.assertFalse(result["instrumentation_valid"])
        result = self.normalize(self.command("cat spec.md")[:1] + end_events())
        self.assertEqual("incomplete", result["events"][0]["status"])

    def test_duplicate_lifecycle_and_malformed_fields_are_instrumentation_defects(self):
        command = self.command("cat spec.md")
        cases = [
            command + [command[1]],
            [command[0]] + command,
            [event("item/completed", item={})],
            self.command("pwd", exitCode=False),
            self.command("pwd", commandActions=None),
        ]
        for events in cases:
            with self.subTest(events=events):
                self.assertFalse(
                    self.normalize(events + end_events())["instrumentation_valid"]
                )

    def test_missing_and_malformed_usage_model_reroute_and_failure_are_separate(self):
        for value in (None, True, -1, 1.5):
            events = end_events()
            events[0]["params"]["tokenUsage"]["total"]["inputTokens"] = value
            self.assertFalse(self.normalize(events)["instrumentation_valid"])
        self.assertFalse(self.normalize(end_events()[1:])["instrumentation_valid"])
        self.assertFalse(
            self.normalize([event("model/rerouted", toModel="other")] + end_events())[
                "instrumentation_valid"
            ]
        )
        events = end_events()
        events[-1]["params"]["turn"]["status"] = "failed"
        result = self.normalize(events)
        self.assertTrue(result["instrumentation_valid"])
        self.assertFalse(result["completed"])
        self.assertEqual("fidelity", result["issues"][0]["kind"])

    def test_partial_output_and_missing_rpc_ids_survive_instrumentation_failure(self):
        events = [
            event("turn/started", turn={"id": "turn"}),
            event("item/agentMessage/delta", itemId="answer", delta="Partial "),
            event("item/agentMessage/delta", itemId="answer", delta="answer"),
        ]
        result = self.normalize(events, thread_id=None, turn_id=None)
        self.assertFalse(result["instrumentation_valid"])
        self.assertEqual("Partial answer", result["output"])
        self.assertEqual("thread", result["thread_id"])
        self.assertFalse(result["completed"])

    def test_overlapping_hook_and_setup_fail_even_with_right_completion_order(self):
        pre = self.command(
            "python3 .pilot/marker_hook.py pilot-pre-marker", identifier="pre"
        )
        setup = self.command(SETUP_COMMAND, identifier="setup")
        result = self.normalize([pre[0], setup[0], pre[1], setup[1]] + end_events())
        self.assertTrue(result["instrumentation_valid"])
        self.assertEqual(
            ["hook", "setup", "unknown"], [e["type"] for e in result["events"]]
        )
        self.assertTrue(any("overlap" in i["detail"] for i in result["issues"]))

    def test_safe_directory_discovery_retains_audit_not_fake_reads(self):
        result = self.normalize(
            self.command("pwd && ls -la .specify && ls specs") + end_events()
        )
        self.assertEqual([], result["events"])
        self.assertEqual(3, len(result["diagnostics"]))
        self.assertEqual([], result["issues"])

    def test_thread_scoped_reroute_and_error_invalidate_model_evidence(self):
        for method in ("model/rerouted", "error"):
            notification = {"method": method, "params": {"threadId": "thread"}}
            result = self.normalize([notification] + end_events())
            self.assertFalse(result["instrumentation_valid"])
            self.assertEqual("instrumentation", result["issues"][0]["kind"])

    def test_user_shell_and_stdin_interactions_are_not_attributed_to_agent(self):
        for source in ("userShell", "unifiedExecInteraction", "future"):
            result = self.normalize(
                self.command("cat spec.md", source=source) + end_events()
            )
            self.assertEqual("unknown", result["events"][0]["type"])
            self.assertEqual(source, result["events"][0]["command_source"])
            self.assertTrue(result["instrumentation_valid"])


if __name__ == "__main__":
    unittest.main()
