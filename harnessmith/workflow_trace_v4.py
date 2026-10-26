"""Schema-4 offline trace attribution with bounded append and partial-read proofs.

Captured code is parsed as data and is never evaluated or executed. V3 helpers
remain frozen. The lifecycle driver is versioned here so new operation facts are
audited in their original order, without mutating old module globals or traces.
"""

from __future__ import annotations

import ast
import hashlib
import math
from pathlib import Path
import re

from .workflow_fidelity import PACKAGE
from .workflow_trace import (
    IsolationError,
    MODEL,
    PASSIVE_ITEMS,
    WorkflowTraceError,
    _shell_body,
)
from .workflow_trace_v3 import (
    CACHE_WARNING,
    FAILURE,
    _classify_v2,
    _command_operations_v3,
    _literal_words,
    _map_path,
    _pinned_bytes,
    _read_coverage,
    _read_output,
    _statements,
)

INSTRUMENTATION = "codex-workflow-trace-v4"
RUNTIME_FAILURE = re.compile(
    FAILURE.pattern + r"|(?m:^\s*(?:SyntaxError|IndentationError|AssertionError):)",
    re.I,
)


def _strict_path(value, cwd, workspace, recorded_workspace):
    """New proofs reject links, including aliases that resolve inside the root."""
    if not isinstance(value, str):
        raise ValueError("path must be a literal string")
    raw = Path(value)
    if recorded_workspace is not None and raw.is_absolute():
        try:
            raw = workspace / raw.relative_to(recorded_workspace)
        except ValueError as exc:
            raise IsolationError("recorded path escapes workspace") from exc
    raw = raw if raw.is_absolute() else cwd / raw
    path = _map_path(value, cwd, workspace, recorded_workspace)
    for candidate in [raw, *raw.parents]:
        if candidate == workspace:
            break
        if candidate.is_symlink():
            raise IsolationError("symlink is not admissible for a new read/write proof")
    return path


def _command_context(item, workspace, recorded_workspace):
    if item.get("source", "agent") not in {"agent", "unifiedExecStartup"}:
        raise ValueError("command source is not a verified agent command")
    value = item.get("cwd")
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError("command cwd must be absolute")
    cwd = workspace / _strict_path(value, workspace, workspace, recorded_workspace)
    actions = item.get("commandActions")
    if not isinstance(actions, list) or any(not isinstance(a, dict) for a in actions):
        raise ValueError("missing or malformed commandActions")
    return cwd


def _declared_reads(item, reads, cwd, workspace, recorded_workspace):
    for action in item["commandActions"]:
        if (
            action.get("type") == "read"
            and _strict_path(action.get("path"), cwd, workspace, recorded_workspace)
            not in reads
        ):
            raise ValueError("declared read disagrees with certified parsed command")


def _append_ast(words, cwd, workspace, manifest, recorded_workspace):
    """Admit exactly eight statements, literal Path and literal bytes only."""
    if words[:2] not in (["python3", "-c"], ["/usr/bin/python3", "-c"]):
        raise ValueError("unverified Python append executable")
    if len(words) != 3:
        raise ValueError("Python append requires one script argument")
    try:
        parsed = ast.parse(words[2], mode="exec")
    except (SyntaxError, ValueError) as exc:
        raise ValueError("invalid Python append syntax") from exc
    body = parsed.body
    if len(body) != 8:
        raise ValueError("unsupported internal append statement count")
    names = []
    for index in (1, 2, 3, 5):
        statement = body[index]
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            raise ValueError("append requires simple, distinct variable assignments")
        names.append(statement.targets[0].id)
    if len(set(names)) != 4 or set(names) & {"Path", "print"}:
        raise ValueError("append variables must be distinct and cannot shadow builtins")
    p, old, add, new = names
    constructor, payload = body[1].value, body[3].value
    if not (
        isinstance(constructor, ast.Call)
        and len(constructor.args) == 1
        and isinstance(constructor.args[0], ast.Constant)
        and type(constructor.args[0].value) is str
        and isinstance(payload, ast.Constant)
        and type(payload.value) is bytes
        and payload.value
    ):
        raise ValueError("append requires a literal path and nonempty literal bytes")
    literal_path = constructor.args[0].value
    # Comparing complete trees also rejects extra calls, keywords, alternate
    # write modes, missing reads/assertions, slices, transforms and imports.
    expected = ast.parse(
        "from pathlib import Path; "
        f"{p}=Path({literal_path!r}); {old}={p}.read_bytes(); "
        f"{add}={payload.value!r}; {p}.open('ab').write({add}); "
        f"{new}={p}.read_bytes(); assert {new} == {old} + {add}; "
        f"print({new}.decode())",
        mode="exec",
    )
    if ast.dump(parsed) != ast.dump(expected):
        raise ValueError(
            "Python append is outside the bounded read/write/assert grammar"
        )
    path = _strict_path(literal_path, cwd, workspace, recorded_workspace)
    if path != manifest.get("target"):
        raise ValueError("Python append target is not the prepared artifact")
    return path, payload.value


