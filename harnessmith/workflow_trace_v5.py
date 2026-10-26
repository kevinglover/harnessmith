"""Schema-5 offline attribution of bounded Python reads and existing append proofs.

Only static AST shapes and exact captured outputs are interpreted. Captured code
is never executed. Frozen v4 helpers retain their historical semantics; the new
lifecycle driver supplies explicit ordering for prewrite and final-byte proofs.
"""

from __future__ import annotations

import ast
import hashlib
import math
from pathlib import Path

from .workflow_fidelity import PACKAGE
from .workflow_trace import IsolationError, MODEL, PASSIVE_ITEMS, WorkflowTraceError, _shell_body
from .workflow_trace_v3 import CACHE_WARNING, _absence_certificate, _classify_v2, _literal_words, _map_path, _pinned_bytes, _statements
from .workflow_trace_v4 import RUNTIME_FAILURE, _command_context, _command_operations_v4, _declared_reads, _discovery, _strict_path

INSTRUMENTATION = "codex-workflow-trace-v5"
PYTHON = (["python3", "-c"], ["/usr/bin/python3", "-c"])

def _python_read_ast(words):
    """Return one of two complete read-only trees; never execute captured code."""
    if words[:2] not in PYTHON or len(words) != 3:
        raise ValueError("read-only Python requires a verified executable and one script")
    try:
        parsed = ast.parse(words[2], mode="exec")
    except (ValueError, SyntaxError) as exc:
        raise ValueError("invalid read-only Python syntax") from exc
    body = parsed.body
    if len(body) < 4:
        raise ValueError("unsupported read-only Python statement count")
    assignment = body[1]
    if not (
        isinstance(assignment, ast.Assign)
        and len(assignment.targets) == 1
        and isinstance(assignment.targets[0], ast.Name)
        and isinstance(assignment.value, ast.Call)
        and len(assignment.value.args) == 1
        and isinstance(assignment.value.args[0], ast.Constant)
        and type(assignment.value.args[0].value) is str
    ):
        raise ValueError("read-only Python requires a literal Path assignment")
    name = assignment.targets[0].id
    if name in {"Path", "print", "repr"}:
        raise ValueError("read variables cannot shadow imported names or builtins")
    path = assignment.value.args[0].value
    prefix = f"from pathlib import Path; {name}=Path({path!r}); "
    expected = ast.parse(
        prefix + f"print('EXISTS', {name}.exists()); "
        f"print({name}.read_text() if {name}.exists() else '')"
    )
    if ast.dump(parsed) == ast.dump(expected):
        return path, "exists", []
    byte_assignment = body[2]
    if not (
        isinstance(byte_assignment, ast.Assign)
        and len(byte_assignment.targets) == 1
        and isinstance(byte_assignment.targets[0], ast.Name)
    ):
        raise ValueError("byte read requires a simple variable assignment")
    byte_name = byte_assignment.targets[0].id
    if byte_name in {name, "Path", "print", "repr"}:
        raise ValueError("byte variables must be distinct and cannot shadow builtins")
    expected_prefix = ast.parse(prefix + f"{byte_name}={name}.read_bytes()")
    if [ast.dump(node) for node in body[:3]] != [
        ast.dump(node) for node in expected_prefix.body
    ]:
        raise ValueError("byte read is outside the bounded literal grammar")
    # Exactly one repr and one decode, in order; zero, one or two literal
    # labels may occur before them. Labels have no side effects or formatting.
    if len(body) not in {5, 6, 7}:
        raise ValueError("unsupported number of byte-read print statements")
    representations = [
        ast.dump(ast.parse(f"print(repr({byte_name}))").body[0]),
        ast.dump(ast.parse(f"print({byte_name}.decode())").body[0]),
    ]
    parts, next_representation = [], 0
    for statement in body[3:]:
        if (
            next_representation < 2
            and ast.dump(statement) == representations[next_representation]
        ):
            parts.append(("repr", None) if next_representation == 0 else ("text", None))
            next_representation += 1
        elif (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "print"
            and not statement.value.keywords
            and len(statement.value.args) == 1
            and isinstance(statement.value.args[0], ast.Constant)
            and type(statement.value.args[0].value) in {str, bytes}
            and next_representation < 2
        ):
            parts.append(("label", statement.value.args[0].value))
        else:
            raise ValueError("byte-read print is outside the bounded literal grammar")
    if next_representation != 2:
        raise ValueError("byte read requires repr and complete decode output")
    return path, "bytes", parts


