"""Intermediate representation and output models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class FrontmatterField:
    """One top-level YAML field, retained as source text."""

    key: str
    raw: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Section:
    """A Markdown heading section with stable identity and source provenance."""

    heading: str
    level: int
    identity: str
    occurrence: int
    heading_text: str
    start_line: int
    end_line: int
    start_offset: int
    end_offset: int
    text: str


@dataclass(frozen=True)
class SkillIR:
    """Lossless source representation used by optimization passes."""

    source_path: Path
    source_id: str
    source_text: str
    source_sha256: str
    frontmatter: Tuple[FrontmatterField, ...]
    body: str
    body_start_line: int
    sections: Tuple[Section, ...]

    def field(self, key: str) -> Optional[FrontmatterField]:
        for item in self.frontmatter:
            if item.key == key:
                return item
        return None


@dataclass(frozen=True)
class InvocationPolicy:
    """Canonical invocation behavior independent of harness syntax."""

    allow_model: bool = True
    allow_user: bool = True


@dataclass
class CompiledPackage:
    """Files and metadata produced by one compiler run."""

    skill_name: str
    target: str
    files: Dict[str, str]
    manifest: Dict[str, object]
    metrics: Dict[str, int]
    transformations: List[Dict[str, object]] = field(default_factory=list)
    binary_files: Dict[str, bytes] = field(default_factory=dict)
    executable_files: Tuple[str, ...] = ()

    def file_bytes(self) -> Mapping[str, bytes]:
        """Return every package file in its exact on-disk representation."""

        values = {
            path: content.encode("utf-8") for path, content in self.files.items()
        }
        overlap = set(values).intersection(self.binary_files)
        if overlap:
            raise ValueError(
                "package paths cannot be both text and binary: %s"
                % ", ".join(sorted(overlap))
            )
        values.update(self.binary_files)
        return values
