"""Command-line interface for Harnessmith."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .audit import audit_skill
from .compiler import CompileOptions, compile_skill, write_package
from .contracts import Diagnostic, Remediation, Severity, SourceSpan
from .diagnostics import (
    diagnostics_fail_threshold,
    render_diagnostics_json,
    render_diagnostics_sarif,
    render_diagnostics_text,
)
from .errors import SkillCompilerError
from .recipe import load_recipe
from .targets import TARGET_NAMES
from .verification import compare_package, verify_compiled_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harnessmith",
        description="Audit or compile an Agent Skill for a target harness.",
        epilog=(
            "To verify an existing compiled package, run: "
            "harnessmith verify PACKAGE [--json]"
        ),
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument(
        "source", type=Path, help="Path to a SKILL.md or its containing directory"
    )
    parser.add_argument(
        "--target",
        choices=TARGET_NAMES,
        help="Target harness; may instead be supplied by --recipe",
    )
    parser.add_argument(
        "--output", type=Path, help="Exact output skill directory (compile mode only)"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Analyze context pressure and review candidates without writing files",
    )
    parser.add_argument(
        "--recipe",
        type=Path,
        help="Versioned JSON recipe with reviewed transformations and source hash",
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
            "Apply the specialized Spec Kit extension-hook optimization; equivalent "
            "to the recipe optimization spec-kit-extension-hooks"
        ),
    )
    parser.add_argument(
        "--invocation",
        choices=("source", "explicit", "automatic"),
        default=None,
        help=(
            "Preserve source invocation semantics or apply an explicit operator policy"
        ),
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
    parser.add_argument(
        "--format",
        choices=("text", "json", "sarif"),
        dest="audit_format",
        help="Diagnostic output format (audit mode only)",
    )
    parser.add_argument(
        "--fail-on",
        choices=("note", "warning", "error"),
        help=(
            "Return exit code 1 when an audit diagnostic meets or exceeds this "
            "severity"
        ),
    )
    preview = parser.add_mutually_exclusive_group()
    preview.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile and validate without writing the output directory",
    )
    preview.add_argument(
        "--diff",
        action="store_true",
        help="Report output changes without writing the output directory",
    )
    return parser


def build_verify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harnessmith verify",
        description="Independently verify a compiled Harnessmith package.",
    )
    parser.add_argument("package", type=Path, help="Compiled skill package directory")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    if argv and argv[0] == "verify":
        return _verify_main(argv[1:])
    args = build_parser().parse_args(argv)
    try:
        recipe = load_recipe(args.recipe) if args.recipe else None
        target = args.target or (recipe.target if recipe else None)
        if target is None:
            raise SkillCompilerError("--target is required unless supplied by --recipe")
        if args.target and recipe and recipe.target and args.target != recipe.target:
            raise SkillCompilerError(
                "--target %s conflicts with recipe target %s"
                % (args.target, recipe.target)
            )

        if args.audit:
            if args.json and args.audit_format not in (None, "json"):
                raise SkillCompilerError(
                    "--json conflicts with --format %s" % args.audit_format
                )
            report = audit_skill(args.source, target, source_id=args.source_id)
            if (
                recipe
                and recipe.source_sha256
                and report["source"]["sha256"] != recipe.source_sha256
            ):
                report["warnings"].append(
                    "source hash differs from the selected recipe; "
                    "re-audit before compiling"
                )
            diagnostics = _diagnostics_from_report(report)
            # --json predates structured diagnostics and intentionally retains
            # the complete audit report for backwards compatibility.
            if args.json:
                _print_audit(report, True)
            else:
                _print_audit(report, False, args.audit_format or "text", diagnostics)
            if args.fail_on and diagnostics_fail_threshold(diagnostics, args.fail_on):
                return 1
            return 0

        if args.audit_format is not None or args.fail_on is not None:
            raise SkillCompilerError("--format and --fail-on require --audit")

        if args.output is None:
            raise SkillCompilerError("--output is required when compiling")
        extract_sections = (
            tuple(args.extract_section)
            if args.extract_section
            else (recipe.extract_sections if recipe else ())
        )
        optimizations = recipe.optimizations if recipe else ()
        package = compile_skill(
            args.source,
            CompileOptions(
                target=target,
                extract_sections=extract_sections,
                optimize_extension_hooks=(
                    args.optimize_extension_hooks
                    or "spec-kit-extension-hooks" in optimizations
                ),
                invocation=args.invocation
                or (recipe.invocation if recipe else "source"),
                source_id=args.source_id,
                max_root_tokens=(
                    args.max_root_tokens
                    if args.max_root_tokens is not None
                    else (recipe.max_root_tokens if recipe else None)
                ),
                max_normal_path_tokens=(
                    args.max_normal_path_tokens
                    if args.max_normal_path_tokens is not None
                    else (recipe.max_normal_path_tokens if recipe else None)
                ),
                expected_source_sha256=recipe.source_sha256 if recipe else None,
                recipe_id=recipe.path.as_posix() if recipe else None,
                recipe_sha256=recipe.sha256 if recipe else None,
            ),
        )
        diff = compare_package(package.files, args.output)
        if not args.dry_run and not args.diff:
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
    if args.dry_run or args.diff:
        report["written"] = False
        report["diff"] = diff.as_dict()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        normal_reduction = package.metrics["normal_path_reduction_percent"]
        normal_label = (
            "%d%% smaller" % normal_reduction
            if normal_reduction >= 0
            else "%d%% larger" % abs(normal_reduction)
        )
        verb = "Previewed" if args.dry_run or args.diff else "Compiled"
        print(
            "%s %s for %s: %d%% smaller root; normal static path %s "
            "(%d -> %d estimated tokens)"
            % (
                verb,
                package.skill_name,
                package.target,
                package.metrics["root_reduction_percent"],
                normal_label,
                package.metrics["source_skill_token_estimate"],
                package.metrics["normal_path_instruction_token_estimate"],
            )
        )
        if args.diff:
            print("Added: %s" % (", ".join(diff.added) or "none"))
            print("Modified: %s" % (", ".join(diff.modified) or "none"))
            print("Removed: %s" % (", ".join(diff.removed) or "none"))
        print("Output: %s%s" % (args.output, " (not written)" if args.dry_run or args.diff else ""))
    return 0


def _verify_main(argv: Sequence[str]) -> int:
    args = build_verify_parser().parse_args(argv)
    report = verify_compiled_package(args.package)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        if report.valid:
            print("Verified %s: package is valid" % report.package)
        else:
            print("Verification failed for %s" % report.package)
            for issue in report.issues:
                print("- %s: %s" % (issue.code, issue.message))
        for name, status in sorted(report.checks.items()):
            print("%s: %s" % (name.replace("_", " ").title(), status))
    return 0 if report.valid else 1


def _print_audit(
    report: object,
    as_json: bool,
    output_format: str = "text",
    diagnostics: Sequence[Diagnostic] = (),
) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    if output_format == "json":
        print(render_diagnostics_json(diagnostics))
        return
    if output_format == "sarif":
        print(render_diagnostics_sarif(diagnostics, __version__))
        return
    assert isinstance(report, dict)
    metrics = report["metrics"]
    resources = report["bundled_resources"]
    print(
        "Audited %s for %s: %d estimated tokens, %d review candidate(s)"
        % (
            report["skill"],
            report["target"],
            metrics["source_token_estimate"],
            metrics["review_candidate_count"],
        )
    )
    print(
        "Resources: %d references, %d scripts, %d assets"
        % (
            resources["references"]["files"],
            resources["scripts"]["files"],
            resources["assets"]["files"],
        )
    )
    for candidate in report["review_candidates"]:
        print(
            "- %s (%d tokens): %s"
            % (
                candidate["heading"],
                candidate["token_estimate"],
                "; ".join(candidate["reasons"]),
            )
        )
    for warning in report["warnings"]:
        print("Warning: %s" % warning)
    rendered = render_diagnostics_text(diagnostics)
    if rendered:
        print("Diagnostics:")
        print(rendered)
    print("No files written.")


def _diagnostics_from_report(report: object) -> list[Diagnostic]:
    """Restore public diagnostic values serialized by ``audit_skill``."""

    assert isinstance(report, dict)
    diagnostics: list[Diagnostic] = []
    for value in report.get("diagnostics", []):
        assert isinstance(value, dict)
        source_value = value.get("source_span")
        source_span = None
        if isinstance(source_value, dict):
            source_span = SourceSpan(
                path=str(source_value["path"]),
                start_line=int(source_value["start_line"]),
                end_line=int(source_value["end_line"]),
                start_column=(
                    int(source_value["start_column"])
                    if "start_column" in source_value
                    else None
                ),
                end_column=(
                    int(source_value["end_column"])
                    if "end_column" in source_value
                    else None
                ),
            )
        remediation_value = value.get("remediation")
        remediation = None
        if isinstance(remediation_value, dict):
            recipe_fragment = remediation_value.get("recipe_fragment")
            remediation = Remediation(
                summary=str(remediation_value["summary"]),
                recipe_fragment=(
                    recipe_fragment if isinstance(recipe_fragment, dict) else None
                ),
                requires_review=bool(remediation_value["requires_review"]),
            )
        estimated_savings = value.get("estimated_savings_tokens")
        diagnostics.append(
            Diagnostic(
                rule_id=str(value["rule_id"]),
                severity=Severity(str(value["severity"])),
                message=str(value["message"]),
                rationale=str(value["rationale"]),
                source_span=source_span,
                estimated_savings_tokens=(
                    int(estimated_savings) if estimated_savings is not None else None
                ),
                remediation=remediation,
                schema_version=int(value.get("schema_version", 1)),
            )
        )
    return diagnostics


if __name__ == "__main__":
    raise SystemExit(main())
