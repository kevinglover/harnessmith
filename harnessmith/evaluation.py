"""Deterministic behavioral-equivalence evaluation for compiled skills.

The offline evaluator intentionally makes no model calls.  It compares source and
compiled packages against versioned scenario contracts and replays a checked-in
mock transcript.  Live evaluators are an explicit, disabled-by-default extension
point and their runtime measurements are kept separate from static compiler data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Protocol, Tuple

from .adapters import source_invocation_policy
from .audit import audit_skill
from .compiler import CompileOptions, compile_skill
from .contracts import CapabilityStatus
from .fixture_corpus import load_and_validate_manifest
from .metrics import estimate_tokens
from .parser import parse_skill
from .targets import get_target


EVALUATION_SCHEMA_VERSION = 1
_ASSERTION_KINDS = frozenset(("output_contains", "output_not_contains"))


class EvaluationScenarioError(ValueError):
    """Raised when a scenario is malformed or cannot be evaluated safely."""


@dataclass(frozen=True)
class ExpectedInvocation:
    allow_model: bool
    allow_user: bool


@dataclass(frozen=True)
class SemanticAssertion:
    kind: str
    value: str


@dataclass(frozen=True)
class MockTranscript:
    invoked: bool
    output: str
    actions: Tuple[str, ...]
    reference_loads: Tuple[str, ...]


@dataclass(frozen=True)
class EvaluationScenario:
    scenario_id: str
    fixture_id: str
    target: str
    prompt: str
    expected_invocation: ExpectedInvocation
    extract_sections: Tuple[str, ...]
    required_constraints: Tuple[str, ...]
    forbidden_actions: Tuple[str, ...]
    expected_reference_loads: Tuple[str, ...]
    semantic_assertions: Tuple[SemanticAssertion, ...]
    mock_transcript: MockTranscript
    schema_version: int = EVALUATION_SCHEMA_VERSION


@dataclass(frozen=True)
class EvaluationCheck:
    check_id: str
    scope: str
    passed: bool
    message: str


@dataclass(frozen=True)
class EvaluationResult:
    scenario_id: str
    fixture_id: str
    target: str
    passed: bool
    checks: Tuple[EvaluationCheck, ...]
    fidelity: Mapping[str, int]
    static_metrics: Mapping[str, int]
    runtime_metrics: Optional[Mapping[str, object]] = None
    schema_version: int = EVALUATION_SCHEMA_VERSION

    def to_json(self, *, indent: int = 2) -> str:
        """Return a deterministic, machine-readable result document."""

        return json.dumps(asdict(self), indent=indent, sort_keys=True) + "\n"


@dataclass(frozen=True)
class RuntimeObservation:
    """Nondeterministic output returned by an explicitly enabled live evaluator."""

    invoked: bool
    output: str
    reference_loads: Tuple[str, ...] = ()
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None


class LiveEvaluator(Protocol):
    """Optional provider interface; implementations may perform external calls."""

    def evaluate(
        self, scenario: EvaluationScenario, variant: str
    ) -> RuntimeObservation: ...


def load_scenario(path: Path) -> EvaluationScenario:
    """Load and strictly validate one versioned JSON scenario."""

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationScenarioError(
            "cannot read evaluation scenario: %s" % exc
        ) from exc
    if not isinstance(value, dict):
        raise EvaluationScenarioError("scenario must be a JSON object")
    expected_keys = {
        "schema_version",
        "scenario_id",
        "fixture_id",
        "target",
        "prompt",
        "expected_invocation",
        "compilation",
        "required_constraints",
        "forbidden_actions",
        "expected_reference_loads",
        "semantic_assertions",
        "mock_transcript",
    }
    if set(value) != expected_keys:
        raise EvaluationScenarioError("scenario has missing or unknown fields")
    if value["schema_version"] != EVALUATION_SCHEMA_VERSION:
        raise EvaluationScenarioError("unsupported evaluation scenario schema version")

    invocation = _object(value, "expected_invocation")
    if set(invocation) != {"allow_model", "allow_user"} or any(
        not isinstance(invocation[key], bool) for key in invocation
    ):
        raise EvaluationScenarioError("expected_invocation must contain two booleans")
    compilation = _object(value, "compilation")
    if set(compilation) != {"extract_sections"}:
        raise EvaluationScenarioError("compilation must contain only extract_sections")
    transcript = _object(value, "mock_transcript")
    if set(transcript) != {"invoked", "output", "actions", "reference_loads"}:
        raise EvaluationScenarioError("mock_transcript has missing or unknown fields")
    if not isinstance(transcript["invoked"], bool) or not isinstance(
        transcript["output"], str
    ):
        raise EvaluationScenarioError(
            "mock transcript invoked/output types are invalid"
        )

    assertions_value = value["semantic_assertions"]
    if not isinstance(assertions_value, list):
        raise EvaluationScenarioError("semantic_assertions must be an array")
    assertions = []
    for index, assertion in enumerate(assertions_value):
        if not isinstance(assertion, dict) or set(assertion) != {"kind", "value"}:
            raise EvaluationScenarioError("semantic_assertions[%d] is invalid" % index)
        kind = _nonempty_string(assertion, "kind")
        if kind not in _ASSERTION_KINDS:
            raise EvaluationScenarioError("unknown semantic assertion: %s" % kind)
        assertions.append(SemanticAssertion(kind, _nonempty_string(assertion, "value")))

    return EvaluationScenario(
        scenario_id=_nonempty_string(value, "scenario_id"),
        fixture_id=_nonempty_string(value, "fixture_id"),
        target=_nonempty_string(value, "target"),
        prompt=_nonempty_string(value, "prompt"),
        expected_invocation=ExpectedInvocation(
            invocation["allow_model"], invocation["allow_user"]
        ),
        extract_sections=_string_array(compilation, "extract_sections"),
        required_constraints=_string_array(value, "required_constraints"),
        forbidden_actions=_string_array(value, "forbidden_actions"),
        expected_reference_loads=_string_array(value, "expected_reference_loads"),
        semantic_assertions=tuple(assertions),
        mock_transcript=MockTranscript(
            transcript["invoked"],
            transcript["output"],
            _string_array(transcript, "actions"),
            _string_array(transcript, "reference_loads"),
        ),
    )


def evaluate_scenario(
    scenario: EvaluationScenario, *, repository_root: Path
) -> EvaluationResult:
    """Compile and evaluate a scenario entirely offline."""

    repository_root = Path(repository_root).resolve()
    records = load_and_validate_manifest(
        repository_root / "fixtures" / "manifest.json", repository_root
    )
    fixtures = {record.fixture_id: record for record in records}
    if scenario.fixture_id not in fixtures:
        raise EvaluationScenarioError("unknown fixture_id: %s" % scenario.fixture_id)
    record = fixtures[scenario.fixture_id]
    if scenario.target not in record.expected_targets:
        raise EvaluationScenarioError(
            "fixture %s is not compatible with target %s"
            % (scenario.fixture_id, scenario.target)
        )
    source = repository_root / record.source_path
    ir = parse_skill(source, source_id=record.source_path)
    package = compile_skill(
        source,
        CompileOptions(
            target=scenario.target,
            extract_sections=scenario.extract_sections,
            source_id=record.source_path,
            expected_source_sha256=record.source_sha256,
        ),
    )

    checks = []
    policy = source_invocation_policy(ir)
    expected_policy = scenario.expected_invocation
    checks.append(
        _check(
            "invocation-policy",
            "canonical-and-compiled",
            policy.allow_model == expected_policy.allow_model
            and policy.allow_user == expected_policy.allow_user
            and _compiled_invocation_is_represented(
                package.files, scenario.target, expected_policy
            ),
            "source invocation policy matches the scenario and is compiled fail-closed",
        )
    )
    audit = audit_skill(source, scenario.target, source_id=record.source_path)
    actual_diagnostics = tuple(
        diagnostic["rule_id"] for diagnostic in audit["diagnostics"]
    )
    checks.append(
        _check(
            "expected-diagnostics",
            "canonical",
            actual_diagnostics == record.expected_diagnostics,
            "audit diagnostics match the fixture's pinned expectations",
        )
    )
    expected_invoked = expected_policy.allow_user
    checks.append(
        _check(
            "mock-invocation",
            "mock-transcript",
            scenario.mock_transcript.invoked == expected_invoked,
            "mock user prompt invocation matches expected user policy",
        )
    )

    canonical_text = ir.source_text
    compiled_text = "\n".join(
        content
        for path, content in sorted(package.files.items())
        if path.endswith(".md")
    )
    for index, constraint in enumerate(scenario.required_constraints):
        checks.append(
            _check(
                "required-constraint-%d" % (index + 1),
                "canonical-and-compiled",
                constraint in canonical_text and constraint in compiled_text,
                "required constraint is retained verbatim in both variants",
            )
        )
    for index, action in enumerate(scenario.forbidden_actions):
        checks.append(
            _check(
                "forbidden-action-%d" % (index + 1),
                "mock-transcript",
                action not in scenario.mock_transcript.actions,
                "mock transcript does not perform forbidden action %r" % action,
            )
        )

    actual_loads = scenario.mock_transcript.reference_loads
    checks.append(
        _check(
            "reference-loads",
            "compiled-package-and-mock-transcript",
            actual_loads == scenario.expected_reference_loads
            and all(path in package.files for path in actual_loads),
            "mock reference loads exactly match expected compiled package references",
        )
    )
    for index, assertion in enumerate(scenario.semantic_assertions):
        found = assertion.value in scenario.mock_transcript.output
        passed = found if assertion.kind == "output_contains" else not found
        checks.append(
            _check(
                "semantic-%d" % (index + 1),
                "mock-transcript",
                passed,
                "%s assertion for %r" % (assertion.kind, assertion.value),
            )
        )

    passed_count = sum(check.passed for check in checks)
    static_metrics = {
        "canonical_token_estimate": estimate_tokens(ir.source_text),
        "compiled_root_token_estimate": package.metrics[
            "compiled_root_token_estimate"
        ],
        "compiled_normal_path_token_estimate": package.metrics[
            "normal_path_instruction_token_estimate"
        ],
    }
    return EvaluationResult(
        scenario_id=scenario.scenario_id,
        fixture_id=scenario.fixture_id,
        target=scenario.target,
        passed=passed_count == len(checks),
        checks=tuple(checks),
        fidelity={"passed_checks": passed_count, "total_checks": len(checks)},
        static_metrics=static_metrics,
        runtime_metrics=None,
    )


def run_live_evaluation(
    scenario: EvaluationScenario,
    evaluator: LiveEvaluator,
    *,
    enabled: bool = False,
) -> Mapping[str, RuntimeObservation]:
    """Run an optional provider twice only after explicit caller opt-in.

    This function is never used by the offline evaluator.  Keeping the opt-in at
    the call boundary makes accidental network use in normal tests unlikely.
    """

    if not enabled:
        raise RuntimeError("live evaluation is disabled; pass enabled=True explicitly")
    return {
        "canonical": evaluator.evaluate(scenario, "canonical"),
        "compiled": evaluator.evaluate(scenario, "compiled"),
    }


def _check(check_id: str, scope: str, passed: bool, message: str) -> EvaluationCheck:
    return EvaluationCheck(check_id, scope, passed, message)


def _compiled_invocation_is_represented(
    files: Mapping[str, str], target: str, expected: ExpectedInvocation
) -> bool:
    """Confirm the target's emitted representation of the canonical policy."""

    definition = get_target(target)
    model_capability = definition.capability("invocation.model")
    user_capability = definition.capability("invocation.user")
    if (
        not expected.allow_model
        and model_capability.status != CapabilityStatus.SUPPORTED
    ):
        return False
    if not expected.allow_user and user_capability.status != CapabilityStatus.SUPPORTED:
        return False
    root = files["SKILL.md"]
    if target in ("cursor", "claude"):
        model_value = "false" if expected.allow_model else "true"
        if "disable-model-invocation: %s" % model_value not in root:
            return False
    elif target == "codex":
        policy_file = "agents/openai.yaml" in files
        if policy_file != (not expected.allow_model):
            return False
    elif target == "generic" and not expected.allow_model:
        return False

    if target == "claude":
        return "user-invocable: %s" % str(expected.allow_user).lower() in root
    return expected.allow_user


def _object(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise EvaluationScenarioError("%s must be an object" % key)
    return result


def _nonempty_string(value: Mapping[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise EvaluationScenarioError("%s must be a non-empty string" % key)
    return result


def _string_array(value: Mapping[str, object], key: str) -> Tuple[str, ...]:
    result = value.get(key)
    if not isinstance(result, list) or any(
        not isinstance(item, str) or not item for item in result
    ):
        raise EvaluationScenarioError("%s must be an array of non-empty strings" % key)
    if len(result) != len(set(result)):
        raise EvaluationScenarioError("%s values must be unique" % key)
    return tuple(result)
