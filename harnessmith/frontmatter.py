"""Lossless handling for the top level of SKILL.md YAML frontmatter.

The compiler does not round-trip YAML through a serializer. Instead, it keeps
each top-level field as source text and only parses the scalar fields needed
for capability decisions. This preserves nested metadata, lists, comments,
quoting, and formatting without adding a YAML dependency.
"""

from __future__ import annotations

import json
import re
from typing import Iterable, List, Optional, Sequence, Tuple

from .errors import SkillCompilerError
from .model import FrontmatterField


_TOP_LEVEL_FIELD = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)")


def split_frontmatter(text: str) -> Tuple[Tuple[FrontmatterField, ...], str, int]:
    """Split frontmatter from body and retain top-level fields losslessly."""

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise SkillCompilerError("SKILL.md must start with YAML frontmatter")

    closing = None
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n") == "---":
            closing = index
            break
    if closing is None:
        raise SkillCompilerError("SKILL.md frontmatter has no closing '---'")

    fm_lines = lines[1:closing]
    starts: List[Tuple[int, str]] = []
    for index, line in enumerate(fm_lines):
        match = _TOP_LEVEL_FIELD.match(line.rstrip("\r\n"))
        if match:
            starts.append((index, match.group(1)))
        elif not starts and line.strip() and not line.lstrip().startswith("#"):
            raise SkillCompilerError(
                "frontmatter content before the first top-level field is unsupported"
            )

    if not starts:
        raise SkillCompilerError("SKILL.md frontmatter is empty")
    if starts[0][0] != 0:
        raise SkillCompilerError(
            "frontmatter comments or blank lines before the first field are unsupported"
        )

    fields: List[FrontmatterField] = []
    seen = set()
    for item_index, (start, key) in enumerate(starts):
        if key in seen:
            raise SkillCompilerError("duplicate frontmatter field: %s" % key)
        seen.add(key)
        end = (
            starts[item_index + 1][0]
            if item_index + 1 < len(starts)
            else len(fm_lines)
        )
        raw = "".join(fm_lines[start:end])
        fields.append(
            FrontmatterField(
                key=key,
                raw=raw,
                start_line=start + 2,
                end_line=end + 1,
            )
        )

    body = "".join(lines[closing + 1 :])
    return tuple(fields), body, closing + 2


def scalar_value(field: Optional[FrontmatterField], default: object = None) -> object:
    """Parse a single-line YAML scalar used by compiler decisions.

    Complex values remain preserved in ``raw`` but are rejected if a compiler
    decision would require interpreting them.
    """

    if field is None:
        return default
    first_line = field.raw.splitlines()[0]
    value = first_line.split(":", 1)[1].strip()
    if not value or value in ("|", ">", "|-", ">-", "|+", ">+"):
        raise SkillCompilerError(
            "frontmatter field '%s' must be a single-line scalar for compilation"
            % field.key
        )
    if value.startswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise SkillCompilerError(
                "invalid quoted scalar for '%s': %s" % (field.key, exc)
            ) from exc
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise SkillCompilerError("invalid quoted scalar for '%s'" % field.key)
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in ("true", "yes", "on", "1"):
        return True
    if lowered in ("false", "no", "off", "0"):
        return False
    if lowered in ("null", "~"):
        return None
    return value


def render_frontmatter(fields: Sequence[FrontmatterField]) -> str:
    return "---\n%s---\n" % "".join(_ensure_newline(item.raw) for item in fields)


def replace_scalar(
    fields: Sequence[FrontmatterField], key: str, value: object
) -> Tuple[FrontmatterField, ...]:
    """Replace or append a scalar field while preserving all other fields."""

    raw = "%s: %s\n" % (key, _encode_scalar(value))
    replacement = FrontmatterField(key=key, raw=raw, start_line=0, end_line=0)
    output: List[FrontmatterField] = []
    replaced = False
    for field in fields:
        if field.key == key:
            output.append(replacement)
            replaced = True
        else:
            output.append(field)
    if not replaced:
        output.append(replacement)
    return tuple(output)


def filter_fields(
    fields: Sequence[FrontmatterField], allowed: Iterable[str]
) -> Tuple[Tuple[FrontmatterField, ...], Tuple[str, ...]]:
    allowed_set = set(allowed)
    kept = tuple(field for field in fields if field.key in allowed_set)
    dropped = tuple(field.key for field in fields if field.key not in allowed_set)
    return kept, dropped


def _encode_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if not isinstance(value, str):
        raise SkillCompilerError("only scalar string/bool/null values can be rendered")
    return json.dumps(value, ensure_ascii=False)


def _ensure_newline(value: str) -> str:
    return value if value.endswith(("\n", "\r")) else value + "\n"
