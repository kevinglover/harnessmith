"""Offline validation for the checked-in fixture corpus.

This module deliberately has no network access and no compiler dependency. It
validates the versioned fixture contract and confirms that every checked-in
source still has its recorded digest.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Mapping, Tuple

from .contracts import CONTRACT_SCHEMA_VERSION, FixtureRecord
from .targets import TARGET_NAMES


TARGETS = frozenset(TARGET_NAMES)
_FIXTURE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DIAGNOSTIC_ID = re.compile(r"^HS[0-9]+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RECORD_KEYS = frozenset(
    (
        "fixture_id",
        "repository",
        "revision",
        "license",
        "source_path",
        "source_sha256",
        "expected_targets",
        "expected_diagnostics",
    )
)


class FixtureValidationError(ValueError):
    """Raised when corpus metadata or pinned source content is invalid."""


def load_and_validate_manifest(
    manifest_path: Path, repository_root: Path
) -> Tuple[FixtureRecord, ...]:
    """Load *manifest_path* and validate all records and local source hashes."""

    manifest_path = Path(manifest_path)
    repository_root = Path(repository_root).resolve()
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureValidationError("cannot read fixture manifest: %s" % exc) from exc

    if not isinstance(document, dict) or set(document) != {"schema_version", "fixtures"}:
        raise FixtureValidationError("manifest must contain only schema_version and fixtures")
    if (
        not isinstance(document["schema_version"], int)
        or isinstance(document["schema_version"], bool)
        or document["schema_version"] != CONTRACT_SCHEMA_VERSION
    ):
        raise FixtureValidationError("unsupported fixture manifest schema version")
    if not isinstance(document["fixtures"], list):
        raise FixtureValidationError("fixtures must be an array")

    records = tuple(
        _record_from_json(item, repository_root, index)
        for index, item in enumerate(document["fixtures"])
    )
    fixture_ids = [record.fixture_id for record in records]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise FixtureValidationError("fixture_id values must be unique")
    return records


def _record_from_json(
    value: object, repository_root: Path, index: int
) -> FixtureRecord:
    label = "fixtures[%d]" % index
    if not isinstance(value, dict) or set(value) != _RECORD_KEYS:
        raise FixtureValidationError("%s has missing or unknown fields" % label)
    item: Mapping[str, object] = value
    fixture_id = _required_string(item, "fixture_id", label)
    if not _FIXTURE_ID.fullmatch(fixture_id):
        raise FixtureValidationError("%s fixture_id is invalid" % label)

    source_path = _required_string(item, "source_path", label)
    relative = Path(source_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise FixtureValidationError("%s source_path must be repository-relative" % label)
    resolved = (repository_root / relative).resolve()
    try:
        resolved.relative_to(repository_root)
    except ValueError as exc:
        raise FixtureValidationError("%s source_path escapes the repository" % label) from exc
    if not resolved.is_file():
        raise FixtureValidationError("%s source file does not exist" % label)

    source_sha256 = _required_string(item, "source_sha256", label)
    if not _SHA256.fullmatch(source_sha256):
        raise FixtureValidationError("%s source_sha256 is invalid" % label)
    actual_sha256 = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if actual_sha256 != source_sha256:
        raise FixtureValidationError(
            "%s source hash mismatch: expected %s, got %s"
            % (label, source_sha256, actual_sha256)
        )

    expected_targets = _unique_string_array(item, "expected_targets", label)
    if not set(expected_targets).issubset(TARGETS):
        raise FixtureValidationError("%s contains an unknown expected target" % label)
    expected_diagnostics = _unique_string_array(
        item, "expected_diagnostics", label
    )
    if any(not _DIAGNOSTIC_ID.fullmatch(value) for value in expected_diagnostics):
        raise FixtureValidationError("%s contains an invalid diagnostic ID" % label)

    return FixtureRecord(
        fixture_id=fixture_id,
        repository=_required_string(item, "repository", label),
        revision=_required_string(item, "revision", label),
        license=_required_string(item, "license", label),
        source_path=source_path,
        source_sha256=source_sha256,
        expected_targets=expected_targets,
        expected_diagnostics=expected_diagnostics,
    )


def _required_string(item: Mapping[str, object], key: str, label: str) -> str:
    value = item[key]
    if not isinstance(value, str) or not value:
        raise FixtureValidationError("%s.%s must be a non-empty string" % (label, key))
    return value


def _unique_string_array(
    item: Mapping[str, object], key: str, label: str
) -> Tuple[str, ...]:
    value = item[key]
    if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
        raise FixtureValidationError("%s.%s must be an array of strings" % (label, key))
    if len(value) != len(set(value)):
        raise FixtureValidationError("%s.%s values must be unique" % (label, key))
    return tuple(value)
