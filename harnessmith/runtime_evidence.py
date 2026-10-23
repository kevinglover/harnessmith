"""Opt-in, paired runtime evidence; no built-in network provider or model claims."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol, Tuple
from uuid import uuid4

from . import __version__
from .compiler import CompileOptions, compile_skill
from .evaluation import EvaluationScenario, evaluate_scenario
from .evaluation_turns import TurnTrace, check_turns, parse_trace
from .fixture_corpus import load_and_validate_manifest


@dataclass(frozen=True)
class RuntimeEnvironment:
    harness: str
    harness_version: str
    model: str
    model_version: str
    mode: str
    mode_version: str
    instrumentation_version: str
    permission_policy: str
    cache_policy: str
    configuration_id: str


@dataclass(frozen=True)
class RuntimeTurnInput:
    event: str
    prompt: str
    invocation: str


@dataclass(frozen=True)
class RuntimeRequest:
    """One fresh session containing the ordered turns, with exact package bytes."""

    scenario_id: str
    target: str
    turns: Tuple[RuntimeTurnInput, ...]
    variant: str
    sample: int
    session_id: str
    files: Mapping[str, bytes]
    executable_files: Tuple[str, ...]
    environment: RuntimeEnvironment


@dataclass(frozen=True)
class RuntimeSample:
    """Provider-reported measurements for an entire fresh-session trace."""

    turns: Tuple[TurnTrace, ...]
    input_tokens: int
    output_tokens: int
    latency_ms: int


class EvidenceEvaluator(Protocol):
    def evaluate(self, request: RuntimeRequest) -> RuntimeSample: ...


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _file_hashes(files: Mapping[str, bytes]) -> Mapping[str, str]:
    return {
        path: hashlib.sha256(content).hexdigest()
        for path, content in sorted(files.items())
    }


def run_runtime_evidence(
    scenario: EvaluationScenario,
    evaluator: EvidenceEvaluator,
    *,
    repository_root: Path,
    environment: RuntimeEnvironment,
    samples: int = 3,
    enabled: bool = False,
    evidence_kind: str = "runtime",
) -> Mapping[str, object]:
    """Collect repeated pairs after validation, alternating variant order.

    Providers must honor fresh session IDs and the declared environment, install
    the supplied bytes, and return measured (not estimated) usage. Local mocks
    must explicitly use evidence_kind='mock'. No aggregate efficiency claim is
    inferred from these observations.
    """
    if enabled is not True:
        raise RuntimeError("runtime evidence is disabled; pass enabled=True explicitly")
    if scenario.schema_version != 2 or not scenario.turns:
        raise ValueError("runtime evidence requires a version-2 turn scenario")
    if type(samples) is not int or samples < 2:
        raise ValueError("at least two paired samples are required")
    if evidence_kind not in ("runtime", "mock"):
        raise ValueError("evidence_kind must be runtime or mock")
    if not isinstance(environment, RuntimeEnvironment) or any(
        not isinstance(value, str) or not value.strip()
        for value in asdict(environment).values()
    ):
        raise ValueError(
            "all runtime environment identifiers must be non-empty strings"
        )
    root = Path(repository_root).resolve()
    offline = evaluate_scenario(scenario, repository_root=root)
    if not offline.passed:
        raise ValueError(
            "offline scenario contract failed; runtime provider was not called"
        )
    records = load_and_validate_manifest(root / "fixtures/manifest.json", root)
    record = next(
        record for record in records if record.fixture_id == scenario.fixture_id
    )
    source = root / record.source_path
    configuration = {
        "target": scenario.target,
        "extract_sections": scenario.extract_sections,
    }
    package = compile_skill(
        source,
        CompileOptions(
            target=scenario.target,
            extract_sections=scenario.extract_sections,
            source_id=record.source_path,
            expected_source_sha256=record.source_sha256,
        ),
    )
    canonical = {}
    executable = []
    for path in sorted(source.parent.rglob("*")):
        if path.is_symlink():
            raise ValueError("canonical runtime package must not contain symlinks")
        if path.is_file():
            relative = path.relative_to(source.parent).as_posix()
            canonical[relative] = path.read_bytes()
            if path.stat().st_mode & 0o111:
                executable.append(relative)
    if hashlib.sha256(canonical["SKILL.md"]).hexdigest() != record.source_sha256:
        raise ValueError("canonical source changed during runtime preparation")
    packages = {"canonical": canonical, "compiled": dict(package.file_bytes())}
    modes = {"canonical": tuple(executable), "compiled": package.executable_files}
    run_id = str(uuid4())
    observations = []
    for sample in range(1, samples + 1):
        order = ("canonical", "compiled") if sample % 2 else ("compiled", "canonical")
        for variant in order:
            session_id = "%s/%d/%s" % (run_id, sample, variant)
            request = RuntimeRequest(
                scenario.scenario_id,
                scenario.target,
                tuple(
                    RuntimeTurnInput(turn.event, turn.prompt, turn.invocation)
                    for turn in scenario.turns
                ),
                variant,
                sample,
                session_id,
                MappingProxyType(packages[variant]),
                modes[variant],
                environment,
            )
            observation = evaluator.evaluate(request)
            if not isinstance(observation, RuntimeSample):
                raise ValueError("provider must return RuntimeSample")
            for name in ("input_tokens", "output_tokens", "latency_ms"):
                value = getattr(observation, name)
                if type(value) is not int or value < 0:
                    raise ValueError("measured %s must be a nonnegative integer" % name)
            if not isinstance(observation.turns, tuple) or any(
                not isinstance(trace, TurnTrace) for trace in observation.turns
            ):
                raise ValueError("provider turns must be a tuple of TurnTrace")
            traces = tuple(parse_trace(asdict(trace)) for trace in observation.turns)
            checks = check_turns(
                scenario.turns,
                traces,
                variant=variant,
                allow_model=scenario.expected_invocation.allow_model,
                allow_user=scenario.expected_invocation.allow_user,
                forbidden_actions=scenario.forbidden_actions,
                available_files=tuple(packages[variant]),
            )
            observations.append(
                {
                    "sample": sample,
                    "variant": variant,
                    "session_id": session_id,
                    "observation": asdict(observation),
                    "passed": all(check[1] for check in checks),
                    "checks": [
                        {"check_id": key, "passed": passed, "message": message}
                        for key, passed, message in checks
                    ],
                }
            )
    return {
        "schema_version": 1,
        "evidence_kind": evidence_kind,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "compiler_version": __version__,
        "scenario_id": scenario.scenario_id,
        "scenario_sha256": _digest(asdict(scenario)),
        "source_sha256": record.source_sha256,
        "compilation": configuration,
        "compilation_sha256": _digest(configuration),
        "recipe_sha256": None,  # Direct extraction configuration, not a recipe run.
        "environment": asdict(environment),
        "samples": samples,
        "packages": {
            variant: {"files": _file_hashes(files), "executable_files": modes[variant]}
            for variant, files in packages.items()
        },
        "static_metrics": dict(offline.static_metrics),
        "passed": all(item["passed"] for item in observations),
        "observations": observations,
    }
