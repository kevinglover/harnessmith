"""Schema-7 attribution for exact terminal discovery after pinned cat reads.

Captured commands remain data. Only literal ``cat FILE`` prefixes followed by
one terminal ``rg --files DIRECTORY`` are newly certified. A successful terminal
exit and exact pinned output establish attribution, not workflow separation.
The frozen v6 parser remains unchanged; real failures and unrelated issues stay.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

from .workflow_trace import IsolationError, PASSIVE_ITEMS
from .workflow_trace_v3 import _literal_words, _pinned_bytes, _statements
from .workflow_trace_v4 import RUNTIME_FAILURE, _command_context, _declared_reads, _strict_path
from .workflow_trace_v6 import (
    READ_ONLY_DIAGNOSTICS,
    _certificate_shell_body,
    normalize_events as normalize_v6,
)

INSTRUMENTATION = "codex-workflow-trace-v7"
UNPROVEN = "individual statement success unproven"
PROVENANCE = ("raw_item_id", "raw_start_index", "raw_completion_index")
PASSIVE = PASSIVE_ITEMS | {"agentMessage"}


def _same_item(left, right):
    return all(left.get(key) == right.get(key) for key in PROVENANCE)


def _terminal_words(record):
    statements, connectors = _statements(_certificate_shell_body(record["raw_command"]))
    if (not statements or len(connectors) != len(statements) - 1
            or any(separator not in {";", "\n", "&&"} for separator in connectors)):
        raise ValueError("terminal discovery requires literal sequenced commands")
    words = [_literal_words(statement) for statement in statements]
    if len(words[-1]) != 3 or words[-1][:2] != ["rg", "--files"]:
        raise ValueError("terminal discovery requires one literal directory and no flags")
    return statements, words


def _lifecycle(events, result, record):
    """No new proof may cross an incomplete, overlapping or mutating prefix."""
    if not result.get("instrumentation_valid"):
        raise ValueError("terminal discovery requires valid instrumentation")
    start, end = record.get("raw_start_index"), record.get("raw_completion_index")
    if (type(start) is not int or type(end) is not int or not 0 <= start < end < len(events)
            or not record.get("lifecycle_valid") or record.get("status") != "completed"
            or type(record.get("exit_code")) is not int or record["exit_code"] != 0):
        raise ValueError("terminal discovery requires a successful complete lifecycle")
    endpoints: dict[str, dict[str, tuple[int, dict]]] = {}
    for index, raw in enumerate(events):
        if not isinstance(raw, dict) or not isinstance(raw.get("params", {}), dict):
            raise ValueError("malformed raw event")
        if raw.get("method") not in {"item/started", "item/completed"}:
            continue
        params = raw["params"]
        item = params.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("malformed raw lifecycle item")
        if item.get("type") in PASSIVE:
            continue
        turn = params.get("turn", {})
        if (params.get("threadId") != result["thread_id"] or not isinstance(turn, dict)
                or params.get("turnId", turn.get("id")) != result["turn_id"]):
            if index <= end:
                raise ValueError("terminal discovery prefix contains another operation scope")
            continue
        kind = raw["method"]
        pair = endpoints.setdefault(item["id"], {})
        if kind in pair:
            raise ValueError("duplicate raw lifecycle endpoint")
        pair[kind] = (index, item)
    facts = result["events"] + result["diagnostics"]
    records = {entry["raw_item_id"]: entry for entry in result["command_records"]}
    for item_id, pair in endpoints.items():
        before, after = pair.get("item/started"), pair.get("item/completed")
        if before is not None and before[0] > end and (after is None or after[0] > end):
            continue
        if before is None or after is None or not before[0] < after[0]:
            raise ValueError("terminal discovery prefix has an incomplete lifecycle")
        first, last = before[1], after[1]
        if (first.get("type") != "commandExecution" or last.get("type") != "commandExecution"
                or first.get("status") != "inProgress"
                or any(first.get(key) != last.get(key) for key in ("command", "cwd"))
                or first.get("source", "agent") != last.get("source", "agent")
                or last.get("source", "agent") not in {"agent", "unifiedExecStartup"}):
            raise ValueError("terminal discovery prefix lifecycle fields disagree")
        if item_id == record["raw_item_id"]:
            if (before[0], after[0]) != (start, end):
                raise ValueError("terminal discovery coordinates disagree")
            continue
        prior_record = records.get(item_id, {})
        if (after[0] >= start or not prior_record.get("lifecycle_valid")
                or prior_record.get("status") != "completed"
                or type(prior_record.get("exit_code")) is not int
                or prior_record["exit_code"] != 0):
            raise ValueError("terminal discovery has overlapping or unsuccessful prefix")
        _certificate_shell_body(prior_record["raw_command"])
        prior = [fact for fact in facts if fact.get("raw_item_id") == item_id]
        if not prior or any(
            fact.get("status") != "completed" or fact.get("exit_code", 0) != 0
            or fact.get("type") not in {"read", "diagnostic", "setup"}
            or (fact.get("type") == "setup" and not fact.get("absence_preserving"))
            or (fact.get("type") == "diagnostic"
                and fact.get("reason") not in READ_ONLY_DIAGNOSTICS)
            or (fact.get("reason") == "fixture absence" and not fact.get("certified_absence"))
            for fact in prior
        ):
            raise ValueError("terminal discovery prefix contains mutation or uncertainty")
    pair = endpoints.get(record["raw_item_id"], {})
    if "item/completed" not in pair:
        raise ValueError("terminal discovery lacks a matching raw completion")
    return pair["item/completed"][1]


def _inventory(root_word, cwd, workspace, manifest, recorded_workspace):
    """Bound the complete visible path list to unchanged pinned tree membership."""
    if (root_word.startswith("-") or any(part in {".", ".."} for part in root_word.split("/"))
            or any(character in root_word for character in "\n\r\t\\")):
        raise ValueError("discovery root must have an unambiguous literal spelling")
    root = _strict_path(root_word, cwd, workspace, recorded_workspace)
    if root == "." or any(part.startswith(".") for part in Path(root).parts):
        raise ValueError("new discovery proof requires a visible scoped directory")
    directory = workspace / root
    if not directory.is_dir():
        raise ValueError("discovery root does not exist as a directory")
    baseline = manifest.get("baseline")
    if (not isinstance(baseline, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            or not re.fullmatch(r"[0-9a-f]{64}", value) for key, value in baseline.items())
            or hashlib.sha256(json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != manifest.get("baseline_inventory_sha256")):
        raise ValueError("discovery requires the pinned baseline inventory")
    prefix = root + "/"
    pinned = {path for path in baseline if path.startswith(prefix)}
    if not pinned:
        raise ValueError("discovery requires a nonempty pinned scoped inventory")
    current = set()
    for parent, directories, files in os.walk(directory, followlinks=False):
        for name in directories + files:
            candidate = Path(parent) / name
            relative = _strict_path(str(candidate), workspace, workspace, None)
            if candidate.is_symlink() or not (candidate.is_dir() or candidate.is_file()):
                raise ValueError("discovery tree contains an unsupported filesystem entry")
            if candidate.is_file():
                current.add(relative)
    if current != pinned:
        raise ValueError("discovery tree membership differs from the pinned inventory")
    visible = {path for path in pinned
               if not any(part.startswith(".") for part in Path(path[len(prefix):]).parts)}
    if not visible:
        raise ValueError("zero-exit discovery must have nonempty visible files")
    expected = {root_word.rstrip("/") + "/" + path[len(prefix):] for path in visible}
    return root, expected


def _proof(events, result, record, statements, words, workspace, manifest, recorded_workspace):
    item = _lifecycle(events, result, record)
    cwd = _command_context(item, workspace, recorded_workspace)
    output = item.get("aggregatedOutput")
    if not isinstance(output, str) or RUNTIME_FAILURE.search(output):
        raise ValueError("terminal discovery requires exact clean captured output")
    expected_prefix, reads = "", []
    for command in words[:-1]:
        if len(command) != 2 or command[0] not in {"cat", "/bin/cat"} or command[1].startswith("-"):
            raise ValueError("only literal single-file cat prefixes are supported")
        path = _strict_path(command[1], cwd, workspace, recorded_workspace)
        data = _pinned_bytes(path, workspace, manifest).decode("utf-8")
        if not data:
            raise ValueError("empty output cannot establish a preceding cat")
        expected_prefix += data
        reads.append(path)
    _declared_reads(item, set(reads), cwd, workspace, recorded_workspace)
    root, expected_paths = _inventory(words[-1][2], cwd, workspace, manifest, recorded_workspace)
    if not output.startswith(expected_prefix):
        raise ValueError("terminal discovery lacks the exact ordered pinned read prefix")
    suffix = output[len(expected_prefix):]
    returned = suffix.splitlines()
    if (not suffix.endswith("\n") or "\r" in suffix or not returned
            or len(returned) != len(set(returned)) or set(returned) != expected_paths):
        raise ValueError("terminal discovery output differs from the complete pinned path list")
    facts = sorted((fact for fact in result["events"] + result["diagnostics"]
                    if _same_item(fact, record)), key=lambda fact: fact["raw_operation_index"])
    if len(facts) != len(words):
        raise ValueError("terminal discovery does not have complete operation coverage")
    for index, (path, fact) in enumerate(zip(reads, facts)):
        if (fact.get("type") != "read" or fact.get("path") != path
                or fact.get("status") != "completed" or fact.get("exit_code") != 0
                or fact.get("raw_operation_index") != index):
            raise ValueError("terminal discovery has an unproven prefix read")
    terminal = facts[-1]
    if terminal.get("raw_operation_index") != len(words) - 1:
        raise ValueError("terminal discovery operation position disagrees")
    repair = (terminal.get("type") == "unknown" and terminal.get("reason") == UNPROVEN
              and terminal.get("status") == "unverified" and terminal.get("exit_code") == 0
              and terminal.get("raw_statement") == statements[-1])
    credited = (terminal.get("type") == "diagnostic" and terminal.get("reason") == "file discovery"
                and terminal.get("status") == "completed" and terminal.get("exit_code") == 0)
    if not (repair or credited):
        raise ValueError("terminal discovery cannot replace another operation or failure")
    issues = [issue for issue in result["issues"] if _same_item(issue, record)]
    expected_issues = [{"kind": "fidelity", "detail": detail,
                        **{key: record[key] for key in PROVENANCE}}
                       for detail in (UNPROVEN, "failed or incomplete operation")]
    if issues != (expected_issues if repair else []):
        raise ValueError("terminal discovery has unrelated or ambiguous item issues")
    return terminal, expected_issues if repair else [], {
        "version": 1, "instrumentation": INSTRUMENTATION,
        "proof": "literal-terminal-rg", "root": root,
        "baseline_inventory_sha256": manifest["baseline_inventory_sha256"],
        "captured_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "discovered_paths": sorted(expected_paths), "prefix_reads": reads,
        "complete_command_coverage": True, "terminal_exit_attributable": True,
        "stderr_stripped": False, "workflow_separation_implied": False,
        "superseded_inherited_issues": expected_issues if repair else [],
        "inherited_attribution": {key: terminal[key] for key in
                                  ("type", "status", "reason", "raw_statement") if key in terminal},
    }


def normalize_events(events, **kwargs):
    """Add bounded proofs without rewriting raw records or inherited failures."""
    result = normalize_v6(events, **kwargs)
    result.update(schema_version=7, instrumentation=INSTRUMENTATION,
                  base_normalizer="codex-workflow-trace-v6")
    workspace = Path(kwargs["workspace"]).resolve()
    recorded = kwargs.get("recorded_workspace")
    recorded = Path(recorded) if recorded is not None else None
    for record in result["command_records"]:
        try:
            statements, words = _terminal_words(record)
        except (ValueError, TypeError, KeyError):
            continue
        try:
            terminal, retired_issues, proof = _proof(
                events, result, record, statements, words, workspace, kwargs["manifest"], recorded,
            )
        except (ValueError, IsolationError, TypeError, KeyError, OSError, UnicodeError) as exc:
            # V6 already credits standalone/&& discovery from its aggregate exit.
            # Only that same narrow candidate is hardened by this new proof gate.
            credited = [fact for fact in result["diagnostics"] if _same_item(fact, record)
                        and fact.get("reason") == "file discovery"
                        and fact.get("raw_operation_index") == len(words) - 1]
            for fact in credited:
                result["diagnostics"].remove(fact)
                failed = {**fact, "type": "unknown", "status": "unverified",
                          "reason": "terminal discovery proof rejected: " + str(exc)}
                result["events"].append(failed)
                result["issues"].append({"kind": "fidelity", "detail": failed["reason"],
                                         **{key: record[key] for key in PROVENANCE}})
            continue
        diagnostic = {**terminal, "type": "diagnostic", "reason": "file discovery",
                      "status": "completed", "exit_code": 0, "paths": [proof["root"]],
                      "patterns": [], "include_hidden": False,
                      "certifies_file_contents": False, "certifies_absence": False,
                      "success_evidence": "exact pinned reads, complete scoped path output and terminal exit",
                      "terminal_discovery_certificate": proof}
        if terminal in result["events"]:
            result["events"].remove(terminal)
            result["diagnostics"].append(diagnostic)
        else:
            result["diagnostics"][result["diagnostics"].index(terminal)] = diagnostic
        for issue in retired_issues:
            result["issues"].remove(issue)
    return result
