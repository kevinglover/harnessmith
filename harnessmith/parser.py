"""Parse canonical SKILL.md files into a provenance-aware IR."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .errors import SkillCompilerError
from .frontmatter import scalar_value, split_frontmatter
from .model import Section, SkillIR


_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*(?:\r?\n)?$")


def parse_skill(path: Path, source_id: Optional[str] = None) -> SkillIR:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fields, body, body_start_line = split_frontmatter(text)
    name_field = next((item for item in fields if item.key == "name"), None)
    description_field = next(
        (item for item in fields if item.key == "description"), None
    )
    name = scalar_value(name_field)
    description = scalar_value(description_field)
    if not isinstance(name, str) or not name:
        raise SkillCompilerError("frontmatter requires a non-empty scalar 'name'")
    if not isinstance(description, str) or not description:
        raise SkillCompilerError("frontmatter requires a non-empty scalar 'description'")

    return SkillIR(
        source_path=path,
        source_id=source_id or path.as_posix(),
        source_text=text,
        source_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        frontmatter=fields,
        body=body,
        body_start_line=body_start_line,
        sections=_parse_sections(body, body_start_line),
    )


def _parse_sections(body: str, body_start_line: int) -> Tuple[Section, ...]:
    lines = body.splitlines(keepends=True)
    headings: List[Tuple[int, int, int, str]] = []
    offset = 0
    in_fence = False
    fence_marker = ""

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        fence = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
            offset += len(line)
            continue
        if not in_fence:
            match = _HEADING.match(line)
            if match:
                headings.append(
                    (index, offset, len(match.group(1)), match.group(2).strip())
                )
        offset += len(line)

    sections: List[Section] = []
    total_length = len(body)
    for index, (line_index, start, level, heading) in enumerate(headings):
        end = total_length
        end_line_index = len(lines)
        for next_line, next_offset, next_level, _ in headings[index + 1 :]:
            if next_level <= level:
                end = next_offset
                end_line_index = next_line
                break
        sections.append(
            Section(
                heading=heading,
                level=level,
                start_line=body_start_line + line_index,
                end_line=body_start_line + end_line_index - 1,
                start_offset=start,
                end_offset=end,
                text=body[start:end],
            )
        )
    return tuple(sections)
