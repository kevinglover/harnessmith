"""Independent verification and no-write comparison of compiled packages."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .compiler import CompileOptions, compile_skill, verify_package
from .errors import SkillCompilerError
from .manifest import (
    is_safe_relative_path,
    manifest_validation_errors,
    require_valid_manifest,
)
from .metrics import estimate_tokens
from .parser import parse_skill
from .recipe import load_recipe
from .targets import get_target


@dataclass(frozen=True)
class VerificationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class VerificationReport:
    package: Path
    target: Optional[str]
    issues: Tuple[VerificationIssue, ...]
    checks: Mapping[str, str]

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> Dict[str, object]:
        return {
            "valid": self.valid,
            "package": self.package.as_posix(),
            "target": self.target,
            "checks": dict(sorted(self.checks.items())),
            "issues": [
                {"code": issue.code, "message": issue.message}
                for issue in self.issues
            ],
        }


@dataclass(frozen=True)
class PackageDiff:
    added: Tuple[str, ...]
    modified: Tuple[str, ...]
    removed: Tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.added or self.modified or self.removed)

    def as_dict(self) -> Dict[str, object]:
        return {
            "changed": self.changed,
            "added": list(self.added),
            "modified": list(self.modified),
            "removed": list(self.removed),
        }


def verify_compiled_package(package_dir: Path) -> VerificationReport:
    """Verify a compiled package without modifying it."""

    package_dir = Path(package_dir)
    issues: List[VerificationIssue] = []
    checks: Dict[str, str] = {}
    manifest_path = package_dir / ".harnessmith.json"
    if not package_dir.is_dir():
        return _report(package_dir, None, [("HS501", "package directory does not exist")], checks)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return _report(package_dir, None, [("HS501", "package manifest is missing or is a symlink")], checks)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return _report(package_dir, None, [("HS501", "cannot read package manifest: %s" % exc)], checks)
    if not isinstance(manifest, dict):
        return _report(package_dir, None, [("HS502", "manifest root must be an object")], checks)

    target = manifest.get("target") if isinstance(manifest.get("target"), str) else None
    _validate_manifest(manifest, issues)
    checks["manifest"] = "passed" if not issues else "failed"
    if issues:
        return VerificationReport(package_dir, target, tuple(issues), checks)
    if target is not None:
        try:
            get_target(target)
        except SkillCompilerError as exc:
            issues.append(VerificationIssue("HS503", str(exc)))
    checks["target"] = "passed" if target is not None and not any(i.code == "HS503" for i in issues) else "failed"

    file_map = manifest.get("files")
    safe_files: Dict[str, Path] = {}
    if isinstance(file_map, dict):
        for relative, expected_hash in sorted(file_map.items()):
            if not isinstance(relative, str) or not _is_safe_relative(relative) or relative == ".harnessmith.json":
                issues.append(VerificationIssue("HS504", "unsafe manifest file path: %r" % relative))
                continue
            path = package_dir / relative
            safe_files[relative] = path
            if _has_symlink_component(package_dir, path):
                issues.append(VerificationIssue("HS504", "owned file must not be a symlink: %s" % relative))
            elif not path.is_file():
                issues.append(VerificationIssue("HS505", "owned file is missing: %s" % relative))
            else:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != expected_hash:
                    issues.append(VerificationIssue("HS506", "owned file hash differs: %s" % relative))
                expected_executable = relative in manifest.get("executables", [])
                actual_executable = bool(path.stat().st_mode & 0o111)
                if expected_executable != actual_executable:
                    issues.append(
                        VerificationIssue(
                            "HS506", "owned file executable mode differs: %s" % relative
                        )
                    )

        expected_paths = set(safe_files) | {".harnessmith.json"}
        for path in sorted(package_dir.rglob("*")):
            if path.is_dir() and not path.is_symlink():
                continue
            relative = path.relative_to(package_dir).as_posix()
            if relative not in expected_paths:
                issues.append(
                    VerificationIssue(
                        "HS505", "unexpected package path: %s" % relative
                    )
                )
    checks["file_hashes"] = "failed" if any(i.code in {"HS504", "HS505", "HS506"} for i in issues) else "passed"

    source = _resolve_recorded_path(manifest.get("source"), package_dir)
    source_hash = _record_hash(manifest.get("source"))
    if source is None:
        checks["source"] = "not_checked"
    elif source.is_symlink() or not source.is_file():
        checks["source"] = "not_checked"
    else:
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != source_hash:
            issues.append(VerificationIssue("HS507", "source hash differs from the manifest: %s" % source))
            checks["source"] = "failed"
        else:
            checks["source"] = "passed"

    recipe = _resolve_recorded_path(manifest.get("recipe"), package_dir)
    recipe_hash = _record_hash(manifest.get("recipe"))
    if recipe is None:
        checks["recipe"] = "not_checked"
    elif recipe.is_symlink() or not recipe.is_file():
        issues.append(VerificationIssue("HS508", "recorded recipe cannot be resolved: %s" % recipe))
        checks["recipe"] = "failed"
    elif hashlib.sha256(recipe.read_bytes()).hexdigest() != recipe_hash:
        issues.append(VerificationIssue("HS508", "recipe hash differs from the manifest: %s" % recipe))
        checks["recipe"] = "failed"
    else:
        checks["recipe"] = "passed"

    if source is not None and checks.get("source") == "passed" and checks.get("file_hashes") == "passed" and safe_files:
        try:
            _verify_metrics(manifest, source, safe_files)
            checks["metrics"] = "passed"
            _verify_invariants(manifest, source, safe_files)
            checks["invariants"] = "passed"
        except SkillCompilerError as exc:
            code = "HS509" if "metric" in str(exc) else "HS510"
            issues.append(VerificationIssue(code, str(exc)))
            checks["metrics" if code == "HS509" else "invariants"] = "failed"
    else:
        checks["metrics"] = "not_checked"
        checks["invariants"] = "not_checked"

    if source is not None and recipe is not None and checks.get("source") == "passed" and checks.get("recipe") == "passed":
        try:
            expected = _regenerate(source, recipe, manifest)
            disk = {
                name: path.read_bytes()
                for name, path in safe_files.items()
                if path.is_file() and not path.is_symlink()
            }
            disk[".harnessmith.json"] = manifest_path.read_bytes()
            if expected.file_bytes() != disk:
                raise SkillCompilerError("deterministic regeneration differs from package contents")
            checks["regeneration"] = "passed"
        except (OSError, UnicodeError, SkillCompilerError) as exc:
            issues.append(VerificationIssue("HS511", str(exc)))
            checks["regeneration"] = "failed"
    else:
        checks["regeneration"] = "not_checked"

    return VerificationReport(package_dir, target, tuple(issues), checks)


def compare_package(
    files: Mapping[str, Union[str, bytes]], output: Path
) -> PackageDiff:
    """Compare desired package contents with compiler-owned output, without writes."""

    output = Path(output)
    desired = set(files)
    old_owned: set[str] = set()
    if output.exists():
        if not output.is_dir() or output.is_symlink():
            raise SkillCompilerError("output exists and is not a safe directory: %s" % output)
        manifest_path = output / ".harnessmith.json"
        entries = list(output.iterdir())
        if entries and not manifest_path.is_file():
            raise SkillCompilerError("refusing to compare non-compiler output directory: %s" % output)
        if manifest_path.is_file():
            manifest = _read_owned_manifest(manifest_path)
            old_owned = set(manifest["files"]) | {".harnessmith.json"}

    added: List[str] = []
    modified: List[str] = []
    for relative in sorted(desired):
        if not _is_safe_relative(relative):
            raise SkillCompilerError("unsafe generated output path: %s" % relative)
        path = output / relative
        if relative not in old_owned or not path.exists():
            added.append(relative)
        elif _has_symlink_component(output, path):
            raise SkillCompilerError("unsafe symlink in generated output path: %s" % relative)
        else:
            try:
                expected = files[relative]
                expected_bytes = (
                    expected.encode("utf-8") if isinstance(expected, str) else expected
                )
                differs = not path.is_file() or path.read_bytes() != expected_bytes
            except OSError as exc:
                raise SkillCompilerError("cannot compare output file %s: %s" % (relative, exc)) from exc
            if differs:
                modified.append(relative)
    removed = sorted(old_owned - desired)
    return PackageDiff(tuple(added), tuple(modified), tuple(removed))


def _validate_manifest(manifest: Mapping[str, object], issues: List[VerificationIssue]) -> None:
    issues.extend(
        VerificationIssue("HS502", message)
        for message in manifest_validation_errors(manifest)
    )


def _verify_metrics(manifest: Mapping[str, object], source: Path, files: Mapping[str, Path]) -> None:
    metrics = manifest.get("metrics")
    assert isinstance(metrics, dict)
    texts = _read_utf8_files(files)
    source_text = source.read_text(encoding="utf-8")
    references = {k: v for k, v in texts.items() if k.startswith("references/")}
    scripts = {k: v for k, v in texts.items() if k.startswith("scripts/")}
    conditional = {
        str(item.get("fallback"))
        for item in manifest.get("transformations", [])
        if isinstance(item, dict) and item.get("type") == "resolve-extension-hooks"
    }
    mandatory_paths = {
        str(item.get("output"))
        for item in manifest.get("transformations", [])
        if isinstance(item, dict)
        and item.get("type") == "extract-section"
        and isinstance(item.get("output"), str)
    } - conditional
    root = texts.get("SKILL.md", "")
    values = {
        "source_skill_chars": len(source_text),
        "source_skill_token_estimate": estimate_tokens(source_text),
        "compiled_root_chars": len(root),
        "compiled_root_token_estimate": estimate_tokens(root),
        "reference_chars": sum(map(len, references.values())),
        "reference_token_estimate": sum(estimate_tokens(v) for v in references.values()),
        "script_chars": sum(map(len, scripts.values())),
        "script_token_estimate": estimate_tokens("".join(scripts.values())),
    }
    mandatory = "".join(v for k, v in references.items() if k in mandatory_paths)
    conditional_text = "".join(v for k, v in references.items() if k in conditional)
    values.update({
        "mandatory_reference_chars": len(mandatory),
        "mandatory_reference_token_estimate": estimate_tokens(mandatory),
        "conditional_reference_chars": len(conditional_text),
        "conditional_reference_token_estimate": estimate_tokens(conditional_text),
        "normal_path_instruction_chars": len(root) + len(mandatory),
        "normal_path_instruction_token_estimate": estimate_tokens(root + mandatory),
        "packaged_instruction_chars": len(root) + sum(map(len, references.values())),
        "packaged_instruction_token_estimate": estimate_tokens(root + "".join(references.values())),
        "root_char_reduction": len(source_text) - len(root),
        "root_reduction_percent": round((1 - len(root) / len(source_text)) * 100) if source_text else 0,
        "normal_path_reduction_percent": round((1 - (len(root) + len(mandatory)) / len(source_text)) * 100) if source_text else 0,
    })
    for key, value in values.items():
        if metrics.get(key) != value:
            raise SkillCompilerError("manifest metric differs from package: %s" % key)


def _verify_invariants(manifest: Mapping[str, object], source: Path, files: Mapping[str, Path]) -> None:
    _verify_preserved_resources(manifest, source, files)
    ir = parse_skill(source)
    transformations = list(manifest.get("transformations", []))
    extracted = tuple(str(item["heading"]) for item in transformations if isinstance(item, dict) and item.get("type") == "extract-section" and isinstance(item.get("heading"), str))
    # Early schema-v1 manifests identified extracted sections by heading only.
    # Enrich a verification-only copy so current invariant checks remain
    # backwards compatible without mutating the package.
    from .transforms import resolve_section
    normalized = []
    for item in transformations:
        if isinstance(item, dict) and item.get("type") == "extract-section" and "section_id" not in item and isinstance(item.get("heading"), str):
            item = dict(item)
            item["section_id"] = resolve_section(ir, item["heading"]).identity
        normalized.append(item)
    texts = _read_utf8_files(files)
    binary = {
        name: path.read_bytes()
        for name, path in files.items()
        if name not in texts
    }
    from .model import CompiledPackage
    package = CompiledPackage(
        skill_name="verified",
        target=str(manifest.get("target")),
        files=texts,
        manifest=dict(manifest),
        metrics=dict(manifest.get("metrics", {})),
        transformations=normalized,
        binary_files=binary,
        executable_files=tuple(manifest.get("executables", [])),
    )
    verify_package(ir, package, extracted)


def _regenerate(source: Path, recipe_path: Path, manifest: Mapping[str, object]):
    recipe = load_recipe(recipe_path)
    target = str(manifest["target"])
    if recipe.target and recipe.target != target:
        raise SkillCompilerError("recipe target conflicts with package target")
    return compile_skill(source, CompileOptions(
        target=target,
        extract_sections=recipe.extract_sections,
        optimize_extension_hooks="spec-kit-extension-hooks" in recipe.optimizations,
        invocation=recipe.invocation,
        source_id=str(manifest["source"]["path"]),  # type: ignore[index]
        max_root_tokens=recipe.max_root_tokens,
        max_normal_path_tokens=recipe.max_normal_path_tokens,
        expected_source_sha256=recipe.source_sha256,
        recipe_id=str(manifest["recipe"]["path"]),  # type: ignore[index]
        recipe_sha256=recipe.sha256,
    ))


def _resolve_recorded_path(record: object, package_dir: Path) -> Optional[Path]:
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        return None
    value = Path(record["path"])
    candidates = [value] if value.is_absolute() else [Path.cwd() / value, package_dir / value, package_dir.parent / value]
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0] if candidates else None)


def _record_hash(record: object) -> Optional[str]:
    return record.get("sha256") if isinstance(record, dict) and isinstance(record.get("sha256"), str) else None


def _is_safe_relative(relative: str) -> bool:
    return is_safe_relative_path(relative)


def _has_symlink_component(root: Path, path: Path) -> bool:
    cursor = path
    while True:
        if cursor.is_symlink():
            return True
        if cursor == root:
            return False
        if root not in cursor.parents:
            return True
        cursor = cursor.parent


def _read_owned_manifest(path: Path) -> Mapping[str, object]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SkillCompilerError("cannot safely read existing compiler manifest: %s" % exc) from exc
    manifest = require_valid_manifest(manifest)
    files = manifest["files"]
    assert isinstance(files, dict)
    for relative in files:
        if not isinstance(relative, str) or not _is_safe_relative(relative):
            raise SkillCompilerError("unsafe generated output path: %r" % relative)
    return manifest


def _read_utf8_files(files: Mapping[str, Path]) -> Dict[str, str]:
    texts: Dict[str, str] = {}
    for name, path in files.items():
        try:
            texts[name] = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
    return texts


def _verify_preserved_resources(
    manifest: Mapping[str, object], source: Path, files: Mapping[str, Path]
) -> None:
    records = [
        item
        for item in manifest.get("transformations", [])
        if isinstance(item, dict) and item.get("type") == "preserve-resource"
    ]
    recorded_paths = [item.get("path") for item in records]
    if any(not isinstance(path, str) or not _is_safe_relative(path) for path in recorded_paths):
        raise SkillCompilerError("preserved resource has an unsafe path")
    if len(recorded_paths) != len(set(recorded_paths)):
        raise SkillCompilerError("preserved resource paths are duplicated")

    source_paths = set()
    for directory_name in ("references", "scripts", "assets"):
        directory = source.parent / directory_name
        if not directory.exists():
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise SkillCompilerError("preserved resource directory is unsafe: %s" % directory)
        for path in directory.rglob("*"):
            relative = path.relative_to(source.parent).as_posix()
            if path.is_symlink():
                raise SkillCompilerError("preserved resource is a symlink: %s" % relative)
            if path.is_dir():
                continue
            if not path.is_file():
                raise SkillCompilerError("preserved resource is not a regular file: %s" % relative)
            source_paths.add(relative)
    if source_paths != set(recorded_paths):
        raise SkillCompilerError("preserved resource inventory differs from the source package")

    executables = set(manifest.get("executables", []))
    for item in records:
        relative = str(item["path"])
        source_path = source.parent / relative
        output_path = files.get(relative)
        expected_hash = item.get("source_sha256")
        if not isinstance(expected_hash, str):
            raise SkillCompilerError("preserved resource hash is invalid: %s" % relative)
        source_bytes = source_path.read_bytes()
        if hashlib.sha256(source_bytes).hexdigest() != expected_hash:
            raise SkillCompilerError("preserved resource hash differs: %s" % relative)
        if output_path is None or output_path.read_bytes() != source_bytes:
            raise SkillCompilerError("preserved resource output differs: %s" % relative)
        expected_executable = item.get("executable")
        if not isinstance(expected_executable, bool):
            raise SkillCompilerError("preserved resource mode is invalid: %s" % relative)
        if expected_executable != (relative in executables):
            raise SkillCompilerError("preserved resource mode differs: %s" % relative)


def _report(package: Path, target: Optional[str], raw: Sequence[Tuple[str, str]], checks: Mapping[str, str]) -> VerificationReport:
    return VerificationReport(package, target, tuple(VerificationIssue(*item) for item in raw), checks)
