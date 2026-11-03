from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from harnessmith.native_contract import (
    integrity_findings, parse_trajectory, trajectory_schema, usage_totals,
)


def counters(input_tokens=10, cached_input_tokens=2, output_tokens=3):
    return dict(input_tokens=input_tokens, cached_input_tokens=cached_input_tokens,
                output_tokens=output_tokens, cache_write_input_tokens=0, reasoning_output_tokens=0)


def event(kind, event_id, data=None, turn_id=None, cause=None, thread_id="parent", origin="native"):
    return dict(event_id=event_id, sequence=0, elapsed_ms=0, thread_id=thread_id,
                turn_id=turn_id, causal_event_id=cause, origin=origin,
                raw_ref="raw.jsonl#" + event_id, kind=kind, data=data or {})


def permissions(event_id="permissions", thread_id="parent"):
    return event("permission.snapshot", event_id, dict(
        policy_id="isolated-v1", allow_read=["workspace"], allow_write=["workspace"],
        network=False, approval_policy="on-request"), thread_id=thread_id)


def usage(work_ids, interval_id="u1", thread_id="parent", **changes):
    result = dict(interval_id=interval_id, thread_id=thread_id, meter_id="meter-1",
                  counter_epoch="epoch-1", basis="delta", baseline_reason="request_delta",
                  work_ids=work_ids, raw_ref="usage.jsonl#" + interval_id,
                  normalization_ref="synthetic-normalization-v1", unavailable_reason=None, baseline=None, final=counters())
    result.update(changes)
    return result


def fixture():
    return dict(schema_version=1, trajectory_id="attempt-1", target="codex",
                surface="synthetic-app-server", host_version="test-only",
                mode="mock", capture_status="complete", capture_elapsed_ms=180000, events=[
                    event("thread.started", "thread"), permissions(),
                    event("turn.started", "start", {"turn_role": "task", "prompt_ref": "prompt.txt"}, "t1"),
                    event("turn.completed", "end", {"status": "completed"}, "t1", "start"),
                ], usage=[usage(["start"])])


def parsed(value):
    for index, item in enumerate(value["events"]):
        item["sequence"] = index
        item["elapsed_ms"] = index
    return parse_trajectory(value)


def codes(value):
    return {item.code for item in integrity_findings(parsed(value))}


