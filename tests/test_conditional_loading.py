from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from harnessmith.compiler import CompileOptions, compile_skill, write_package
from harnessmith.errors import SkillCompilerError
from harnessmith.evaluation import load_scenario
from harnessmith.load_policy import ConditionalSection
from harnessmith.manifest import manifest_validation_errors
from harnessmith.recipe import load_recipe
from harnessmith.runtime_comparison import (
    main,
    run_strategy_comparison,
)
from harnessmith.runtime_evidence import RuntimeEnvironment, RuntimeSample
from harnessmith.verification import verify_compiled_package

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills/speckit-checklist/SKILL.md"
RECIPE = ROOT / "recipes/speckit-checklist.conditional.codex.json"


class ConditionalLoadingTests(unittest.TestCase):
    def options(self):
        recipe = load_recipe(RECIPE)
        return CompileOptions(
            target="codex",
            extract_sections=recipe.extract_sections,
            conditional_sections=recipe.conditional_sections,
            expected_source_sha256=recipe.source_sha256,
            source_id=str(SOURCE),
            recipe_id=str(RECIPE),
            recipe_sha256=recipe.sha256,
        )

    def test_default_remains_mandatory_and_reference_bytes_match(self):
        options = self.options()
        conditional = compile_skill(SOURCE, options)
        mandatory = compile_skill(
            SOURCE,
            replace(
                options, conditional_sections=(), recipe_id=None, recipe_sha256=None
            ),
        )
        self.assertEqual(1, mandatory.manifest["schema_version"])
        self.assertEqual(2, conditional.manifest["schema_version"])
        self.assertIn("Do not continue until it is loaded", mandatory.files["SKILL.md"])
        self.assertNotIn(
            "Do not continue until it is loaded", conditional.files["SKILL.md"]
        )
        self.assertEqual(0, conditional.metrics["mandatory_reference_chars"])
        self.assertGreater(conditional.metrics["conditional_reference_chars"], 0)
        self.assertEqual(
            conditional.metrics["compiled_root_token_estimate"],
            conditional.metrics["normal_path_instruction_token_estimate"],
        )
        for path in mandatory.files:
            if path.startswith("references/"):
                self.assertEqual(mandatory.files[path], conditional.files[path])

    def test_independent_verification_and_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "compiled"
            write_package(compile_skill(SOURCE, self.options()), output)
            report = verify_compiled_package(output)
            self.assertTrue(report.valid, report.issues)
            self.assertEqual("passed", report.checks["regeneration"])
            self.assertEqual("passed", report.checks["metrics"])

    def test_changed_directive_fails_even_after_output_hash_update(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "compiled"
            write_package(compile_skill(SOURCE, self.options()), output)
            root = output / "SKILL.md"
            root.write_text(
                root.read_text().replace(
                    "Otherwise skip this reference", "Otherwise load this reference"
                )
            )
            manifest = output / ".harnessmith.json"
            d = json.loads(manifest.read_text())
            d["files"]["SKILL.md"] = hashlib.sha256(root.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(d))
            report = verify_compiled_package(output)
            self.assertFalse(report.valid)
            self.assertEqual("failed", report.checks["invariants"])

    def test_unpinned_drift_unknown_selector_and_conflicts_fail_closed(self):
        options = self.options()
        for changed in [
            replace(options, expected_source_sha256=None),
            replace(options, expected_source_sha256="0" * 64),
            replace(options, optimize_extension_hooks=True),
            replace(options, extract_sections=()),
            replace(options, conditional_sections=options.conditional_sections * 2),
        ]:
            with self.assertRaises(SkillCompilerError):
                compile_skill(SOURCE, changed)
        with self.assertRaises(SkillCompilerError):
            ConditionalSection("Examples", "\n", "reviewed")

    def test_recipe_contract_rejects_unreviewed_or_malformed_policies(self):
        original = json.loads(RECIPE.read_text())
        section = original["extract_sections"][0]
        mutations = [
            lambda d: d.update(schema_version=1),
            lambda d: d.update(schema_version=True),
            lambda d: d.pop("source_sha256"),
            lambda d: d["conditional_sections"][section].update(optional=False),
            lambda d: d["conditional_sections"][section].pop("rationale"),
            lambda d: d["conditional_sections"][section].update(when=" "),
            lambda d: d.update(extract_sections=[]),
        ]
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "recipe.json"
            for mutate in mutations:
                d = json.loads(json.dumps(original))
                mutate(d)
                p.write_text(json.dumps(d))
                with self.assertRaises(SkillCompilerError):
                    load_recipe(p)

    def test_conditional_manifest_cannot_masquerade_as_version_one(self):
        package = compile_skill(SOURCE, self.options())
        self.assertFalse(manifest_validation_errors(package.manifest))
        self.assertTrue(
            manifest_validation_errors({**package.manifest, "schema_version": 1})
        )


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.scenario = load_scenario(
            ROOT / "evaluations/scenarios/checklist-core-security-codex.json"
        )
        self.recipe = load_recipe(RECIPE)
        self.environment = RuntimeEnvironment(*(["test"] * 10))
        self.requests = []
        scenario = self.scenario
        requests = self.requests

        class Provider:
            def evaluate(self, request):
                requests.append(request)
                variant = "canonical" if request.variant == "canonical" else "compiled"
                return RuntimeSample(
                    tuple(getattr(t, "mock_" + variant) for t in scenario.turns),
                    100,
                    20,
                    5,
                )

        self.provider = Provider()

    def run_comparison(self, **changes):
        options = dict(
            recipe=self.recipe,
            repository_root=ROOT,
            environment=self.environment,
            samples=3,
            enabled=True,
            evidence_kind="mock",
        )
        options.update(changes)
        return run_strategy_comparison(self.scenario, self.provider, **options)

    def test_rotates_three_positions_keeps_provenance_and_no_answer_leak(self):
        report = self.run_comparison()
        self.assertTrue(report["passed"])
        self.assertEqual(
            [
                "canonical",
                "mandatory",
                "conditional",
                "mandatory",
                "conditional",
                "canonical",
                "conditional",
                "canonical",
                "mandatory",
            ],
            [r.variant for r in self.requests],
        )
        self.assertEqual(9, len({r.session_id for r in self.requests}))
        self.assertEqual(self.recipe.sha256, report["recipe_sha256"])
        for r in self.requests:
            self.assertFalse(hasattr(r, "scenario"))
            self.assertFalse(hasattr(r.turns[0], "expected_actions"))
            with self.assertRaises(TypeError):
                r.files["SKILL.md"] = b"changed"

    @unittest.skipUnless(
        importlib.util.find_spec("jsonschema"), "requires development dependencies"
    )
    def test_comparison_report_schema(self):
        from jsonschema import validate

        report = self.run_comparison()
        validate(
            json.loads(json.dumps(report)),
            json.loads((ROOT / "schemas/runtime-comparison.schema.json").read_text()),
        )

    def test_disabled_invalid_samples_and_recipe_mismatch_never_call_provider(self):
        for changes in [
            dict(enabled=False),
            dict(samples=2),
            dict(samples=True),
            dict(recipe=replace(self.recipe, source_sha256="0" * 64)),
            dict(recipe=replace(self.recipe, target="claude")),
            dict(recipe=replace(self.recipe, extract_sections=())),
        ]:
            with self.assertRaises((ValueError, RuntimeError)):
                self.run_comparison(**changes)
        self.assertEqual([], self.requests)

    def test_bad_observations_retained_and_missing_usage_rejected(self):
        from harnessmith.evaluation_turns import TurnTrace

        self.provider.evaluate = lambda request: RuntimeSample(
            (TurnTrace(True, "wrong", (), ()),), 1, 2, 3
        )
        self.assertFalse(self.run_comparison()["passed"])
        self.provider.evaluate = lambda request: RuntimeSample((), True, 2, 3)
        with self.assertRaises(ValueError):
            self.run_comparison()

    def test_prepare_only_uses_no_auth_and_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "prepared"
            args = [
                str(ROOT / "evaluations/scenarios/checklist-core-security-codex.json"),
                "--recipe",
                str(RECIPE),
                "--output",
                str(output),
                "--auth-file",
                str(Path(directory) / "missing"),
            ]
            self.assertEqual(0, main(args))
            self.assertTrue((output / "conditional/SKILL.md").exists())
            self.assertFalse((output / "raw").exists())
            self.assertEqual(2, main(args))
            self.assertFalse((output / "incomplete.json").exists())


if __name__ == "__main__":
    unittest.main()
