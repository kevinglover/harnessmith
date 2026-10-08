"""Versioned, target-neutral contracts shared by Harnessmith subsystems.

These models intentionally contain no audit, adapter, or compiler policy.  They
give those subsystems a common vocabulary while their implementations evolve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


CONTRACT_SCHEMA_VERSION = 1


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"


class CapabilityStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    LOSSY = "lossy"


@dataclass(frozen=True)
class SourceSpan:
    """One-based inclusive source location."""

    path: str
    start_line: int
    end_line: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("source span path must not be empty")
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError("source span lines must be one-based and ordered")
        for column in (self.start_column, self.end_column):
            if column is not None and column < 1:
                raise ValueError("source span columns must be one-based")


@dataclass(frozen=True)
class Remediation:
    summary: str
    recipe_fragment: Optional[Dict[str, object]] = None
    requires_review: bool = True


@dataclass(frozen=True)
class Diagnostic:
    """Stable finding emitted by analysis or verification."""

    rule_id: str
    severity: Severity
    message: str
    rationale: str
    source_span: Optional[SourceSpan] = None
    estimated_savings_tokens: Optional[int] = None
    remediation: Optional[Remediation] = None
    schema_version: int = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.rule_id.startswith("HS") or not self.rule_id[2:].isdigit():
            raise ValueError("diagnostic rule_id must have the form HS<number>")
        if not self.message or not self.rationale:
            raise ValueError("diagnostic message and rationale must not be empty")
        if self.estimated_savings_tokens is not None and self.estimated_savings_tokens < 0:
            raise ValueError("estimated token savings cannot be negative")


@dataclass(frozen=True)
class Capability:
    """One adapter behavior and how faithfully a target represents it."""

    name: str
    status: CapabilityStatus
    explanation: str
    native_representation: Optional[str] = None


@dataclass(frozen=True)
class AdapterCapabilities:
    target: str
    capabilities: Tuple[Capability, ...]
    schema_version: int = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        names = [item.name for item in self.capabilities]
        if not self.target or len(names) != len(set(names)):
            raise ValueError("adapter target must be set and capability names unique")


@dataclass(frozen=True)
class FixtureRecord:
    """Pinned source material used by the offline evaluation corpus."""

    fixture_id: str
    repository: str
    revision: str
    license: str
    source_path: str
    source_sha256: str
    expected_targets: Tuple[str, ...]
    expected_diagnostics: Tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = CONTRACT_SCHEMA_VERSION
