"""Strict, provider-neutral turn contracts shared by mock and runtime scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple


@dataclass(frozen=True)
class TurnTrace:
    invoked: bool
    output: str
    actions: Tuple[str, ...]
    reference_loads: Tuple[str, ...]


@dataclass(frozen=True)
class EvaluationTurn:
    event: str
    prompt: str
    invocation: str
    expected_invoked: bool
    expected_actions: Tuple[str, ...]
    canonical_reference_loads: Tuple[str, ...]
    compiled_reference_loads: Tuple[str, ...]
    output_contains: Tuple[str, ...]
    output_not_contains: Tuple[str, ...]
    mock_canonical: TurnTrace
    mock_compiled: TurnTrace


EVENTS = ("prompt", "approval", "abort", "hook", "continuation", "compaction")


def _strings(value: object) -> Tuple[str, ...]:
    # Order and repetitions matter for action and reference traces.
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError("trace fields must be arrays of non-empty strings")
    return tuple(value)


def parse_trace(value: object) -> TurnTrace:
    if not isinstance(value, dict) or set(value) != {
        "invoked",
        "output",
        "actions",
        "reference_loads",
    }:
        raise ValueError("trace has missing or unknown fields")
    if type(value["invoked"]) is not bool or not isinstance(value["output"], str):
        raise ValueError("trace invoked/output types are invalid")
    return TurnTrace(
        value["invoked"],
        value["output"],
        _strings(value["actions"]),
        _strings(value["reference_loads"]),
    )


def parse_turns(value: object) -> Tuple[EvaluationTurn, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("turns must be a non-empty array")
    turns = []
    for item in value:
        if not isinstance(item, dict) or set(item) != set(
            EvaluationTurn.__dataclass_fields__
        ):
            raise ValueError("turn has missing or unknown fields")
        if item["event"] not in EVENTS or item["invocation"] not in (
            "user",
            "model",
            "none",
        ):
            raise ValueError("unknown turn event or invocation channel")
        if not isinstance(item["prompt"], str) or not item["prompt"].strip():
            raise ValueError("turn prompt must be non-empty")
        if type(item["expected_invoked"]) is not bool:
            raise ValueError("expected_invoked must be a boolean")
        if item["invocation"] == "none" and item["expected_invoked"]:
            raise ValueError("no-invocation turn cannot expect invocation")
        turns.append(
            EvaluationTurn(
                event=item["event"],
                prompt=item["prompt"],
                invocation=item["invocation"],
                expected_invoked=item["expected_invoked"],
                expected_actions=_strings(item["expected_actions"]),
                canonical_reference_loads=_strings(item["canonical_reference_loads"]),
                compiled_reference_loads=_strings(item["compiled_reference_loads"]),
                output_contains=_strings(item["output_contains"]),
                output_not_contains=_strings(item["output_not_contains"]),
                mock_canonical=parse_trace(item["mock_canonical"]),
                mock_compiled=parse_trace(item["mock_compiled"]),
            )
        )
    return tuple(turns)


def check_turns(
    turns: Sequence[EvaluationTurn],
    traces: Sequence[TurnTrace],
    *,
    variant: str,
    allow_model: bool,
    allow_user: bool,
    forbidden_actions: Sequence[str],
    available_files: Sequence[str],
) -> Tuple[Tuple[str, bool, str], ...]:
    """Score exact ordered actions/reads and per-turn invocation/output expectations."""
    if variant not in ("canonical", "compiled"):
        raise ValueError("unknown variant")
    checks = [("turn-count", len(turns) == len(traces), "one trace per scenario turn")]
    for index, (turn, trace) in enumerate(zip(turns, traces), 1):
        prefix = "turn-%d-" % index
        permitted = {"user": allow_user, "model": allow_model, "none": False}[
            turn.invocation
        ]
        references = getattr(turn, variant + "_reference_loads")
        values: Mapping[str, bool] = {
            "invocation": trace.invoked == turn.expected_invoked
            and (not trace.invoked or permitted),
            "actions": trace.actions == turn.expected_actions,
            "forbidden-actions": not set(trace.actions).intersection(forbidden_actions),
            "reference-loads": trace.reference_loads == references
            and all(path in available_files for path in trace.reference_loads),
            "output": all(text in trace.output for text in turn.output_contains)
            and all(text not in trace.output for text in turn.output_not_contains),
        }
        checks.extend(
            (prefix + key, passed, "%s: %s" % (turn.event, key))
            for key, passed in values.items()
        )
    return tuple(checks)