def _read_bytes(path, workspace, manifest, prior_events, start_index):
    """Select pinned initial bytes or actual final bytes after an ordered write."""
    writes = [event for event in prior_events if event.get("type") == "write"
              and event.get("path") == path]
    if not writes:
        return _pinned_bytes(path, workspace, manifest), "before"
    if path != manifest.get("target") or any(
        event.get("status") != "completed"
        or event.get("exit_code", 0) != 0
        or type(event.get("raw_completion_index")) is not int
        or type(start_index) is not int
        or event["raw_completion_index"] >= start_index
        for event in writes
    ):
        raise ValueError("final read lacks completed write-before-read ordering")
    if any(
        event.get("type") == "unknown"
        and event.get("raw_completion_index", -1) >= writes[-1]["raw_completion_index"]
        for event in prior_events
    ):
        raise ValueError("unknown operation intervenes between write and final read")
    data = (workspace / path).read_bytes()
    if not data:
        raise ValueError("final artifact is empty")
    return data, "after"


def _read_fact(path, data, timing):
    fact = {
        "type": "read", "path": path,
        "read_sha256": hashlib.sha256(data).hexdigest(),
        "read_coverage": {"complete": True},
        "success_evidence": "bounded read-only grammar, exact captured output and selected bytes",
    }
    fact["read_after_write" if timing == "after" else "read_before_write"] = True
    return fact


def _python_read_output(
    words, cwd, workspace, manifest, recorded_workspace, absence_safe,
    prior_events, start_index,
):
    literal, mode, parts = _python_read_ast(words)
    path = _strict_path(literal, cwd, workspace, recorded_workspace)
    if mode == "exists" and path in manifest.get("pinned_absent_paths", []):
        if (path != ".specify/extensions.yml" or any(
                event.get("type") in {"write", "unknown", "setup", "hook"}
                for event in prior_events)):
            raise ValueError("extension absence lacks an unchanged pinned absence fact")
        _absence_certificate(path, workspace, manifest, absence_safe)
        return "EXISTS False\n\n", [{
            "type": "diagnostic", "path": path, "certified_absence": True,
            "reason": "fixture absence",
            "success_evidence": "pinned initial absence and exact bounded Python existence output",
        }]
    data, timing = _read_bytes(path, workspace, manifest, prior_events, start_index)
    text = data.decode("utf-8")
    if mode == "exists":
        expected = "EXISTS True\n" + text + "\n"
    else:
        expected = "".join(
            (repr(data) if kind == "repr" else text if kind == "text" else str(value)) + "\n"
            for kind, value in parts
        )
    return expected, [_read_fact(path, data, timing)]


def _discovery_suffix(output, operation, cwd, workspace, recorded_workspace):
    """Validate listing shape/scope; discovery still proves no contents/absence."""
    if not output or not output.endswith("\n"):
        raise ValueError("successful discovery requires a complete captured listing")
    seen = set()
    roots = operation["paths"]
    for line in output.splitlines():
        if not line or line in seen or RUNTIME_FAILURE.search(line):
            raise ValueError("discovery output is duplicate, empty or a diagnostic")
        seen.add(line)
        path = _strict_path(line, cwd, workspace, recorded_workspace)
        if not (workspace / path).is_file() or not any(
            root in {".", ""} or path == root or path.startswith(root + "/")
            for root in roots
        ):
            raise ValueError("discovery output escapes its declared file scope")


