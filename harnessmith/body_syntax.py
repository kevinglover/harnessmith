"""Advisory host-syntax scanning; never evaluate or rewrite skill content."""

from __future__ import annotations

import re
from typing import List, Optional

from .contracts import Diagnostic, Remediation, Severity, SourceSpan
from .errors import SkillCompilerError
from .metadata import string_list, string_value
from .model import SkillIR
from .targets import get_target

_SUBSTITUTION = (
    r"\$ARGUMENTS(?:\[[0-9]+\])?(?![\w])"
    r"|\$\{CLAUDE_(?:SESSION_ID|EFFORT|SKILL_DIR|PROJECT_DIR|PLUGIN_ROOT|PLUGIN_DATA)\}"
    r"|\$[0-9]+(?![\w])"
)
_DYNAMIC = r"!`[^`\n]+`"
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def body_syntax_diagnostics(ir: SkillIR, target: str) -> List[Diagnostic]:
    target = get_target(target).name
    if target == "claude":
        return []
    patterns = [_SUBSTITUTION, _DYNAMIC]
    arguments = ir.field("arguments")
    if arguments:
        try:
            try:
                names = string_value(arguments).split()
            except SkillCompilerError:
                names = string_list(arguments)
            patterns.extend(
                r"\$" + re.escape(name) + r"(?![\w])" for name in names if name
            )
        except SkillCompilerError:
            # Frontmatter adaptation rejects unsupported arguments independently.
            pass
    tokens = re.compile("|".join(patterns))
    findings: List[Diagnostic] = []
    fence: Optional[str] = None
    fence_length = 0
    in_comment = False
    inline_ticks: Optional[int] = None
    for line_number, line in enumerate(ir.body.splitlines(), ir.body_start_line):
        marker = _FENCE.match(line)
        if fence:
            context = "fenced code"
            if (
                marker
                and marker[1][0] == fence
                and len(marker[1]) >= fence_length
                and not marker[2].strip()
            ):
                fence = None
                continue
        elif marker and not (marker[1][0] == "`" and "`" in marker[2]):
            fence, fence_length = marker[1][0], len(marker[1])
            inline_ticks = None
            continue
        else:
            context = "body text"
        # Determine lexical context at each match, including multiline comments
        # and code spans. Markdown context is not a host preprocessing guarantee.
        contexts = {}
        index = 0
        while index < len(line):
            contexts[index] = (
                context
                if fence
                else (
                    "HTML comment"
                    if in_comment
                    else "inline code"
                    if inline_ticks
                    else "indented code"
                    if line.startswith(("    ", "\t"))
                    else "quoted example"
                    if line.lstrip().startswith(">")
                    else "body text"
                )
            )
            if not fence:
                if in_comment and line.startswith("-->", index):
                    in_comment = False
                elif not inline_ticks and line.startswith("<!--", index):
                    in_comment = True
                elif not in_comment and line[index] == "`":
                    run = len(line[index:]) - len(line[index:].lstrip("`"))
                    if inline_ticks is None:
                        inline_ticks = run
                    elif inline_ticks == run:
                        inline_ticks = None
                    for offset in range(1, run):
                        contexts[index + offset] = contexts[index]
                    index += run
                    continue
            index += 1
        if not line.strip():
            inline_ticks = None
        for match in tokens.finditer(line):
            preceding = line[: match.start()]
            escaped = (len(preceding) - len(preceding.rstrip("\\"))) % 2 == 1
            location = contexts.get(match.start(), context)
            literal = escaped or location != "body text"
            findings.append(
                Diagnostic(
                    "HS308" if literal else "HS307",
                    Severity.NOTE if literal else Severity.WARNING,
                    "Claude-specific syntax %s in %s for '%s'"
                    % (match[0], "escaped text" if escaped else location, target),
                    (
                        "This may be a literal example; Markdown quoting and escaping "
                        "are not evidence that a host skips preprocessing. "
                        if literal
                        else ""
                    )
                    + "Byte preservation does not establish command expansion or substitution support.",
                    SourceSpan(
                        ir.source_id,
                        line_number,
                        line_number,
                        match.start() + 1,
                        match.end(),
                    ),
                    remediation=Remediation(
                        "Review whether this is instructional or literal. Use portable inputs "
                        "or a target with the required behavior; no content is executed or rewritten."
                    ),
                )
            )
    return findings


def tool_semantics_diagnostics(ir: SkillIR, target: str) -> List[Diagnostic]:
    definition = get_target(target)
    findings = []
    for key in ("allowed-tools", "disallowed-tools"):
        field = ir.field(key)
        if field is None or key not in definition.frontmatter_fields:
            continue
        findings.append(
            Diagnostic(
                "HS306",
                Severity.WARNING,
                "Tool metadata '%s' is preserved without a runtime enforcement guarantee"
                % key,
                "allowed-tools is preapproval metadata, not an exclusive tool restriction. "
                "Runtime behavior depends on host version and permission settings; it has not been tested.",
                SourceSpan(
                    ir.source_id, max(1, field.start_line), max(1, field.end_line)
                ),
                remediation=Remediation(
                    "Verify permissions in the intended host/version before relying on this policy."
                ),
            )
        )
    return findings