def _append_operations(item, words, cwd, workspace, manifest, recorded_workspace):
    path, addition = _append_ast(words, cwd, workspace, manifest, recorded_workspace)
    if not isinstance(manifest.get("baseline_target_hex"), str):
        raise ValueError("internal append requires independently pinned before bytes")
    before = _pinned_bytes(path, workspace, manifest)
    after = before + addition
    output = item.get("aggregatedOutput", "")
    if not isinstance(output, str):
        raise ValueError("append output must be captured text")
    clean = CACHE_WARNING.sub("", output)
    if (
        not before
        or item.get("status") != "completed"
        or type(item.get("exitCode")) is not int
        or item["exitCode"] != 0
        or clean != after.decode("utf-8") + "\n"
        or RUNTIME_FAILURE.search(clean)
        or (workspace / path).read_bytes() != after
    ):
        raise ValueError(
            "append lacks successful execution and exact before/final/output proof"
        )
    _declared_reads(item, {path}, cwd, workspace, recorded_workspace)
    evidence = "literal append AST, pinned before bytes, assertion, exact print and final bytes"
    before_hash, after_hash = (
        hashlib.sha256(data).hexdigest() for data in (before, after)
    )
    result = []
    if output != clean:
        result.append(
            {
                "type": "diagnostic",
                "reason": "corroborated internal append macOS cache warning",
                "raw_warning_output": "".join(CACHE_WARNING.findall(output)),
                "success_evidence": evidence,
            }
        )
    return result + [
        {
            "type": "read",
            "path": path,
            "read_before_write": True,
            "read_sha256": before_hash,
            "read_coverage": {"complete": True},
            "success_evidence": evidence,
        },
        {
            "type": "write",
            "path": path,
            "write_mode": "append",
            "before_sha256": before_hash,
            "payload_sha256": hashlib.sha256(addition).hexdigest(),
            "after_sha256": after_hash,
            "success_evidence": evidence,
        },
        {
            "type": "read",
            "path": path,
            "read_after_write": True,
            "read_sha256": after_hash,
            "read_coverage": {"complete": True},
            "success_evidence": evidence,
        },
    ]


def _discovery(words, cwd, workspace, manifest, recorded_workspace):
    if words[:2] != ["rg", "--files"] or words.count("--hidden") > 1:
        raise ValueError("unsupported bounded file discovery")
    hidden, cleaned, index = False, words[:2], 2
    while index < len(words):
        word = words[index]
        if word == "--hidden":
            hidden = True
        elif word == "-g" and index + 1 < len(words):
            cleaned.extend(words[index : index + 2])
            index += 1
        else:
            if not word.startswith("-"):
                _strict_path(word, cwd, workspace, recorded_workspace)
            cleaned.append(word)
        index += 1
    operation = _classify_v2(cleaned, cwd, workspace, manifest, recorded_workspace)[0]
    # No follow-links, unrestricted glob flags or filesystem scans are admitted.
    for path in operation["paths"]:
        _strict_path(str(workspace / path), workspace, workspace, None)
    operation["include_hidden"] = hidden
    operation["certifies_file_contents"] = False
    operation["certifies_absence"] = False
    operation["hidden_patterns_without_hidden"] = not hidden and any(
        any(
            part.startswith(".") and part not in {".", ".."}
            for part in Path(pattern.lstrip("!")).parts
        )
        for pattern in operation["patterns"]
    )
    return operation


