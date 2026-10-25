"""Conservative, offline normalization of the workflow pilot's App Server trace.

This module never executes commands. A successful shell exit is not permission to
invent reads from stdout, nor proof that an unfamiliar command was harmless.
Unknown operations remain failing events; neutral discovery is retained in a
separate audit list. Raw indices address the supplied notification list (zero
based), which the collector must retain verbatim alongside the observation.
"""

from __future__ import annotations

from pathlib import Path
import re
import shlex
import math

from .workflow_fidelity import SETUP, SETUP_COMMAND


INSTRUMENTATION = "codex-workflow-trace-v1"
MODEL = "gpt-6-luna"
OPERATIONS = {"commandExecution", "fileChange"}
PASSIVE_ITEMS = {"userMessage", "reasoning", "plan"}


class WorkflowTraceError(ValueError):
    """The caller supplied unusable inputs, rather than a captured session."""


class IsolationError(ValueError):
    """A known operation addresses a path outside its synthetic workspace."""


def _relative(value, cwd, workspace):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("missing or malformed path")
    path = Path(value)
    path = path if path.is_absolute() else cwd / path
    # Resolve existing links and reject escapes, including non-existing targets.
    try:
        return path.resolve().relative_to(workspace).as_posix()
    except ValueError as exc:
        raise IsolationError("operation addresses a path outside workspace") from exc


def _shell_body(command):
    if not isinstance(command, str) or not command.strip():
        raise ValueError("missing command")
    lexer = shlex.shlex(command, posix=True)
    lexer.whitespace_split = True
    executable = next(iter(lexer), None)
    if executable in {"sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh"}:
        words = shlex.split(command)
        if len(words) > 1 and words[1] not in {"-c", "-lc"}:
            return command
        if len(words) != 3 or words[1] not in {"-c", "-lc"}:
            raise ValueError("unrecognized shell wrapper")
        return words[2]
    return command


def _heredoc(body):
    """Recognize a single literal cat heredoc, optionally after safe commands.

    Only a quoted delimiter disables interpolation. The body is never inspected
    as shell code. Both redirection orders are supported; a trailing command is
    deliberately unsupported. The caller still validates every prefix command.
    """
    if "<<" not in body:
        return body, None
    first, separator, rest = body.partition("\n")
    if not separator:
        raise ValueError("incomplete heredoc")
    match = re.search(r"\bcat\s+(.+)$", first)
    if not match:
        raise ValueError("unsupported heredoc command")
    redirects = match.group(1)
    delimiter = re.search(r"<<\s*(['\"])([A-Za-z_][A-Za-z_0-9]*)\1", redirects)
    if not delimiter:
        raise ValueError("heredoc delimiter must be literal and quoted")
    redirect_only = redirects[: delimiter.start()] + redirects[delimiter.end() :]
    write = re.fullmatch(r"\s*(>>?)\s*(.+?)\s*", redirect_only)
    if not write:
        raise ValueError("unsupported heredoc redirection")
    destination = shlex.split(write.group(2))
    if len(destination) != 1 or any(c in destination[0] for c in "$`*?[]{}~"):
        raise ValueError("nonliteral heredoc target")
    lines = rest.splitlines(keepends=True)
    endings = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == delimiter[2]]
    if not endings or endings[0] != len(lines) - 1:
        raise ValueError("heredoc terminator missing or followed by commands")
    prefix = first[: match.start()].strip()
    if prefix:
        if not prefix.endswith("&&"):
            raise ValueError("heredoc prefix must use successful && sequencing")
        prefix = prefix[:-2].strip()
    return prefix, {"type": "write", "path": destination[0], "write_mode": write[1]}


