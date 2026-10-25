from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from harnessmith.evaluation import load_scenario
from harnessmith.recipe import load_recipe
from harnessmith.router_experiment import load_router, quality_checks
from harnessmith.runtime_comparison import prepare_comparison, run_strategy_comparison
from harnessmith.runtime_evidence import RuntimeEnvironment, RuntimeSample

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "evaluations/variants/speckit-checklist-router"
SOURCE = ROOT / "skills/speckit-checklist/SKILL.md"


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.scenario = load_scenario(
            ROOT / "evaluations/scenarios/checklist-core-security-codex.json"
        )
        self.recipe = load_recipe(
            ROOT / "recipes/speckit-checklist.conditional.codex.json"
        )
        self.requests = []

    def run_comparison(self, **changes):
        owner = self

        class Provider:
            def evaluate(self, request):
                owner.requests.append(request)
                return RuntimeSample(
                    (owner.scenario.turns[0].mock_canonical,), 100, 20, 5
                )

        args = dict(
            recipe=self.recipe,
            repository_root=ROOT,
            environment=RuntimeEnvironment(*(["test"] * 10)),
            samples=4,
            enabled=True,
            evidence_kind="mock",
            router_package=ROUTER,
        )
        args.update(changes)
        return run_strategy_comparison(self.scenario, Provider(), **args)

    def test_retention_and_small_root(self):
        files, review = load_router(ROUTER, SOURCE.read_bytes())
        self.assertLess(len(files["SKILL.md"]), len(SOURCE.read_bytes()) / 4)
        self.assertEqual("reviewed-semantic-redesign", review["kind"])
        self.assertIn(b"EXECUTE_COMMAND", files["references/project-generation.md"])

    def test_tampering_and_source_drift_rejected(self):
        with self.assertRaises(ValueError):
            load_router(ROUTER, b"changed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "router"
            shutil.copytree(ROUTER, path)
            shutil.copy(
                ROUTER.with_suffix(".review.json"), path.with_suffix(".review.json")
            )
            (path / "SKILL.md").write_text("changed")
            with self.assertRaises(ValueError):
                load_router(path, SOURCE.read_bytes())

    def test_rotation_quality_and_no_rubric_leak(self):
        report = self.run_comparison()
        self.assertTrue(report["passed"])
        self.assertEqual(2, report["schema_version"])
        self.assertEqual(16, len(self.requests))
        for position in range(4):
            self.assertEqual(
                set(report["strategies"]),
                {self.requests[i + position].variant for i in range(0, 16, 4)},
            )
        for request in self.requests:
            self.assertEqual(self.scenario.turns[0].prompt, request.turns[0].prompt)
            self.assertFalse(hasattr(request, "router_review"))
            self.assertFalse(hasattr(request, "quality_checks"))

    def test_preflight_drift_and_insufficient_samples_make_no_calls(self):
        with self.assertRaises(ValueError):
            self.run_comparison(samples=3)
        _, _, provenance = prepare_comparison(self.scenario, self.recipe, ROOT, ROUTER)
        provenance["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.run_comparison(expected_provenance=provenance)
        self.assertFalse(self.requests)

    def test_quality_rejects_bad_count_checked_items_missing_traceability_and_quotes(
        self,
    ):
        good = self.scenario.turns[0].mock_canonical.output
        for bad in (
            good.replace("[ ]", "[x]", 1),
            good + "\n- [ ] CHK005 More?",
            good.replace("[Gap]", "[Completeness]"),
        ):
            self.assertFalse(
                all(c[1] for c in quality_checks(self.scenario.scenario_id, bad))
            )
        self.assertFalse(
            all(
                c[1]
                for c in quality_checks("checklist-optional-most-codex", "CHK001 ?")
            )
        )
        with self.assertRaises(ValueError):
            self.run_comparison(recipe=replace(self.recipe, source_sha256="0" * 64))

    @unittest.skipUnless(
        importlib.util.find_spec("jsonschema"), "requires development dependencies"
    )
    def test_schema(self):
        from jsonschema import validate

        validate(
            json.loads(json.dumps(self.run_comparison())),
            json.loads(
                (ROOT / "schemas/runtime-comparison-v2.schema.json").read_text()
            ),
        )