def _read_chain(
    item, statements, connectors, cwd, workspace, manifest, recorded_workspace
):
    """Prove exact ordered prefix reads; retain the nonzero command separately.

    Only cat/sed reads and literal labels may precede one terminal rg --files
    or failed cat. A later arbitrary producer, fallback, pipeline or mutation
    invalidates this proof rather than attributing matching text to a read.
    """
    if not statements or any(c != "&&" for c in connectors):
        raise ValueError("constituent reads require a bounded && chain")
    output = item.get("aggregatedOutput")
    if item.get("status") not in {"completed", "failed"} or not isinstance(output, str):
        raise ValueError("constituent reads require completed captured output")
    code = item.get("exitCode")
    if type(code) is not int:
        raise ValueError("constituent reads require an integer envelope exit")
    if code == 0 and item.get("status") != "completed":
        raise ValueError("zero-exit discovery requires successful completed status")
    parsed = [_literal_words(statement) for statement in statements]
    tail = parsed[-1]
    if tail[:2] == ["rg", "--files"]:
        terminal = _discovery(tail, cwd, workspace, manifest, recorded_workspace)
        if code not in {0, 1}:
            raise ValueError("discovery has an unsupported error exit")
    elif code != 0 and tail[0] in {"cat", "/bin/cat"} and len(parsed) > 1:
        if len(tail) < 2 or "-" in tail[1:]:
            raise ValueError("failed cat must name literal non-stdin arguments")
        for arg in tail[1:]:
            if arg.startswith("-"):
                if not re.fullmatch(r"--?[a-zA-Z][a-zA-Z-]*", arg):
                    raise ValueError("unsupported failed cat option")
            else:
                _strict_path(arg, cwd, workspace, recorded_workspace)
        terminal = {"type": "unknown", "reason": "failed terminal cat arguments"}
    else:
        raise ValueError("no bounded terminal discovery or failed cat")
    result, expected, reads = [], "", set()
    for words in parsed[:-1]:
        operations = _classify_v2(words, cwd, workspace, manifest, recorded_workspace)
        if Path(words[0]).name in {"cat", "sed"}:
            arguments = words[1:] if Path(words[0]).name == "cat" else words[3:]
            if arguments[:1] == ["--"]:
                arguments = arguments[1:]
            for argument in arguments:
                _strict_path(argument, cwd, workspace, recorded_workspace)
        for operation in operations:
            if operation["type"] == "read" and Path(words[0]).name in {"cat", "sed"}:
                path = operation["path"]
                _strict_path(str(workspace / path), workspace, workspace, None)
                _read_coverage(operation, words, workspace, manifest)
                text = _read_output(operation, words, workspace, manifest)
                expected += text
                reads.add(path)
                operation.update(
                    status="completed",
                    exit_code=0,
                    envelope_exit_code=code,
                    constituent_success=True,
                    read_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    success_evidence="pinned bytes in exact ordered bounded command prefix",
                )
                if Path(words[0]).name == "cat":
                    operation["read_coverage"] = {"complete": True}
            elif operation.get("reason") == "literal output label":
                expected += operation.pop("expected_output")
                operation.update(
                    status="completed", exit_code=0, envelope_exit_code=code
                )
            else:
                raise ValueError(
                    "unsupported producer before terminal failure/discovery"
                )
            result.append(operation)
    if not output.startswith(expected):
        raise ValueError("constituent read lacks exact pinned output prefix")
    suffix = output[len(expected) :]
    if terminal["type"] == "unknown":
        if not re.search(
            r"(?m)^cat: .*?(?:No such file or directory|illegal option|invalid option|"
            r"unrecognized option|Permission denied)",
            suffix,
            re.I,
        ):
            raise ValueError("terminal cat failure is not corroborated")
    elif code == 1 and suffix:
        raise ValueError("no-match discovery must have empty remaining output")
    elif code == 0 and RUNTIME_FAILURE.search(output):
        raise ValueError("discovery envelope contains failure output")
    _declared_reads(item, reads, cwd, workspace, recorded_workspace)
    if code:
        result.append(
            {
                "type": "unknown",
                "status": "failed",
                "exit_code": code,
                "envelope_exit_code": code,
                "reason": "nonzero command retained after proven constituent reads",
                "raw_statement": statements[-1],
                "failure_output": bool(suffix),
            }
        )
    else:
        result.append(terminal)
    return result


