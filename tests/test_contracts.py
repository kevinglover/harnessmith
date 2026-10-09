from __future__ import annotations

import json
import unittest
from pathlib import Path

from harnessmith.contracts import (
    AdapterCapabilities,
    Capability,
    CapabilityStatus,
    Diagnostic,
    FixtureRecord,
    Severity,
    SourceSpan,
)
from harnessmith.targets import TARGET_NAMES


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_all_published_schemas_are_versioned_json(self) -> None:
        schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
        self.assertEqual(5, len(schemas))
        for path in schemas:
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", document["$schema"])
            self.assertIn("schema_version", document["properties"])
            self.assertEqual(1, document["properties"]["schema_version"]["const"])

    def test_published_target_enums_match_the_runtime_registry(self) -> None:
        expected = list(TARGET_NAMES)
        recipe = json.loads((ROOT / "schemas/recipe.schema.json").read_text())
        fixture = json.loads(
            (ROOT / "schemas/fixture-manifest.schema.json").read_text()
        )
        package = json.loads(
            (ROOT / "schemas/package-manifest.schema.json").read_text()
        )
        self.assertEqual(expected, recipe["properties"]["target"]["enum"])
        self.assertEqual(
            expected,
            fixture["properties"]["fixtures"]["items"]["properties"]
            ["expected_targets"]["items"]["enum"],
        )
        self.assertEqual(expected, package["properties"]["target"]["enum"])

    def test_diagnostic_requires_stable_id_and_ordered_span(self) -> None:
        diagnostic = Diagnostic(
            rule_id="HS201",
            severity=Severity.WARNING,
            message="Root exceeds its recommended budget",
            rationale="Always-loaded context is expensive",
            source_span=SourceSpan("SKILL.md", 1, 3),
            estimated_savings_tokens=12,
        )
        self.assertEqual("HS201", diagnostic.rule_id)
        with self.assertRaises(ValueError):
            Diagnostic("budget", Severity.WARNING, "message", "rationale")
        with self.assertRaises(ValueError):
            SourceSpan("SKILL.md", 3, 2)

    def test_adapter_capabilities_reject_duplicate_names(self) -> None:
        capability = Capability(
            "invocation.user", CapabilityStatus.SUPPORTED, "Native field"
        )
        with self.assertRaises(ValueError):
            AdapterCapabilities("claude", (capability, capability))

    def test_fixture_contract_carries_pinned_provenance(self) -> None:
        fixture = FixtureRecord(
            fixture_id="synthetic-small",
            repository="local",
            revision="v1",
            license="CC0-1.0",
            source_path="fixtures/synthetic-small/SKILL.md",
            source_sha256="a" * 64,
            expected_targets=("generic",),
            expected_diagnostics=(),
        )
        self.assertEqual(1, fixture.schema_version)


if __name__ == "__main__":
    unittest.main()
