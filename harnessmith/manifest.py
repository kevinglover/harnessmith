"""Strict validation shared by package verification and output ownership checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Mapping

from .errors import SkillCompilerError


SHA256 = re.compile(r"^[0-9a-f]{64}$")
METRIC_KEYS = frozenset(
    (
        "source_skill_chars",
        "source_skill_token_estimate",
        "compiled_root_chars",
        "compiled_root_token_estimate",
        "reference_chars",
        "reference_token_estimate",
        "mandatory_reference_chars",
        "mandatory_reference_token_estimate",
        "conditional_reference_chars",
        "conditional_reference_token_estimate",
        "script_chars",
        "script_token_estimate",
        "normal_path_instruction_chars",
        "normal_path_instruction_token_estimate",
        "normal_path_reduction_percent",
        "packaged_instruction_chars",
        "packaged_instruction_token_estimate",
        "root_char_reduction",
        "root_reduction_percent",
    )
)
TRANSFORMATION_TYPES = frozenset(
    (
        "extract-section",
        "frontmatter-filter",
        "invocation-adapter",
        "invocation-policy-override",
        "preserve-resource",
        "resolve-extension-hooks",
    )
)


def manifest_validation_errors(manifest: object) -> List[str]:
    """Return structural errors without following any recorded paths."""

    if not isinstance(manifest, dict):
        return ["manifest root must be an object"]
    required = {
        "schema_version",
        "compiler",
        "target",
        "source",
        "transformations",
        "metrics",
        "files",
    }
    allowed = required | {"recipe", "executables"}
    errors: List[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    if set(manifest) - allowed or not required.issubset(manifest):
        errors.append("manifest has missing or unknown top-level fields")

    compiler = manifest.get("compiler")
    if (
        not isinstance(compiler, dict)
        or set(compiler) != {"name", "version"}
        or compiler.get("name") != "harnessmith"
        or not _nonempty_string(compiler.get("version"))
    ):
        errors.append("manifest compiler ownership is invalid")

    if not isinstance(manifest.get("target"), str):
        errors.append("manifest target must be a string")

    for key in ("source", "recipe"):
        record = manifest.get(key)
        if key == "recipe" and record is None:
            continue
        if not _valid_record(record):
            errors.append("manifest %s record is invalid" % key)

    transformations = manifest.get("transformations")
    if not isinstance(transformations, list):
        errors.append("manifest transformations must be an array")
    else:
        for index, item in enumerate(transformations):
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("type"), str)
                or item.get("type") not in TRANSFORMATION_TYPES
                or not _valid_transformation(item)
            ):
                errors.append(
                    "manifest transformation %d is invalid" % index
                )

    metrics = manifest.get("metrics")
    if (
        not isinstance(metrics, dict)
        or set(metrics) != METRIC_KEYS
        or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in metrics.values()
        )
    ):
        errors.append("manifest metrics are invalid")

    files = manifest.get("files")
    if (
        not isinstance(files, dict)
        or not files
        or any(
            not isinstance(path, str)
            or not isinstance(digest, str)
            or not SHA256.fullmatch(digest)
            for path, digest in files.items()
        )
    ):
        errors.append("manifest files map is invalid")

    executables = manifest.get("executables", [])
    if (
        not isinstance(executables, list)
        or any(not isinstance(path, str) for path in executables)
        or len(executables) != len(set(executables))
        or (isinstance(files, dict) and any(path not in files for path in executables))
    ):
        errors.append("manifest executables list is invalid")
    return errors


def require_valid_manifest(manifest: object) -> Mapping[str, object]:
    """Return a valid manifest or raise the compiler's public error type."""

    errors = manifest_validation_errors(manifest)
    if errors:
        raise SkillCompilerError(
            "invalid Harnessmith manifest: %s" % "; ".join(errors)
        )
    assert isinstance(manifest, dict)
    return manifest


def is_safe_relative_path(relative: str) -> bool:
    if not relative or "\x00" in relative or "\\" in relative:
        return False
    path = Path(relative)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() != "."
    )


def _valid_record(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"path", "sha256"}
        and _nonempty_string(value.get("path"))
        and "\x00" not in value["path"]
        and isinstance(value.get("sha256"), str)
        and bool(SHA256.fullmatch(value["sha256"]))
    )


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _valid_transformation(item: Mapping[str, object]) -> bool:
    kind = item.get("type")
    if kind == "frontmatter-filter":
        return (
            set(item) == {"type", "dropped", "reason"}
            and _string_list(item.get("dropped"))
            and _nonempty_string(item.get("reason"))
        )
    if kind == "invocation-adapter":
        return (
            set(item) == {"type", "source", "output"}
            and _nonempty_string(item.get("source"))
            and _nonempty_string(item.get("output"))
        )
    if kind == "invocation-policy-override":
        return (
            set(item) == {"type", "source", "output"}
            and _valid_policy(item.get("source"))
            and _valid_policy(item.get("output"))
        )
    if kind == "extract-section":
        return (
            set(item) in (
                {"type", "heading", "source_lines", "source_sha256", "output"},
                {
                    "type",
                    "heading",
                    "section_id",
                    "source_lines",
                    "source_sha256",
                    "output",
                },
            )
            and _nonempty_string(item.get("heading"))
            and (
                "section_id" not in item
                or _nonempty_string(item.get("section_id"))
            )
            and _valid_lines(item.get("source_lines"))
            and _valid_sha256(item.get("source_sha256"))
            and _safe_output(item.get("output"))
        )
    if kind == "preserve-resource":
        return (
            set(item)
            == {"type", "path", "content", "source_sha256", "executable"}
            and _safe_output(item.get("path"))
            and item.get("content") in ("text", "binary")
            and _valid_sha256(item.get("source_sha256"))
            and isinstance(item.get("executable"), bool)
        )
    if kind == "resolve-extension-hooks":
        return (
            set(item)
            == {
                "type",
                "phase",
                "event",
                "source_heading",
                "source_lines",
                "source_sha256",
                "replacement_sha256",
                "output",
                "fallback",
                "script",
            }
            and item.get("phase") in ("before", "after")
            and _nonempty_string(item.get("event"))
            and _nonempty_string(item.get("source_heading"))
            and _valid_lines(item.get("source_lines"))
            and _valid_sha256(item.get("source_sha256"))
            and _valid_sha256(item.get("replacement_sha256"))
            and _safe_output(item.get("output"))
            and _safe_output(item.get("fallback"))
            and _safe_output(item.get("script"))
        )
    return False


def _valid_policy(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"allow_model", "allow_user"}
        and all(isinstance(item, bool) for item in value.values())
    )


def _valid_lines(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        and value[0] >= 1
        and value[1] >= value[0]
    )


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def _safe_output(value: object) -> bool:
    return isinstance(value, str) and is_safe_relative_path(value)


def _string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(_nonempty_string(item) for item in value)
        and len(value) == len(set(value))
    )
