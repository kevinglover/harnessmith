"""Schema-9 proofs for a same-path conditional with guarded literal ABSENT.

Frozen v8 remains unchanged. Captured commands are data, never rewritten or
executed. New proofs require exact output and a complete sequential prefix.
The sole mutation allowance is a native target-only append followed by a
separate exact readback, and applies only to a later extension-absence probe.
"""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import re
import stat

from .workflow_trace_v3 import _absence_certificate, _literal_words, _pinned_bytes, _statements
from .workflow_trace_v4 import RUNTIME_FAILURE, _command_context, _declared_reads, _strict_path
from .workflow_trace_v5 import _read_fact
from .workflow_trace_v6 import CONFIG, READ_ONLY_DIAGNOSTICS, _certificate_shell_body
from .workflow_trace_v7 import PROVENANCE, UNPROVEN, _same_item
from .workflow_trace_v8 import (
    ERRORS, OVERLAP, _complete, _endpoints, _intrinsic, _inventory_pin,
    _repair_dependencies as _repair_v8_dependencies,
    _safe_prefix as _safe_v8_prefix,
    normalize_events as normalize_v8,
)

INSTRUMENTATION = "codex-workflow-trace-v9"
UNSUPPORTED = "unsupported operator in simple command"
DISCOVERY = "terminal discovery proof rejected: terminal discovery prefix contains mutation or uncertainty"


def _conditional(item, workspace, manifest, recorded):
    statements, connectors = _statements(_certificate_shell_body(item["command"]))
    if len(statements) != 1 or connectors:
        raise ValueError("guarded echo requires one standalone conditional")
    match = re.fullmatch(
        r"if\s+\[\s+-f\s+(.+?)\s+\]\s*;\s*then\s+(.+?)\s*;\s*else\s+(.+?)\s*;\s*fi",
        statements[0], re.S,
    )
    if match is None:
        raise ValueError("unsupported guarded-echo conditional")
    tested, yes = _literal_words("cat " + match[1])[1:], _literal_words(match[2])
    absent, separators = _statements(match[3])
    if len(absent) != 2 or separators != ["&&"]:
        raise ValueError("absence marker must be guarded by one successful test")
    no, marker = [_literal_words(part) for part in absent]
    if (len(tested) != 1 or len(yes) != 2 or yes[0] not in {"cat", "/bin/cat"}
            or yes[1] != tested[0] or no != ["test", "!", "-e", tested[0]]
            or marker != ["echo", "ABSENT"] or tested[0].startswith("-")
            or any(c in tested[0] for c in "\n\r\t\\")
            or any(p in {".", ".."} for p in tested[0].split("/"))):
        raise ValueError("both branches require the same literal path and guarded ABSENT")
    cwd = _command_context(item, workspace, recorded)
    path = _strict_path(tested[0], cwd, workspace, recorded)
    _declared_reads(item, {path}, cwd, workspace, recorded)
    output = item.get("aggregatedOutput")
    if path in manifest.get("pinned_absent_paths", []):
        if path != CONFIG or output != "ABSENT\n":
            raise ValueError("absence requires exact extension marker output")
        _absence_certificate(path, workspace, manifest, True)
        fact = {"type": "diagnostic", "path": path, "reason": "fixture absence",
                "certified_absence": True}
        field = "absence_certificate"
    else:
        data = _pinned_bytes(path, workspace, manifest)
        if (not data or not isinstance(output, str) or output != data.decode("utf-8")
                or RUNTIME_FAILURE.search(output)):
            raise ValueError("present branch requires exact nonempty pinned bytes")
        fact, field = _read_fact(path, data, "before"), "conditional_read_certificate"
    return [fact], field, {
        "proof": "literal-else-test-echo", "path": path,
        "output_representation": "text", "absence_marker": "ABSENT\n",
        "captured_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
    }


def _facts(result, item_id):
    return [fact for fact in result["events"] + result["diagnostics"]
            if fact.get("raw_item_id") == item_id]


