"""Strict, versioned optimization recipes for reproducible compilation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from .errors import SkillCompilerError


TARGETS = ("generic", "cursor", "claude", "codex")
INVOCATION_POLICIES = ("source", "explicit", "automatic")
OPTIMIZATIONS = ("spec-kit-extension-hooks",)
_TOP_LEVEL_KEYS = {
    "schema_version",
    "target",
    "source_sha256",
    "invocation",
    "extract_sections",
    "optimizations",
    "budgets",
}
_BUDGET_KEYS = {"root_tokens", "normal_path_tokens"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Recipe:
    """Validated compiler choices that can be reviewed and versioned."""

    path: Path
    sha256: str
    target: Optional[str]
    source_sha256: Optional[str]
    invocation: str
    extract_sections: Tuple[str, ...]
    optimizations: Tuple[str, ...]
    max_root_tokens: Optional[int]
    max_normal_path_tokens: Optional[int]


def load_recipe(path: Path) -> Recipe:
    """Load a recipe and reject ambiguous or unknown configuration."""

    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise SkillCompilerError("cannot read recipe '%s': %s" % (path, exc)) from exc
    if not isinstance(data, dict):
        raise SkillCompilerError("recipe root must be a JSON object")

    unknown = sorted(set(data) - _TOP_LEVEL_KEYS)
    if unknown:
        raise SkillCompilerError("recipe has unknown keys: %s" % ", ".join(unknown))
    if data.get("schema_version") != 1:
        raise SkillCompilerError("recipe schema_version must be 1")

    target = data.get("target")
    if target is not None and target not in TARGETS:
        raise SkillCompilerError(
            "recipe target must be one of: %s" % ", ".join(TARGETS)
        )

    invocation = data.get("invocation", "source")
    if invocation not in INVOCATION_POLICIES:
        raise SkillCompilerError(
            "recipe invocation must be one of: %s"
            % ", ".join(INVOCATION_POLICIES)
        )

    source_sha256 = data.get("source_sha256")
    if source_sha256 is not None and (
        not isinstance(source_sha256, str) or not _SHA256.fullmatch(source_sha256)
    ):
        raise SkillCompilerError("recipe source_sha256 must be 64 lowercase hex digits")

    extract_sections = _string_tuple(data, "extract_sections")
    if len(set(extract_sections)) != len(extract_sections):
        raise SkillCompilerError("recipe extract_sections contains duplicates")

    optimizations = _string_tuple(data, "optimizations")
    unknown_optimizations = sorted(set(optimizations) - set(OPTIMIZATIONS))
    if unknown_optimizations:
        raise SkillCompilerError(
            "recipe has unknown optimizations: %s"
            % ", ".join(unknown_optimizations)
        )
    if len(set(optimizations)) != len(optimizations):
        raise SkillCompilerError("recipe optimizations contains duplicates")

    budgets = data.get("budgets", {})
    if not isinstance(budgets, dict):
        raise SkillCompilerError("recipe budgets must be a JSON object")
    unknown_budgets = sorted(set(budgets) - _BUDGET_KEYS)
    if unknown_budgets:
        raise SkillCompilerError(
            "recipe has unknown budget keys: %s" % ", ".join(unknown_budgets)
        )
    max_root_tokens = _positive_integer(budgets, "root_tokens")
    max_normal_path_tokens = _positive_integer(budgets, "normal_path_tokens")

    return Recipe(
        path=path,
        sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        target=target,
        source_sha256=source_sha256,
        invocation=invocation,
        extract_sections=extract_sections,
        optimizations=optimizations,
        max_root_tokens=max_root_tokens,
        max_normal_path_tokens=max_normal_path_tokens,
    )


def _string_tuple(data: Dict[str, object], key: str) -> Tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise SkillCompilerError(
            "recipe %s must be an array of non-empty strings" % key
        )
    return tuple(value)


def _positive_integer(data: Dict[str, object], key: str) -> Optional[int]:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SkillCompilerError("recipe budget %s must be a positive integer" % key)
    return value
