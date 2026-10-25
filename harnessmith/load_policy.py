"""Explicit, source-reviewed conditional extraction policies; never inferred."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from .errors import SkillCompilerError


@dataclass(frozen=True)
class ConditionalSection:
    section: str
    when: str
    rationale: str

    def __post_init__(self):
        for value in (self.section, self.when, self.rationale):
            if (
                not isinstance(value, str)
                or not value.strip()
                or any(ord(c) < 32 for c in value)
            ):
                raise SkillCompilerError(
                    "conditional section fields must be non-empty single-line text"
                )

    def policy(self):
        return {"optional": True, "when": self.when, "rationale": self.rationale}


def parse_conditional_sections(value: object) -> Tuple[ConditionalSection, ...]:
    if not isinstance(value, dict):
        raise SkillCompilerError("conditional_sections must be an object")
    result = []
    for section, policy in value.items():
        if (
            not isinstance(policy, dict)
            or set(policy) != {"optional", "when", "rationale"}
            or policy.get("optional") is not True
        ):
            raise SkillCompilerError(
                "conditional sections require optional=true, when and rationale"
            )
        result.append(ConditionalSection(section, policy["when"], policy["rationale"]))
    return tuple(result)


def conditional_directive(
    heading: str, filename: str, policy: Mapping[str, object]
) -> str:
    return (
        heading
        + "\n"
        + (
            "**Optional reference — load only when:** %s\n\n"
            "When this condition applies, read [`%s`](%s) completely before using its guidance. "
            "Otherwise skip this reference and continue with the core instructions. "
            "Do not load it merely because it is linked here.\n\n"
            % (policy["when"], filename, filename)
        )
    )
