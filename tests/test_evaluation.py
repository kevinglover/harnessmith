from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith.evaluation import (
    EVALUATION_SCHEMA_VERSION,
    EvaluationScenarioError,
    RuntimeObservation,
    evaluate_scenario,
    load_scenario,
    run_live_evaluation,
)


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evaluations" / "scenarios"


class EvaluationTests(unittest.TestCase):
    def test_checked_in_scenarios_pass_offline(self) -> None:
        for path in sorted(SCENARIOS.glob("*.json")):
            with self.subTest(path=path.name):
                result = evaluate_scenario(load_scenario(path), repository_root=ROOT)
                self.assertTrue(result.passed)
                self.assertIsNone(result.runtime_metrics)
                self.assertEqual(
                    result.fidelity["passed_checks"],
                    result.fidelity["total_checks"],
                )
                self.assertGreater(
                    result.static_metrics["canonical_token_estimate"], 0
                )
                self.assertEqual(
                    json.loads(result.to_json())["schema_version"],
                    EVALUATION_SCHEMA_VERSION,
                )

    def test_extracted_reference_and_static_metrics_are_separate(self) -> None:
        scenario = load_scenario(SCENARIOS / "model-card-examples.json")
        result = evaluate_scenario(scenario, repository_root=ROOT)
        reference_check = next(
            check for check in result.checks if check.check_id == "reference-loads"
        )
        self.assertTrue(reference_check.passed)
        self.assertEqual(
            set(result.static_metrics),
            {
                "canonical_token_estimate",
                "compiled_root_token_estimate",
                "compiled_normal_path_token_estimate",
            },
        )
        self.assertNotIn("latency_ms", result.static_metrics)

    def test_failed_mock_assertion_produces_explainable_result(self) -> None:
        value = json.loads(
            (SCENARIOS / "concise-review.json").read_text(encoding="utf-8")
        )
        value["mock_transcript"]["actions"].append("invent-defect")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            result = evaluate_scenario(load_scenario(path), repository_root=ROOT)
        self.assertFalse(result.passed)
        self.assertTrue(
            any(
                check.check_id == "forbidden-action-1" and not check.passed
                for check in result.checks
            )
        )

    def test_scenario_loader_rejects_unknown_fields(self) -> None:
        value = json.loads(
            (SCENARIOS / "concise-review.json").read_text(encoding="utf-8")
        )
        value["surprise"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(
                EvaluationScenarioError, "missing or unknown"
            ):
                load_scenario(path)

    def test_live_evaluator_requires_explicit_opt_in(self) -> None:
        scenario = load_scenario(SCENARIOS / "concise-review.json")

        class StubEvaluator:
            def __init__(self) -> None:
                self.calls = []

            def evaluate(self, scenario, variant):
                self.calls.append(variant)
                return RuntimeObservation(
                    True, "ok", input_tokens=1, output_tokens=1
                )

        evaluator = StubEvaluator()
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            run_live_evaluation(scenario, evaluator)
        self.assertEqual(evaluator.calls, [])
        observations = run_live_evaluation(scenario, evaluator, enabled=True)
        self.assertEqual(list(observations), ["canonical", "compiled"])
        self.assertEqual(evaluator.calls, ["canonical", "compiled"])


if __name__ == "__main__":
    unittest.main()