def _segments(body):
    if not body:
        return []
    if any(c in body for c in "$`*?[]{}~"):
        raise ValueError("shell expansion or substitution is unsupported")
    lexer = shlex.shlex(body, posix=True, punctuation_chars=";&|<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    result = []
    words: list[str] = []
    for token in lexer:
        if token == "&&":
            if not words:
                raise ValueError("empty compound command")
            result.append(words)
            words = []
        elif token in {";", "\n"}:
            raise ValueError("aggregate exit cannot establish each statement's success")
        elif token and all(c in ";&|<>\n" for c in token):
            raise ValueError("unsupported shell operator")
        else:
            words.append(token)
    if not words:
        raise ValueError("incomplete compound command")
    result.append(words)
    return result


def _classify_words(words, cwd, workspace, manifest):
    executable, args = words[0], words[1:]
    command = Path(executable).name
    # Executables are deliberately restricted to system names and known paths.
    if "/" in executable and executable not in {
        "/bin/cat",
        "/bin/ls",
        "/bin/pwd",
        "/bin/mkdir",
        "/usr/bin/sed",
        "/bin/bash",
        "/bin/sh",
        "/usr/bin/python3",
    }:
        try:
            setup_path = _relative(executable, cwd, workspace)
        except IsolationError:
            setup_path = None
        if setup_path != SETUP:
            raise ValueError("unrecognized executable path")
    setup_words = words
    if command in {"bash", "sh"} and args:
        setup_words = args
    if len(setup_words) == 4:
        try:
            is_setup = _relative(setup_words[0], cwd, workspace) == SETUP
        except ValueError:
            is_setup = False
        if is_setup and setup_words[1:] == [
            "--json",
            "--template",
            "checklist-template",
        ]:
            return [{"type": "setup", "command": SETUP_COMMAND}]
    if command == "python3" and len(args) == 2:
        if _relative(args[0], cwd, workspace) == ".pilot/marker_hook.py":
            if re.fullmatch(r"pilot-[a-z]+(?:-[a-z]+)*", args[1]):
                return [{"type": "hook", "command": args[1]}]
    if command == "cat":
        paths = args[1:] if args[:1] == ["--"] else args
        if not paths or any(p.startswith("-") for p in paths):
            raise ValueError("unsupported cat arguments")
        return [{"type": "read", "path": _relative(p, cwd, workspace)} for p in paths]
    if command == "sed":
        if (
            len(args) < 3
            or args[0] != "-n"
            or not re.fullmatch(r"\d+(?:,\d+)?p", args[1])
        ):
            raise ValueError("only literal sed print ranges are supported")
        paths = args[2:]
        if paths[:1] == ["--"]:
            paths = paths[1:]
        if not paths or any(p.startswith("-") for p in paths):
            raise ValueError("unsupported sed paths")
        return [{"type": "read", "path": _relative(p, cwd, workspace)} for p in paths]
    if command == "pwd" and args in ([], ["-P"], ["-L"]):
        return [
            {
                "type": "diagnostic",
                "reason": "working-directory discovery",
                "path": _relative(str(cwd), cwd, workspace),
            }
        ]
    if command == "ls":
        paths = []
        for arg in args:
            if arg.startswith("-") and arg != "--":
                if not re.fullmatch(r"-[alAdFhprt1]+", arg):
                    raise ValueError("unsupported ls options")
            elif arg != "--":
                paths.append(_relative(arg, cwd, workspace))
        return [
            {
                "type": "diagnostic",
                "reason": "directory discovery",
                "paths": paths or [_relative(str(cwd), cwd, workspace)],
            }
        ]
    if command == "mkdir" and args[:1] == ["-p"] and len(args) > 1:
        target = Path(manifest["target"])
        parents = {p.as_posix() for p in target.parents if p.as_posix() != "."}
        paths = [_relative(p, cwd, workspace) for p in args[1:]]
        if not all(p in parents for p in paths):
            raise ValueError("mkdir affects a directory outside artifact ancestry")
        return [
            {
                "type": "diagnostic",
                "reason": "artifact directory creation",
                "paths": paths,
                "artifact": manifest["target"],
            }
        ]
    raise ValueError("unrecognized command")


def _command_operations(item, workspace, manifest):
    if item.get("source", "agent") not in {"agent", "unifiedExecStartup"}:
        raise ValueError("command source is not a verified agent command")
    cwd_value = item.get("cwd")
    if not isinstance(cwd_value, str) or not Path(cwd_value).is_absolute():
        raise ValueError("command cwd must be absolute")
    cwd = Path(cwd_value).resolve()
    try:
        cwd.relative_to(workspace)
    except ValueError as exc:
        raise IsolationError("command cwd is outside workspace") from exc
    body, write = _heredoc(_shell_body(item.get("command")))
    result = []
    for words in _segments(body):
        result.extend(_classify_words(words, cwd, workspace, manifest))
    if write:
        write["path"] = _relative(write["path"], cwd, workspace)
        if write["path"] != manifest["target"]:
            raise ValueError("shell write target is not the prepared artifact")
        result.append(write)
    # CommandAction is a best-effort annotation, not a substitute for checking
    # the whole command. Retain it; accept declared reads only when syntax agrees.
    actions = item.get("commandActions")
    if not isinstance(actions, list) or any(not isinstance(a, dict) for a in actions):
        raise ValueError("missing or malformed commandActions")
    reads = {op["path"] for op in result if op["type"] == "read"}
    for action in actions:
        if action.get("type") == "read":
            declared = _relative(action.get("path"), cwd, workspace)
            if declared not in reads:
                raise ValueError("declared read disagrees with parsed command")
    return result


def normalize_events(events, *, thread_id, turn_id, workspace, manifest, latency_ms):
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
    result = {
        "schema_version": 1,
        "evidence_kind": "externally-captured-observation",
        "instrumentation": INSTRUMENTATION,
        "model": MODEL,
        "completed": False,
        "events": [],
        "diagnostics": [],
        "issues": [],
        "output": "",
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
                    operations = _command_operations(item, workspace, manifest)
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
                        path = _relative(change.get("path"), workspace, workspace)
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
                    and status == "completed"
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
                    if status != "completed" or (
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
