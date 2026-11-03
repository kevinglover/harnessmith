"""Bounded conditional and independent-read attribution for schema 8.

Raw events are never rewritten or executed. The frozen schema-7 observation is
retained except for explicitly identified artificial attribution failures whose
exact facts/issues are copied into a new proof. Concurrency is admitted only for
complete, independently proven read-only commands; it proves no workflow order.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re

from .workflow_fidelity import PACKAGE
from .workflow_trace import IsolationError
from .workflow_trace_v3 import (
    _absence_certificate,
    _literal_words,
    _pinned_bytes,
    _statements,
)
from .workflow_trace_v4 import (
    RUNTIME_FAILURE,
    _command_context,
    _declared_reads,
    _strict_path,
)
from .workflow_trace_v5 import _python_read_chain, _read_fact, _standalone_cat_read
from .workflow_trace_v6 import CONFIG, READ_ONLY_DIAGNOSTICS, _certificate_shell_body
from .workflow_trace_v7 import (
    PASSIVE,
    PROVENANCE,
    UNPROVEN,
    _inventory,
    _same_item,
    _terminal_words,
)
from .workflow_trace_v7 import normalize_events as normalize_v7

INSTRUMENTATION = "codex-workflow-trace-v8"
OVERLAP = "exact read overlaps an uncompleted operation"
CONDITIONAL = "unsupported literal output command"
DEPENDENCY = "required read did not complete before consuming action started"
ERRORS = (ValueError, IsolationError, TypeError, KeyError, OSError, UnicodeError)


def _inventory_pin(manifest):
    baseline = manifest.get("baseline")
    if (
        not isinstance(baseline, dict)
        or any(
            not isinstance(path, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            for path, digest in baseline.items()
        )
        or hashlib.sha256(
            json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        != manifest.get("baseline_inventory_sha256")
    ):
        raise ValueError("new attribution requires the pinned inventory")


def _endpoints(events, result):
    """Retain other scopes too: they must not silently disappear from a prefix."""
    pairs: dict[tuple, dict[str, tuple[int, dict]]] = {}
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not isinstance(event.get("params", {}), dict):
            raise ValueError("malformed raw event")
        if event.get("method") not in {"item/started", "item/completed"}:
            continue
        params, method = event["params"], event["method"]
        item = params.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("malformed raw lifecycle")
        if item.get("type") in PASSIVE:
            continue
        turn = params.get("turn", {})
        scope = (
            params.get("threadId"),
            params.get("turnId", turn.get("id") if isinstance(turn, dict) else None),
        )
        key = (*scope, item["id"])
        pair = pairs.setdefault(key, {})
        if method in pair:
            raise ValueError("duplicate raw lifecycle endpoint")
        pair[method] = (index, item)
    return pairs


def _complete(record, pair, workspace, recorded):
    first, last = pair.get("item/started"), pair.get("item/completed")
    if (
        first is None
        or last is None
        or first[0] >= last[0]
        or (first[0], last[0])
        != (record.get("raw_start_index"), record.get("raw_completion_index"))
        or not record.get("lifecycle_valid")
        or first[1].get("type") != "commandExecution"
        or last[1].get("type") != "commandExecution"
        or first[1].get("status") != "inProgress"
        or last[1].get("status") != "completed"
        or type(last[1].get("exitCode")) is not int
        or last[1]["exitCode"] != 0
        or any(
            first[1].get(field) != last[1].get(field) for field in ("command", "cwd")
        )
        or first[1].get("source", "agent") != last[1].get("source", "agent")
    ):
        raise ValueError(
            "new attribution requires consistent successful command lifecycle"
        )
    if not _command_context(last[1], workspace, recorded).is_dir():
        raise ValueError("new attribution requires an existing command directory")
    _certificate_shell_body(last[1]["command"])
    return last[1]


def _conditional(item, workspace, manifest, recorded):
    statements, connectors = _statements(_certificate_shell_body(item["command"]))
    if len(statements) != 1 or connectors:
        raise ValueError("else-test requires a standalone conditional")
    match = re.fullmatch(
        r"if\s+\[\s+-f\s+(.+?)\s+\]\s*;\s*then\s+(.+?)\s*;\s*else\s+(.+?)\s*;\s*fi",
        statements[0],
        re.S,
    )
    if match is None:
        raise ValueError("unsupported conditional")
    tested, yes, no = (
        _literal_words("cat " + match[1])[1:],
        _literal_words(match[2]),
        _literal_words(match[3]),
    )
    if (
        len(tested) != 1
        or len(yes) != 2
        or yes[0] not in {"cat", "/bin/cat"}
        or no != ["test", "!", "-e", tested[0]]
        or yes[1] != tested[0]
        or tested[0].startswith("-")
    ):
        raise ValueError("both conditional branches must use the same literal path")
    cwd = _command_context(item, workspace, recorded)
    path = _strict_path(tested[0], cwd, workspace, recorded)
    _declared_reads(item, {path}, cwd, workspace, recorded)
    output = item.get("aggregatedOutput")
    if path in manifest.get("pinned_absent_paths", []):
        if path != CONFIG or "aggregatedOutput" not in item or output not in (None, ""):
            raise ValueError("absence proof requires extension path and empty output")
        _absence_certificate(path, workspace, manifest, True)
        fact = {
            "type": "diagnostic",
            "path": path,
            "reason": "fixture absence",
            "certified_absence": True,
        }
        field = "absence_certificate"
    else:
        data = _pinned_bytes(path, workspace, manifest)
        if (
            not data
            or not isinstance(output, str)
            or output != data.decode("utf-8")
            or RUNTIME_FAILURE.search(output)
        ):
            raise ValueError("present conditional requires exact nonempty pinned bytes")
        fact, field = _read_fact(path, data, "before"), "conditional_read_certificate"
    representation = "null" if output is None else "text"
    return (
        [fact],
        field,
        {
            "proof": "literal-else-test",
            "path": path,
            "output_representation": representation,
            "captured_output_sha256": hashlib.sha256(
                (output or "").encode()
            ).hexdigest(),
        },
    )


def _intrinsic(item, record, workspace, manifest, recorded):
    """Prove the complete static command, independently of other command facts."""
    body = _certificate_shell_body(item["command"])
    if body.strip().startswith("if "):
        return _conditional(item, workspace, manifest, recorded)
    statements, connectors = _statements(body)
    words = [_literal_words(statement) for statement in statements]
    cwd = _command_context(item, workspace, recorded)
    if len(words) == 1 and words[0][0] in {"cat", "/bin/cat"}:
        operations = _standalone_cat_read(
            item,
            words[0],
            cwd,
            workspace,
            manifest,
            recorded,
            [],
            record["raw_start_index"],
        )
    elif any(
        part[:2] in (["python3", "-c"], ["/usr/bin/python3", "-c"]) for part in words
    ):
        operations = _python_read_chain(
            item,
            statements,
            connectors,
            cwd,
            workspace,
            manifest,
            recorded,
            True,
            [],
            record["raw_start_index"],
        )
        if any(
            operation.get("type") not in {"read", "diagnostic"}
            or (
                operation.get("type") == "diagnostic"
                and operation.get("reason")
                != "corroborated read-only Python cache warning"
            )
            for operation in operations
        ):
            raise ValueError("concurrent Python proof requires only complete reads")
    else:
        _, words = _terminal_words(record)
        expected, operations = "", []
        for command in words[:-1]:
            if (
                len(command) != 2
                or command[0] not in {"cat", "/bin/cat"}
                or command[1].startswith("-")
            ):
                raise ValueError("discovery prefix must contain only literal cat reads")
            path = _strict_path(command[1], cwd, workspace, recorded)
            data = _pinned_bytes(path, workspace, manifest)
            if not data:
                raise ValueError("discovery prefix must return nonempty bytes")
            expected += data.decode("utf-8")
            operations.append(_read_fact(path, data, "before"))
        root, paths = _inventory(words[-1][2], cwd, workspace, manifest, recorded)
        output = item.get("aggregatedOutput")
        if (
            not isinstance(output, str)
            or not output.startswith(expected)
            or RUNTIME_FAILURE.search(output)
        ):
            raise ValueError("discovery requires exact pinned prefix")
        suffix = output[len(expected) :]
        lines = suffix.splitlines()
        if (
            not suffix.endswith("\n")
            or "\r" in suffix
            or len(lines) != len(set(lines))
            or set(lines) != paths
        ):
            raise ValueError("discovery requires exact complete scoped inventory")
        _declared_reads(
            item, {fact["path"] for fact in operations}, cwd, workspace, recorded
        )
        operations.append(
            {
                "type": "diagnostic",
                "reason": "file discovery",
                "paths": [root],
                "patterns": [],
                "include_hidden": False,
                "certifies_file_contents": False,
                "certifies_absence": False,
            }
        )
        return (
            operations,
            "terminal_discovery_certificate",
            {
                "proof": "literal-terminal-rg",
                "root": root,
                "prefix_reads": [fact["path"] for fact in operations[:-1]],
                "discovered_paths": sorted(paths),
                "terminal_exit_attributable": True,
                "workflow_separation_implied": False,
                "captured_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
            },
        )
    return (
        operations,
        "read_only_attribution_certificate",
        {
            "proof": "independent-exact-read",
            "captured_output_sha256": hashlib.sha256(
                item["aggregatedOutput"].encode()
            ).hexdigest(),
        },
    )


def _full_reads(candidate):
    """Concurrency covers full reads, never an absence/discovery diagnostic."""
    operations = candidate[0]
    return any(operation.get("type") == "read" for operation in operations) and all(
        (
            operation.get("type") == "read"
            and operation.get("read_coverage", {}).get("complete") is True
        )
        or (
            operation.get("type") == "diagnostic"
            and operation.get("reason") == "corroborated read-only Python cache warning"
        )
        for operation in operations
    )


def _safe_prefix(record, pairs, records, candidates, result, workspace, recorded):
    start, end = record["raw_start_index"], record["raw_completion_index"]
    # A peer can outlive this item. Expand through the complete connected
    # overlap group before checking hazards, including a write that starts only
    # after this item's completion but before its read-only peer finishes.
    frontier = end
    changed = True
    while changed:
        changed = False
        for pair in pairs.values():
            before, after = pair.get("item/started"), pair.get("item/completed")
            if (
                before is not None
                and after is not None
                and before[0] <= frontier
                and after[0] >= start
                and after[0] > frontier
            ):
                frontier = after[0]
                changed = True
    relevant = {}
    for key, pair in pairs.items():
        before, after = pair.get("item/started"), pair.get("item/completed")
        if (
            before is not None
            and before[0] > frontier
            and (after is None or after[0] > frontier)
        ):
            continue
        if key[:2] != (result["thread_id"], result["turn_id"]):
            raise ValueError("new proof prefix contains another operation scope")
        relevant[key] = pair
    overlap = []
    for key, pair in relevant.items():
        before, after = pair.get("item/started"), pair.get("item/completed")
        other = records.get(key[2])
        if other is None:
            raise ValueError("new proof prefix contains unknown or mutating operation")
        _complete(other, pair, workspace, recorded)
        if key[2] == record["raw_item_id"]:
            continue
        if after[0] >= start:
            if (
                key[2] not in candidates
                or not _full_reads(candidates[key[2]])
                or not _full_reads(candidates[record["raw_item_id"]])
            ):
                raise ValueError("overlap lacks independent complete read-only proof")
            overlap.append(key[2])
        elif key[2] not in candidates:
            facts = [
                fact
                for fact in result["events"] + result["diagnostics"]
                if _same_item(fact, other)
            ]
            if not facts or any(
                fact.get("status") != "completed"
                or fact.get("exit_code", 0) != 0
                or fact.get("type") not in {"read", "diagnostic", "setup"}
                or (fact.get("type") == "setup" and not fact.get("absence_preserving"))
                or (
                    fact.get("type") == "diagnostic"
                    and fact.get("reason")
                    not in READ_ONLY_DIAGNOSTICS
                    | {"corroborated synthetic adapter macOS cache warning"}
                )
                or (
                    fact.get("reason") == "fixture absence"
                    and not fact.get("certified_absence")
                )
                for fact in facts
            ):
                raise ValueError("prefix contains mutation, failure or uncertainty")
    return sorted(overlap)


def _replace(record, candidate, result, manifest, overlap):
    facts = sorted(
        (
            fact
            for fact in result["events"] + result["diagnostics"]
            if _same_item(fact, record)
        ),
        key=lambda fact: fact["raw_operation_index"],
    )
    issues = [issue for issue in result["issues"] if _same_item(issue, record)]
    operations, field, detail = candidate
    unknown = [fact for fact in facts if fact.get("type") == "unknown"]
    allowed = (
        {CONDITIONAL}
        if field in {"absence_certificate", "conditional_read_certificate"}
        else {OVERLAP}
        if field == "read_only_attribution_certificate"
        else {UNPROVEN}
    )
    if (
        len(unknown) != 1
        or unknown[0].get("reason") not in allowed
        and not (
            field == "terminal_discovery_certificate"
            and str(unknown[0].get("reason", "")).startswith(
                "terminal discovery proof rejected: "
            )
        )
        or unknown[0].get("status") not in {"completed", "unverified"}
        or unknown[0].get("exit_code") != 0
    ):
        return
    details = [unknown[0]["reason"]]
    if (
        unknown[0].get("status") == "unverified"
        and unknown[0].get("reason") == UNPROVEN
    ):
        details.append("failed or incomplete operation")
    expected_issues = [
        {
            "kind": "fidelity",
            "detail": detail,
            **{key: record[key] for key in PROVENANCE},
        }
        for detail in details
    ]
    if issues != expected_issues:
        return
    # Do not erase independent facts, failures or unexpected partial coverage.
    if field != "terminal_discovery_certificate" and len(facts) != 1:
        return
    if field == "terminal_discovery_certificate" and (
        len(facts) != len(operations)
        or any(
            fact.get("type") != "read"
            or fact.get("path") != operation.get("path")
            or fact.get("status") != "completed"
            or fact.get("exit_code") != 0
            for fact, operation in zip(facts[:-1], operations[:-1])
        )
    ):
        return
    proof = {
        "version": 1,
        "instrumentation": INSTRUMENTATION,
        **detail,
        "baseline_inventory_sha256": manifest["baseline_inventory_sha256"],
        "complete_command_coverage": True,
        "stderr_stripped": False,
        "overlapping_read_only_item_ids": overlap,
        "superseded_inherited_issues": copy.deepcopy(issues),
        "superseded_inherited_facts": copy.deepcopy(facts),
    }
    base = {
        key: unknown[0][key]
        for key in (*PROVENANCE, "raw_command", "command_actions", "command_source")
        if key in unknown[0]
    }
    for fact in facts:
        result["events" if fact in result["events"] else "diagnostics"].remove(fact)
    for issue in issues:
        result["issues"].remove(issue)
    for index, operation in enumerate(operations):
        fact = {
            **base,
            **operation,
            "status": "completed",
            "exit_code": 0,
            "raw_operation_index": index,
            field: copy.deepcopy(proof),
        }
        result["diagnostics" if fact["type"] == "diagnostic" else "events"].append(fact)


def _repair_dependencies(result, manifest):
    for issue in list(result["issues"]):
        if issue.get("kind") != "fidelity" or issue.get("detail") != DEPENDENCY:
            continue
        path, item_id = issue.get("path"), issue.get("consumer_item_id")
        consumers = [
            fact
            for fact in result["events"]
            if fact.get("raw_item_id") == item_id
            and fact.get("type") in {"write", "setup", "hook", "read"}
        ]
        shadows = [
            fact
            for fact in result["events"]
            if fact.get("raw_item_id") == item_id
            and fact.get("type") == "unknown"
            and fact.get("reason") == DEPENDENCY
            and fact.get("dependency_path") == path
        ]
        if (
            len(consumers) != 1
            or len(shadows) != 1
            or (
                path not in manifest.get("required_reads", [])
                and path
                not in [
                    PACKAGE + "/" + p for p in manifest.get("expected_references", [])
                ]
            )
        ):
            continue
        consumer = consumers[0]
        reads = [
            fact
            for fact in result["events"]
            if fact.get("type") == "read"
            and fact.get("path") == path
            and fact.get("status") == "completed"
            and fact.get("exit_code") == 0
            and fact.get("raw_completion_index", -1)
            < consumer.get("raw_start_index", -1)
            and any(
                field in fact
                for field in (
                    "conditional_read_certificate",
                    "read_only_attribution_certificate",
                )
            )
        ]
        if not reads:
            continue
        result["issues"].remove(issue)
        result["events"].remove(shadows[0])
        consumer.setdefault("dependency_attribution_certificates", []).append(
            {
                "version": 1,
                "instrumentation": INSTRUMENTATION,
                "path": path,
                "read_item_ids": [read["raw_item_id"] for read in reads],
                "superseded_inherited_issues": [copy.deepcopy(issue)],
                "superseded_inherited_facts": [copy.deepcopy(shadows[0])],
            }
        )


def normalize_events(events, **kwargs):
    result = normalize_v7(events, **kwargs)
    result.update(
        schema_version=8,
        instrumentation=INSTRUMENTATION,
        base_normalizer="codex-workflow-trace-v7",
    )
    if not result.get("instrumentation_valid") or any(
        issue.get("kind") == "isolation" for issue in result["issues"]
    ):
        return result
    workspace = Path(kwargs["workspace"]).resolve()
    recorded = (
        Path(kwargs["recorded_workspace"])
        if kwargs.get("recorded_workspace") is not None
        else None
    )
    manifest = kwargs["manifest"]
    try:
        _inventory_pin(manifest)
        pairs = _endpoints(events, result)
    except ERRORS:
        return result
    records = {record["raw_item_id"]: record for record in result["command_records"]}
    candidates = {}
    for item_id, record in records.items():
        try:
            item = _complete(
                record,
                pairs[(result["thread_id"], result["turn_id"], item_id)],
                workspace,
                recorded,
            )
            candidates[item_id] = _intrinsic(
                item, record, workspace, manifest, recorded
            )
        except ERRORS:
            continue
    for item_id, candidate in candidates.items():
        try:
            overlaps = _safe_prefix(
                records[item_id],
                pairs,
                records,
                candidates,
                result,
                workspace,
                recorded,
            )
        except ERRORS as exc:
            if str(exc) == "new proof prefix contains another operation scope":
                record = records[item_id]
                facts = [
                    fact
                    for fact in result["events"] + result["diagnostics"]
                    if _same_item(fact, record)
                ]
                detail = "new read-only attribution scope guard found another operation scope"
                result["events"].append(
                    {
                        **{key: record[key] for key in PROVENANCE},
                        "type": "unknown",
                        "status": "unverified",
                        "exit_code": 0,
                        "reason": detail,
                        "raw_operation_index": max(
                            (fact["raw_operation_index"] for fact in facts), default=-1
                        )
                        + 1,
                        "scope_guard_evidence": {
                            "instrumentation": INSTRUMENTATION,
                            "inherited_facts": copy.deepcopy(facts),
                        },
                    }
                )
                result["issues"].append(
                    {
                        "kind": "fidelity",
                        "detail": detail,
                        **{key: record[key] for key in PROVENANCE},
                    }
                )
            continue
        _replace(records[item_id], candidate, result, manifest, overlaps)
    _repair_dependencies(result, manifest)
    result["events"].sort(
        key=lambda fact: (
            fact.get("raw_completion_index") or 0,
            fact.get("raw_operation_index", 0),
        )
    )
    result["diagnostics"].sort(
        key=lambda fact: (
            fact.get("raw_completion_index") or 0,
            fact.get("raw_operation_index", 0),
        )
    )
    return result
