"""Stable audit rules for source validity, efficiency, and compatibility."""

from __future__ import annotations

from typing import Iterable, List, Mapping, Optional

from ..contracts import Diagnostic, Remediation, Severity, SourceSpan
from ..model import Section, SkillIR


ROOT_TOKEN_BUDGET = 5000


def analyze_audit_diagnostics(
    ir: SkillIR,
    target: str,
    root_tokens: int,
    sections: Iterable[Mapping[str, object]],
    compatibility_error: Optional[str] = None,
) -> List[Diagnostic]:
    """Return findings in stable source/rule order.

    Rule namespaces are intentionally coarse and public: HS1xx describes source
    validity, HS2xx context efficiency, and HS3xx target compatibility.
    """

    findings: List[Diagnostic] = []
    section_reports = list(sections)
    section_by_identity = {
        (section.heading, section.start_line, section.end_line): section
        for section in ir.sections
    }

    duplicates = {
        section.heading
        for section in ir.sections
        if sum(item.heading == section.heading for item in ir.sections) > 1
    }
    for section in ir.sections:
        if section.heading not in duplicates:
            continue
        findings.append(
            Diagnostic(
                rule_id="HS101",
                severity=Severity.WARNING,
                message="Duplicate heading cannot be selected unambiguously: %s"
                % section.heading,
                rationale=(
                    "Heading-only recipes cannot identify which occurrence should "
                    "be transformed."
                ),
                source_span=_section_span(ir, section),
                remediation=Remediation(
                    summary="Rename duplicate headings before selecting this section.",
                    requires_review=True,
                ),
            )
        )

    if root_tokens > ROOT_TOKEN_BUDGET:
        findings.append(
            Diagnostic(
                rule_id="HS201",
                severity=Severity.WARNING,
                message=(
                    "Root is %d estimated tokens; recommended maximum is %d"
                    % (root_tokens, ROOT_TOKEN_BUDGET)
                ),
                rationale=(
                    "Always-loaded instructions above the recommended budget increase "
                    "context pressure for every invocation."
                ),
                source_span=_document_span(ir),
                estimated_savings_tokens=root_tokens - ROOT_TOKEN_BUDGET,
                remediation=Remediation(
                    summary=(
                        "Review HS214 candidates for lossless extraction into "
                        "references."
                    ),
                    recipe_fragment={"budgets": {"root_tokens": ROOT_TOKEN_BUDGET}},
                    requires_review=True,
                ),
            )
        )

    for report in section_reports:
        if report.get("classification") != "review-for-reference":
            continue
        key = (
            report["heading"],
            report["source_lines"][0],  # type: ignore[index]
            report["source_lines"][1],  # type: ignore[index]
        )
        section = section_by_identity[key]
        tokens = int(report["token_estimate"])
        reasons = "; ".join(str(item) for item in report["reasons"])
        findings.append(
            Diagnostic(
                rule_id="HS214",
                severity=Severity.NOTE,
                message=(
                    "Section '%s' is a reference-extraction candidate (%d tokens)"
                    % (section.heading, tokens)
                ),
                rationale=reasons,
                source_span=_section_span(ir, section),
                estimated_savings_tokens=tokens,
                remediation=Remediation(
                    summary=(
                        "Review load gates and behavior-bearing instructions, then "
                        "extract this section losslessly."
                    ),
                    recipe_fragment={"extract_sections": [section.heading]},
                    requires_review=True,
                ),
            )
        )

    if compatibility_error:
        findings.append(
            Diagnostic(
                rule_id="HS305",
                severity=Severity.ERROR,
                message="Target '%s' cannot preserve source semantics" % target,
                rationale=compatibility_error,
                source_span=_frontmatter_span(ir),
                remediation=Remediation(
                    summary=(
                        "Choose a target with the required capability or explicitly "
                        "revise the source semantics."
                    ),
                    requires_review=True,
                ),
            )
        )

    severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.NOTE: 2}
    return sorted(
        findings,
        key=lambda item: (
            item.source_span.start_line if item.source_span else 0,
            severity_order[item.severity],
            item.rule_id,
            item.message,
        ),
    )


def _document_span(ir: SkillIR) -> SourceSpan:
    return SourceSpan(ir.source_id, 1, max(1, len(ir.source_text.splitlines())))


def _frontmatter_span(ir: SkillIR) -> SourceSpan:
    end = max((field.end_line for field in ir.frontmatter), default=1)
    return SourceSpan(ir.source_id, 1, end)


def _section_span(ir: SkillIR, section: Section) -> SourceSpan:
    return SourceSpan(ir.source_id, section.start_line, section.end_line)
