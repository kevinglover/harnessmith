"""Harness capability definitions and target-specific rendering policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

from .errors import SkillCompilerError
from .frontmatter import filter_fields, replace_scalar, scalar_value
from .model import FrontmatterField, InvocationPolicy, SkillIR


STANDARD_FIELDS: Set[str] = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

CLAUDE_FIELDS: Set[str] = STANDARD_FIELDS | {
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "background",
    "hooks",
    "paths",
    "shell",
}

CURSOR_FIELDS: Set[str] = STANDARD_FIELDS | {
    "paths",
    "disable-model-invocation",
    "icon",
    "color",
}

CODEX_FIELDS: Set[str] = STANDARD_FIELDS


@dataclass(frozen=True)
class AdaptedFrontmatter:
    fields: Tuple[FrontmatterField, ...]
    extra_files: Dict[str, str]
    transformations: List[Dict[str, object]]


def source_invocation_policy(ir: SkillIR) -> InvocationPolicy:
    disabled = scalar_value(ir.field("disable-model-invocation"), False)
    user_invocable = scalar_value(ir.field("user-invocable"), True)
    if not isinstance(disabled, bool):
        raise SkillCompilerError("disable-model-invocation must be boolean")
    if not isinstance(user_invocable, bool):
        raise SkillCompilerError("user-invocable must be boolean")
    return InvocationPolicy(allow_model=not disabled, allow_user=user_invocable)


def adapt_frontmatter(
    ir: SkillIR, target: str, invocation: InvocationPolicy
) -> AdaptedFrontmatter:
    target = target.lower()
    if target not in ("generic", "cursor", "claude", "codex"):
        raise SkillCompilerError("unknown target: %s" % target)

    if target == "claude":
        allowed = CLAUDE_FIELDS
    elif target == "cursor":
        allowed = CURSOR_FIELDS
    else:
        allowed = CODEX_FIELDS

    _validate_unsupported_fields(ir, target, allowed)
    fields, dropped = filter_fields(ir.frontmatter, allowed)
    transformations: List[Dict[str, object]] = []
    original_invocation = source_invocation_policy(ir)
    if invocation != original_invocation:
        transformations.append(
            {
                "type": "invocation-policy-override",
                "source": {
                    "allow_model": original_invocation.allow_model,
                    "allow_user": original_invocation.allow_user,
                },
                "output": {
                    "allow_model": invocation.allow_model,
                    "allow_user": invocation.allow_user,
                },
            }
        )
    if dropped:
        transformations.append(
            {
                "type": "frontmatter-filter",
                "dropped": list(dropped),
                "reason": "not supported by target; defaults or presentation-only metadata preserved behavior",
            }
        )

    extra_files: Dict[str, str] = {}
    if target == "claude":
        fields = replace_scalar(
            fields, "disable-model-invocation", not invocation.allow_model
        )
        fields = replace_scalar(fields, "user-invocable", invocation.allow_user)
    elif target == "cursor":
        if not invocation.allow_user:
            raise SkillCompilerError(
                "Cursor cannot represent user-invocable: false without weakening invocation semantics"
            )
        fields = replace_scalar(
            fields, "disable-model-invocation", not invocation.allow_model
        )
    elif target == "codex":
        if not invocation.allow_user:
            raise SkillCompilerError(
                "Codex cannot represent user-invocable: false without weakening invocation semantics"
            )
        if not invocation.allow_model:
            extra_files["agents/openai.yaml"] = (
                "policy:\n  allow_implicit_invocation: false\n"
            )
            transformations.append(
                {
                    "type": "invocation-adapter",
                    "source": "canonical invocation policy: explicit-only",
                    "output": "agents/openai.yaml policy.allow_implicit_invocation: false",
                }
            )
    else:
        if invocation != InvocationPolicy():
            raise SkillCompilerError(
                "the generic Agent Skills standard has no portable invocation policy for this source"
            )

    return AdaptedFrontmatter(
        fields=fields,
        extra_files=extra_files,
        transformations=transformations,
    )


def _validate_unsupported_fields(
    ir: SkillIR, target: str, allowed: Sequence[str]
) -> None:
    """Reject behavior-bearing fields that an adapter cannot preserve."""

    safe_to_drop = {
        "argument-hint",
        "user-invocable",
        "disable-model-invocation",
        "icon",
        "color",
    }
    allowed_set = set(allowed)
    for field in ir.frontmatter:
        if field.key in allowed_set or field.key in safe_to_drop:
            continue
        raise SkillCompilerError(
            "target '%s' cannot preserve frontmatter field '%s'"
            % (target, field.key)
        )