def _python_read_chain(
    item, statements, connectors, cwd, workspace, manifest, recorded_workspace,
    absence_safe, prior_events, start_index,
):
    if not statements or any(connector != "&&" for connector in connectors):
        raise ValueError("read-only Python supports only standalone or bounded && commands")
    if (item.get("status") not in {"completed", "failed"}
            or type(item.get("exitCode")) is not int
            or (item.get("exitCode") == 0 and item.get("status") != "completed")):
        raise ValueError("read-only Python requires a completed integer-exit command")
    parsed = [_literal_words(statement) for statement in statements]
    if not any(words[:2] in PYTHON for words in parsed):
        raise ValueError("no bounded read-only Python operation")
    output = item.get("aggregatedOutput")
    if not isinstance(output, str):
        raise ValueError("read-only Python requires captured text output")
    expected, result, reads = "", [], set()
    discovery = None
    for index, words in enumerate(parsed):
        if words[:2] in PYTHON:
            text, operations = _python_read_output(
                words, cwd, workspace, manifest, recorded_workspace, absence_safe,
                prior_events, start_index,
            )
            expected += text
        elif words[0] in {"cat", "/bin/cat"} and len(words) > 1:
            arguments = words[1:]
            if arguments[:1] == ["--"]:
                arguments = arguments[1:]
            if not arguments or any(arg.startswith("-") for arg in arguments):
                raise ValueError("bounded cat requires literal file arguments")
            operations = []
            for argument in arguments:
                path = _strict_path(argument, cwd, workspace, recorded_workspace)
                data, timing = _read_bytes(path, workspace, manifest, prior_events, start_index)
                expected += data.decode("utf-8")
                operations.append(_read_fact(path, data, timing))
        elif words[:2] == ["rg", "--files"] and index == len(parsed) - 1:
            discovery = _discovery(words, cwd, workspace, manifest, recorded_workspace)
            if len(words) == 2 or (len(words) == 3 and words[-1] == "--hidden"):
                raise ValueError("read-only chain discovery must be explicitly scoped")
            operations = [discovery]
        elif words[0] in {"printf", "echo"}:
            operations = _classify_v2(words, cwd, workspace, manifest, recorded_workspace)
            expected += operations[0].pop("expected_output")
        else:
            raise ValueError("unsupported operation in read-only Python chain")
        for operation in operations:
            if operation["type"] == "read":
                reads.add(operation["path"])
        result.extend(operations)
    _declared_reads(item, reads, cwd, workspace, recorded_workspace)
    clean = CACHE_WARNING.sub("", output)
    if RUNTIME_FAILURE.search(clean) or not clean.startswith(expected):
        raise ValueError("read-only command lacks exact complete ordered output")
    suffix = clean[len(expected):]
    if discovery is None:
        if suffix or item["exitCode"] != 0:
            raise ValueError("read-only command has extra output or nonzero exit")
    elif item["exitCode"] == 0:
        _discovery_suffix(suffix, discovery, cwd, workspace, recorded_workspace)
    elif item["exitCode"] == 1 and not suffix:
        # Prefix proofs remain useful, but this envelope is still a failure.
        result.pop()
        result.append({
            "type": "unknown", "status": "failed", "exit_code": 1,
            "reason": "nonzero discovery retained after exact read-only prefix",
        })
    else:
        raise ValueError("discovery exit/output cannot be corroborated")
    if output != clean:
        warnings = CACHE_WARNING.findall(output)
        # Startup can report the same exact pair more than once per invocation.
        # Count is not success evidence: the complete static grammar, selected
        # bytes and exact remaining output independently establish the operation.
        result.insert(0, {
            "type": "diagnostic", "reason": "corroborated read-only Python cache warning",
            "raw_warning_output": "".join(warnings),
            "success_evidence": "complete bounded read-only operation and exact captured output",
        })
    for operation in result:
        if operation.get("status") != "failed":
            operation.update(status="completed", exit_code=0, envelope_exit_code=item["exitCode"])
    return result


