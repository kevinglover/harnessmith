from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from harnessmith.evaluation import (
    EvaluationScenarioError,
    evaluate_scenario,
    load_scenario,
)
from harnessmith.evaluation_turns import TurnTrace
from harnessmith.runtime_evidence import (
    RuntimeEnvironment,
    RuntimeSample,
    run_runtime_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evaluations/scenarios"
ENVIRONMENT = RuntimeEnvironment(
    "test-harness",
    "1",
    "test-model",
    "1",
    "test-mode",
    "1",
    "test-instrumentation-v1",
    "read-only",
    "cold",
    "deterministic-stub-v1",
)


class ReplayProvider:
    def __init__(self, scenario):
        self.scenario = scenario
        self.requests = []
        self.transform = lambda observation: observation

    def evaluate(self, request):
        self.requests.append(request)
        return self.transform(
            RuntimeSample(
                tuple(
                    getattr(turn, "mock_" + request.variant)
                    for turn in self.scenario.turns
                ),
                input_tokens=100,
                output_tokens=20,
                latency_ms=5,
            )
        )


class TurnEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.scenario = load_scenario(SCENARIOS / "lifecycle-generic.json")

    def test_matrix_covers_all_targets_and_lifecycle_events(self):
        scenarios = [load_scenario(path) for path in SCENARIOS.glob("*.json")]
        lifecycle = [
            scenario
            for scenario in scenarios
            if scenario.scenario_id.startswith("lifecycle-")
        ]
        self.assertEqual(
            {"generic", "cursor", "claude", "codex"}, {s.target for s in lifecycle}
        )
        for scenario in lifecycle:
            self.assertEqual(
                {"prompt", "approval", "continuation", "compaction", "hook", "abort"},
                {turn.event for turn in scenario.turns},
            )
            self.assertTrue(evaluate_scenario(scenario, repository_root=ROOT).passed)
        for prefix in ("explicit-channel-", "non-trigger-"):
            selected = [s for s in scenarios if s.scenario_id.startswith(prefix)]
            self.assertTrue(selected)
            for scenario in selected:
                self.assertFalse(scenario.turns[0].expected_invoked)
                self.assertTrue(
                    evaluate_scenario(scenario, repository_root=ROOT).passed
                )

    def test_bad_canonical_or_compiled_turn_fails_independently(self):
        for variant in ("canonical", "compiled"):
            for index, changed in [
                (0, {"invoked": False}),
                (0, {"actions": ("request-approval", "inspect-change")}),
                (0, {"actions": ("inspect-change", "request-approval", "run-checks")}),
                (1, {"actions": ("deploy",)}),
                (2, {"output": "Invented findings"}),
                (3, {"reference_loads": ("missing.md",)}),
                (4, {"actions": ("report-hook-failure", "retry-hook")}),
                (5, {"actions": ("run-checks",)}),
            ]:
                with self.subTest(variant=variant, index=index, changed=changed):
                    turns = list(self.scenario.turns)
                    field = "mock_" + variant
                    turns[index] = replace(
                        turns[index],
                        **{field: replace(getattr(turns[index], field), **changed)},
                    )
                    result = evaluate_scenario(
                        replace(self.scenario, turns=tuple(turns)), repository_root=ROOT
                    )
                    self.assertFalse(result.passed)
                    self.assertTrue(
                        any(
                            not c.passed and c.scope == "mock-" + variant
                            for c in result.checks
                        )
                    )

    def test_model_cannot_invoke_explicit_only_skill(self):
        scenario = load_scenario(SCENARIOS / "explicit-channel-codex.json")
        turn = replace(
            scenario.turns[0],
            expected_invoked=True,
            mock_canonical=replace(scenario.turns[0].mock_canonical, invoked=True),
            mock_compiled=replace(scenario.turns[0].mock_compiled, invoked=True),
        )
        self.assertFalse(
            evaluate_scenario(
                replace(scenario, turns=(turn, *scenario.turns[1:])),
                repository_root=ROOT,
            ).passed
        )

    def test_loader_rejects_malformed_turns_and_boolean_versions(self):
        original = json.loads((SCENARIOS / "lifecycle-generic.json").read_text())
        mutations = [
            lambda d: d.update(schema_version=True),
            lambda d: d.update(schema_version=2.0),
            lambda d: d.update(turns=[]),
            lambda d: d.update(prompt="different prompt"),
            lambda d: d["turns"][0].update(event="unknown"),
            lambda d: d["turns"][0].update(invocation="unknown"),
            lambda d: d["turns"][0].update(expected_invoked=1),
            lambda d: d["turns"][0].update(invocation="none"),
            lambda d: d["turns"][0].update(expected_actions=[False]),
            lambda d: d["turns"][0]["mock_compiled"].update(invoked=1),
            lambda d: d["turns"][0].update(surprise=True),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.json"
            for mutate in mutations:
                value = json.loads(json.dumps(original))
                mutate(value)
                path.write_text(json.dumps(value))
                with self.assertRaises(EvaluationScenarioError):
                    load_scenario(path)


class RuntimeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.scenario = load_scenario(SCENARIOS / "lifecycle-generic.json")
        self.provider = ReplayProvider(self.scenario)

    def run_evidence(self, **kwargs):
        options = dict(
            repository_root=ROOT,
            environment=ENVIRONMENT,
            samples=2,
            enabled=True,
            evidence_kind="mock",
        )
        options.update(kwargs)
        return run_runtime_evidence(self.scenario, self.provider, **options)

    def test_disabled_and_invalid_configuration_never_calls_provider(self):
        for options in [
            dict(enabled=False),
            dict(enabled=1),
            dict(samples=1),
            dict(samples=True),
            dict(samples=2.5),
            dict(evidence_kind="unknown"),
            dict(environment=replace(ENVIRONMENT, model_version=" ")),
        ]:
            with (
                self.subTest(options=options),
                self.assertRaises((RuntimeError, ValueError)),
            ):
                self.run_evidence(**options)
        self.assertEqual([], self.provider.requests)
        with self.assertRaisesRegex(ValueError, "version-2"):
            run_runtime_evidence(
                load_scenario(SCENARIOS / "concise-review.json"),
                self.provider,
                repository_root=ROOT,
                environment=ENVIRONMENT,
                enabled=True,
            )
        self.assertEqual([], self.provider.requests)

    def test_repeated_pairs_have_provenance_isolation_and_no_answer_leakage(self):
        evidence = self.run_evidence()
        self.assertTrue(evidence["passed"])
        self.assertEqual("mock", evidence["evidence_kind"])
        self.assertEqual(
            ["canonical", "compiled", "compiled", "canonical"],
            [r.variant for r in self.provider.requests],
        )
        self.assertEqual(4, len({r.session_id for r in self.provider.requests}))
        self.assertEqual(64, len(evidence["source_sha256"]))
        self.assertEqual(64, len(evidence["scenario_sha256"]))
        self.assertEqual(64, len(evidence["compilation_sha256"]))
        self.assertIsNone(evidence["recipe_sha256"])
        self.assertEqual(asdict(ENVIRONMENT), evidence["environment"])
        self.assertNotIn("references/examples.md", self.provider.requests[0].files)
        self.assertIn("references/examples.md", self.provider.requests[1].files)
        self.assertFalse(hasattr(self.provider.requests[0], "scenario"))
        self.assertFalse(
            hasattr(self.provider.requests[0].turns[0], "expected_actions")
        )
        with self.assertRaises(TypeError):
            self.provider.requests[0].files["SKILL.md"] = b"mutated"
        from jsonschema import validate

        validate(
            json.loads(json.dumps(evidence)),
            json.loads((ROOT / "schemas/runtime-evidence.schema.json").read_text()),
        )

    def test_wrong_runtime_trace_fails_without_losing_raw_evidence(self):
        self.provider.transform = lambda sample: replace(
            sample, turns=(TurnTrace(True, "bad", ("deploy",), ()),)
        )
        evidence = self.run_evidence()
        self.assertFalse(evidence["passed"])
        self.assertEqual(
            ("deploy",),
            evidence["observations"][0]["observation"]["turns"][0]["actions"],
        )
        self.assertTrue(
            any(not c["passed"] for c in evidence["observations"][0]["checks"])
        )

    def test_missing_or_invalid_usage_is_not_reported_as_measured(self):
        for field in ("input_tokens", "output_tokens", "latency_ms"):
            for invalid in (None, True, -1, 1.5):
                with self.subTest(field=field, invalid=invalid):
                    self.provider.transform = lambda sample: replace(
                        sample, **{field: invalid}
                    )
                    with self.assertRaisesRegex(ValueError, "measured"):
                        self.run_evidence()

    def test_bad_offline_contract_prevents_runtime_calls(self):
        self.scenario = replace(self.scenario, required_constraints=("not in source",))
        with self.assertRaisesRegex(ValueError, "offline scenario contract failed"):
            self.run_evidence()
        self.assertEqual([], self.provider.requests)

    def test_scenario_and_configuration_hashes_track_changes(self):
        before = self.run_evidence()
        self.scenario = replace(self.scenario, scenario_id="renamed")
        renamed = self.run_evidence()
        self.assertNotEqual(before["scenario_sha256"], renamed["scenario_sha256"])
        self.assertEqual(before["compilation_sha256"], renamed["compilation_sha256"])


if __name__ == "__main__":
    unittest.main()
