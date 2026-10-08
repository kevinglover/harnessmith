#!/usr/bin/env python3
"""Dependency-light repository checks used by local development and CI."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
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
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validator_for(document).check_schema(document)
        except Exception as exc:  # jsonschema exposes several validation errors
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
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
                errors.append(f"{path.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not local.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing link target: {target}")
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
