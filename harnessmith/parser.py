"""Parse canonical SKILL.md files into a provenance-aware IR."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .errors import SkillCompilerError
from .frontmatter import scalar_value, split_frontmatter
from .model import Section, SkillIR


_ATX_HEADING = re.compile(
    r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*(?:\r?\n)?$"
)
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*(?:\r?\n)?$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)(?:\r?\n)?$")
_HTML_START = re.compile(
    r"^ {0,3}(?:<!--|<(script|pre|style)(?:\s|>|$)|<(address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:\s|/?>|$))",
    re.IGNORECASE,
)


def parse_skill(path: Path, source_id: Optional[str] = None) -> SkillIR:
    path = Path(path)
    if path.is_dir():
        path = path / "SKILL.md"
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
    offsets: List[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line)
    headings: List[Tuple[int, int, int, str, str]] = []
    fence_char: Optional[str] = None
    fence_length = 0
    html_end: Optional[re.Pattern[str]] = None

    for index, line in enumerate(lines):
        if fence_char is not None:
            close = re.match(
                r"^ {0,3}(%s{%d,})[ \t]*(?:\r?\n)?$"
                % (re.escape(fence_char), fence_length),
                line,
            )
            if close:
                fence_char = None
                fence_length = 0
            continue
        fence = _FENCE.match(line)
        if fence and not (fence.group(1).startswith("`") and "`" in fence.group(2)):
            fence_char = fence.group(1)[0]
            fence_length = len(fence.group(1))
            continue
        if html_end is not None:
            if html_end.search(line):
                html_end = None
            continue
        html = _HTML_START.match(line)
        if html:
            lowered = line.lower()
            if "<!--" in lowered and "-->" not in lowered:
                html_end = re.compile(r"-->")
            elif html.group(1) and "</%s>" % html.group(1).lower() not in lowered:
                html_end = re.compile(r"</%s\s*>" % html.group(1), re.IGNORECASE)
            elif html.group(2):
                html_end = re.compile(r"^\s*$")
            # Block tags end at a blank line. Ignoring their opening line prevents
            # HTML headings from becoming compiler section boundaries.
            continue
        match = _ATX_HEADING.match(line)
        if match:
            heading = (match.group(2) or "").strip()
            heading = re.sub(r"[ \t]+#+[ \t]*$", "", heading)
            headings.append(
                (index, offsets[index], len(match.group(1)), heading, line)
            )
            continue
        if index > 0 and _SETEXT.match(line):
            previous = lines[index - 1]
            title = previous.rstrip("\r\n")
            if title.strip() and not title.startswith((" ", "\t")):
                # The preceding line is the start of a Setext heading. It cannot
                # already be consumed by another heading construct.
                if not headings or headings[-1][0] != index - 1:
                    level = 1 if line.lstrip().startswith("=") else 2
                    headings.append(
                        (
                            index - 1,
                            offsets[index - 1],
                            level,
                            title.strip(),
                            previous + line,
                        )
                    )

    sections: List[Section] = []
    total_length = len(body)
    occurrences: Dict[str, int] = {}
    for index, (line_index, start, level, heading, heading_text) in enumerate(headings):
        end = total_length
        end_line_index = len(lines)
        for next_line, next_offset, next_level, _, _ in headings[index + 1 :]:
            if next_level <= level:
                end = next_offset
                end_line_index = next_line
                break
        occurrences[heading] = occurrences.get(heading, 0) + 1
        occurrence = occurrences[heading]
        sections.append(
            Section(
                heading=heading,
                level=level,
                identity="%s[%d]" % (heading, occurrence),
                occurrence=occurrence,
                heading_text=heading_text,
                start_line=body_start_line + line_index,
                end_line=body_start_line + end_line_index - 1,
                start_offset=start,
                end_offset=end,
                text=body[start:end],
            )
        )
    return tuple(sections)
