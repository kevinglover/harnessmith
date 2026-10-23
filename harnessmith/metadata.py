"""Validate interpreted metadata without reserializing its source fields.

The supported YAML subset is deliberately conservative. Anchors, tags and complex
collections are rejected when validation would otherwise have to guess a type.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional

from .contracts import Diagnostic, Remediation, Severity, SourceSpan
from .errors import SkillCompilerError
from .frontmatter import scalar_value
from .model import FrontmatterField, SkillIR
from .targets import get_target

_NUMBER = re.compile(
    r"[-+]?(?:0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|"
    r"[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][-+]?[0-9]+)?|"
    r"\.[0-9_]+(?:[eE][-+]?[0-9]+)?|\.inf|\.nan)$",
    re.I,
)

_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}|"
    r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)"
    r"[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?"
    r"(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?"
)


def _without_comment(value: str) -> str:
    quote = None
    index = 0
    while index < len(value):
        char = value[index]
        if quote:
            if char == "\\" and quote == '"':
                index += 2
                continue
            if char == quote:
                if quote == "'" and value[index : index + 2] == "''":
                    index += 2
                    continue
                quote = None
        elif char in "\"'" and (
            index == 0 or value[index - 1].isspace() or value[index - 1] in "[{,:"
        ):
            quote = char
        elif char == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
        index += 1
    return value.rstrip()


def string_value(field: FrontmatterField) -> str:
    """Read a string scalar, rejecting collections and implicit YAML types."""
    lines = field.raw.splitlines()
    value = _without_comment(lines[0].split(":", 1)[1].strip())
    if not value or value[0] in "[{&*!":
        raise SkillCompilerError("must be a string scalar")
    if value.startswith("'") and not re.fullmatch(r"'(?:[^']|'')*'", value):
        raise SkillCompilerError("invalid single-quoted string")
    if value[0] not in "\"'|>" and (
        re.search(r":(?:\s|$)", value) or re.match(r"[-?:](?:\s|$)", value)
    ):
        raise SkillCompilerError("must be a string scalar")
    if value[0] in "|>":
        # Top-level comments belong to the raw field span, not its string value.
        content = [lines[0]] + [line for line in lines[1:] if not line.startswith("#")]
        if any(line.strip() and not line.startswith(" ") for line in content[1:]):
            raise SkillCompilerError("block string content must be indented")
        parsed = scalar_value(
            FrontmatterField(
                field.key, "\n".join(content), field.start_line, field.end_line
            )
        )
    else:
        if any(
            _without_comment(line).strip() and not line.startswith(" ")
            for line in lines[1:]
        ):
            raise SkillCompilerError("scalar continuation must be indented")
        tail = [_without_comment(line).strip() for line in lines[1:]]
        tail = [line for line in tail if line]
        if tail:
            if value[0] in "\"'" or any(
                re.match(r"(?:-\s|[^:]+:\s)", line) for line in tail
            ):
                raise SkillCompilerError("unsupported scalar continuation")
            value = " ".join([value, *tail])
        if _NUMBER.fullmatch(value) or _TIMESTAMP.fullmatch(value):
            raise SkillCompilerError("must be a string scalar")
        parsed = scalar_value(
            FrontmatterField(field.key, field.key + ": " + value, 1, 1)
        )
    if not isinstance(parsed, str):
        raise SkillCompilerError("must be a string scalar")
    return parsed


def _flow_parts(value: str, *, mapping: bool = False) -> List[str]:
    """Split a flat flow collection, retaining commas within quoted strings."""
    parts: List[str] = []
    start = 0
    scalar_start = True
    quote = None
    index = 0
    while index < len(value):
        char = value[index]
        if quote:
            if char == "\\" and quote == '"':
                index += 2
                continue
            if char == quote:
                if quote == "'" and value[index : index + 2] == "''":
                    index += 2
                    continue
                quote = None
        elif char in "\"'" and scalar_start:
            quote = char
            scalar_start = False
        elif mapping and char == ":" and (
            index + 1 == len(value)
            or value[index + 1].isspace()
            or value[start:index].strip().startswith(("'", '"'))
        ):
            scalar_start = True
        elif char in "[]{}":
            raise SkillCompilerError("nested flow collections are unsupported")
        elif char == ",":
            parts.append(value[start:index].strip())
            start = index + 1
            scalar_start = True
        elif not char.isspace():
            scalar_start = False
        index += 1
    if quote:
        raise SkillCompilerError("unterminated quoted value")
    if value[start:].strip():
        parts.append(value[start:].strip())
    return parts


def _string(text: str) -> str:
    return string_value(FrontmatterField("value", "value: " + text, 1, 1))


def string_list(field: FrontmatterField) -> List[str]:
    lines = field.raw.splitlines()
    first = _without_comment(lines[0].split(":", 1)[1].strip())
    if first.startswith("[") and first.endswith("]"):
        if any(_without_comment(line).strip() for line in lines[1:]):
            raise SkillCompilerError("unsupported list continuation")
        entries = _flow_parts(first[1:-1])
    elif not first:
        entries = []
        indentation = None
        for line in lines[1:]:
            stripped = _without_comment(line).strip()
            if not stripped:
                continue
            if not re.match(r"^\s+-\s+", line):
                raise SkillCompilerError("expected a flat YAML string list")
            leading = len(line) - len(line.lstrip(" "))
            if indentation is None:
                indentation = leading
            if leading != indentation:
                raise SkillCompilerError("tool lists must have consistent indentation")
            entries.append(stripped[2:].strip())
        if not entries:
            raise SkillCompilerError("expected a tool list, not null")
    else:
        raise SkillCompilerError("expected a string or flat YAML string list")
    return [_string(entry) for entry in entries]


def _validate_mapping(field: FrontmatterField) -> None:
    lines = field.raw.splitlines()
    first = _without_comment(lines[0].split(":", 1)[1].strip())
    if first.startswith("{") and first.endswith("}"):
        if any(_without_comment(line).strip() for line in lines[1:]):
            raise SkillCompilerError("unsupported mapping continuation")
        entries = _flow_parts(first[1:-1], mapping=True)
    elif not first:
        entries = []
        indentation: Optional[int] = None
        for line in lines[1:]:
            if not _without_comment(line).strip():
                continue
            leading = len(line) - len(line.lstrip(" "))
            if indentation is None:
                indentation = leading
            if not leading or leading != indentation:
                raise SkillCompilerError("metadata must be a flat string-to-string map")
            entries.append(line.strip())
        if not entries:
            raise SkillCompilerError("metadata must be a map, not null")
    else:
        raise SkillCompilerError("metadata must be a string-to-string map")
    keys = set()
    for entry in entries:
        match = re.fullmatch(
            r"""("(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^:]+):\s*(.*)""", entry
        )
        if not match:
            raise SkillCompilerError("metadata entries require string keys and values")
        if match[1][0] not in "\"'" and not re.match(r":\s+", entry[len(match[1]) :]):
            raise SkillCompilerError(
                "plain mapping keys require a space after the colon"
            )
        key, value = _string(match[1]), _string(match[2])
        if key in keys or key == "<<":
            raise SkillCompilerError("duplicate or merge metadata key")
        keys.add(key)
        assert isinstance(value, str)


