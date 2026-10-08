"""Independent verification and no-write comparison of compiled packages."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .compiler import CompileOptions, compile_skill, verify_package
from .errors import SkillCompilerError
from .metrics import estimate_tokens
from .parser import parse_skill
from .recipe import load_recipe
from .targets import get_target


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


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
            disk = {name: path.read_text(encoding="utf-8") for name, path in safe_files.items() if path.is_file() and not path.is_symlink()}
            disk[".harnessmith.json"] = manifest_path.read_text(encoding="utf-8")
            if expected.files != disk:
                raise SkillCompilerError("deterministic regeneration differs from package contents")
            checks["regeneration"] = "passed"
        except (OSError, UnicodeError, SkillCompilerError) as exc:
            issues.append(VerificationIssue("HS511", str(exc)))
            checks["regeneration"] = "failed"
    else:
        checks["regeneration"] = "not_checked"

    return VerificationReport(package_dir, target, tuple(issues), checks)


def compare_package(files: Mapping[str, str], output: Path) -> PackageDiff:
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
                differs = not path.is_file() or path.read_text(encoding="utf-8") != files[relative]
            except (OSError, UnicodeError) as exc:
                raise SkillCompilerError("cannot compare output file %s: %s" % (relative, exc)) from exc
            if differs:
                modified.append(relative)
    removed = sorted(old_owned - desired)
    return PackageDiff(tuple(added), tuple(modified), tuple(removed))


def _validate_manifest(manifest: Mapping[str, object], issues: List[VerificationIssue]) -> None:
    required = {"schema_version", "compiler", "target", "source", "transformations", "metrics", "files"}
    allowed = required | {"recipe"}
    if manifest.get("schema_version") != 1:
        issues.append(VerificationIssue("HS502", "manifest schema_version must be 1"))
    if set(manifest) - allowed or not required.issubset(manifest):
        issues.append(VerificationIssue("HS502", "manifest has missing or unknown top-level fields"))
    compiler = manifest.get("compiler")
    if not isinstance(compiler, dict) or compiler.get("name") != "harnessmith" or not isinstance(compiler.get("version"), str):
        issues.append(VerificationIssue("HS502", "manifest compiler ownership is invalid"))
    if not isinstance(manifest.get("transformations"), list) or not isinstance(manifest.get("metrics"), dict):
        issues.append(VerificationIssue("HS502", "manifest transformations or metrics are invalid"))
    files = manifest.get("files")
    if not isinstance(files, dict) or not all(isinstance(k, str) and isinstance(v, str) and _SHA256.fullmatch(v) for k, v in files.items()):
        issues.append(VerificationIssue("HS502", "manifest files map is invalid"))
    for key in ("source", "recipe"):
        record = manifest.get(key)
        if key == "recipe" and record is None:
            continue
        if not isinstance(record, dict) or set(record) != {"path", "sha256"} or not isinstance(record.get("path"), str) or not _SHA256.fullmatch(str(record.get("sha256", ""))):
            issues.append(VerificationIssue("HS502", "manifest %s record is invalid" % key))


def _verify_metrics(manifest: Mapping[str, object], source: Path, files: Mapping[str, Path]) -> None:
    metrics = manifest.get("metrics")
    assert isinstance(metrics, dict)
    texts = {name: path.read_text(encoding="utf-8") for name, path in files.items()}
    source_text = source.read_text(encoding="utf-8")
    references = {k: v for k, v in texts.items() if k.startswith("references/")}
    scripts = {k: v for k, v in texts.items() if k.startswith("scripts/")}
    conditional = {
        str(item.get("fallback"))
        for item in manifest.get("transformations", [])
        if isinstance(item, dict) and item.get("type") == "resolve-extension-hooks"
    }
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
    mandatory = "".join(v for k, v in references.items() if k not in conditional)
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
    texts = {name: path.read_text(encoding="utf-8") for name, path in files.items()}
    from .model import CompiledPackage
    package = CompiledPackage("verified", str(manifest.get("target")), texts, dict(manifest), dict(manifest.get("metrics", {})), normalized)
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
    if not relative or "\x00" in relative or "\\" in relative:
        return False
    path = Path(relative)
    return not path.is_absolute() and ".." not in path.parts


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
    if not isinstance(manifest, dict) or not isinstance(manifest.get("compiler"), dict) or manifest["compiler"].get("name") != "harnessmith" or not isinstance(manifest.get("files"), dict):
        raise SkillCompilerError("existing manifest has invalid ownership or files map")
    for relative in manifest["files"]:
        if not isinstance(relative, str) or not _is_safe_relative(relative):
            raise SkillCompilerError("unsafe generated output path: %r" % relative)
    return manifest


def _report(package: Path, target: Optional[str], raw: Sequence[Tuple[str, str]], checks: Mapping[str, str]) -> VerificationReport:
    return VerificationReport(package, target, tuple(VerificationIssue(*item) for item in raw), checks)