def _classified_operations_v4(
    item, workspace, manifest, recorded_workspace, absence_safe, lifecycle_valid
):
    body = _shell_body(item.get("command"))
    if "<<" in body:
        return _command_operations_v3(
            item, workspace, manifest, recorded_workspace, absence_safe
        )
    statements, connectors = _statements(body)
    words = [_literal_words(part) for part in statements if not part.startswith("if ")]
    python = len(words) == 1 and words[0][:2] in (
        ["python3", "-c"],
        ["/usr/bin/python3", "-c"],
    )
    discovery = any(part[:2] == ["rg", "--files"] for part in words)
    failed_chain = item.get("exitCode") != 0 and len(words) > 1
    if python or discovery or failed_chain:
        if not lifecycle_valid:
            raise ValueError(
                "new command proof requires matching start/completion lifecycle"
            )
        cwd = _command_context(item, workspace, recorded_workspace)
        if python and len(statements) == 1 and not connectors:
            return _append_operations(
                item, words[0], cwd, workspace, manifest, recorded_workspace
            )
        try:
            return _read_chain(
                item,
                statements,
                connectors,
                cwd,
                workspace,
                manifest,
                recorded_workspace,
            )
        except IsolationError:
            raise
        except (ValueError, OSError, UnicodeError):
            # Do not lose conservative v3 coverage for other established
            # compound grammars (for example its terminal sort pipeline).
            pass
    return _command_operations_v3(
        item, workspace, manifest, recorded_workspace, absence_safe
    )


def _command_operations_v4(
    item, workspace, manifest, recorded_workspace, absence_safe, lifecycle_valid
):
    # Every classification path, including the unchanged heredoc recognizer,
    # receives the same failure retention after successful attribution.
    try:
        result = _classified_operations_v4(
            item, workspace, manifest, recorded_workspace, absence_safe, lifecycle_valid
        )
    except IsolationError:
        raise
    except (ValueError, KeyError, OSError, UnicodeError) as exc:
        result = [{"type": "unknown", "reason": str(exc)}]
    output = item.get("aggregatedOutput", "")
    if isinstance(output, str) and any(
        "cache warning" in operation.get("reason", "") for operation in result
    ):
        # Exclude only the exact independently corroborated warning lines.
        # Other diagnostics in the same command still defeat clean success.
        output = CACHE_WARNING.sub("", output)
    if (
        isinstance(output, str)
        and RUNTIME_FAILURE.search(output)
        and not any(operation.get("status") == "failed" for operation in result)
    ):
        result.append(
            {
                "type": "unknown",
                "status": "failed",
                "failure_output": True,
                "reason": "captured constituent failure retained despite envelope/recovery",
            }
        )
    return result


