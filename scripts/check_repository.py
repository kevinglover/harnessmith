#!/usr/bin/env python3
"""Dependency-light repository checks used by local development and CI."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from dataclasses import asdict
from typing import Iterable, List
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")


def _documentation_files() -> Iterable[Path]:
    for name in (
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
    ):
        path = ROOT / name
        if path.exists():
            yield path
    yield from (ROOT / "docs").rglob("*.md")


def check_schemas() -> List[str]:
    try:
        from jsonschema.validators import validator_for
    except ImportError:
        return ["jsonschema is required for the schema check; install .[dev]"]

    errors: List[str] = []
    validators = {}
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validator_class = validator_for(document)
            validator_class.check_schema(document)
            validators[path.name] = validator_class(document)
        except Exception as exc:  # jsonschema exposes several validation errors
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    instances = {
        "fixture-manifest.schema.json": [ROOT / "fixtures" / "manifest.json"],
        "package-manifest.schema.json": sorted(
            (ROOT / "examples" / "compiled").rglob(".harnessmith.json")
        ),
        "recipe.schema.json": sorted((ROOT / "recipes").glob("*.json")),
    }
    for schema_name, paths in instances.items():
        validator = validators.get(schema_name)
        if validator is None:
            continue
        for path in paths:
            try:
                instance = json.loads(path.read_text(encoding="utf-8"))
                for error in sorted(
                    validator.iter_errors(instance),
                    key=lambda item: tuple(str(part) for part in item.absolute_path),
                ):
                    location = ".".join(str(item) for item in error.path) or "$"
                    errors.append(
                        f"{path.relative_to(ROOT)}:{location}: {error.message}"
                    )
            except (OSError, ValueError) as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")
    # Scenarios have independently versioned contracts; reject unknown versions.
    for path in sorted((ROOT / "evaluations/scenarios").glob("*.json")):
        try:
            instance = json.loads(path.read_text(encoding="utf-8"))
            version = instance.get("schema_version")
            name = {
                1: "evaluation-scenario.schema.json",
                2: "evaluation-scenario-v2.schema.json",
            }.get(version)
            if name is None or type(version) is not int:
                errors.append(f"{path.relative_to(ROOT)}: unsupported scenario version")
                continue
            validator = validators.get(name)
            if validator is None:
                errors.append(f"{path.relative_to(ROOT)}: missing or invalid schema {name}")
                continue
            for error in validator.iter_errors(instance):
                errors.append(f"{path.relative_to(ROOT)}: {error.message}")
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    # Check emitted capabilities as well as schemas; v2 must not masquerade as v1.
    sys.path.insert(0, str(ROOT))
    from harnessmith.targets import capability_documents

    capability_validator = validators.get("adapter-capabilities-v2.schema.json")
    if capability_validator is not None:
        for target, contract in capability_documents().items():
            document = json.loads(json.dumps(asdict(contract)))
            legacy_validator = validators.get("adapter-capabilities.schema.json")
            if legacy_validator is not None and legacy_validator.is_valid(document):
                errors.append(f"capabilities/{target}: v1 accepted a v2 document")
            for error in capability_validator.iter_errors(document):
                errors.append(f"capabilities/{target}: {error.message}")
    return errors


def check_docs() -> List[str]:
    errors: List[str] = []
    for path in sorted(_documentation_files()):
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            parsed = urlsplit(target)
            if not target or target.startswith("#") or parsed.scheme or parsed.netloc:
                continue
            local = (path.parent / unquote(parsed.path)).resolve()
            try:
                local.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(
                    f"{path.relative_to(ROOT)}: link escapes repository: {target}"
                )
                continue
            if not local.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: missing link target: {target}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "check", choices=("schemas", "docs", "all"), nargs="?", default="all"
    )
    args = parser.parse_args()
    errors: List[str] = []
    if args.check in ("schemas", "all"):
        errors.extend(check_schemas())
    if args.check in ("docs", "all"):
        errors.extend(check_docs())
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Repository {args.check} check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
