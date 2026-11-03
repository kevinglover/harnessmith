"""Additive native trajectory contract; never a live collector or behavior grade.

Bad observations remain parseable. Integrity findings and unavailable usage are
reported separately so callers can retain the original attempt before stopping.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Mapping, Optional, Tuple

SCHEMA_VERSION = 1
TEXT = {"type": "string", "minLength": 1, "pattern": r"\S"}
NULLABLE_TEXT = {"type": ["string", "null"], "minLength": 1, "pattern": r"\S"}
STRINGS = {"type": "array", "items": TEXT, "uniqueItems": True}
NATURAL = {"type": "integer", "minimum": 0}


def _enum(*values: str) -> dict:
    return {"enum": list(values)}


EVENT_FIELDS = {
    "thread.started": {},
    "thread.disconnected": {"process_id": TEXT},
    "thread.resumed": {"previous_process_id": TEXT, "process_id": TEXT},
    "thread.forked": {"parent_thread_id": TEXT, "parent_event_id": TEXT},
    "turn.started": {"turn_role": _enum("task", "control"), "prompt_ref": NULLABLE_TEXT},
    "turn.completed": {"status": _enum("completed", "failed", "interrupted")},
    "approval.requested": {"approval_id": TEXT, "action_id": TEXT},
    "approval.decided": {"approval_id": TEXT, "decision": _enum("grant", "deny")},
    "action.proposed": {"action_id": TEXT, "operation": TEXT, "input_ref": TEXT},
    "action.started": {
        "action_id": TEXT, "approval_id": NULLABLE_TEXT,
        "operation": TEXT, "path": NULLABLE_TEXT, "input_ref": TEXT,
        "dispatch": _enum("tool", "skill_command", "host_hook", "boundary_probe"),
    },
    "action.completed": {
        "action_id": TEXT, "status": _enum("succeeded", "failed", "cancelled"),
        "exit_code": {"type": ["integer", "null"]}, "output_ref": NULLABLE_TEXT,
    },
    "interrupt.requested": {"request_id": TEXT},
    "interrupt.completed": {
        "request_id": TEXT, "status": _enum("cancelled", "already_complete"),
    },
    "compaction.started": {
        "compaction_id": TEXT, "trigger": _enum("explicit", "idle", "automatic"),
    },
    "compaction.completed": {"compaction_id": TEXT},
    "permission.snapshot": {
        "policy_id": TEXT, "allow_read": STRINGS, "allow_write": STRINGS,
        "network": {"type": "boolean"}, "approval_policy": TEXT,
    },
    "invocation.observed": {
        "skill_id": TEXT, "package_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "channel": _enum("explicit", "implicit", "abstained"),
        "evidence_ref": TEXT,
    },
    "output.recorded": {"output_ref": TEXT},
    "discovery.snapshot": {
        "catalog_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "evidence_ref": TEXT, "complete": {"type": "boolean"},
    },
    "read.observed": {
        "action_id": TEXT, "path": TEXT,
        "blob_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "byte_start": NATURAL, "byte_end": NATURAL, "complete": {"type": "boolean"},
        "category": _enum("package_reference", "project_context", "target", "other"),
    },
}
EVENT_ENVELOPE = {
    "event_id": TEXT, "sequence": NATURAL, "elapsed_ms": NATURAL, "thread_id": TEXT,
    "turn_id": NULLABLE_TEXT, "causal_event_id": NULLABLE_TEXT,
    "origin": _enum("native", "controller", "mock"), "raw_ref": TEXT,
}
COUNTER_FIELDS = {key: {"type": ["integer", "null"], "minimum": 0} for key in (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
)}
USAGE_FIELDS = {
    "interval_id": TEXT, "thread_id": TEXT, "meter_id": TEXT,
    "counter_epoch": TEXT, "basis": _enum("delta", "cumulative"),
    "baseline_reason": _enum("request_delta", "fresh", "inherited", "reset", "continuation"),
    "work_ids": {"type": "array", "items": TEXT, "minItems": 1, "uniqueItems": True},
    "raw_ref": TEXT, "normalization_ref": TEXT, "unavailable_reason": NULLABLE_TEXT,
}


def _object(properties: dict) -> dict:
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def trajectory_schema() -> dict:
    """Return the published structural schema (cross-record rules are separate)."""
    counters = _object(COUNTER_FIELDS)
    usage = _object({**USAGE_FIELDS,
                     "baseline": {"oneOf": [counters, {"type": "null"}]},
                     "final": {"oneOf": [counters, {"type": "null"}]}})
    events = [_object({**EVENT_ENVELOPE, "kind": {"const": kind},
                       "data": _object(fields)})
              for kind, fields in EVENT_FIELDS.items()]
    for definition in events:
        if definition["properties"]["kind"].get("const") == "turn.started":
            definition["properties"]["data"]["oneOf"] = [
                {"properties": {"turn_role": {"const": "task"}, "prompt_ref": TEXT}},
                {"properties": {"turn_role": {"const": "control"}, "prompt_ref": {"type": "null"}}},
            ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://harnessmith.dev/schemas/native-trajectory-v1.schema.json",
        "title": "Native trajectory v1 (prospective; not runtime qualification)",
        **_object({
            "schema_version": {"type": "integer", "const": SCHEMA_VERSION},
            "trajectory_id": TEXT, "target": _enum("generic", "codex", "claude", "cursor"),
            "surface": TEXT, "host_version": TEXT, "mode": _enum("native", "mock"),
            "capture_status": _enum("complete", "interrupted", "incomplete"),
            "capture_elapsed_ms": NATURAL,
            "events": {"type": "array", "items": {"oneOf": events}},
            "usage": {"type": "array", "items": usage},
        }),
    }


def _fields(value: object, fields: Mapping[str, dict], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(label + ": missing or unknown fields")
    for name, spec in fields.items():
        item = value[name]
        if "const" in spec and (type(item) is not type(spec["const"]) or item != spec["const"]):
            raise ValueError(label + "." + name + ": wrong constant")
        if "enum" in spec and item not in spec["enum"]:
            raise ValueError(label + "." + name + ": unknown value")
        types = spec.get("type", [])
        types = [types] if isinstance(types, str) else types
        if item is None and "null" in types:
            continue
        valid = not types
        if "string" in types:
            valid = (isinstance(item, str) and bool(item.strip())
                     and re.search(spec.get("pattern", r"\S"), item) is not None)
        if "integer" in types:
            valid = type(item) is int and item >= spec.get("minimum", item)
        if "boolean" in types:
            valid = type(item) is bool
        if "array" in types:
            valid = (isinstance(item, list)
                     and all(isinstance(s, str) and s.strip() for s in item)
                     and len(item) == len(set(item))
                     and len(item) >= spec.get("minItems", 0))
        if not valid:
            raise ValueError(label + "." + name + ": invalid type/value")
    return value


@dataclass(frozen=True)
class NativeEvent:
    event_id: str
    sequence: int
    elapsed_ms: int
    thread_id: str
    turn_id: Optional[str]
    causal_event_id: Optional[str]
    origin: str
    raw_ref: str
    kind: str
    data: Mapping[str, Any]


@dataclass(frozen=True)
class UsageInterval:
    interval_id: str
    thread_id: str
    meter_id: str
    counter_epoch: str
    basis: str
    baseline_reason: str
    work_ids: Tuple[str, ...]
    raw_ref: str
    normalization_ref: str
    unavailable_reason: Optional[str]
    baseline: Optional[Mapping[str, Optional[int]]]
    final: Optional[Mapping[str, Optional[int]]]


@dataclass(frozen=True)
class NativeTrajectory:
    trajectory_id: str
    target: str
    surface: str
    host_version: str
    mode: str
    capture_status: str
    capture_elapsed_ms: int
    events: Tuple[NativeEvent, ...]
    usage: Tuple[UsageInterval, ...]
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class IntegrityFinding:
    code: str
    record_id: str
    reason: str


def parse_trajectory(value: object) -> NativeTrajectory:
    """Parse shape only. Call integrity_findings before using any measurements."""
    fields = trajectory_schema()["properties"]
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError("trajectory: missing or unknown fields")
    _fields({k: v for k, v in value.items() if k not in ("events", "usage")},
            {k: v for k, v in fields.items() if k not in ("events", "usage")}, "trajectory")
    events = []
    usage = []
    for key in ("events", "usage"):
        if not isinstance(value[key], list):
            raise ValueError(key + " must be an array")
    for item in value["events"]:
        if (not isinstance(item, dict) or not isinstance(item.get("kind"), str)
                or item["kind"] not in EVENT_FIELDS):
            raise ValueError("unknown native event kind")
        kind = item["kind"]
        _fields(item, {**EVENT_ENVELOPE, "kind": {"const": kind}, "data": {}}, "event")
        data = _fields(item["data"], EVENT_FIELDS[kind], kind)
        if kind == "turn.started" and ((data["turn_role"] == "task") != (data["prompt_ref"] is not None)):
            raise ValueError("task turns require prompt_ref; control turns require null prompt_ref")
        events.append(NativeEvent(**{**item, "data": dict(data)}))
    for item in value["usage"]:
        _fields(item, {**USAGE_FIELDS, "baseline": {}, "final": {}}, "usage")
        for counter in ("baseline", "final"):
            if item[counter] is not None:
                _fields(item[counter], COUNTER_FIELDS, counter)
        usage.append(UsageInterval(**{**item, "work_ids": tuple(item["work_ids"]),
                    "baseline": None if item["baseline"] is None else dict(item["baseline"]),
                    "final": None if item["final"] is None else dict(item["final"])}))
    return NativeTrajectory(**{**value, "events": tuple(events), "usage": tuple(usage)})


def integrity_findings(trajectory: NativeTrajectory) -> Tuple[IntegrityFinding, ...]:
    """Check causal integrity; findings do not discard or regrade observations."""
    findings = []

    def flag(code: str, record: str, reason: str) -> None:
        findings.append(IntegrityFinding(code, record, reason))

    seen: Dict[str, NativeEvent] = {}
    threads = set()
    disconnected = {}
    turns = {}
    active = {}
    approvals = {}
    decisions = {}
    actions = {}
    completed_actions = set()
    action_results = {}
    interrupts = {}
    interrupt_ids = set()
    stopped = set()
    compactions = {}
    completed_compactions = set()
    permissions = {}
    permission_refresh = set()
    previous_sequence = -1
    previous_elapsed = -1
    for event in trajectory.events:
        kind, data, eid, tid = event.kind, event.data, event.event_id, event.thread_id
        if eid in seen or event.sequence <= previous_sequence:
            flag("event-order", eid, "duplicate ID or non-increasing sequence")
        previous_sequence = event.sequence
        if event.elapsed_ms < previous_elapsed or event.elapsed_ms > trajectory.capture_elapsed_ms:
            flag("event-time", eid, "event timestamp is reordered or outside capture duration")
        previous_elapsed = event.elapsed_ms
        cause = seen.get(event.causal_event_id or "")
        if event.causal_event_id is not None and cause is None:
            flag("causal-reference", eid, "cause is absent or not earlier")
        if trajectory.mode == "native" and event.origin == "mock":
            flag("mock-in-native", eid, "mock evidence cannot establish a native boundary")
        if kind in ("thread.started", "thread.forked"):
            if tid in threads:
                flag("thread-identity", eid, "thread already exists")
            if kind == "thread.forked":
                parent = seen.get(str(data["parent_event_id"]))
                if (data["parent_thread_id"] not in threads or parent is None
                        or parent.thread_id != data["parent_thread_id"]
                        or event.causal_event_id != data["parent_event_id"]):
                    flag("fork-lineage", eid, "fork does not identify an earlier parent event")
                if data["parent_thread_id"] in permissions:
                    permissions[tid] = permissions[data["parent_thread_id"]]
            threads.add(tid)
            permission_refresh.add(tid)
        elif tid not in threads:
            flag("thread-identity", eid, "event refers to an unstarted thread")
        if kind == "thread.disconnected":
            disconnected[tid] = event
        elif kind == "thread.resumed":
            permission_refresh.add(tid)
            old = disconnected.pop(tid, None)
            if (old is None or cause != old
                    or old.data["process_id"] != data["previous_process_id"]
                    or data["previous_process_id"] == data["process_id"]):
                flag("resume-boundary", eid, "resume lacks correlated disconnect and new process")
        if kind == "turn.started":
            if tid in disconnected:
                flag("resume-boundary", eid, "work started before native resume")
            if event.turn_id is None or event.turn_id in turns or tid in active:
                flag("turn-lifecycle", eid, "missing/duplicate turn or overlapping active turn")
            if tid not in permissions or tid in permission_refresh:
                flag("permission-missing", eid, "effective permissions absent before work")
            turns[event.turn_id] = event
            active[tid] = event.turn_id
        elif kind == "turn.completed":
            if event.turn_id is None or active.get(tid) != event.turn_id:
                flag("turn-lifecycle", eid, "completion has no matching active turn")
            if cause != turns.get(event.turn_id):
                flag("turn-lifecycle", eid, "completion lacks its causal turn start")
            active.pop(tid, None)
        elif event.turn_id is not None and active.get(tid) != event.turn_id:
            flag("turn-lifecycle", eid, "event is outside its active turn")
        if kind == "permission.snapshot":
            old = permissions.get(tid)
            if old is not None and (
                not set(data["allow_read"]).issubset(old["allow_read"])
                or not set(data["allow_write"]).issubset(old["allow_write"])
                or (data["network"] and not old["network"])
                or data["approval_policy"] != old["approval_policy"]
            ):
                flag("permission-transition", eid, "permission widening or changed approval policy")
            permissions[tid] = data
            permission_refresh.discard(tid)
        if kind == "read.observed":
            action = actions.get(str(data["action_id"]))
            if (action is None or data["action_id"] not in completed_actions
                    or action.thread_id != tid or action.turn_id != event.turn_id
                    or action_results.get(str(data["action_id"]), {}).get("status") != "succeeded"
                    or action_results.get(str(data["action_id"]), {}).get("exit_code") not in (None, 0)
                    or event.causal_event_id != action_results.get(str(data["action_id"]), {}).get("event_id")
                    or data["byte_end"] < data["byte_start"]):
                flag("read-attribution", eid, "read lacks completed action or valid byte range")
        if kind == "approval.requested":
            if str(data["action_id"]) in actions:
                flag("unauthorized-action", eid, "approval was requested after its action had already started")
            aid = str(data["approval_id"])
            if aid in approvals:
                flag("approval-identity", eid, "duplicate approval ID")
            approvals[aid] = event
        elif kind == "approval.decided":
            aid = str(data["approval_id"])
            request = approvals.get(aid)
            if (request is None or cause != request or request.thread_id != tid
                    or request.turn_id != event.turn_id or aid in decisions):
                flag("approval-causality", eid, "decision lacks a unique correlated request")
            decisions[aid] = event
        elif kind == "action.started":
            if tid in disconnected:
                flag("resume-boundary", eid, "action started while its thread was disconnected")
            if event.turn_id is None and data["dispatch"] != "boundary_probe":
                flag("turn-lifecycle", eid, "task execution requires a turn identity")
            action = str(data["action_id"])
            if action in actions:
                flag("action-identity", eid, "duplicate action ID")
            if tid not in permissions or tid in permission_refresh:
                flag("permission-missing", eid, "effective permissions must be refreshed before action")
            if event.turn_id in stopped:
                flag("action-after-abort", eid, "action began after cancellation request")
            aid = data["approval_id"]
            matching_requests = [request for request in approvals.values()
                                 if request.data["action_id"] == action]
            if aid is None and matching_requests:
                flag("unauthorized-action", eid, "action omitted its pending/decided approval identity")
            if aid is not None:
                request, decision = approvals.get(str(aid)), decisions.get(str(aid))
                if (request is None or decision is None or cause != decision
                        or request.data["action_id"] != action or request.thread_id != tid
                        or request.turn_id != event.turn_id
                        or decision.data["decision"] != "grant"):
                    flag("unauthorized-action", eid, "action lacks its earlier native grant")
            actions[action] = event
        elif kind == "action.completed":
            action = str(data["action_id"])
            start = actions.get(action)
            if (start is None or cause != start or start.thread_id != tid
                    or start.turn_id != event.turn_id or action in completed_actions):
                flag("action-lifecycle", eid, "completion lacks one matching action start")
            completed_actions.add(action)
            action_results[action] = {**data, "event_id": eid}
            if data["status"] == "succeeded" and data["exit_code"] not in (None, 0):
                flag("action-status", eid, "successful completion contradicts its nonzero exit code")
            if data["output_ref"] is None:
                flag("action-output-missing", eid, "null output retained; no read/execution proof inferred")
        elif kind == "interrupt.requested":
            rid = str(data["request_id"])
            if rid in interrupt_ids or event.turn_id is None:
                flag("interrupt-lifecycle", eid, "duplicate interrupt or absent turn")
            interrupt_ids.add(rid)
            interrupts[rid] = event
            stopped.add(event.turn_id)
        elif kind == "interrupt.completed":
            request = interrupts.pop(str(data["request_id"]), None)
            if request is None or cause != request or request.turn_id != event.turn_id:
                flag("interrupt-lifecycle", eid, "acknowledgment lacks matching interrupt request")
        elif kind == "compaction.started":
            cid = str(data["compaction_id"])
            if cid in compactions:
                flag("compaction-lifecycle", eid, "duplicate compaction ID")
            compactions[cid] = event
        elif kind == "compaction.completed":
            cid = str(data["compaction_id"])
            start = compactions.get(cid)
            if start is None or cause != start or start.thread_id != tid or cid in completed_compactions:
                flag("compaction-lifecycle", eid, "completion lacks one matching native compaction")
            completed_compactions.add(cid)
            permission_refresh.add(tid)
        if (trajectory.mode == "native" and event.origin == "controller"
                and kind not in ("thread.disconnected", "interrupt.requested")):
            flag("native-evidence-missing", eid, "controller narration cannot prove this native event")
        seen[eid] = event
    if trajectory.target == "generic" and trajectory.mode != "mock":
        flag("offline-target", trajectory.trajectory_id, "generic is an offline contract target")
    if trajectory.capture_status != "complete":
        flag("capture-incomplete", trajectory.trajectory_id, trajectory.capture_status)
    if (active or set(actions) - completed_actions or set(compactions) - completed_compactions
            or interrupts or set(approvals) - set(decisions)):
        flag("lifecycle-incomplete", trajectory.trajectory_id, "unclosed turn/action/compaction/interrupt/approval")
    required_work = {e.event_id for e in trajectory.events if e.kind in ("turn.started", "compaction.started")}
    if not required_work:
        flag("work-missing", trajectory.trajectory_id, "trajectory contains no task turn or compaction")
    covered = set()
    intervals = set()
    meters = {}
    for interval in trajectory.usage:
        iid = interval.interval_id
        if iid in intervals:
            flag("usage-identity", iid, "duplicate usage interval")
        intervals.add(iid)
        if covered.intersection(interval.work_ids):
            flag("usage-overlap", iid, "work counted in multiple intervals")
        for work in interval.work_ids:
            event = seen.get(work)
            if event is None or work not in required_work or event.thread_id != interval.thread_id:
                flag("usage-attribution", iid, "unknown work or wrong thread")
        covered.update(interval.work_ids)
        if (interval.final is None or interval.unavailable_reason is not None
                or any(value is None for value in interval.final.values())
                or (interval.baseline is not None and any(value is None for value in interval.baseline.values()))):
            flag("usage-unavailable", iid, interval.unavailable_reason or "missing counters")
            continue
        final = {k: int(v) for k, v in interval.final.items() if v is not None}
        baseline = None if interval.baseline is None else {k: int(v) for k, v in interval.baseline.items() if v is not None}
        if baseline is not None and baseline["cached_input_tokens"] + baseline["cache_write_input_tokens"] > baseline["input_tokens"]:
            flag("usage-counters", iid, "baseline cached input exceeds input")
        if final["cached_input_tokens"] + final["cache_write_input_tokens"] > final["input_tokens"]:
            flag("usage-counters", iid, "cache read/write input exceeds normalized input")
        if baseline is not None and baseline["reasoning_output_tokens"] > baseline["output_tokens"]:
            flag("usage-counters", iid, "baseline reasoning output exceeds output")
        if final["reasoning_output_tokens"] > final["output_tokens"]:
            flag("usage-counters", iid, "reasoning output exceeds normalized output")
        if interval.basis == "delta":
            if interval.baseline is not None or interval.baseline_reason != "request_delta":
                flag("usage-baseline", iid, "delta counters require null baseline and request_delta")
        else:
            key = (interval.thread_id, interval.meter_id, interval.counter_epoch)
            if baseline is None or interval.baseline_reason == "request_delta":
                flag("usage-baseline", iid, "cumulative counters require a documented baseline")
            elif any(final[k] < baseline[k] for k in COUNTER_FIELDS):
                flag("usage-reset", iid, "counter decreased within an epoch")
            elif key in meters and interval.baseline_reason in ("fresh", "reset", "inherited"):
                flag("usage-baseline", iid, "fresh/reset/inherited baselines require a new meter epoch")
            elif key in meters and baseline != meters[key]:
                flag("usage-baseline", iid, "cumulative intervals are not contiguous within epoch")
            elif interval.baseline_reason in ("fresh", "reset") and any(baseline.values()):
                flag("usage-baseline", iid, "fresh/reset counters must start at zero")
            if baseline is not None and final["cached_input_tokens"] + final["cache_write_input_tokens"] - baseline["cached_input_tokens"] - baseline["cache_write_input_tokens"] > final["input_tokens"] - baseline["input_tokens"]:
                flag("usage-counters", iid, "delta cached input exceeds input")
            if baseline is not None and final["reasoning_output_tokens"] - baseline["reasoning_output_tokens"] > final["output_tokens"] - baseline["output_tokens"]:
                flag("usage-counters", iid, "delta reasoning output exceeds output")
            meters[key] = final
    if covered != required_work:
        flag("usage-coverage", trajectory.trajectory_id, "every task turn and compaction needs attributable usage")
    return tuple(findings)


def usage_totals(trajectory: NativeTrajectory) -> Optional[Mapping[str, int]]:
    """Return totals only for intact, fully attributable records; unknown is None."""
    if integrity_findings(trajectory):
        return None
    totals = {key: 0 for key in COUNTER_FIELDS}
    for interval in trajectory.usage:
        assert interval.final is not None
        for key in totals:
            final = interval.final[key]
            baseline = interval.baseline[key] if interval.baseline is not None else 0
            assert final is not None and baseline is not None
            totals[key] += final - baseline
    return totals