def normalize_events(
    events,
    *,
    thread_id,
    turn_id,
    workspace,
    manifest,
    latency_ms,
    recorded_workspace=None,
):
    """Return retained observations, issues and a separate instrumentation flag.

    ``issues[].kind`` distinguishes ``instrumentation`` defects (collector should
    stop) from ``fidelity`` failures/unverifiable operations (retain and score).
    Model identity is requested identity: the collector must separately verify
    thread/start's returned model and retain that response. A reroute invalidates
    the observation even if the thread eventually finishes.
    """
    if not isinstance(events, list) or not isinstance(manifest, dict):
        raise WorkflowTraceError("events must be a list and manifest an object")
    workspace = Path(workspace).resolve()
    recorded_workspace = (
        Path(recorded_workspace) if recorded_workspace is not None else None
    )
    if recorded_workspace is not None and not recorded_workspace.is_absolute():
        raise WorkflowTraceError("recorded_workspace must be an absolute recorded root")
    result = {
        "schema_version": 4,
        "command_records": [],
        "evidence_kind": "externally-captured-observation",
        "instrumentation": INSTRUMENTATION,
        "model": MODEL,
        "completed": False,
        "events": [],
        "diagnostics": [],
        "issues": [],
        "output": "",
        "final_output": None,
        "commentary": [],
        "messages": [],
        "usage": None,
        "thread_id": thread_id,
        "turn_id": turn_id,
    }
    starts, completed_items, outputs = {}, set(), []
    deltas: dict[str, list[str]] = {}
    usage = None
    usage_index = None
    completion_index = None

    def issue(kind, detail, **extra):
        result["issues"].append({"kind": kind, "detail": detail, **extra})

    if not isinstance(thread_id, str) or not isinstance(turn_id, str):
        issue("instrumentation", "thread and turn IDs were not established")
        # Preserve a known stream even if an RPC response was interrupted.
        for event in events:
            if not isinstance(event, dict) or not isinstance(event.get("params"), dict):
                continue
            params = event["params"]
            candidate = params.get("turn")
            if event.get("method") == "turn/started" and isinstance(candidate, dict):
                thread_id = thread_id or params.get("threadId")
                turn_id = turn_id or candidate.get("id")
        result["thread_id"], result["turn_id"] = thread_id, turn_id
    if manifest.get("model") != MODEL:
        issue("instrumentation", "manifest model is not approved GPT-6 Luna")
    if (
        type(latency_ms) not in (int, float)
        or latency_ms < 0
        or not math.isfinite(latency_ms)
    ):
        issue("instrumentation", "invalid measured latency")
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not isinstance(event.get("params", {}), dict):
            issue("instrumentation", "malformed notification", raw_event_index=index)
            continue
        method, params = event.get("method"), event.get("params", {})
        if params.get("threadId") != thread_id:
            continue
        # Model identity and server failures invalidate this fresh, single-turn
        # thread even when an implementation emits a thread-scoped notice.
        if method == "model/rerouted":
            issue(
                "instrumentation",
                "model rerouted; approved model identity invalid",
                raw_event_index=index,
            )
            continue
        if method == "error":
            issue(
                "instrumentation",
                "server error notification",
                raw_event_index=index,
                error=params.get("error"),
                will_retry=params.get("willRetry"),
            )
            continue
        turn = params.get("turn", {})
        if not isinstance(turn, dict):
            issue("instrumentation", "malformed turn object", raw_event_index=index)
            continue
        if params.get("turnId", turn.get("id")) != turn_id:
            continue
        if method == "thread/tokenUsage/updated":
            token_usage = params.get("tokenUsage")
            usage = token_usage.get("total") if isinstance(token_usage, dict) else None
            usage_index = index
        elif method == "item/agentMessage/delta":
            if isinstance(params.get("itemId"), str) and isinstance(
                params.get("delta"), str
            ):
                deltas.setdefault(params["itemId"], []).append(params["delta"])
            else:
                issue(
                    "instrumentation",
                    "malformed agent text delta",
                    raw_event_index=index,
                )
        elif method == "turn/completed":
            if completion_index is not None:
                issue(
                    "instrumentation",
                    "duplicate turn completion",
                    raw_event_index=index,
                )
            completion_index = index
            result["completed"] = turn.get("status") == "completed"
            if not result["completed"]:
                issue(
                    "fidelity",
                    "turn did not complete",
                    status=turn.get("status"),
                    error=turn.get("error"),
                )
        elif method in {"item/started", "item/completed"}:
            item = params.get("item")
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                issue(
                    "instrumentation",
                    "malformed item or missing item ID",
                    raw_event_index=index,
                )
                result["events"].append(
                    {
                        "type": "unknown",
                        "status": "unverified",
                        "raw_item_id": None,
                        "raw_start_index": None,
                        "raw_completion_index": index,
                    }
                )
                continue
            item_id = item["id"]
            if method == "item/started":
                if item_id in starts:
                    issue(
                        "instrumentation",
                        "duplicate item start",
                        raw_event_index=index,
                        raw_item_id=item_id,
                    )
                starts[item_id] = (index, item)
                continue
            if item_id in completed_items:
                issue(
                    "instrumentation",
                    "duplicate completed item",
                    raw_event_index=index,
                    raw_item_id=item_id,
                )
            completed_items.add(item_id)
            kind = item.get("type")
            start = starts.get(item_id)
            provenance = {
                "raw_item_id": item_id,
                "raw_start_index": start[0] if start else None,
                "raw_completion_index": index,
            }
            if start and start[1].get("type") != kind:
                issue(
                    "instrumentation",
                    "item type changed across lifecycle",
                    **provenance,
                )
            if kind == "agentMessage":
                if isinstance(item.get("text"), str):
                    result["messages"].append(
                        {
                            **provenance,
                            "status": "completed",
                            "phase": item.get("phase"),
                            "text": item["text"],
                        }
                    )
                    outputs.append(item["text"])
                    if item.get("phase") == "final_answer":
                        result["final_output"] = (
                            result["final_output"] + "\n"
                            if result["final_output"]
                            else ""
                        ) + item["text"]
                    elif item.get("phase") == "commentary":
                        result["commentary"].append(item["text"])
                else:
                    issue("instrumentation", "malformed agent text", **provenance)
                continue
            if kind in PASSIVE_ITEMS:
                continue
            if not start:
                issue("instrumentation", "operation lacks start evidence", **provenance)
            status = item.get("status", "unverified")
            base = {**provenance, "status": status}
            if kind == "commandExecution":
                lifecycle_valid = bool(
                    start
                    and start[0] < index
                    and start[1].get("type") == kind
                    and start[1].get("status") == "inProgress"
                    and start[1].get("command") == item.get("command")
                    and start[1].get("cwd") == item.get("cwd")
                )
                if start and not lifecycle_valid:
                    issue(
                        "instrumentation",
                        "command lifecycle start fields disagree with completion",
                        **provenance,
                    )
                result["command_records"].append(
                    {
                        **provenance,
                        "status": status,
                        "exit_code": item.get("exitCode"),
                        "raw_command": item.get("command"),
                        "aggregated_output": item.get("aggregatedOutput"),
                        "lifecycle_valid": lifecycle_valid,
                    }
                )
                base.update(
                    exit_code=item.get("exitCode"),
                    raw_command=item.get("command"),
                    command_actions=item.get("commandActions"),
                    command_source=item.get("source", "agent"),
                )
                if (
                    not isinstance(item.get("command"), str)
                    or not isinstance(item.get("cwd"), str)
                    or not isinstance(item.get("commandActions"), list)
                    or (status == "completed" and type(item.get("exitCode")) is not int)
                ):
                    issue(
                        "instrumentation",
                        "malformed command execution fields",
                        **provenance,
                    )
                try:
                    # Initial negative fixture facts survive only bounded
                    # read-only prefixes, with no overlapping unknown command.
                    absence_safe = not any(
                        e["type"] in {"write", "unknown"}
                        or (
                            e["type"] in {"setup", "hook"}
                            and not e.get("absence_preserving")
                        )
                        or e.get("status") != "completed"
                        or e.get("exit_code", 0) != 0
                        for e in result["events"]
                    ) and not any(
                        other_id != item_id
                        and other_id not in completed_items
                        and other_item.get("type")
                        not in PASSIVE_ITEMS | {"agentMessage"}
                        for other_id, (_, other_item) in starts.items()
                    )
                    operations = _command_operations_v4(
                        item,
                        workspace,
                        manifest,
                        recorded_workspace,
                        absence_safe,
                        lifecycle_valid,
                    )
                except IsolationError as exc:
                    issue("isolation", str(exc), **provenance)
                    operations = [{"type": "unknown", "reason": str(exc)}]
                except (ValueError, KeyError, OSError, UnicodeError) as exc:
                    operations = [{"type": "unknown", "reason": str(exc)}]
            elif kind == "fileChange":
                operations = []
                changes = item.get("changes")
                if not isinstance(changes, list) or not changes:
                    changes = [{}]
                for change in changes:
                    try:
                        if not isinstance(change, dict):
                            raise ValueError("malformed file change")
                        change_kind = change.get("kind", {})
                        if (
                            not isinstance(change_kind, dict)
                            or change_kind.get("type") not in {"add", "update"}
                            or change_kind.get("move_path") is not None
                        ):
                            raise ValueError("file deletion, move or unknown change")
                        path = _map_path(
                            change.get("path"), workspace, workspace, recorded_workspace
                        )
                        operations.append(
                            {
                                "type": "write",
                                "path": path,
                                "change_kind": change_kind,
                                "diff": change.get("diff"),
                            }
                        )
                    except IsolationError as exc:
                        issue("isolation", str(exc), **provenance)
                        operations.append(
                            {"type": "unknown", "reason": str(exc), "change": change}
                        )
                    except ValueError as exc:
                        operations.append(
                            {"type": "unknown", "reason": str(exc), "change": change}
                        )
            else:
                operations = [
                    {
                        "type": "unknown",
                        "reason": "unsupported item type",
                        "raw_item_type": kind,
                    }
                ]
            for operation_index, operation in enumerate(operations):
                entry = {**base, **operation, "raw_operation_index": operation_index}
                if (
                    operation["type"] == "diagnostic"
                    and entry["status"] == "completed"
                    and entry.get("exit_code") == 0
                ):
                    result["diagnostics"].append(entry)
                else:
                    if operation["type"] == "diagnostic":
                        entry["type"] = "unknown"
                    result["events"].append(entry)
                    if entry["type"] == "unknown":
                        issue(
                            "fidelity",
                            entry.get("reason", "unclassified operation"),
                            **provenance,
                        )
                    if entry["status"] != "completed" or (
                        kind == "commandExecution" and entry.get("exit_code") != 0
                    ):
                        issue(
                            "fidelity", "failed or incomplete operation", **provenance
                        )
    for item_id, (index, item) in starts.items():
        if item_id not in completed_items and item.get("type") not in PASSIVE_ITEMS | {
            "agentMessage"
        }:
            entry = {
                "type": "unknown",
                "status": "incomplete",
                "raw_item_id": item_id,
                "raw_start_index": index,
                "raw_completion_index": None,
                "raw_item_type": item.get("type"),
            }
            result["events"].append(entry)
            issue(
                "instrumentation",
                "operation lacks completion evidence",
                raw_item_id=item_id,
            )
    if completion_index is None:
        issue("instrumentation", "missing turn completion")
    required_usage = (
        "inputTokens",
        "cachedInputTokens",
        "outputTokens",
        "reasoningOutputTokens",
        "totalTokens",
    )
    if not isinstance(usage, dict) or any(
        type(usage.get(k)) is not int or usage[k] < 0 for k in required_usage
    ):
        issue(
            "instrumentation",
            "missing or malformed final thread total usage",
            raw_event_index=usage_index,
        )
    else:
        if (
            usage["cachedInputTokens"] > usage["inputTokens"]
            or usage["reasoningOutputTokens"] > usage["outputTokens"]
            or usage["totalTokens"] != usage["inputTokens"] + usage["outputTokens"]
        ):
            issue(
                "instrumentation",
                "inconsistent final thread total usage",
                raw_event_index=usage_index,
            )
        result["usage"] = {
            **usage,
            "latency_ms": latency_ms,
            "raw_event_index": usage_index,
            "measurement": "last thread/tokenUsage/updated total; not summed",
        }
    for diagnostic in result["diagnostics"]:
        if diagnostic.get("reason") == "artifact directory creation":
            diagnostic["associated_write_item_ids"] = [
                e["raw_item_id"]
                for e in result["events"]
                if e["type"] == "write"
                and e.get("path") == diagnostic["artifact"]
                and e["raw_completion_index"] >= diagnostic["raw_completion_index"]
            ]
            if not diagnostic["associated_write_item_ids"]:
                issue(
                    "fidelity",
                    "directory creation has no subsequent artifact write",
                    raw_item_id=diagnostic["raw_item_id"],
                )
                result["events"].append({**diagnostic, "type": "unknown"})
    # Completion ordering alone can hide an unawaited hook. These independent
    # audit failures are also retained as unknown events so the frozen checker
    # cannot report a pass while only a side channel says fidelity failed.
    project = [e for e in result["events"] if e["type"] in {"setup", "hook", "write"}]
    for left, right in zip(project, project[1:]):
        if (
            left["raw_item_id"] != right["raw_item_id"]
            and right.get("raw_start_index") is not None
            and left.get("raw_completion_index") is not None
            and right["raw_start_index"] < left["raw_completion_index"]
        ):
            issue(
                "fidelity",
                "project operations overlap; awaiting is unproven",
                left_item_id=left["raw_item_id"],
                right_item_id=right["raw_item_id"],
            )
            result["events"].append(
                {
                    **right,
                    "type": "unknown",
                    "reason": "project operations overlap; awaiting is unproven",
                }
            )
    # Completion-sorted event lists do not prove that inputs were available when
    # a consuming action started. Check dependency lifecycle boundaries, while
    # allowing explicitly sequenced operations inside one bounded shell item.
    dependencies = [(path, {"write"}) for path in manifest.get("required_reads", [])]
    dependencies += [
        (PACKAGE + "/" + path, {"setup", "hook", "write", "read"})
        for path in manifest.get("expected_references", [])
    ]
    dependencies.append((".specify/extensions.yml", {"hook"}))
    for path, consumer_types in dependencies:
        reads = [
            e for e in result["events"] if e["type"] == "read" and e.get("path") == path
        ]
        consumers = [
            e
            for e in result["events"]
            if e["type"] in consumer_types
            and e.get("raw_start_index") is not None
            and not (
                e["type"] == "read" and str(e.get("path", "")).startswith(PACKAGE + "/")
            )
        ]
        if not reads or not consumers:
            continue  # The checker separately rejects absent required evidence.
        consumer = min(
            consumers, key=lambda e: (e["raw_start_index"], e["raw_operation_index"])
        )

        def ready(read):
            if read.get("status") != "completed" or read.get("exit_code") != 0:
                return False
            if read["raw_item_id"] == consumer["raw_item_id"]:
                return read["raw_operation_index"] < consumer["raw_operation_index"]
            return (
                read.get("raw_completion_index") is not None
                and read["raw_completion_index"] < consumer["raw_start_index"]
            )

        if not any(ready(read) for read in reads):
            detail = "required read did not complete before consuming action started"
            issue(
                "fidelity",
                detail,
                path=path,
                consumer_item_id=consumer["raw_item_id"],
                read_item_ids=[e["raw_item_id"] for e in reads],
            )
            result["events"].append(
                {
                    **consumer,
                    "type": "unknown",
                    "reason": detail,
                    "dependency_path": path,
                }
            )
    for item_id, fragments in deltas.items():
        if item_id not in completed_items:
            outputs.append("".join(fragments))
            result["diagnostics"].append(
                {
                    "type": "partial-output",
                    "raw_item_id": item_id,
                    "reason": "retained text deltas without completed message",
                }
            )
    result["output"] = "\n".join(outputs)
    result["instrumentation_valid"] = not any(
        i["kind"] == "instrumentation" for i in result["issues"]
    )
    return result
