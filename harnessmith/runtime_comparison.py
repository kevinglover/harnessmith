"""Three-way runtime comparison with frozen scenarios and rotated strategy order."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from types import MappingProxyType
from uuid import uuid4

from . import __version__
from .codex_runtime import CONFIG, INSTRUMENTATION, CodexEvaluator, CodexRuntimeError
from .compiler import CompileOptions, compile_skill
from .errors import SkillCompilerError
from .evaluation import evaluate_scenario, load_scenario
from .evaluation_turns import check_turns, parse_trace, TurnTrace
from .fixture_corpus import load_and_validate_manifest
from .recipe import load_recipe
from .router_experiment import load_router, quality_checks
from .runtime_evidence import (
    RuntimeEnvironment,
    RuntimeRequest,
    RuntimeSample,
    RuntimeTurnInput,
    _digest,
    _file_hashes,
)


STRATEGIES = ("canonical", "mandatory", "conditional")


def prepare_comparison(scenario, recipe, repository_root, router_package=None):
    root = Path(repository_root).resolve()
    if scenario.schema_version != 2 or not scenario.turns:
        raise ValueError("comparison requires a version-2 scenario")
    offline = evaluate_scenario(scenario, repository_root=root)
    if not offline.passed:
        raise ValueError("offline scenario contract failed")
    if (
        not recipe.conditional_sections
        or recipe.optimizations
        or recipe.invocation != "source"
    ):
        raise ValueError(
            "comparison requires conditional sections, source invocation and no other optimizations"
        )
    if (
        recipe.target != scenario.target
        or recipe.extract_sections != scenario.extract_sections
    ):
        raise ValueError(
            "recipe target and extraction selectors must match the frozen scenario"
        )
    records = load_and_validate_manifest(root / "fixtures/manifest.json", root)
    record = next(r for r in records if r.fixture_id == scenario.fixture_id)
    if recipe.source_sha256 != record.source_sha256:
        raise ValueError("recipe and scenario must pin the same source")
    source = root / record.source_path
    packages, modes, metrics = {}, {}, {}
    canonical, executable = {}, []
    for path in sorted(source.parent.rglob("*")):
        if path.is_symlink():
            raise ValueError("runtime source package cannot contain symlinks")
        if path.is_file():
            relative = path.relative_to(source.parent).as_posix()
            canonical[relative] = path.read_bytes()
            if path.stat().st_mode & 0o111:
                executable.append(relative)
    if hashlib.sha256(canonical["SKILL.md"]).hexdigest() != record.source_sha256:
        raise ValueError("source changed during comparison preparation")
    packages["canonical"], modes["canonical"] = canonical, tuple(executable)
    for strategy in STRATEGIES[1:]:
        conditional = strategy == "conditional"
        package = compile_skill(
            source,
            CompileOptions(
                target=scenario.target,
                extract_sections=scenario.extract_sections,
                conditional_sections=recipe.conditional_sections if conditional else (),
                source_id=record.source_path,
                expected_source_sha256=record.source_sha256,
                recipe_id=str(recipe.path.resolve()) if conditional else None,
                recipe_sha256=recipe.sha256 if conditional else None,
                max_root_tokens=recipe.max_root_tokens if conditional else None,
                max_normal_path_tokens=recipe.max_normal_path_tokens
                if conditional
                else None,
            ),
        )
        packages[strategy] = dict(package.file_bytes())
        modes[strategy] = package.executable_files
        metrics[strategy] = dict(package.metrics)
    provenance = {
        "compiler_version": __version__,
        "scenario_id": scenario.scenario_id,
        "scenario_sha256": _digest(asdict(scenario)),
        "source_sha256": record.source_sha256,
        "recipe_sha256": recipe.sha256,
        "packages": {
            s: {"files": _file_hashes(packages[s]), "executable_files": modes[s]}
            for s in STRATEGIES
        },
        "static_metrics": metrics,
        "conditional_policies": {
            p.section: p.policy() for p in recipe.conditional_sections
        },
    }
    if router_package is not None:
        quality_checks(
            scenario.scenario_id, ""
        )  # reject unsupported rubrics before calls
        files, review = load_router(router_package, canonical["SKILL.md"])
        packages["router"], modes["router"] = files, ()
        provenance["packages"]["router"] = {
            "files": _file_hashes(files),
            "executable_files": (),
        }
        provenance["router_review"] = review
        provenance["static_metrics"]["router"] = {
            "compiled_root_chars": len(files["SKILL.md"].decode()),
            "compiled_root_token_estimate": (len(files["SKILL.md"].decode()) + 3) // 4,
        }
    return packages, modes, provenance


def run_strategy_comparison(
    scenario,
    evaluator,
    *,
    recipe,
    repository_root,
    environment,
    samples=3,
    enabled=False,
    evidence_kind="runtime",
    router_package=None,
    expected_provenance=None,
):
    if enabled is not True:
        raise RuntimeError("runtime comparison is disabled; pass enabled=True")
    strategies = STRATEGIES + (("router",) if router_package is not None else ())
    if type(samples) is not int or samples < len(strategies):
        raise ValueError("enough samples are needed to rotate all strategy positions")
    if evidence_kind not in ("runtime", "mock"):
        raise ValueError("unknown evidence kind")
    if not isinstance(environment, RuntimeEnvironment) or any(
        not isinstance(v, str) or not v.strip() for v in asdict(environment).values()
    ):
        raise ValueError("runtime environment identifiers must be non-empty strings")
    packages, modes, provenance = prepare_comparison(
        scenario, recipe, repository_root, router_package
    )
    if expected_provenance is not None and provenance != expected_provenance:
        raise ValueError("comparison inputs changed after preparation")
    observations = []
    run_id = str(uuid4())
    for index in range(samples):
        shift = index % len(strategies)
        order = strategies[shift:] + strategies[:shift]
        for strategy in order:
            session_id = "%s/%d/%s" % (run_id, index + 1, strategy)
            request = RuntimeRequest(
                scenario.scenario_id,
                scenario.target,
                tuple(
                    RuntimeTurnInput(t.event, t.prompt, t.invocation)
                    for t in scenario.turns
                ),
                strategy,
                index + 1,
                session_id,
                MappingProxyType(packages[strategy]),
                modes[strategy],
                environment,
            )
            observation = evaluator.evaluate(request)
            if not isinstance(observation, RuntimeSample):
                raise ValueError("provider must return RuntimeSample")
            for field in ("input_tokens", "output_tokens", "latency_ms"):
                if (
                    type(getattr(observation, field)) is not int
                    or getattr(observation, field) < 0
                ):
                    raise ValueError("invalid measured " + field)
            if not isinstance(observation.turns, tuple) or any(
                not isinstance(t, TurnTrace) for t in observation.turns
            ):
                raise ValueError("provider must return a tuple of TurnTrace")
            traces = tuple(parse_trace(asdict(t)) for t in observation.turns)
            checks = check_turns(
                scenario.turns,
                traces,
                variant="canonical" if strategy == "canonical" else "compiled",
                allow_model=scenario.expected_invocation.allow_model,
                allow_user=scenario.expected_invocation.allow_user,
                forbidden_actions=scenario.forbidden_actions,
                available_files=tuple(packages[strategy]),
            )
            if router_package is not None:
                checks = tuple(checks) + tuple(
                    quality_checks(
                        scenario.scenario_id, "\n".join(t.output for t in traces)
                    )
                )
            observations.append(
                {
                    "sample": index + 1,
                    "strategy": strategy,
                    "session_id": session_id,
                    "observation": asdict(observation),
                    "passed": all(c[1] for c in checks),
                    "checks": [
                        {"check_id": k, "passed": p, "message": m} for k, p, m in checks
                    ],
                }
            )
    return {
        "schema_version": 2 if router_package is not None else 1,
        "evidence_kind": evidence_kind,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **provenance,
        "environment": asdict(environment),
        "samples": samples,
        "strategies": list(strategies),
        "observations": observations,
        "passed": all(o["passed"] for o in observations),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--router-package", type=Path)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--auth-file", type=Path, default=Path.home() / ".codex/auth.json"
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="make real model calls; default only prepares packages",
    )
    args = parser.parse_args(argv)
    if args.samples < (4 if args.router_package else 3) or args.timeout <= 0:
        parser.error(
            "enough samples to rotate strategies and a positive timeout are required"
        )
    created_output = False
    try:
        scenario, recipe = load_scenario(args.scenario), load_recipe(args.recipe)
        if (
            scenario.target != "codex"
            or len(scenario.turns) != 1
            or scenario.turns[0].event != "prompt"
            or scenario.turns[0].invocation != "user"
        ):
            raise ValueError(
                "Codex comparison CLI supports single explicit prompt turns"
            )
        packages, modes, provenance = prepare_comparison(
            scenario, recipe, args.repository_root, args.router_package
        )
        args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
        created_output = True
        for strategy, files in packages.items():
            for name, data in files.items():
                path = args.output / strategy / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                path.chmod(0o755 if name in modes[strategy] else 0o644)
        (args.output / "preparation.json").write_text(
            json.dumps(provenance, indent=2) + "\n"
        )
        if not args.enabled:
            print(f"Prepared {len(packages)} strategies; no model calls: {args.output}")
            return 0
        executable = shutil.which(args.codex)
        if not executable or not args.auth_file.is_file():
            raise ValueError("Codex executable and local auth.json required")
        version = subprocess.check_output(
            [executable, "--version"], text=True, timeout=10
        ).strip()
        environment = RuntimeEnvironment(
            "codex",
            version,
            args.model,
            "requested-id:" + args.model + ";backend-snapshot-unreported",
            "app-server-stdio",
            version,
            INSTRUMENTATION,
            "read-only;approval=never",
            "fresh-session;provider-cache-uncontrolled",
            _digest(CONFIG),
        )
        evaluator = CodexEvaluator(
            executable=executable,
            auth_file=args.auth_file,
            output_dir=args.output / "raw",
            timeout=args.timeout,
        )
        report = run_strategy_comparison(
            scenario,
            evaluator,
            recipe=recipe,
            repository_root=args.repository_root,
            environment=environment,
            samples=args.samples,
            enabled=True,
            router_package=args.router_package,
            expected_provenance=provenance,
        )
        # The collector prepares again: abort rather than silently run changed inputs.
        if any(report[key] != value for key, value in provenance.items()):
            raise ValueError("comparison inputs changed after preparation")
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(str(args.output / "report.json"))
        return 0 if report["passed"] else 1
    except (ValueError, OSError, SkillCompilerError, CodexRuntimeError) as exc:
        if created_output and not (args.output / "report.json").exists():
            (args.output / "incomplete.json").write_text(
                json.dumps({"completed": False, "error": str(exc)}, indent=2) + "\n"
            )
        print(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
