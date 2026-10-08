"""Machine-readable target registry for adapter implementations and tooling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterator, Mapping, Optional, Tuple

from .contracts import AdapterCapabilities, Capability, CapabilityStatus
from .errors import SkillCompilerError


STANDARD_FRONTMATTER_FIELDS = frozenset(
    {
        "name",
        "description",
        "license",
        "compatibility",
        "metadata",
        "allowed-tools",
    }
)


def _capability(
    name: str,
    status: CapabilityStatus,
    explanation: str,
    native_representation: Optional[str] = None,
) -> Capability:
    return Capability(name, status, explanation, native_representation)


@dataclass(frozen=True)
class TargetDefinition:
    """Declarative contract consumed by an adapter and external tooling."""

    name: str
    frontmatter_fields: FrozenSet[str]
    capabilities: AdapterCapabilities

    def __post_init__(self) -> None:
        if self.capabilities.target != self.name:
            raise ValueError("target definition and capability target must match")

    def capability(self, name: str) -> Capability:
        for item in self.capabilities.capabilities:
            if item.name == name:
                return item
        raise KeyError(name)


_COMMON_PACKAGE_CAPABILITIES = (
    _capability(
        "content.references",
        CapabilityStatus.SUPPORTED,
        "References can be included as package files and linked from SKILL.md.",
        "references/",
    ),
    _capability(
        "content.scripts",
        CapabilityStatus.SUPPORTED,
        "Helper scripts can be included in the compiled skill package.",
        "scripts/",
    ),
    _capability(
        "tools.allowlist",
        CapabilityStatus.SUPPORTED,
        "Allowed tools are represented by standard skill frontmatter.",
        "allowed-tools",
    ),
)


def _contract(target: str, *items: Capability) -> AdapterCapabilities:
    return AdapterCapabilities(target=target, capabilities=tuple(items))


# These declarations are deliberately independent even where field names overlap.
# A target changing its contract must not silently change another target.
GENERIC = TargetDefinition(
    name="generic",
    frontmatter_fields=frozenset(set(STANDARD_FRONTMATTER_FIELDS)),
    capabilities=_contract(
        "generic",
        _capability(
            "invocation.model",
            CapabilityStatus.UNSUPPORTED,
            "The portable Agent Skills format has no model-invocation control.",
        ),
        _capability(
            "invocation.user",
            CapabilityStatus.UNSUPPORTED,
            "The portable Agent Skills format has no user-invocation control.",
        ),
        _capability(
            "arguments",
            CapabilityStatus.UNSUPPORTED,
            "Harness-specific argument metadata has no portable representation.",
        ),
        _capability(
            "frontmatter.extensions",
            CapabilityStatus.UNSUPPORTED,
            "Only standard Agent Skills frontmatter is portable.",
        ),
        *_COMMON_PACKAGE_CAPABILITIES,
    ),
)

CURSOR = TargetDefinition(
    name="cursor",
    frontmatter_fields=frozenset(
        set(STANDARD_FRONTMATTER_FIELDS)
        | {"paths", "disable-model-invocation", "icon", "color"}
    ),
    capabilities=_contract(
        "cursor",
        _capability(
            "invocation.model",
            CapabilityStatus.SUPPORTED,
            "Model invocation can be disabled natively.",
            "disable-model-invocation",
        ),
        _capability(
            "invocation.user",
            CapabilityStatus.UNSUPPORTED,
            "Cursor cannot hide a skill from user invocation without weakening semantics.",
        ),
        _capability(
            "arguments",
            CapabilityStatus.UNSUPPORTED,
            "Claude argument metadata is presentation-only and is omitted.",
        ),
        _capability(
            "frontmatter.extensions",
            CapabilityStatus.SUPPORTED,
            "Cursor path and presentation metadata are represented natively.",
            "paths, icon, color",
        ),
        *_COMMON_PACKAGE_CAPABILITIES,
    ),
)

CLAUDE = TargetDefinition(
    name="claude",
    frontmatter_fields=frozenset(
        set(STANDARD_FRONTMATTER_FIELDS)
        | {
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
    ),
    capabilities=_contract(
        "claude",
        _capability(
            "invocation.model",
            CapabilityStatus.SUPPORTED,
            "Model invocation can be disabled natively.",
            "disable-model-invocation",
        ),
        _capability(
            "invocation.user",
            CapabilityStatus.SUPPORTED,
            "User invocation can be disabled natively.",
            "user-invocable",
        ),
        _capability(
            "arguments",
            CapabilityStatus.SUPPORTED,
            "Argument hints and declarations are native frontmatter.",
            "argument-hint, arguments",
        ),
        _capability(
            "frontmatter.extensions",
            CapabilityStatus.SUPPORTED,
            "Claude-specific execution and agent fields are preserved.",
            "Claude Code skill frontmatter",
        ),
        *_COMMON_PACKAGE_CAPABILITIES,
        _capability(
            "tools.denylist",
            CapabilityStatus.SUPPORTED,
            "Disallowed tools are represented natively.",
            "disallowed-tools",
        ),
    ),
)

CODEX = TargetDefinition(
    name="codex",
    frontmatter_fields=frozenset(set(STANDARD_FRONTMATTER_FIELDS)),
    capabilities=_contract(
        "codex",
        _capability(
            "invocation.model",
            CapabilityStatus.SUPPORTED,
            "Implicit invocation can be disabled in Codex metadata.",
            "agents/openai.yaml policy.allow_implicit_invocation",
        ),
        _capability(
            "invocation.user",
            CapabilityStatus.UNSUPPORTED,
            "Codex cannot hide a skill from user invocation without weakening semantics.",
        ),
        _capability(
            "arguments",
            CapabilityStatus.UNSUPPORTED,
            "Claude argument metadata is presentation-only and is omitted.",
        ),
        _capability(
            "frontmatter.extensions",
            CapabilityStatus.UNSUPPORTED,
            "Only standard skill frontmatter is emitted in SKILL.md.",
        ),
        *_COMMON_PACKAGE_CAPABILITIES,
        _capability(
            "metadata.extra_files",
            CapabilityStatus.SUPPORTED,
            "Codex policy metadata can accompany the skill.",
            "agents/openai.yaml",
        ),
    ),
)


_TARGETS: Mapping[str, TargetDefinition] = {
    item.name: item for item in (GENERIC, CURSOR, CLAUDE, CODEX)
}
TARGET_NAMES: Tuple[str, ...] = tuple(_TARGETS)


def normalize_target(target: str) -> str:
    """Return a canonical target name or fail with the public adapter error."""

    normalized = target.lower()
    if normalized not in _TARGETS:
        raise SkillCompilerError("unknown target: %s" % normalized)
    return normalized


def get_target(target: str) -> TargetDefinition:
    return _TARGETS[normalize_target(target)]


def iter_targets() -> Iterator[TargetDefinition]:
    return iter(_TARGETS.values())


def capability_documents() -> Dict[str, AdapterCapabilities]:
    """Return immutable capability contracts indexed by canonical target name."""

    return {name: definition.capabilities for name, definition in _TARGETS.items()}
