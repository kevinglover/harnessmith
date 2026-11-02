"""Schema-10 attribution for literal ``if test -f`` / ``printf`` probes.

The frozen schema-9 observation is the starting point. Captured commands are
never rewritten or executed; exact failures are retained inside new proofs.
Only a literal same-path conditional and the already bounded downstream
attribution rules are added. Native append/readback constraints remain intact.
"""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import re
import shlex

from .workflow_trace_v3 import _absence_certificate, _literal_words, _pinned_bytes, _statements
from .workflow_trace_v4 import RUNTIME_FAILURE, _command_context, _declared_reads, _strict_path
from .workflow_trace_v5 import _read_fact
from .workflow_trace_v6 import CONFIG, _certificate_shell_body
from .workflow_trace_v7 import PROVENANCE, UNPROVEN, _same_item
from .workflow_trace_v8 import (
    ERRORS, OVERLAP, _complete, _endpoints, _intrinsic, _inventory_pin,
    _safe_prefix as _safe_read_prefix,
)
from .workflow_trace_v9 import (
    DISCOVERY, UNSUPPORTED, _conditional as _guarded_conditional, _facts,
    _repair_dependencies as _repair_v9_dependencies, _safe_prefix,
    normalize_events as normalize_v9,
)

INSTRUMENTATION = "codex-workflow-trace-v10"
CONDITIONAL = "unsupported conditional; only literal fixture existence/read"


def _shell_body(command):
    """Admit canonical shell quoting or one expansion-free double-quoted word.

    shlex alone does not perform shell expansion and must not turn outer-shell
    substitutions into apparent inner literals. Keep raw command text intact.
    """
    body = _certificate_shell_body(command)
    if body == command:
        return body
    match = re.fullmatch(r"(?:/bin/)?(?:sh|bash|zsh)\s+-c\s+(.+)", command, re.S)
    if match is None:
        raise ValueError("unsupported wrapper spelling")
    argument = match[1]
    if argument == shlex.quote(body):
        return body
    if not (argument.startswith('"') and argument.endswith('"')):
        raise ValueError("wrapper must use a supported literal quoted argument")
    value, index = "", 1
    while index < len(argument) - 1:
        char = argument[index]
        if char in '$`"':
            raise ValueError("outer wrapper expansion or quote concatenation is unsupported")
        if char == "\\":
            index += 1
            if index == len(argument) - 1:
                raise ValueError("unterminated outer wrapper escape")
            char = argument[index]
            if char not in '$`"\\\n':
                value += "\\"
            if char == "\n":
                index += 1
                continue
        value += char
        index += 1
    if value != body:
        raise ValueError("wrapper shell decoding disagrees with literal parser")
    return body


def _conditional(item, workspace, manifest, recorded):
    statements, connectors = _statements(_shell_body(item["command"]))
    if len(statements) != 1 or connectors:
        raise ValueError("test/printf requires one standalone conditional")
    match = re.fullmatch(
        r"if\s+test\s+-f\s+(.+?)\s*;\s*then\s+(.+?)\s*;\s*else\s+(.+?)\s*;\s*fi",
        statements[0], re.S,
    )
    if match is None:
        raise ValueError("unsupported test/printf conditional")
    tested = _literal_words("cat " + match[1])[1:]
    yes, no = _literal_words(match[2]), _literal_words(match[3])
    if (len(tested) != 1 or len(yes) != 2 or yes[0] not in {"cat", "/bin/cat"}
            or yes[1] != tested[0] or no != ["printf", r"ABSENT\n"]
            or tested[0].startswith("-")
            or any(c in tested[0] for c in "\n\r\t\\")
            or any(p in {".", ".."} for p in tested[0].split("/"))):
        raise ValueError("test/printf requires the same literal path and exact marker format")
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
        "proof": "literal-test-f-printf", "path": path,
        "output_representation": "text", "absence_marker": "ABSENT\n",
        "captured_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
    }


def _replace(record, candidate, result, manifest, native, overlap=()):
    facts = sorted(_facts(result, record["raw_item_id"]), key=lambda fact: fact["raw_operation_index"])
    issues = [issue for issue in result["issues"] if _same_item(issue, record)]
    operations, field, detail = candidate
    unknown = [fact for fact in facts if fact.get("type") == "unknown"]
    if field == "terminal_discovery_certificate":
        allowed = {DISCOVERY, UNPROVEN}
    elif field == "read_only_attribution_certificate":
        allowed = {OVERLAP}
    else:
        allowed = {CONDITIONAL} if detail.get("proof") == "literal-test-f-printf" else {UNSUPPORTED}
    if len(unknown) != 1 or unknown[0].get("reason") not in allowed:
        return False
    expected = [unknown[0]["reason"]]
    if unknown[0].get("reason") == UNPROVEN and unknown[0].get("status") == "unverified":
        expected.append("failed or incomplete operation")
    if (unknown[0].get("status") not in {"completed", "unverified"}
            or type(unknown[0].get("exit_code")) is not int or unknown[0]["exit_code"] != 0
            or issues != [{"kind": "fidelity", "detail": message,
                           **{key: record[key] for key in PROVENANCE}} for message in expected]
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
    previous = {id(proof) for fact in result["events"]
                for proof in fact.get("dependency_attribution_certificates", [])}
    _repair_v9_dependencies(result, manifest)
    for fact in result["events"]:
        for proof in fact.get("dependency_attribution_certificates", []):
            if id(proof) not in previous:
                proof["instrumentation"] = INSTRUMENTATION


def normalize_events(events, **kwargs):
    result = normalize_v9(events, **kwargs)
    result.update(schema_version=10, instrumentation=INSTRUMENTATION,
                  base_normalizer="codex-workflow-trace-v9")
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
            _shell_body(item["command"])
            intrinsic[item_id] = _intrinsic(item, record, workspace, manifest, recorded)
        except ERRORS:
            continue
    repaired: set[str] = set()
    for record in sorted(records.values(), key=lambda value: value.get("raw_start_index", -1)):
        try:
            item = _complete(record, pairs[(result["thread_id"], result["turn_id"], record["raw_item_id"])],
                             workspace, recorded)
            if _shell_body(item["command"]).strip().startswith("if "):
                try:
                    candidate = _conditional(item, workspace, manifest, recorded)
                except ERRORS:
                    if not repaired:
                        continue
                    # Mixed fresh traces may use the previously supported spelling
                    # after a new test/printf read. Its static/prefix rules stay frozen.
                    candidate = _guarded_conditional(item, workspace, manifest, recorded)
                native = _safe_prefix(record, candidate, pairs, records, result, workspace, manifest, recorded)
                overlap = []
            else:
                if not repaired:
                    continue
                candidate = intrinsic[record["raw_item_id"]]
                if candidate[1] not in {"terminal_discovery_certificate", "read_only_attribution_certificate"}:
                    continue
                overlap = _safe_read_prefix(record, pairs, records, intrinsic, result, workspace, recorded)
                native = []
            for prior in records.values():
                if prior.get("raw_start_index", -1) <= record["raw_completion_index"]:
                    _shell_body(prior["raw_command"])
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
