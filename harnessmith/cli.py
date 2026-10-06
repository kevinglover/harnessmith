"""Command-line interface for Harnessmith."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .compiler import CompileOptions, compile_skill, write_package
from .errors import SkillCompilerError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harnessmith",
        description="Compile one canonical Agent Skill into a harness-aware package.",
    )
    parser.add_argument("source", type=Path, help="Path to the canonical SKILL.md")
    parser.add_argument(
        "--target",
        required=True,
        choices=("generic", "cursor", "claude", "codex"),
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Exact output skill directory"
    )
    parser.add_argument(
        "--extract-section",
        action="append",
        default=[],
        help="Exact ATX heading text to move losslessly into references/ (repeatable)",
    )
    parser.add_argument(
        "--optimize-extension-hooks",
        action="store_true",
        help=(
            "Replace reviewed Spec Kit hook contracts with a read-only resolver "
            "and an exact fallback reference"
        ),
    )
    parser.add_argument(
        "--invocation",
        choices=("source", "explicit", "automatic"),
        default="source",
        help="Preserve source invocation semantics or apply an explicit operator policy",
    )
    parser.add_argument(
        "--source-id",
        help="Stable provenance path recorded instead of the source argument",
    )
    parser.add_argument(
        "--max-root-tokens",
        type=int,
        help="Fail when the estimated generated root exceeds this budget",
    )
    parser.add_argument(
        "--max-normal-path-tokens",
        type=int,
        help="Fail when root plus mandatory references exceeds this budget",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the compile report as JSON"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        package = compile_skill(
            args.source,
            CompileOptions(
                target=args.target,
                extract_sections=tuple(args.extract_section),
                optimize_extension_hooks=args.optimize_extension_hooks,
                invocation=args.invocation,
                source_id=args.source_id or args.source.as_posix(),
                max_root_tokens=args.max_root_tokens,
                max_normal_path_tokens=args.max_normal_path_tokens,
            ),
        )
        write_package(package, args.output)
    except (OSError, SkillCompilerError) as exc:
        print("harnessmith: error: %s" % exc, file=sys.stderr)
        return 2

    report = {
        "skill": package.skill_name,
        "target": package.target,
        "output": args.output.as_posix(),
        "metrics": package.metrics,
        "files": sorted(package.files),
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        normal_reduction = package.metrics["normal_path_reduction_percent"]
        normal_label = (
            "%d%% smaller" % normal_reduction
            if normal_reduction >= 0
            else "%d%% larger" % abs(normal_reduction)
        )
        print(
            "Compiled %s for %s: %d%% smaller root; normal static path %s "
            "(%d -> %d estimated tokens)"
            % (
                package.skill_name,
                package.target,
                package.metrics["root_reduction_percent"],
                normal_label,
                package.metrics["source_skill_token_estimate"],
                package.metrics["normal_path_instruction_token_estimate"],
            )
        )
        print("Output: %s" % args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