def _standalone_cat_read(
    item, words, cwd, workspace, manifest, recorded_workspace, prior_events, start_index,
):
    """A full standalone cat can carry the same exact-byte proof as Python."""
    arguments = words[1:]
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    if len(arguments) != 1 or arguments[0].startswith("-"):
        raise ValueError("standalone cat proof requires exactly one literal file")
    if (item.get("status") != "completed" or type(item.get("exitCode")) is not int
            or item["exitCode"] != 0):
        raise ValueError("standalone cat proof requires successful completed execution")
    path = _strict_path(arguments[0], cwd, workspace, recorded_workspace)
    data, timing = _read_bytes(path, workspace, manifest, prior_events, start_index)
    output = item.get("aggregatedOutput")
    if not isinstance(output, str) or output != data.decode("utf-8"):
        raise ValueError("standalone cat lacks exact complete selected-byte output")
    if RUNTIME_FAILURE.search(output):
        raise ValueError("standalone cat output contains an execution failure")
    _declared_reads(item, {path}, cwd, workspace, recorded_workspace)
    return [_read_fact(path, data, timing)]


def _command_operations_v5(
    item, workspace, manifest, recorded_workspace, absence_safe, lifecycle_valid,
    prior_events, start_index, read_order_safe,
):
    try:
        body = _shell_body(item.get("command"))
        statements, connectors = _statements(body) if "<<" not in body else ([], [])
        words = [_literal_words(part) for part in statements if not part.startswith("if ")]
        candidates = [part for part in words if part[:2] in PYTHON]
        standalone_cat = (len(statements) == len(words) == 1 and not connectors
                          and words[0][0] in {"cat", "/bin/cat"})
        # A recognized read tree selects the new whole-command validator.
        # Unsupported trees continue through the frozen append/write grammar.
        recognized = False
        for candidate in candidates:
            try:
                _python_read_ast(candidate)
                recognized = True
            except ValueError:
                pass
        if not recognized and not standalone_cat:
            return _command_operations_v4(
                item, workspace, manifest, recorded_workspace, absence_safe, lifecycle_valid
            )
        if not lifecycle_valid:
            raise ValueError("exact read requires matching start/completion lifecycle")
        if not read_order_safe:
            raise ValueError("exact read overlaps an uncompleted operation")
        cwd = _command_context(item, workspace, recorded_workspace)
        if standalone_cat:
            result = _standalone_cat_read(
                item, words[0], cwd, workspace, manifest, recorded_workspace,
                prior_events, start_index,
            )
        else:
            result = _python_read_chain(
                item, statements, connectors, cwd, workspace, manifest, recorded_workspace,
                absence_safe, prior_events, start_index,
            )
    except IsolationError:
        raise
    except (ValueError, KeyError, OSError, UnicodeError) as exc:
        result = [{"type": "unknown", "reason": str(exc)}]
    output = item.get("aggregatedOutput", "")
    if isinstance(output, str) and any(
        e.get("type") == "diagnostic" and "cache warning" in e.get("reason", "")
        and e.get("raw_warning_output") for e in result
    ):
        output = CACHE_WARNING.sub("", output)
    if (isinstance(output, str) and RUNTIME_FAILURE.search(output)
            and not any(e.get("status") == "failed" for e in result)):
        result.append({"type": "unknown", "status": "failed", "failure_output": True,
                       "reason": "captured constituent failure retained despite envelope/recovery"})
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
        "schema_version": 5,
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
                try:
                    record_cwd = _command_context(item, workspace, recorded_workspace)
                    cwd_relative = record_cwd.relative_to(workspace).as_posix()
                except (ValueError, IsolationError, OSError):
                    cwd_relative = None
                result["command_records"].append(
                    {
                        **provenance,
                        "status": status,
                        "exit_code": item.get("exitCode"),
                        "raw_command": item.get("command"),
                        "raw_cwd": item.get("cwd"),
                        "cwd_relative": cwd_relative,
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
                    operations = _command_operations_v5(
                        item,
                        workspace,
                        manifest,
                        recorded_workspace,
                        absence_safe,
                        lifecycle_valid,
                        result["events"],
                        provenance["raw_start_index"],
                        not any(
                            other_id != item_id
                            and other_id not in completed_items
                            and other_item.get("type") not in PASSIVE_ITEMS | {"agentMessage"}
                            for other_id, (_, other_item) in starts.items()
                        ),
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