def _native_append(pair, result, workspace, manifest, recorded, checkpoint):
    """Account for one known native update without granting arbitrary writes."""
    first, last = pair["item/started"], pair["item/completed"]
    a, b = first[1], last[1]
    changes = b.get("changes")
    if (a.get("type") != "fileChange" or b.get("type") != "fileChange"
            or a.get("status") != "inProgress" or b.get("status") != "completed"
            or a.get("changes") != changes or not isinstance(changes, list)
            or len(changes) != 1 or not isinstance(changes[0], dict)
            or set(changes[0]) != {"path", "kind", "diff"}
            or changes[0]["kind"] not in ({"type": "update"}, {"type": "update", "move_path": None})
            or not isinstance(changes[0]["diff"], str) or not changes[0]["diff"]):
        raise ValueError("post-append absence requires one matching native update")
    target = _strict_path(changes[0]["path"], workspace, workspace, recorded)
    if target != manifest.get("target") or target == CONFIG or CONFIG.startswith(target + "/"):
        raise ValueError("post-append update must touch only the prepared target")
    facts = _facts(result, b["id"])
    if (len(facts) != 1 or facts[0].get("type") != "write"
            or facts[0].get("path") != target or facts[0].get("status") != "completed"
            or facts[0].get("raw_start_index") != first[0]
            or facts[0].get("raw_completion_index") != last[0]
            or any(issue.get("raw_item_id") == b["id"] for issue in result["issues"])):
        raise ValueError("post-append update has unrelated failures or unknown effects")
    before = _pinned_bytes(target, workspace, manifest)
    after = (workspace / target).read_bytes()
    if not before or len(after) <= len(before) or not after.startswith(before):
        raise ValueError("post-append absence requires exact preserved prefix and new bytes")
    # Snapshot corroboration does not replace raw mutation accounting below.
    current = set()
    for directory, names, files in os.walk(workspace, followlinks=False):
        for name in names + files:
            path = Path(directory) / name
            relative = _strict_path(str(path), workspace, workspace, None)
            if not (path.is_file() or path.is_dir()):
                raise ValueError("post-append inventory contains an unsupported entry")
            if path.is_file():
                current.add(relative)
                mode = 0o755 if relative in manifest.get("executable_files", []) else 0o644
                if stat.S_IMODE(path.stat().st_mode) != mode:
                    raise ValueError("post-append inventory file mode changed")
                if relative != target:
                    _pinned_bytes(relative, workspace, manifest)
    if current != set(manifest["baseline"]):
        raise ValueError("post-append inventory differs from the pinned files")
    digest = hashlib.sha256(after).hexdigest()
    reads = [fact for fact in result["events"]
             if fact.get("type") == "read" and fact.get("path") == target
             and fact.get("status") == "completed" and fact.get("exit_code") == 0
             and fact.get("read_after_write") is True
             and fact.get("read_coverage", {}).get("complete") is True
             and fact.get("read_sha256") == digest
             and last[0] < fact.get("raw_start_index", -1)
             and fact.get("raw_completion_index", checkpoint) < checkpoint]
    if not reads:
        raise ValueError("post-append absence requires separate exact final readback")
    return {"raw_item_id": b["id"], "raw_start_index": first[0],
            "raw_completion_index": last[0], "target": target,
            "before_sha256": hashlib.sha256(before).hexdigest(), "after_sha256": digest,
            "before_bytes": len(before), "after_bytes": len(after),
            "readback_item_ids": [fact["raw_item_id"] for fact in reads]}


def _safe_prefix(record, candidate, pairs, records, result, workspace, manifest, recorded):
    start, end = record["raw_start_index"], record["raw_completion_index"]
    native: list[dict] = []
    for key, pair in pairs.items():
        before, after = pair.get("item/started"), pair.get("item/completed")
        if before is not None and before[0] > end and (after is None or after[0] > end):
            continue
        if (key[:2] != (result["thread_id"], result["turn_id"])
                or before is None or after is None or not before[0] < after[0]):
            raise ValueError("guarded-echo prefix has a foreign or incomplete lifecycle")
        if key[2] == record["raw_item_id"]:
            continue
        if after[0] >= start:
            raise ValueError("new conditional/discovery proof cannot overlap an operation")
        if before[1].get("type") == "fileChange":
            if candidate[1] != "absence_certificate" or native:
                raise ValueError("only a sole target append can precede extension absence")
            if any(
                other_key != key and other_pair.get("item/started") is not None
                and other_pair["item/started"][0] <= after[0]
                and (other_pair.get("item/completed") is None
                     or other_pair["item/completed"][0] >= before[0])
                for other_key, other_pair in pairs.items()
            ):
                raise ValueError("native append overlaps another operation")
            native.append(_native_append(pair, result, workspace, manifest, recorded, start))
            continue
        prior = records.get(key[2])
        if prior is None:
            raise ValueError("prefix contains an unknown operation")
        _complete(prior, pair, workspace, recorded)
        facts = _facts(result, key[2])
        if not facts or any(
            fact.get("status") != "completed" or fact.get("exit_code", 0) != 0
            or fact.get("type") not in {"read", "diagnostic", "setup"}
            or (fact.get("type") == "setup" and not fact.get("absence_preserving"))
            or (fact.get("type") == "diagnostic" and fact.get("reason") not in
                READ_ONLY_DIAGNOSTICS | {"corroborated synthetic adapter macOS cache warning"})
            or (fact.get("reason") == "fixture absence" and not fact.get("certified_absence"))
            for fact in facts
        ) or any(_same_item(issue, prior) for issue in result["issues"]):
            raise ValueError("prefix contains mutation, failure or uncertainty")
    return native


