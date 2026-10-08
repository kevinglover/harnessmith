"""Read-only analysis for arbitrary Agent Skills."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from .adapters import adapt_frontmatter, source_invocation_policy
from .diagnostics import analyze_audit_diagnostics, diagnostic_to_dict
from .errors import SkillCompilerError
from .frontmatter import scalar_value
from .metrics import estimate_tokens
from .model import Section, SkillIR
from .parser import parse_skill


_DETAIL_HEADING = re.compile(
    r"\b(reference|examples?|troubleshoot|schema|templates?|appendix|faq|report|"
    r"remediation|advanced|configuration|detection|output|format|guidelines?|"
    r"checklist)\b",
    re.IGNORECASE,
)
_CONDITIONAL_HEADING = re.compile(
    r"\b(optional|when|if|errors?|failures?|fallback|edge cases?)\b",
    re.IGNORECASE,
)
_ROOT_HEADING = re.compile(
    r"\b(overview|workflow|execution|instructions?|requirements?|safety|guardrails?|"
    r"preconditions?|rules|principles|process)\b",
    re.IGNORECASE,
)
_NORMATIVE = re.compile(
    r"\b(MUST(?:\s+NOT)?|NEVER|REQUIRED|STRICTLY|IMPORTANT|ABORT|STOP|WAIT)\b"
    r"|\b[Dd]o not\b"
)


def audit_skill(
    source: Path, target: str, source_id: Optional[str] = None
) -> Dict[str, object]:
    """Describe context pressure and review candidates without changing files."""

    ir = parse_skill(Path(source), source_id=source_id)
    target = target.lower()
    warnings: List[str] = []
    compatibility_error: Optional[str] = None
    target_transformations: List[Dict[str, object]] = []
    target_compatible = True
    try:
        policy = source_invocation_policy(ir)
        adapted = adapt_frontmatter(ir, target, policy)
        target_transformations = adapted.transformations
    except SkillCompilerError as exc:
        target_compatible = False
        compatibility_error = str(exc)
        warnings.append(compatibility_error)

    duplicate_headings = {
        section.heading
        for section in ir.sections
        if sum(item.heading == section.heading for item in ir.sections) > 1
    }
    sections = [
        _audit_section(ir, section, duplicate_headings) for section in ir.sections
    ]
    review_candidates = [
        {
            "heading": section["heading"],
            "level": section["level"],
            "token_estimate": section["token_estimate"],
            "source_lines": section["source_lines"],
            "reasons": section["reasons"],
        }
        for section in sections
        if section["classification"] == "review-for-reference"
    ]

    name = scalar_value(ir.field("name"))
    assert isinstance(name, str)
    root_tokens = estimate_tokens(ir.source_text)
    diagnostics = analyze_audit_diagnostics(
        ir,
        target,
        root_tokens,
        sections,
        compatibility_error=compatibility_error,
    )
    return {
        "schema_version": 1,
        "skill": name,
        "target": target,
        "source": {
            "path": ir.source_id,
            "sha256": ir.source_sha256,
        },
        "target_compatible": target_compatible,
        "warnings": warnings,
        "diagnostics": [diagnostic_to_dict(item) for item in diagnostics],
        "metrics": {
            "source_chars": len(ir.source_text),
            "source_lines": len(ir.source_text.splitlines()),
            "source_token_estimate": root_tokens,
            "recommended_root_token_budget": 5000,
            "over_recommended_root_budget": root_tokens > 5000,
            "section_count": len(ir.sections),
            "review_candidate_count": len(review_candidates),
        },
        "bundled_resources": _resource_inventory(ir.source_path.parent),
        "target_transformations": target_transformations,
        "sections": sections,
        "review_candidates": review_candidates,
        "recipe_template": {
            "schema_version": 1,
            "target": target,
            "source_sha256": ir.source_sha256,
            "invocation": "source",
            "extract_sections": [],
            "optimizations": [],
            "budgets": {"root_tokens": 5000},
        },
    }


def _audit_section(
    ir: SkillIR, section: Section, duplicate_headings: Set[str]
) -> Dict[str, object]:
    tokens = estimate_tokens(section.text)
    has_children = any(
        section.start_offset < candidate.start_offset < section.end_offset
        for candidate in ir.sections
    )
    normative_count = sum(
        1 for line in section.text.splitlines() if _NORMATIVE.search(line)
    )
    reasons: List[str] = []

    if section.heading in duplicate_headings:
        classification = "manual-review"
        reasons.append("heading is duplicated and cannot be selected unambiguously")
    elif section.level == 1:
        classification = "keep-in-root"
        reasons.append("top-level identity and routing context")
    elif _ROOT_HEADING.search(section.heading):
        classification = "keep-in-root"
        reasons.append("heading suggests global workflow or safety context")
    else:
        detail_cue = bool(_DETAIL_HEADING.search(section.heading))
        conditional_cue = bool(_CONDITIONAL_HEADING.search(section.heading))
        if tokens >= 1000 or (tokens >= 250 and (detail_cue or conditional_cue)):
            classification = "review-for-reference"
            if tokens >= 1000:
                reasons.append("large section creates always-loaded context pressure")
            if detail_cue:
                reasons.append("heading suggests detailed or supporting material")
            if conditional_cue:
                reasons.append("heading suggests conditional material")
        else:
            classification = "neutral"

    if has_children:
        reasons.append("contains nested sections; extract only as one reviewed unit")
    if normative_count:
        reasons.append(
            "contains %d behavior-bearing line(s); preserve ordering and load gates"
            % normative_count
        )
    if not reasons:
        reasons.append("no deterministic optimization signal")

    return {
        "heading": section.heading,
        "level": section.level,
        "source_lines": [section.start_line, section.end_line],
        "chars": len(section.text),
        "token_estimate": tokens,
        "has_children": has_children,
        "normative_line_count": normative_count,
        "classification": classification,
        "reasons": reasons,
    }


def _resource_inventory(root: Path) -> Dict[str, Dict[str, int]]:
    inventory: Dict[str, Dict[str, int]] = {}
    for name in ("references", "scripts", "assets"):
        directory = root / name
        files = (
            [path for path in directory.rglob("*") if path.is_file()]
            if directory.is_dir()
            else []
        )
        inventory[name] = {
            "files": len(files),
            "bytes": sum(path.stat().st_size for path in files),
        }
    return inventory