class NativeContractTests(unittest.TestCase):
    def test_published_schema_is_generated_contract(self):
        path = Path(__file__).resolve().parents[1] / "schemas/native-trajectory-v1.schema.json"
        self.assertEqual(trajectory_schema(), json.loads(path.read_text()))

    def test_shape_is_strict_and_does_not_accept_old_scenario(self):
        for mutate in (
            lambda d: d.update(schema_version=True),
            lambda d: d.update(extra=True),
            lambda d: d["events"][0].update(kind="prompt"),
            lambda d: d["events"][0].update(kind=[]),
            lambda d: d["events"][0]["data"].update(unknown=True),
            lambda d: d["usage"][0]["final"].update(input_tokens=True),
            lambda d: d["events"][0].update(origin="narration"),
        ):
            value = fixture()
            mutate(value)
            with self.assertRaises(ValueError):
                parse_trajectory(value)

    def test_valid_synthetic_trajectory_and_usage(self):
        value = parsed(fixture())
        self.assertEqual((), integrity_findings(value))
        self.assertEqual(counters(), usage_totals(value))

    def test_declared_native_rejects_mock_or_controller_proof(self):
        for origin, code in (("mock", "mock-in-native"), ("controller", "native-evidence-missing")):
            value = fixture()
            value["mode"] = "native"
            value["events"][0]["origin"] = origin
            self.assertIn(code, codes(value))

    def test_duplicate_and_reordered_events_are_retained_with_findings(self):
        value = fixture()
        value["events"].append(copy.deepcopy(value["events"][0]))
        self.assertIn("event-order", codes(value))
        trace = parsed(fixture())
        from dataclasses import replace
        trace = replace(trace, events=tuple(reversed(trace.events)))
        self.assertIn("causal-reference", {f.code for f in integrity_findings(trace)})

    def approval_fixture(self, decision="grant"):
        value = fixture()
        value["events"][3:3] = [
            event("action.proposed", "proposed", dict(action_id="a1", operation="write",
                  input_ref="command.txt"), "t1"),
            event("approval.requested", "request", dict(approval_id="approval-1", action_id="a1"), "t1"),
            event("approval.decided", "decision", dict(approval_id="approval-1", decision=decision), "t1", "request"),
            event("action.started", "execute", dict(action_id="a1", approval_id="approval-1",
                  operation="write", path="workspace/allowed.txt", input_ref="command.txt",
                  dispatch="tool"), "t1", "decision"),
            event("action.completed", "result", dict(action_id="a1", status="succeeded",
                  exit_code=0, output_ref="stdout.txt"), "t1", "execute"),
        ]
        return value

    def test_grant_correlation_and_pending_item_not_execution(self):
        self.assertEqual(set(), codes(self.approval_fixture()))
        value = self.approval_fixture("deny")
        del value["events"][6:8]
        self.assertEqual(set(), codes(value))

    def test_action_before_or_after_denial_is_flagged(self):
        self.assertIn("unauthorized-action", codes(self.approval_fixture("deny")))
        missing_id = self.approval_fixture("deny")
        missing_id["events"][6]["data"]["approval_id"] = None
        self.assertIn("unauthorized-action", codes(missing_id))
        value = self.approval_fixture()
        value["events"][5], value["events"][6] = value["events"][6], value["events"][5]
        self.assertIn("unauthorized-action", codes(value))
        value = self.approval_fixture()
        value["events"][6]["data"]["action_id"] = "wrong-action"
        self.assertIn("unauthorized-action", codes(value))

    def test_later_approval_does_not_authorize_prior_unidentified_execution(self):
        for decision in ("grant", "deny"):
            with self.subTest(decision=decision):
                value = self.approval_fixture(decision)
                execution, result = value["events"][6:8]
                execution["data"]["approval_id"] = None
                execution["causal_event_id"] = "proposed"
                del value["events"][6:8]
                value["events"][4:4] = [execution, result]
                self.assertEqual({"unauthorized-action"}, codes(value))
                self.assertIsNone(usage_totals(parsed(value)))

    def test_action_cannot_start_on_disconnected_thread(self):
        value = self.approval_fixture()
        value["events"].insert(6, event("thread.disconnected", "disconnect",
            {"process_id": "process-1"}, "t1", "decision"))
        self.assertIn("resume-boundary", codes(value))
        self.assertIsNone(usage_totals(parsed(value)))

    def test_abort_and_missing_action_output(self):
        value = self.approval_fixture()
        value["events"][6:6] = [
            event("interrupt.requested", "abort", {"request_id": "stop-1"}, "t1"),
            event("interrupt.completed", "cancelled", dict(request_id="stop-1", status="cancelled"), "t1", "abort"),
        ]
        self.assertIn("action-after-abort", codes(value))
        value = self.approval_fixture()
        value["events"][-2]["data"]["output_ref"] = None
        self.assertIn("action-output-missing", codes(value))

    def test_interrupt_identity_cannot_be_reused_after_acknowledgment(self):
        value = fixture()
        value["events"][3:3] = [
            event("interrupt.requested", "abort-1", {"request_id": "stop-1"}, "t1"),
            event("interrupt.completed", "ack-1", dict(request_id="stop-1", status="cancelled"), "t1", "abort-1"),
            event("interrupt.requested", "abort-2", {"request_id": "stop-1"}, "t1"),
            event("interrupt.completed", "ack-2", dict(request_id="stop-1", status="cancelled"), "t1", "abort-2"),
        ]
        self.assertIn("interrupt-lifecycle", codes(value))
        self.assertIsNone(usage_totals(parsed(value)))

    def test_contradictory_nonzero_success_cannot_prove_read(self):
        for exit_code, expected in ((17, {"action-status", "read-attribution"}), (None, set())):
            with self.subTest(exit_code=exit_code):
                value = self.approval_fixture()
                value["events"][-2]["data"]["exit_code"] = exit_code
                value["events"].insert(-1, event("read.observed", "read", dict(
                    action_id="a1", path="workspace/allowed.txt", blob_sha256="a" * 64,
                    byte_start=0, byte_end=5, complete=True, category="target"), "t1", "result"))
                self.assertEqual(expected, codes(value))
                if expected:
                    self.assertIsNone(usage_totals(parsed(value)))

    def test_nonzero_exit_is_observation_not_automatic_integrity_failure(self):
        value = self.approval_fixture()
        value["events"][-2]["data"].update(status="failed", exit_code=19)
        self.assertEqual(set(), codes(value))

    def test_resume_requires_disconnect_new_process_and_permissions(self):
        value = fixture()
        value["events"] += [
            event("thread.disconnected", "disconnect", {"process_id": "p1"}, cause="end"),
            event("thread.resumed", "resume", dict(previous_process_id="p1", process_id="p2"), cause="disconnect"),
            permissions("permissions-2"),
            event("turn.started", "start-2", {"turn_role": "task", "prompt_ref": "next.txt"}, "t2"),
            event("turn.completed", "end-2", {"status": "completed"}, "t2", "start-2"),
        ]
        value["usage"].append(usage(["start-2"], "u2"))
        self.assertEqual(set(), codes(value))
        value["events"][5]["data"]["process_id"] = "p1"
        self.assertIn("resume-boundary", codes(value))
        del value["events"][6]
        self.assertIn("permission-missing", codes(value))

    def test_fork_lineage_and_inherited_usage_not_double_counted(self):
        value = fixture()
        value["events"] += [
            event("thread.forked", "fork", dict(parent_thread_id="parent", parent_event_id="end"), cause="end", thread_id="child"),
            permissions("child-permissions", "child"),
            event("turn.started", "child-start", {"turn_role": "task", "prompt_ref": "child.txt"}, "c1", thread_id="child"),
            event("turn.completed", "child-end", {"status": "completed"}, "c1", "child-start", "child"),
        ]
        value["usage"].append(usage(["child-start"], "child-usage", "child", basis="cumulative",
            baseline_reason="inherited", baseline=counters(), final=counters(16, 3, 8)))
        self.assertEqual(set(), codes(value))
        self.assertEqual(counters(16, 3, 8), usage_totals(parsed(value)))
        value["events"][4]["data"]["parent_thread_id"] = "other"
        self.assertIn("fork-lineage", codes(value))

    def test_compaction_requires_native_boundary_and_own_usage_coverage(self):
        value = fixture()
        value["events"] += [
            event("compaction.started", "compact-start", dict(compaction_id="c1", trigger="explicit")),
            event("compaction.completed", "compact-end", {"compaction_id": "c1"}, cause="compact-start"),
        ]
        self.assertIn("usage-coverage", codes(value))
        value["usage"].append(usage(["compact-start"], "compaction-usage"))
        self.assertEqual(set(), codes(value))
        self.assertEqual(counters(20, 4, 6), usage_totals(parsed(value)))
        value["events"][-1]["data"]["compaction_id"] = "invented"
        self.assertIn("compaction-lifecycle", codes(value))

    def test_internal_compaction_turn_is_separate_from_task_turns(self):
        value = fixture()
        value["events"] += [
            event("turn.started", "control-start", {"turn_role": "control", "prompt_ref": None}, "control-1"),
            event("compaction.started", "compact-start", dict(compaction_id="c1", trigger="explicit"), "control-1"),
            event("compaction.completed", "compact-end", {"compaction_id": "c1"}, "control-1", "compact-start"),
            event("turn.completed", "control-end", {"status": "completed"}, "control-1", "control-start"),
        ]
        value["usage"].append(usage(["control-start", "compact-start"], "compaction-inclusive"))
        self.assertEqual(set(), codes(value))
        self.assertEqual(counters(20, 4, 6), usage_totals(parsed(value)))
        value["events"][4]["data"]["prompt_ref"] = "invented-user-prompt.txt"
        with self.assertRaises(ValueError):
            parsed(value)

    def test_permission_widening_and_interrupted_capture(self):
        value = fixture()
        extra = permissions("changed")
        extra["data"]["network"] = True
        value["events"].append(extra)
        self.assertIn("permission-transition", codes(value))
        value = fixture()
        value["capture_status"] = "interrupted"
        self.assertIn("capture-incomplete", codes(value))
        self.assertIsNone(usage_totals(parsed(value)))

    def test_missing_reset_overlapping_and_unavailable_usage_never_zero(self):
        variants = []
        missing = fixture()
        missing["usage"] = []
        variants.append((missing, "usage-coverage"))
        unavailable = fixture()
        unavailable["usage"][0].update(final=None, unavailable_reason="host did not report")
        variants.append((unavailable, "usage-unavailable"))
        overlap = fixture()
        overlap["usage"].append(usage(["start"], "u2"))
        variants.append((overlap, "usage-overlap"))
        reset = fixture()
        reset["usage"][0].update(basis="cumulative", baseline_reason="inherited", baseline=counters(20, 4, 6))
        variants.append((reset, "usage-reset"))
        for value, code in variants:
            with self.subTest(code=code):
                self.assertIn(code, codes(value))
                self.assertIsNone(usage_totals(parsed(value)))

    def test_empty_capture_cannot_claim_measured_zero_usage(self):
        value = fixture()
        value.update(events=[], usage=[])
        self.assertIn("work-missing", codes(value))
        self.assertIsNone(usage_totals(parsed(value)))

    def test_unknown_cache_write_usage_is_not_assumed_zero(self):
        value = fixture()
        value["usage"][0]["final"]["cache_write_input_tokens"] = None
        self.assertIn("usage-unavailable", codes(value))
        self.assertIsNone(usage_totals(parsed(value)))

    def test_event_time_cannot_exceed_capture_duration(self):
        value = fixture()
        value["capture_elapsed_ms"] = 1
        self.assertIn("event-time", codes(value))

    def test_successful_counter_reset_uses_a_new_epoch_and_zero_baseline(self):
        value = fixture()
        value["usage"][0].update(basis="cumulative", baseline_reason="reset", baseline=counters(0, 0, 0), counter_epoch="restart-2")
        self.assertEqual(set(), codes(value))

    def test_counter_reset_requires_new_epoch_and_preserves_prior_usage(self):
        value = fixture()
        value["usage"][0].update(basis="cumulative", baseline_reason="fresh", baseline=counters(0, 0, 0))
        value["events"] += [
            event("turn.started", "start-2", {"turn_role": "task", "prompt_ref": "next.txt"}, "t2"),
            event("turn.completed", "end-2", {"status": "completed"}, "t2", "start-2"),
        ]
        value["usage"].append(usage(["start-2"], "u2", basis="cumulative", baseline_reason="reset",
            baseline=counters(0, 0, 0), final=counters(6, 1, 2), counter_epoch="epoch-2"))
        self.assertEqual(set(), codes(value))
        self.assertEqual(counters(16, 3, 5), usage_totals(parsed(value)))
        value["usage"][1]["counter_epoch"] = "epoch-1"
        self.assertIn("usage-baseline", codes(value))

    def test_action_after_compaction_requires_refreshed_permissions(self):
        value = self.approval_fixture()
        value["events"][6:6] = [
            event("compaction.started", "compact-start", dict(compaction_id="c1", trigger="automatic"), "t1"),
            event("compaction.completed", "compact-end", {"compaction_id": "c1"}, "t1", "compact-start"),
        ]
        value["usage"][0]["work_ids"].append("compact-start")
        self.assertIn("permission-missing", codes(value))
        snapshot = permissions("refreshed")
        snapshot["turn_id"] = "t1"
        value["events"].insert(8, snapshot)
        self.assertEqual(set(), codes(value))

    def test_read_requires_completed_action_and_exact_blob_identity(self):
        value = self.approval_fixture()
        read = event("read.observed", "read", dict(action_id="a1", path="workspace/allowed.txt",
                     blob_sha256="a" * 64, byte_start=0, byte_end=5, complete=True, category="target"), "t1", "result")
        value["events"].insert(-1, read)
        self.assertEqual(set(), codes(value))
        value["events"][-3]["data"].update(status="failed", exit_code=1)
        self.assertIn("read-attribution", codes(value))
        read["data"]["action_id"] = "unknown"
        self.assertIn("read-attribution", codes(value))
        read["data"]["blob_sha256"] = "not-a-hash"
        with self.assertRaises(ValueError):
            parsed(value)


if __name__ == "__main__":
    unittest.main()
