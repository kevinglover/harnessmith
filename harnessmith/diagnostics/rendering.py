"""Deterministic text, JSON, and SARIF rendering for diagnostics."""

from __future__ import annotations

import json
from typing import Iterable, List, Mapping, Optional, Sequence

from ..contracts import Diagnostic, Severity


_SEVERITY_RANK = {Severity.NOTE: 0, Severity.WARNING: 1, Severity.ERROR: 2}


def diagnostic_to_dict(diagnostic: Diagnostic) -> dict[str, object]:
    """Serialize a diagnostic without exposing dataclass implementation detail."""

    result: dict[str, object] = {
        "schema_version": diagnostic.schema_version,
        "rule_id": diagnostic.rule_id,
        "severity": diagnostic.severity.value,
        "message": diagnostic.message,
        "rationale": diagnostic.rationale,
    }
    if diagnostic.source_span:
        span = diagnostic.source_span
        source: dict[str, object] = {
            "path": span.path,
            "start_line": span.start_line,
            "end_line": span.end_line,
        }
        if span.start_column is not None:
            source["start_column"] = span.start_column
        if span.end_column is not None:
            source["end_column"] = span.end_column
        result["source_span"] = source
    if diagnostic.estimated_savings_tokens is not None:
        result["estimated_savings_tokens"] = diagnostic.estimated_savings_tokens
    if diagnostic.remediation:
        remediation: dict[str, object] = {
            "summary": diagnostic.remediation.summary,
            "requires_review": diagnostic.remediation.requires_review,
        }
        if diagnostic.remediation.recipe_fragment is not None:
            remediation["recipe_fragment"] = diagnostic.remediation.recipe_fragment
        result["remediation"] = remediation
    return result


def render_diagnostics_text(diagnostics: Iterable[Diagnostic]) -> str:
    lines: List[str] = []
    for diagnostic in diagnostics:
        location = ""
        if diagnostic.source_span:
            span = diagnostic.source_span
            location = "%s:%d: " % (span.path, span.start_line)
        lines.append(
            "%s%s %s %s"
            % (
                location,
                diagnostic.rule_id,
                diagnostic.severity.value,
                diagnostic.message,
            )
        )
        lines.append("  %s" % diagnostic.rationale)
        if diagnostic.estimated_savings_tokens is not None:
            lines.append(
                "  Estimated savings: %d tokens"
                % diagnostic.estimated_savings_tokens
            )
        if diagnostic.remediation:
            review = (
                " (review required)"
                if diagnostic.remediation.requires_review
                else ""
            )
            lines.append("  Fix%s: %s" % (review, diagnostic.remediation.summary))
    return "\n".join(lines)


def render_diagnostics_json(diagnostics: Iterable[Diagnostic], indent: int = 2) -> str:
    return json.dumps(
        [diagnostic_to_dict(item) for item in diagnostics],
        indent=indent,
        sort_keys=True,
    )


def render_diagnostics_sarif(
    diagnostics: Sequence[Diagnostic], tool_version: Optional[str] = None
) -> str:
    rules: dict[str, Mapping[str, object]] = {}
    results: List[dict[str, object]] = []
    for diagnostic in diagnostics:
        rules.setdefault(
            diagnostic.rule_id,
            {
                "id": diagnostic.rule_id,
                "name": diagnostic.rule_id,
                "shortDescription": {"text": diagnostic.message},
                "fullDescription": {"text": diagnostic.rationale},
                "defaultConfiguration": {"level": _sarif_level(diagnostic.severity)},
            },
        )
        result: dict[str, object] = {
            "ruleId": diagnostic.rule_id,
            "level": _sarif_level(diagnostic.severity),
            "message": {"text": diagnostic.message},
        }
        if diagnostic.source_span:
            span = diagnostic.source_span
            region: dict[str, int] = {
                "startLine": span.start_line,
                "endLine": span.end_line,
            }
            if span.start_column is not None:
                region["startColumn"] = span.start_column
            if span.end_column is not None:
                region["endColumn"] = span.end_column
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": span.path},
                        "region": region,
                    }
                }
            ]
        properties: dict[str, object] = {"rationale": diagnostic.rationale}
        if diagnostic.estimated_savings_tokens is not None:
            properties["estimatedSavingsTokens"] = diagnostic.estimated_savings_tokens
        if diagnostic.remediation:
            properties["requiresReview"] = diagnostic.remediation.requires_review
            properties["remediation"] = diagnostic.remediation.summary
            if diagnostic.remediation.recipe_fragment is not None:
                properties["recipeFragment"] = diagnostic.remediation.recipe_fragment
        result["properties"] = properties
        results.append(result)

    driver: dict[str, object] = {
        "name": "Harnessmith",
        "informationUri": "https://harnessmith.dev/diagnostics",
        "rules": [rules[key] for key in sorted(rules)],
    }
    if tool_version:
        driver["version"] = tool_version
    document = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": driver}, "results": results}],
    }
    return json.dumps(document, indent=2, sort_keys=True)


def diagnostics_fail_threshold(
    diagnostics: Iterable[Diagnostic], fail_on: Severity | str
) -> bool:
    """Return whether any finding meets or exceeds a CI failure threshold."""

    threshold = fail_on if isinstance(fail_on, Severity) else Severity(fail_on)
    return any(
        _SEVERITY_RANK[item.severity] >= _SEVERITY_RANK[threshold]
        for item in diagnostics
    )


def _sarif_level(severity: Severity) -> str:
    return {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.NOTE: "note",
    }[severity]