def _replace(record, candidate, result, manifest, native, overlap=()):
    facts = sorted(_facts(result, record["raw_item_id"]), key=lambda fact: fact["raw_operation_index"])
    issues = [issue for issue in result["issues"] if _same_item(issue, record)]
    operations, field, detail = candidate
    unknown = [fact for fact in facts if fact.get("type") == "unknown"]
    allowed = {DISCOVERY, UNPROVEN} if field == "terminal_discovery_certificate" else {
        OVERLAP} if field == "read_only_attribution_certificate" else {UNSUPPORTED}
    if len(unknown) != 1 or unknown[0].get("reason") not in allowed:
        return False
    expected = [unknown[0]["reason"]]
    if unknown[0].get("reason") == UNPROVEN and unknown[0].get("status") == "unverified":
        expected.append("failed or incomplete operation")
    if (unknown[0].get("status") not in {"completed", "unverified"}
            or type(unknown[0].get("exit_code")) is not int or unknown[0]["exit_code"] != 0
            or issues != [{"kind": "fidelity", "detail": detail,
                           **{key: record[key] for key in PROVENANCE}} for detail in expected]
            or len(facts) != len(operations)
            or any(fact.get("type") != "read" or fact.get("path") != operation.get("path")
                   or fact.get("status") != "completed" or fact.get("exit_code") != 0
                   for fact, operation in zip(facts[:-1], operations[:-1]))):
        return False
    proof = {"version": 1, "instrumentation": INSTRUMENTATION, **detail,
             "baseline_inventory_sha256": manifest["baseline_inventory_sha256"],
             "complete_command_coverage": True, "stderr_stripped": False,
             "overlapping_read_only_item_ids": list(overlap), "accounted_native_appends": native,
             "superseded_inherited_issues": copy.deepcopy(issues),
             "superseded_inherited_facts": copy.deepcopy(facts)}
    base = {key: unknown[0][key] for key in
            (*PROVENANCE, "raw_command", "command_actions", "command_source") if key in unknown[0]}
    for fact in facts:
        result["events" if fact in result["events"] else "diagnostics"].remove(fact)
    for issue in issues:
        result["issues"].remove(issue)
    for index, operation in enumerate(operations):
        fact = {**base, **operation, "status": "completed", "exit_code": 0,
                "raw_operation_index": index, field: copy.deepcopy(proof)}
        result["diagnostics" if fact["type"] == "diagnostic" else "events"].append(fact)
    return True


def _repair_dependencies(result, manifest):
    # Reuse the frozen exact correlation algorithm, labeling only new proofs.
    previous = {id(proof) for fact in result["events"]
                for proof in fact.get("dependency_attribution_certificates", [])}
    _repair_v8_dependencies(result, manifest)
    for fact in result["events"]:
        for proof in fact.get("dependency_attribution_certificates", []):
            if id(proof) not in previous:
                proof["instrumentation"] = INSTRUMENTATION


def normalize_events(events, **kwargs):
    result = normalize_v8(events, **kwargs)
    result.update(schema_version=9, instrumentation=INSTRUMENTATION,
                  base_normalizer="codex-workflow-trace-v8")
    if not result.get("instrumentation_valid") or any(
        issue.get("kind") == "isolation" for issue in result["issues"]
    ):
        return result
    workspace = Path(kwargs["workspace"]).resolve()
    recorded = Path(kwargs["recorded_workspace"]) if kwargs.get("recorded_workspace") is not None else None
    manifest = kwargs["manifest"]
    try:
        _inventory_pin(manifest)
        pairs = _endpoints(events, result)
    except ERRORS:
        return result
    records = {record["raw_item_id"]: record for record in result["command_records"]}
    intrinsic = {}
    for item_id, record in records.items():
        try:
            item = _complete(record, pairs[(result["thread_id"], result["turn_id"], item_id)], workspace, recorded)
            intrinsic[item_id] = _intrinsic(item, record, workspace, manifest, recorded)
        except ERRORS:
            continue
    repaired: set[str] = set()
    for record in sorted(records.values(), key=lambda value: value.get("raw_start_index", -1)):
        try:
            item = _complete(record, pairs[(result["thread_id"], result["turn_id"], record["raw_item_id"])],
                             workspace, recorded)
            if _certificate_shell_body(item["command"]).strip().startswith("if "):
                candidate = _conditional(item, workspace, manifest, recorded)
                native = _safe_prefix(record, candidate, pairs, records, result, workspace, manifest, recorded)
                overlap = []
            else:
                if not repaired:
                    continue
                candidate = intrinsic[record["raw_item_id"]]
                if candidate[1] not in {"terminal_discovery_certificate", "read_only_attribution_certificate"}:
                    continue
                overlap = _safe_v8_prefix(record, pairs, records, intrinsic, result, workspace, recorded)
                native = []
        except ERRORS:
            continue
        if _replace(record, candidate, result, manifest, native, overlap):
            repaired.add(record["raw_item_id"])
            intrinsic[record["raw_item_id"]] = candidate
            _repair_dependencies(result, manifest)
    for key in ("events", "diagnostics"):
        result[key].sort(key=lambda fact: (fact.get("raw_completion_index") or 0,
                                          fact.get("raw_operation_index", 0)))
    return result