def _separator_comma(value: str) -> bool:
    depth = 0
    for char in value:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            return True
    return False


def metadata_diagnostics(
    ir: SkillIR, target: str, *, directory: bool = False
) -> List[Diagnostic]:
    policy = get_target(target).metadata_policy
    findings: List[Diagnostic] = []

    def report(
        key: str, reason: str, rule: str = "HS102", severity: Severity = Severity.ERROR
    ) -> None:
        field = ir.field(key)
        findings.append(
            Diagnostic(
                rule,
                severity,
                "Invalid %s metadata for '%s': %s" % (key, target, reason),
                "Validation interprets fields without changing their original bytes.",
                SourceSpan(
                    ir.source_id,
                    max(1, field.start_line) if field else 1,
                    max(1, field.end_line) if field else 1,
                ),
                remediation=Remediation(
                    "Correct the field or choose a target supporting its representation."
                ),
            )
        )

    values = {}
    for key, limit in (
        ("name", policy.name_limit),
        ("description", policy.description_limit),
        ("compatibility", policy.compatibility_limit),
        ("license", None),
    ):
        field = ir.field(key)
        if field is None:
            if key in ("name", "description"):
                report(key, "required by the canonical package contract")
            continue
        try:
            value = string_value(field)
            if not value.strip() and key != "license":
                raise SkillCompilerError("must not be empty")
            if limit is not None and len(value) > limit:
                raise SkillCompilerError("must contain at most %d characters" % limit)
            values[key] = value
            if key == "name":
                if policy.portable_name:
                    if (
                        value.startswith("-")
                        or value.endswith("-")
                        or "--" in value
                        or any(
                            not (
                                c == "-" or c.isdigit() or (c.isalpha() and c.islower())
                            )
                            for c in value
                        )
                    ):
                        raise SkillCompilerError(
                            "use lowercase letters, digits and single interior hyphens"
                        )
                elif (
                    value != value.strip()
                    or "  " in value
                    or any(
                        c in "<>"
                        or unicodedata.category(c).startswith("C")
                        or (c.isspace() and c != " ")
                        for c in value
                    )
                ):
                    raise SkillCompilerError(
                        "contains characters refused in Claude command names"
                    )
        except SkillCompilerError as exc:
            report(key, str(exc))

    metadata = ir.field("metadata")
    if metadata:
        try:
            _validate_mapping(metadata)
        except SkillCompilerError as exc:
            report("metadata", str(exc))
    for key in ("allowed-tools", "disallowed-tools"):
        field = ir.field(key)
        if field is None or key not in get_target(target).frontmatter_fields:
            continue
        try:
            try:
                value = string_value(field)
                if not value.strip() or "\n" in value or "\r" in value:
                    raise SkillCompilerError(
                        "expected a nonempty single-line tool string"
                    )
                if not policy.tool_commas and _separator_comma(value):
                    raise SkillCompilerError(
                        "portable tools use a space-separated string"
                    )
            except SkillCompilerError:
                if not policy.tool_lists:
                    raise
                entries = string_list(field)
                if any(not entry.strip() for entry in entries):
                    raise SkillCompilerError("tool list entries must not be empty")
        except SkillCompilerError as exc:
            report(key, str(exc))
    if (
        directory
        and policy.directory_matches_name
        and "name" in values
        and ir.source_path.parent.name != values["name"]
    ):
        report(
            "name",
            "installation directory must be named '%s'; current directory is '%s'"
            % (values["name"], ir.source_path.parent.name),
            "HS103",
            Severity.WARNING,
        )
    return findings


def require_valid_metadata(ir: SkillIR, target: str) -> None:
    errors = metadata_diagnostics(ir, target)
    if errors:
        raise SkillCompilerError(
            "; ".join("%s: %s" % (d.rule_id, d.message) for d in errors)
        )
