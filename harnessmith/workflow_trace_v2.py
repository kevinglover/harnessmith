"""Versioned offline trace parser; never executes or rewrites captured commands.

V2 recognizes a bounded literal shell grammar. An && chain with a successful
exit certifies its recognized commands. For newline/semicolon statements and
conditional reads, a read additionally needs exact stdout from SHA-pinned input
bytes. Unsupported output producers leave the entire command unclassified.
Discovery is never a read.
This is an attribution instrument, not a general shell interpreter or OS audit.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import shlex

from .workflow_fidelity import PACKAGE, SETUP
from .workflow_trace import (
    IsolationError,
    WorkflowTraceError,
    MODEL,
    PASSIVE_ITEMS,
    _classify_words,
    _heredoc,
    _relative,
    _shell_body,
)

INSTRUMENTATION = "codex-workflow-trace-v2"
# The combined stream does not identify stdout versus stderr. These known failure
# diagnostics invalidate clean-success claims even if the final shell exit is 0.
FAILURE = re.compile(
    r"(?:operation not permitted|permission denied|can't create temp file|"
    r"no such file or directory|command not found|Traceback \(most recent call last\))",
    re.I,
)
CACHE_WARNING = re.compile(
    r"(?m)^python3: warning: confstr\(\) failed with code 5: couldn't get path "
    r"of DARWIN_USER_TEMP_DIR; using /tmp instead\r?\n"
    r"python3: error: couldn't create cache file '/tmp/xcrun_db-[A-Za-z0-9]+' "
    r"\(errno=Operation not permitted\)\r?\n"
)


def _split_shell(body):
    """Split operators outside quotes, retaining literal command spelling."""
    tokens, start, quote, index = [], 0, None, 0
    while index < len(body):
        char = body[index]
        if quote:
            if char == quote:
                quote = None
            elif char == "\\" and quote == '"':
                index += 1
            elif char in "$`" and quote == '"':
                raise ValueError("shell expansion or substitution is unsupported")
        elif char in "'\"":
            quote = char
        elif char == "\\":
            index += 1
        elif char == "#":
            raise ValueError("unquoted shell comments are unsupported")
        elif char in "$`*?{}~":
            raise ValueError("shell expansion or substitution is unsupported")
        elif char in ";&|<>\n":
            if body[start:index].strip():
                tokens.append(body[start:index].strip())
            end = index + 1
            if end < len(body) and body[end] == char and char in "&|<>":
                end += 1
            tokens.append(body[index:end])
            index, start = end - 1, end
        index += 1
    if quote:
        raise ValueError("unterminated quote")
    if body[start:].strip():
        tokens.append(body[start:].strip())
    return tokens


def _literal_words(source):
    # Validate tokens even when they came from a conditional branch.
    tokens = _split_shell(source)
    if len(tokens) != 1:
        raise ValueError("unsupported operator in simple command")
    words = shlex.split(source)
    if not words:
        raise ValueError("empty command")
    # Unquoted [] glob expansion is only allowed for the separately parsed test.
    unquoted = re.sub(r"'[^']*'|\"(?:\\.|[^\"])*\"", "", source)
    if "[" in unquoted or "]" in unquoted:
        raise ValueError("unquoted glob is unsupported")
    return words


def _statements(body):
    """Bounded grammar: literals, &&/newline/semicolon, one-level if test."""
    raw = _split_shell(body)
    statements, connectors = [], []
    index = 0
    while index < len(raw):
        if raw[index] in {"\n", ";"}:
            index += 1
            continue
        part = raw[index]
        if part.startswith("if "):
            block = [part]
            index += 1
            while index < len(raw) and raw[index] != "fi":
                block.append(raw[index])
                index += 1
            if index == len(raw):
                raise ValueError("unterminated or nested conditional")
            block.append("fi")
            part = " ".join(block)
        elif part in {"&&", "||", "|", "&", "<", ">", "<<", ">>"}:
            raise ValueError("unsupported shell operator")
        statements.append(part)
        index += 1
        if index < len(raw):
            connectors.append(raw[index])
            index += 1
    if len(connectors) == len(statements):
        if connectors[-1] not in {";", "\n"}:
            raise ValueError("incomplete compound command")
        connectors.pop()
    return statements, connectors


def _pinned_bytes(path, workspace, manifest):
    """Read only independently hashed initial inputs, never mutable after bytes."""
    baseline = manifest.get("baseline", {})
    expected = baseline.get(path)
    if not isinstance(expected, str):
        raise ValueError("read has no pinned initial bytes")
    if path == manifest.get("target") and manifest.get("baseline_target_hex"):
        data = bytes.fromhex(manifest["baseline_target_hex"])
    else:
        target = workspace / path
        _relative(str(target), workspace, workspace)
        data = target.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("pinned input hash mismatch")
    return data


def _map_path(value, cwd, workspace, recorded_workspace):
    if not isinstance(value, str):
        raise ValueError("malformed path")
    if recorded_workspace is not None and Path(value).is_absolute():
        try:
            value = str(workspace / Path(value).relative_to(recorded_workspace))
        except ValueError as exc:
            raise IsolationError("recorded absolute path is outside workspace") from exc
    return _relative(value, cwd, workspace)


def _printf(words):
    if words[0] == "echo" and len(words) >= 2 and not words[1].startswith("-"):
        return " ".join(words[1:]) + "\n"
    if words[0] != "printf" or len(words) < 2:
        raise ValueError("unsupported literal output command")
    fmt = words[1]
    # A deliberately tiny, deterministic subset; no numeric/octal formatting.
    if re.search(r"\\(?![ntr\\])", fmt):
        raise ValueError("unsupported printf escape")
    fmt = fmt.replace("\\n", "\n").replace("\\t", "\t")
    fmt = fmt.replace("\\r", "\r").replace("\\\\", "\\")
    if len(words) == 2 and "%" not in fmt:
        return fmt
    if len(words) == 3 and fmt.count("%s") == 1 and fmt.replace("%s", "").find("%") < 0:
        return fmt.replace("%s", words[2])
    raise ValueError("unsupported printf arguments")


def _classify_v2(words, cwd, workspace, manifest, recorded_workspace):
    # Translate only path positions; never rewrite raw_command/provenance.
    command = Path(words[0]).name
    if command in {"printf", "echo", "rg"} and words[0] != command:
        raise ValueError("qualified output/discovery executable is unverified")
    translated = list(words)
    # Only supported system executables retain absolute paths verbatim.
    system = {
        "/bin/cat",
        "/bin/ls",
        "/bin/pwd",
        "/bin/mkdir",
        "/usr/bin/sed",
        "/bin/bash",
        "/bin/sh",
        "/usr/bin/python3",
    }
    for index, word in enumerate(words):
        if Path(word).is_absolute() and not (index == 0 and word in system):
            translated[index] = str(
                workspace / _map_path(word, cwd, workspace, recorded_workspace)
            )
    if command in {"printf", "echo"}:
        return [
            {
                "type": "diagnostic",
                "reason": "literal output label",
                "expected_output": _printf(words),
            }
        ]
    if command == "rg" and words[1:2] == ["--files"]:
        paths, patterns, index = [], [], 2
        while index < len(words):
            if words[index] == "-g" and index + 1 < len(words):
                pattern = words[index + 1]
                if (
                    pattern.startswith("/")
                    or ".." in Path(pattern).parts
                    or "\\" in pattern
                ):
                    raise IsolationError("discovery pattern escapes workspace")
                patterns.append(pattern)
                index += 2
            elif words[index].startswith("-"):
                raise ValueError("unsupported rg option")
            else:
                paths.append(
                    _map_path(words[index], cwd, workspace, recorded_workspace)
                )
                index += 1
        return [
            {
                "type": "diagnostic",
                "reason": "file discovery",
                "paths": paths or [_relative(str(cwd), cwd, workspace)],
                "patterns": patterns,
            }
        ]
    return _classify_words(translated, cwd, workspace, manifest)


def _read_output(operation, words, workspace, manifest):
    data = _pinned_bytes(operation["path"], workspace, manifest).decode("utf-8")
    if Path(words[0]).name == "sed":
        bounds = words[2].rstrip("p").split(",")
        first, last = int(bounds[0]), int(bounds[-1])
        data = "".join(data.splitlines(keepends=True)[first - 1 : last])
    if not data:
        raise ValueError("empty stdout cannot establish an individual read")
    return data


def _read_coverage(operation, words, workspace, manifest):
    if operation["type"] != "read" or Path(words[0]).name != "sed":
        return
    data = _pinned_bytes(operation["path"], workspace, manifest).decode("utf-8")
    bounds = words[2].rstrip("p").split(",")
    first, last = int(bounds[0]), int(bounds[-1])
    complete = first == 1 and last >= len(data.splitlines())
    operation["read_coverage"] = {
        "first_line": first,
        "last_line": last,
        "pinned_total_lines": len(data.splitlines()),
        "complete": complete,
    }
    mandatory = operation["path"] in manifest.get("required_reads", []) or operation[
        "path"
    ].startswith(PACKAGE + "/references/")
    if mandatory and not complete:
        raise ValueError("partial range cannot satisfy mandatory input/reference read")


def _setup_span(output, cursor, workspace, recorded_workspace, manifest):
    # Validate the known adapter and exact result shape. An arbitrary JSON print
    # does not certify setup because syntax must separately name that adapter.
    _pinned_bytes(SETUP, workspace, manifest)
    template = _pinned_bytes(
        ".specify/templates/checklist-template.md", workspace, manifest
    ).decode("utf-8")
    root = recorded_workspace or workspace
    expected = {
        "FEATURE_DIR": str(root / "specs/001-invitations"),
        "AVAILABLE_DOCS": ["spec.md"],
        "TEMPLATE_CONTENT": template,
    }
    position = cursor
    for line in output[cursor:].splitlines(keepends=True):
        try:
            actual = json.loads(line)
        except ValueError:
            actual = None
        if actual == expected:
            return position + len(line)
        position += len(line)
    raise ValueError("setup stdout does not match pinned adapter result")


def _hook_span(output, cursor, workspace, manifest, command):
    """Corroborate only the two known synthetic marker adapters, never hooks generally."""
    _pinned_bytes(".pilot/marker_hook.py", workspace, manifest)
    if command == "pilot-pre-marker":
        digest = manifest.get("baseline", {}).get(manifest["target"])
    elif command == "pilot-post-marker":
        target = workspace / manifest["target"]
        _relative(str(target), workspace, workspace)
        digest = (
            hashlib.sha256(target.read_bytes()).hexdigest()
            if target.is_file()
            else None
        )
    else:
        raise ValueError("only mandatory synthetic marker results are corroborated")
    expected = {
        "command": command,
        "target_exists": digest is not None,
        "target_sha256": digest,
    }
    position = cursor
    for line in output[cursor:].splitlines(keepends=True):
        try:
            actual = json.loads(line)
        except ValueError:
            actual = None
        if actual == expected:
            return position + len(line)
        position += len(line)
    raise ValueError("hook stdout does not match pinned synthetic marker result")


def _runtime_cache_noise(output, parsed, item, workspace, recorded_workspace, manifest):
    """Exclude exact macOS cache noise only after pinned adapter corroboration."""
    if item.get("status") != "completed" or item.get("exitCode") != 0:
        return output, []
    warnings = CACHE_WARNING.findall(output)
    if not warnings:
        return output, []
    clean = CACHE_WARNING.sub("", output)
    runtime = [
        op for _, _, _, ops in parsed for op in ops if op["type"] in {"setup", "hook"}
    ]
    if not runtime:
        return output, []
    try:
        cursor = 0
        for operation in runtime:
            if operation["type"] == "setup":
                cursor = _setup_span(
                    clean, cursor, workspace, recorded_workspace, manifest
                )
            else:
                cursor = _hook_span(
                    clean, cursor, workspace, manifest, operation["command"]
                )
    except (ValueError, OSError, UnicodeError):
        return output, []
    return clean, [
        {
            "type": "diagnostic",
            "reason": "corroborated synthetic adapter macOS cache warning",
            "raw_warning_output": "".join(warnings),
            "success_evidence": "exit zero, pinned adapter and matching JSON result",
        }
    ]


def _conditional(source, cwd, workspace, manifest, recorded_workspace):
    match = re.fullmatch(
        r"if\s+\[\s+-(f|d)\s+(.+?)\s+\]\s*;\s*then\s+(.+?)\s*;\s*(?:else\s+(.+?)\s*;\s*)?fi",
        source,
        re.S,
    )
    if not match:
        raise ValueError("unsupported conditional; only literal fixture existence/read")
    path_words = _literal_words("cat " + match[2])[1:]
    if len(path_words) != 1:
        raise ValueError("conditional test must name one literal path")
    path = _map_path(path_words[0], cwd, workspace, recorded_workspace)
    baseline = manifest.get("baseline", {})
    exists = (
        path in baseline
        if match[1] == "f"
        else any(p.startswith(path + "/") for p in baseline)
    )
    yes = _literal_words(match[3])
    # Validate BOTH branches even if one would be unexecuted. No arbitrary hook,
    # writes or side effects can hide behind an absent fixture.
    yes_operations = _classify_v2(yes, cwd, workspace, manifest, recorded_workspace)
    if any(
        op["type"] != "read" and op.get("reason") != "file discovery"
        for op in yes_operations
    ):
        raise ValueError("conditional body is not bounded read/discovery")
    if any(op["type"] == "read" and op["path"] != path for op in yes_operations):
        raise ValueError("conditional read differs from tested fixture")
    no = _literal_words(match[4]) if match[4] else None
    if no is not None:
        _printf(no)
    if exists:
        return yes, yes_operations
    return no, [
        {
            "type": "diagnostic",
            "reason": "fixture absence",
            "path": path,
            "expected_output": _printf(no) if no else None,
        }
    ]


def _command_operations_v2(item, workspace, manifest, recorded_workspace):
    if item.get("source", "agent") not in {"agent", "unifiedExecStartup"}:
        raise ValueError("command source is not a verified agent command")
    cwd_value = item.get("cwd")
    if not isinstance(cwd_value, str) or not Path(cwd_value).is_absolute():
        raise ValueError("command cwd must be absolute")
    cwd = workspace / _map_path(cwd_value, workspace, workspace, recorded_workspace)
    body = _shell_body(item.get("command"))
    output = item.get("aggregatedOutput")
    if not isinstance(output, str):
        output = ""
    failed_text = bool(FAILURE.search(output))
    # Keep the known literal heredoc form. Any output failure defeats shell exit0.
    if "<<" in body:
        if failed_text:
            return [
                {
                    "type": "unknown",
                    "status": "failed",
                    "reason": "captured command failure despite aggregate shell exit",
                    "failure_output": True,
                }
            ]
        prefix, write = _heredoc(body)
        parts, connectors = _statements(prefix) if prefix else ([], [])
        if any(c != "&&" for c in connectors):
            raise ValueError("heredoc prefix must prove successful sequencing")
        result = []
        for part in parts:
            result.extend(
                _classify_v2(
                    _literal_words(part), cwd, workspace, manifest, recorded_workspace
                )
            )
        write["path"] = _map_path(write["path"], cwd, workspace, recorded_workspace)
        if write["path"] != manifest["target"]:
            raise ValueError("shell write target is not the prepared artifact")
        return result + [write]
    statements, connectors = _statements(body)
    terminal_discovery = False
    # A deliberately narrow terminal discovery pipeline cannot spoof file
    # contents. Successful && prefixes therefore remain attributable. The rg
    # producer's exit is STILL unavailable behind sort, and remains an unknown
    # event below; this is not general pipeline support or a clean workflow pass.
    if (
        connectors
        and connectors[-1] == "|"
        and all(c == "&&" for c in connectors[:-1])
        and _literal_words(statements[-1]) == ["sort"]
    ):
        candidate = _literal_words(statements[-2])
        discovery = _classify_v2(
            candidate, cwd, workspace, manifest, recorded_workspace
        )
        if len(discovery) == 1 and discovery[0].get("reason") == "file discovery":
            terminal_discovery = True
            statements, connectors = statements[:-1], connectors[:-1]
    if any(c not in {"&&", ";", "\n"} for c in connectors):
        raise ValueError(
            "pipes, fallbacks and unsupported shell operators are unclassified"
        )
    # Preflight the WHOLE grammar before crediting stdout. An arbitrary later
    # command could otherwise print pinned content that a failed earlier cat
    # never read. No stdout fact is attributed through an unknown producer.
    parsed = []
    for statement in statements:
        conditional = statement.startswith("if ")
        if conditional:
            words, operations = _conditional(
                statement, cwd, workspace, manifest, recorded_workspace
            )
        else:
            words = _literal_words(statement)
            operations = _classify_v2(
                words, cwd, workspace, manifest, recorded_workspace
            )
        for operation in operations:
            _read_coverage(operation, words, workspace, manifest)
        parsed.append((statement, conditional, words, operations))
    output, result = _runtime_cache_noise(
        output, parsed, item, workspace, recorded_workspace, manifest
    )
    failed_text = bool(FAILURE.search(output))
    chain_success = (
        item.get("status") == "completed"
        and item.get("exitCode") == 0
        and not failed_text
        and all(c == "&&" for c in connectors)
    )
    cursor = 0
    for statement_index, (statement, conditional, words, operations) in enumerate(
        parsed
    ):
        if terminal_discovery and statement_index == len(parsed) - 1:
            result.append(
                {
                    "type": "unknown",
                    "status": "unverified",
                    "reason": "terminal discovery pipeline producer exit is unavailable",
                    "raw_statement": statement + " | sort",
                }
            )
            continue
        try:
            for operation in operations:
                # Pin + exact stdout evidence is mandatory for aggregate newline
                # success and conditional reads; pure && retains v1 guarantees.
                if operation["type"] == "read" and (not chain_success or conditional):
                    expected = _read_output(operation, words, workspace, manifest)
                    offset = output.find(expected, cursor)
                    if offset < 0:
                        raise ValueError(
                            "read stdout not established from pinned input"
                        )
                    cursor = offset + len(expected)
                    operation["success_evidence"] = (
                        "pinned input bytes in ordered stdout"
                    )
                elif operation["type"] == "setup" and not chain_success:
                    cursor = _setup_span(
                        output, cursor, workspace, recorded_workspace, manifest
                    )
                    operation["success_evidence"] = (
                        "pinned adapter result in ordered stdout"
                    )
                elif operation["type"] == "hook" and not chain_success:
                    cursor = _hook_span(
                        output, cursor, workspace, manifest, operation["command"]
                    )
                    operation["success_evidence"] = (
                        "pinned marker result in ordered stdout"
                    )
                elif operation.get("expected_output") is not None:
                    expected = operation.pop("expected_output")
                    offset = output.find(expected, cursor)
                    if not chain_success and (not expected or offset < 0):
                        raise ValueError("literal branch/output label not established")
                    if offset >= 0:
                        cursor = offset + len(expected)
                elif not chain_success:
                    raise ValueError("individual statement success unproven")
                # Partial command facts must not inherit aggregate success when
                # explicit failure output was captured elsewhere in the item.
                operation["success_evidence"] = operation.get(
                    "success_evidence", "successful bounded && command"
                )
                result.append(operation)
        except IsolationError:
            raise
        except (ValueError, OSError, UnicodeError) as exc:
            result.append(
                {
                    "type": "unknown",
                    "status": "unverified",
                    "reason": str(exc),
                    "raw_statement": statement,
                }
            )
    if failed_text:
        result.append(
            {
                "type": "unknown",
                "status": "failed",
                "reason": "captured command failure despite aggregate shell exit",
                "failure_output": True,
            }
        )
    # CommandActions are best-effort: they may omit individual compound reads,
    # but an asserted read still must agree with a parsed and certified read.
    actions = item.get("commandActions")
    if not isinstance(actions, list) or any(not isinstance(a, dict) for a in actions):
        raise ValueError("missing or malformed commandActions")
    reads = {op["path"] for op in result if op["type"] == "read"}
    for action in actions:
        if (
            action.get("type") == "read"
            and _map_path(action.get("path"), cwd, workspace, recorded_workspace)
            not in reads
        ):
            result.append(
                {
                    "type": "unknown",
                    "reason": "declared read disagrees with certified parsed command",
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
        "schema_version": 2,
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
                    operations = _command_operations_v2(
                        item, workspace, manifest, recorded_workspace
                    )
                except IsolationError as exc:
                    issue("isolation", str(exc), **provenance)
                    operations = [{"type": "unknown", "reason": str(exc)}]
                except (ValueError, KeyError) as exc:
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
                    and item.get("exitCode") == 0
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
                        kind == "commandExecution" and item.get("exitCode") != 0
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
                e["type"] == "read"
                and str(e.get("path", "")).startswith(PACKAGE + "/")
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
