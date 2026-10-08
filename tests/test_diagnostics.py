from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith.audit import audit_skill
from harnessmith.contracts import Diagnostic, Remediation, Severity, SourceSpan
from harnessmith.diagnostics import (
    diagnostic_to_dict,
    diagnostics_fail_threshold,
    render_diagnostics_json,
    render_diagnostics_sarif,
    render_diagnostics_text,
)


class DiagnosticRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.diagnostics = [
            Diagnostic(
                rule_id="HS214",
                severity=Severity.NOTE,
                message="Detailed examples can move to a reference",
                rationale="The section is large and conditionally useful.",
                source_span=SourceSpan("SKILL.md", 8, 14),
                estimated_savings_tokens=320,
                remediation=Remediation(
                    "Review and extract the section.",
                    recipe_fragment={"extract_sections": ["Detailed Examples"]},
                    requires_review=True,
                ),
            )
        ]

    def test_contract_serializer_omits_absent_optional_values(self) -> None:
        result = diagnostic_to_dict(self.diagnostics[0])
        self.assertEqual("note", result["severity"])
        self.assertEqual(8, result["source_span"]["start_line"])
        self.assertNotIn("start_column", result["source_span"])
        self.assertEqual(
            ["Detailed Examples"],
            result["remediation"]["recipe_fragment"]["extract_sections"],
        )

    def test_text_and_json_are_deterministic(self) -> None:
        text = render_diagnostics_text(self.diagnostics)
        self.assertIn("SKILL.md:8: HS214 note", text)
        self.assertIn("Estimated savings: 320 tokens", text)
        self.assertEqual(
            [diagnostic_to_dict(self.diagnostics[0])],
            json.loads(render_diagnostics_json(self.diagnostics)),
        )

    def test_sarif_contains_rules_locations_and_properties(self) -> None:
        document = json.loads(render_diagnostics_sarif(self.diagnostics, "1.2.3"))
        run = document["runs"][0]
        self.assertEqual("2.1.0", document["version"])
        self.assertEqual("1.2.3", run["tool"]["driver"]["version"])
        self.assertEqual("HS214", run["results"][0]["ruleId"])
        self.assertEqual(
            8,
            run["results"][0]["locations"][0]["physicalLocation"]["region"][
                "startLine"
            ],
        )
        self.assertTrue(run["results"][0]["properties"]["requiresReview"])

    def test_failure_threshold_includes_more_severe_findings(self) -> None:
        self.assertFalse(diagnostics_fail_threshold(self.diagnostics, "warning"))
        error = Diagnostic(
            "HS305", Severity.ERROR, "Incompatible", "Semantics cannot be kept."
        )
        self.assertTrue(
            diagnostics_fail_threshold([*self.diagnostics, error], "warning")
        )
        with self.assertRaises(ValueError):
            diagnostics_fail_threshold(self.diagnostics, "fatal")


class AuditDiagnosticTests(unittest.TestCase):
    def test_audit_emits_ordered_efficiency_and_duplicate_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "SKILL.md"
            detail = "A supporting example without normative requirements. " * 100
            skill.write_text(
                "---\nname: diagnostic-example\ndescription: Exercises rules.\n---\n\n"
                "# Diagnostic Example\n\n"
                "## Detailed Examples\n\n"
                + detail
                + "\n\n## Duplicate\nFirst.\n\n## Duplicate\nSecond.\n",
                encoding="utf-8",
            )
            report = audit_skill(skill, "cursor", source_id="fixture/SKILL.md")

        diagnostics = report["diagnostics"]
        self.assertEqual(
            sorted(
                diagnostics,
                key=lambda item: (
                    item["source_span"]["start_line"],
                    {"error": 0, "warning": 1, "note": 2}[item["severity"]],
                    item["rule_id"],
                    item["message"],
                ),
            ),
            diagnostics,
        )
        by_rule = {}
        for diagnostic in diagnostics:
            by_rule.setdefault(diagnostic["rule_id"], []).append(diagnostic)
        self.assertIn("HS214", by_rule)
        self.assertEqual(2, len(by_rule["HS101"]))
        candidate = by_rule["HS214"][0]
        self.assertEqual("fixture/SKILL.md", candidate["source_span"]["path"])
        self.assertTrue(candidate["remediation"]["requires_review"])
        self.assertEqual(
            ["Detailed Examples"],
            candidate["remediation"]["recipe_fragment"]["extract_sections"],
        )

    def test_audit_emits_fail_closed_target_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "SKILL.md"
            skill.write_text(
                "---\n"
                "name: explicit-only\n"
                "description: Cannot be invoked by users.\n"
                "user-invocable: false\n"
                "---\n\n# Explicit only\n",
                encoding="utf-8",
            )
            report = audit_skill(skill, "cursor")

        self.assertFalse(report["target_compatible"])
        finding = next(
            item for item in report["diagnostics"] if item["rule_id"] == "HS305"
        )
        self.assertEqual("error", finding["severity"])
        self.assertIn("cannot represent user-invocable", finding["rationale"])


if __name__ == "__main__":
    unittest.main()
