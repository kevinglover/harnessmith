"""Read-only catalog accounting; no host discovery or model-selection claims."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional

from .contracts import Diagnostic, Remediation, Severity
from .diagnostics import diagnostic_to_dict
from .errors import SkillCompilerError
from .metadata import string_value
from .metrics import estimate_tokens
from .parser import parse_skill


PROFILE_KEYS = {
    "schema_version",
    "profile_id",
    "target",
    "host_version",
    "listing_format",
    "budget_characters",
    "reserved_characters",
    "evidence",
}
LISTING_FORMAT = "json-lines-name-description-path-v1"


def load_catalog_profile(path: Path, target: str) -> Dict[str, object]:
    """Load explicit, versioned operator assumptions, never inferred host limits."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise SkillCompilerError("cannot read catalog profile: %s" % exc) from exc
    if not isinstance(value, dict) or set(value) != PROFILE_KEYS:
        raise SkillCompilerError("catalog profile has missing or unknown fields")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise SkillCompilerError("unsupported catalog profile version")
    for key in ("profile_id", "host_version", "evidence"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise SkillCompilerError(
                "catalog profile %s must be a non-empty string" % key
            )
    if value["target"] != target:
        raise SkillCompilerError("catalog profile target differs from --target")
    if value["listing_format"] != LISTING_FORMAT:
        raise SkillCompilerError("unsupported catalog listing format")
    budget = value["budget_characters"]
    reserved = value["reserved_characters"]
    if budget is not None and (type(budget) is not int or budget < 1):
        raise SkillCompilerError("budget_characters must be null or a positive integer")
    if type(reserved) is not int or reserved < 0:
        raise SkillCompilerError("reserved_characters must be a nonnegative integer")
    return value


def audit_catalog(
    root: Path,
    target: str,
    profile_path: Optional[Path] = None,
) -> Dict[str, object]:
    """Measure the explicit directory recursively in deterministic relative-path order."""
    if target not in ("codex", "claude"):
        raise SkillCompilerError("catalog auditing currently supports codex and claude")
    root = Path(root).resolve()
    if not root.is_dir():
        raise SkillCompilerError("catalog root must be an existing directory")
    profile = (
        load_catalog_profile(profile_path, target)
        if profile_path
        else {
            "schema_version": 1,
            "profile_id": "unbounded-v1",
            "target": target,
            "host_version": "unverified",
            "listing_format": LISTING_FORMAT,
            "budget_characters": None,
            "reserved_characters": 0,
            "evidence": "No measured host budget supplied; synthetic listing only.",
        }
    )
    entries = []
    names = defaultdict(list)
    descriptions = defaultdict(list)
    components = dict(name=0, description=0, path=0, formatting=0)
    listing = ""
    for source in sorted(root.rglob("SKILL.md")):
        # Directory symlinks are not traversed by pathlib.rglob. Reject file links
        # too, so the reported inventory never silently includes external skills.
        if source.is_symlink() or not source.is_file():
            raise SkillCompilerError(
                "catalog SKILL.md must be a regular file: %s" % source
            )
        relative = source.relative_to(root).as_posix()
        ir = parse_skill(source, source_id=relative)
        values = {}
        for key in ("name", "description"):
            field = ir.field(key)
            if field is None:
                raise SkillCompilerError("%s: missing %s" % (relative, key))
            values[key] = string_value(field)
        values["path"] = relative
        line = json.dumps(values, ensure_ascii=False, separators=(",", ":")) + "\n"
        sizes = {key: len(value) for key, value in values.items()}
        # Includes keys, delimiters, quotes, newline, and JSON escape overhead.
        sizes["formatting"] = len(line) - sum(sizes.values())
        for key, size in sizes.items():
            components[key] += size
        entries.append(
            {
                **values,
                "source_sha256": ir.source_sha256,
                "components_characters": sizes,
                "listing_characters": len(line),
            }
        )
        listing += line
        names[values["name"]].append(relative)
        descriptions[" ".join(values["description"].casefold().split())].append(
            relative
        )

    findings = []
    for group, rule, label in (
        (names, "HS401", "Duplicate skill name"),
        (descriptions, "HS403", "Identical normalized discovery description"),
    ):
        for value, paths in sorted(group.items()):
            if len(paths) > 1:
                findings.append(
                    Diagnostic(
                        rule,
                        Severity.WARNING,
                        "%s %r: %s" % (label, value, ", ".join(paths)),
                        "Catalog entries may be hard to distinguish; selection is unmeasured.",
                        remediation=Remediation(
                            "Review names and trigger scopes; no automatic rewrite."
                        ),
                    )
                )
    measured = len(listing)
    reserved = int(profile["reserved_characters"])
    budget = profile["budget_characters"]
    overflow = max(0, measured + reserved - int(budget)) if budget is not None else None
    if overflow:
        findings.append(
            Diagnostic(
                "HS402",
                Severity.WARNING,
                "Synthetic listing plus reserve exceeds the assumed budget by %d characters"
                % overflow,
                "An operator-supplied threshold is advisory, not evidence of host truncation.",
                remediation=Remediation(
                    "Review the catalog and verify host/version assumptions."
                ),
            )
        )
    profile_bytes = json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": 1,
        "evidence_kind": "static-catalog-estimate",
        "target": target,
        "profile": profile,
        "profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "listing_sha256": hashlib.sha256(listing.encode()).hexdigest(),
        "skill_count": len(entries),
        "entries": entries,
        "components_characters": components,
        "listing_characters": measured,
        "listing_token_estimate": estimate_tokens(listing),
        "assumed_total_characters": measured + reserved,
        "overflow_characters": overflow,
        "diagnostics": [diagnostic_to_dict(item) for item in findings],
        "runtime_metrics": None,
    }
