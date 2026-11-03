"""Schema-6 certificates for a narrow literal else-printf absence check.

Frozen v5 remains the complete normalizer. This wrapper only adds a certificate
to its successful absence diagnostic after independently checking the command,
exact output, pinned absence and raw lifecycle prefix. It never executes trace
text, repairs a failed event, or removes an inherited issue.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shlex

from .workflow_trace import IsolationError, PASSIVE_ITEMS, _shell_body
from .workflow_trace_v3 import _absence_certificate, _literal_words, _statements
from .workflow_trace_v4 import RUNTIME_FAILURE, _command_context, _declared_reads, _strict_path
from .workflow_trace_v5 import normalize_events as normalize_v5

INSTRUMENTATION = "codex-workflow-trace-v6"
CONFIG = ".specify/extensions.yml"
PASSIVE = PASSIVE_ITEMS | {"agentMessage"}
# A diagnostic label describes attribution, not necessarily a read-only action:
# inherited mkdir operations are diagnostics too. Admit only reviewed passive
# reasons; new/unknown reasons fail closed until explicitly reviewed here.
READ_ONLY_DIAGNOSTICS = {
    "fixture absence",
    "literal output label",
    "working-directory discovery",
    "directory discovery",
    "file discovery",
    "corroborated read-only Python cache warning",
}


def _certificate_shell_body(command):
    """A new certificate cannot treat login/interactive startup as read-only."""
    body = _shell_body(command)
    words = shlex.split(command)
    if words[0] in {"sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh"}:
        if len(words) != 3 or words[1] != "-c":
            raise ValueError("absence proof requires a non-login -c shell wrapper")
    return body


def _literal_printf(words):
    """One literal format, optionally one %s argument; no shell evaluation."""
    if len(words) not in {2, 3} or words[0] != "printf" or words[1].startswith("-"):
        raise ValueError("absence branch requires bounded literal printf")
    fmt, output, index = words[1], "", 0
    substitutions = 0
    escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\"}
    while index < len(fmt):
        char = fmt[index]
        if char == "\\":
            index += 1
            if index == len(fmt) or fmt[index] not in escapes:
                raise ValueError("unsupported literal printf escape")
            output += escapes[fmt[index]]
        elif char == "%":
            index += 1
            if index == len(fmt) or fmt[index] != "s" or len(words) != 3:
                raise ValueError("unsupported literal printf format")
            substitutions += 1
            output += words[2]
        else:
            output += char
        index += 1
    if substitutions != len(words) - 2 or not output or RUNTIME_FAILURE.search(output):
        raise ValueError("absence output must be nonempty and unambiguous")
    return output


def _absence_command(item, workspace, manifest, recorded_workspace):
    """Validate both branches, including the branch the absent fixture skips."""
    if (item.get("status") != "completed" or type(item.get("exitCode")) is not int
            or item["exitCode"] != 0):
        raise ValueError("absence command requires successful integer exit")
    cwd = _command_context(item, workspace, recorded_workspace)
    statements, connectors = _statements(_certificate_shell_body(item.get("command")))
    if len(statements) != 1 or connectors:
        raise ValueError("absence certificate requires a standalone conditional")
    match = re.fullmatch(
        r"if\s+\[\s+-f\s+(.+?)\s+\]\s*;\s*then\s+(.+?)\s*;\s*else\s+(.+?)\s*;\s*fi",
        statements[0], re.S,
    )
    if not match:
        raise ValueError("unsupported literal file-existence conditional")
    test_words = _literal_words("cat " + match[1])[1:]
    yes, no = _literal_words(match[2]), _literal_words(match[3])
    if len(test_words) != 1 or len(yes) != 2 or yes[0] not in {"cat", "/bin/cat"}:
        raise ValueError("conditional must test and read exactly one literal file")
    tested = _strict_path(test_words[0], cwd, workspace, recorded_workspace)
    read = _strict_path(yes[1], cwd, workspace, recorded_workspace)
    if tested != CONFIG or read != tested or yes[1].startswith("-"):
        raise ValueError("conditional must test and read the same extension path")
    expected = _literal_printf(no)
    if item.get("aggregatedOutput") != expected:
        raise ValueError("absence output must exactly match the literal branch")
    _declared_reads(item, {tested}, cwd, workspace, recorded_workspace)
    # No stderr/cache removal or inference from the final filesystem alone.
    _absence_certificate(tested, workspace, manifest, True)
    return expected


def _raw_prefix(events, result, diagnostic):
    """Require complete non-overlapping raw operations before the checkpoint."""
    if not result.get("instrumentation_valid") or any(
        issue.get("kind") == "isolation" for issue in result["issues"]
    ):
        raise ValueError("absence cannot repair instrumentation or isolation defects")
    start, end = diagnostic.get("raw_start_index"), diagnostic.get("raw_completion_index")
    if type(start) is not int or type(end) is not int or not 0 <= start < end < len(events):
        raise ValueError("absence requires an ordered complete lifecycle")
    starts: dict[str, tuple[int, dict]] = {}
    completions: dict[str, tuple[int, dict]] = {}
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not isinstance(event.get("params", {}), dict):
            raise ValueError("malformed raw event")
        params = event.get("params", {})
        method = event.get("method")
        turn = params.get("turn", {})
        raw_item = params.get("item")
        if (index <= end and method in {"item/started", "item/completed"}
                and (not isinstance(raw_item, dict) or raw_item.get("type") not in PASSIVE)
                and (params.get("threadId") != result["thread_id"]
                     or not isinstance(turn, dict)
                     or params.get("turnId", turn.get("id")) != result["turn_id"])):
            raise ValueError("absence prefix contains an unaccounted operation scope")
        if params.get("threadId") != result["thread_id"]:
            continue
        if not isinstance(turn, dict):
            raise ValueError("malformed raw turn")
        if params.get("turnId", turn.get("id")) != result["turn_id"]:
            continue
        if method not in {"item/started", "item/completed"}:
            continue
        item = params.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("malformed raw lifecycle item")
        if item.get("type") in PASSIVE:
            continue
        destination = starts if method == "item/started" else completions
        if item["id"] in destination:
            raise ValueError("duplicate raw lifecycle endpoint")
        destination[item["id"]] = (index, item)
    item_id = diagnostic["raw_item_id"]
    if item_id not in starts or item_id not in completions:
        raise ValueError("absence lacks both raw lifecycle endpoints")
    first_index, first = starts[item_id]
    last_index, last = completions[item_id]
    if ((first_index, last_index) != (start, end)
            or first.get("type") != "commandExecution"
            or last.get("type") != "commandExecution"
            or first.get("status") != "inProgress"
            or first.get("command") != last.get("command")
            or first.get("cwd") != last.get("cwd")
            or first.get("source", "agent") != last.get("source", "agent")):
        raise ValueError("absence lifecycle fields disagree")
    facts = result["events"] + result["diagnostics"]
    records = {record["raw_item_id"]: record for record in result["command_records"]}
    for other_id in set(starts) | set(completions):
        if other_id == item_id:
            continue
        before = starts.get(other_id)
        after = completions.get(other_id)
        # Later operations do not invalidate an earlier certificate. Any start
        # before its completion must be fully accounted for, even still-open or
        # completed only after the checkpoint.
        if ((before is not None and before[0] > end)
                and (after is None or after[0] > end)):
            continue
        if (before is None or after is None or not before[0] < after[0] < start
                or before[1].get("type") != "commandExecution"
                or after[1].get("type") != "commandExecution"
                or before[1].get("status") != "inProgress"):
            raise ValueError("absence prefix has an unknown or overlapping operation")
        record = records.get(other_id, {})
        if (not record.get("lifecycle_valid") or record.get("status") != "completed"
                or type(record.get("exit_code")) is not int or record["exit_code"] != 0
                or before[1].get("source", "agent") != after[1].get("source", "agent")
                or after[1].get("source", "agent") not in {"agent", "unifiedExecStartup"}):
            raise ValueError("absence prefix lacks a verified command lifecycle")
        _certificate_shell_body(record["raw_command"])
        prior = [fact for fact in facts if fact.get("raw_item_id") == other_id]
        if not prior or any(
            fact.get("type") not in {"read", "diagnostic"}
            or fact.get("status") != "completed" or fact.get("exit_code", 0) != 0
            or (fact.get("type") == "diagnostic"
                and fact.get("reason") not in READ_ONLY_DIAGNOSTICS)
            or (fact.get("reason") == "fixture absence" and not fact.get("certified_absence"))
            for fact in prior
        ):
            raise ValueError("absence prefix contains mutation or unverified operation")
    return last


def normalize_events(events, **kwargs):
    """Preserve frozen-v5 attribution and add only the independently proven fact."""
    result = normalize_v5(events, **kwargs)
    result["schema_version"] = 6
    result["instrumentation"] = INSTRUMENTATION
    result["base_normalizer"] = "codex-workflow-trace-v5"
    workspace = Path(kwargs["workspace"]).resolve()
    recorded = kwargs.get("recorded_workspace")
    recorded = Path(recorded) if recorded is not None else None
    for diagnostic in result["diagnostics"]:
        if (diagnostic.get("reason") != "fixture absence"
                or diagnostic.get("path") != CONFIG
                or diagnostic.get("certified_absence") is not False
                or diagnostic.get("status") != "completed"
                or diagnostic.get("exit_code") != 0):
            continue
        try:
            item = _raw_prefix(events, result, diagnostic)
            expected = _absence_command(item, workspace, kwargs["manifest"], recorded)
            if any(fact.get("raw_item_id") == diagnostic["raw_item_id"]
                   for fact in result["events"]):
                raise ValueError("absence command contains another failed or unverified fact")
        except (ValueError, IsolationError, KeyError, TypeError, OSError, UnicodeError):
            continue
        diagnostic.update(
            certified_absence=True,
            success_evidence="pinned initial absence, standalone safe literal branches, exact output and disjoint read-only prefix",
            absence_certificate={
                "version": 1,
                "instrumentation": INSTRUMENTATION,
                "base_normalizer": "codex-workflow-trace-v5",
                "proof": "literal-else-printf",
                "baseline_inventory_sha256": kwargs["manifest"]["baseline_inventory_sha256"],
                "captured_output_sha256": hashlib.sha256(expected.encode("utf-8")).hexdigest(),
                "raw_prefix_checked": True,
                "stderr_stripped": False,
            },
        )
    return result
