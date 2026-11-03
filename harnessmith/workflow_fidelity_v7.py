"""Prospective v7 adapter for the schema-6 literal shell absence certificate.

The authored router v6 and all frozen v6 hard gates remain unchanged. Only new
v7 bundles can be checked; bounded screens never replace retained raw review.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re

from . import workflow_fidelity as v1
from . import workflow_fidelity_v3 as v3
from . import workflow_fidelity_v4 as v4
from . import workflow_fidelity_v5 as v5
from . import workflow_fidelity_v6 as v6
from .router_experiment import load_router
from .workflow_fidelity_v6 import (
    _artifact_claims, _extension_checks, _git_claims, _reference_check,
    _replace_checks, _separate_final_readback,
)


PILOT = "evaluations/workflow-fidelity-v7"
CHECKER = "harnessmith/workflow_fidelity_v7.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v8.md"
MODULES = {**v6.MODULES, "checker-v7.py": CHECKER,
           "trace-v6.py": "harnessmith/workflow_trace_v6.py"}


def prepare_pilot(repository_root, output):
    """Pin the actual inherited/new instruments for exactly one offline append case."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (config.get("schema_version") != 7
            or config.get("pilot_id") != "opt-004-workflow-fidelity-v7"
            or config.get("model") != "gpt-6-luna"
            or config.get("reasoning_effort") != "low"
            or config.get("repetitions") != 1
            or config.get("strategies") != ["router-v6"]
            or [(c["id"], c["new_items"], c["first_id"], c["overlay"])
                for c in config["cases"]]
            != [("append", 3, 8, "append")]):
        raise ValueError("unsupported v7 pilot design; version a changed design")
    source = (root / v1._relative(config["source"])).read_bytes()
    router_path = root / v1._relative(config["router"])
    if root / v1._relative(config["router_review"]) != router_path.with_suffix(".review.json"):
        raise ValueError("router review must be adjacent to its package")
    router, review = load_router(router_path, source)
    fixtures = v1._files(root / v1._relative(config["fixtures"]))
    instruments = {name: (root / path).read_bytes() for name, path in MODULES.items()}
    instruments.update({"rubric.md": (root / RUBRIC).read_bytes(), "pilot.json": config_bytes})
    target = v1._relative(config["target"])
    prepared = []
    for case in config["cases"]:
        prefix = v1._relative(case["overlay"]) + "/"
        overlay = {p[len(prefix):]: data for p, data in fixtures.items() if p.startswith(prefix)}
        if not overlay:
            raise ValueError("missing case overlay")
        files = {p[len("common/"):]: data for p, data in fixtures.items() if p.startswith("common/")}
        files.update(overlay)
        files.update({v1.PACKAGE + "/" + p: data for p, data in router.items()})
        prepared.append((case, (root / v1._relative(case["prompt"])).read_bytes(), files))
    output.mkdir(parents=True, exist_ok=False)
    (output / "instrument").mkdir()
    for name, data in instruments.items():
        (output / "instrument" / name).write_bytes(data)
    sessions = []
    for case, prompt, files in prepared:
        session_id = case["id"] + "-router-v6-instrument-v7"
        directory = output / session_id
        workspace = directory / "workspace"
        workspace.mkdir(parents=True)
        for name, data in files.items():
            path = workspace / v1._relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o755 if name == v1.SETUP else 0o644)
        (directory / "prompt.md").write_bytes(prompt)
        baseline = {p: v1._sha(data) for p, data in files.items()}
        manifest = {
            "schema_version": 1, "checker_version": 7, "observation_schema_version": 6,
            "pilot_id": config["pilot_id"], "session_id": session_id,
            "case": case["id"], "strategy": "router-v6",
            "evidence_kind": "offline-preparation", "model": config["model"],
            "reasoning_effort": config["reasoning_effort"], "target": target,
            "new_items": case["new_items"], "first_id": case["first_id"],
            "baseline_target_hex": files.get(target, b"").hex(), "baseline": baseline,
            "baseline_inventory_sha256": v1._sha(json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()),
            "pinned_absent_paths": [p for p in (".specify/extensions.yml", "specs/001-invitations/plan.md", "specs/001-invitations/tasks.md") if p not in files],
            "executable_files": [v1.SETUP],
            "required_reads": [".specify/memory/constitution.md", "specs/001-invitations/spec.md"]
            + ([".specify/extensions.yml"] if case["id"] == "hooks" else [target]),
            "expected_references": ["references/project-generation.md"],
            "provenance": {
                "source_path": config["source"], "source_sha256": v1._sha(source),
                "recipe_sha256": None, "recipe_status": "not-applicable: authored router-v6 redesign",
                "router_review_sha256": review["review_sha256"],
                "package": {p: v1._sha(data) for p, data in router.items()},
                "fixtures": {p: v1._sha(data) for p, data in fixtures.items()},
                "pilot_config_sha256": v1._sha(config_bytes), "prompt_sha256": v1._sha(prompt),
                "instruments": {p: v1._sha(data) for p, data in instruments.items()},
            },
        }
        v1._json(directory / "manifest.json", manifest)
        sessions.append({"id": session_id, "manifest": session_id + "/manifest.json",
                         "prompt": session_id + "/prompt.md",
                         "manifest_sha256": v1._sha((directory / "manifest.json").read_bytes())})
    summary = {
        "schema_version": 7, "checker_version": 7, "observation_schema_version": 6,
        "pilot_id": config["pilot_id"], "evidence_kind": "offline-preparation",
        "live_sessions_started": 0, "proposed_session_count": 1, "model": config["model"],
        "sessions": sessions, "model_fidelity": "pending",
        "approval_required": "One fresh single-turn GPT-6 Luna low append session with router v6 and instrument v7; no retries; not authorized.",
    }
    v1._json(output / "preparation.json", summary)
    return summary



def check_workspace(manifest_path, observation):
    """Apply new screens only to a new v7 bundle; never regrade old evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("checker_version") != 7 or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v7"
            or manifest.get("observation_schema_version") != 6):
        raise ValueError("v7 checker requires a newly prepared v7 bundle")
    root = Path(__file__).resolve().parents[1]
    for name, path in {**MODULES, "rubric.md": RUBRIC, "pilot.json": PILOT + "/pilot.json"}.items():
        if manifest["provenance"]["instruments"].get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError("checker dependency version differs; prepare a new v7 bundle")
    if observation.get("schema_version") != 6:
        raise ValueError("unsupported v6 observation schema")
    final = observation.get("final_output") or ""
    commentary = observation.get("commentary", "")
    if isinstance(commentary, list) and all(isinstance(part, str) for part in commentary):
        commentary = "\n".join(commentary)
    if not isinstance(final, str) or not isinstance(commentary, str):
        raise ValueError("final_output and commentary must be text")
    legacy = copy.deepcopy(observation)
    legacy.update(schema_version=1, output=commentary + "\n" + final)
    report = v1.check_workspace(manifest_path, legacy)
    target = manifest_path.parent / "workspace" / manifest["target"]
    artifact = target.read_bytes() if target.exists() else b""
    before = bytes.fromhex(manifest["baseline_target_hex"])
    try:
        items = v1.ITEM.findall((artifact[len(before):] if artifact.startswith(before) else artifact).decode())
    except UnicodeDecodeError:
        items = []
    evidence = [v4._topic_evidence(line) for _, _, line in items]
    topics = {"expiration", "outcomes", "retention"} | ({"authorization"} if manifest["case"] != "append" else set())
    def check(dimension, name, passed, detail):
        return {"dimension": dimension, "name": name, "passed": bool(passed), "detail": detail}
    _replace_checks(report, "content", [check("content", "one-item-per-requested-topic-heuristic",
        len(evidence) == len(topics) and all(len(e) == 1 for e in evidence) and set().union(*evidence) == topics,
        "Frozen v4 bounded topic cues; semantic and policy review remain mandatory.")])
    _replace_checks(report, "formatting", [
        check("formatting", "missing-policy-gap-markers-heuristic", items and all(re.search(r"\[[^\]\n]*\bGap\b[^\]\n]*\]", line, re.I) for _, _, line in items), "Every synthetic missing-policy question requires a bracketed Gap marker."),
        check("formatting", "final-report", v5._final_report(final, str(target.resolve()), manifest["new_items"], bool(before)), "Frozen completed-report grammar plus bounded singular item/question checklist modifiers; wrong, planned, negated and contradictory counts cannot supply a pass."),
    ])
    _replace_checks(report, "reference_behavior", [_reference_check(manifest, observation)])
    workflow = report["dimensions"]["workflow"]["checks"]
    workflow[:] = [c for c in workflow if c["name"] not in {"final-report", "hook-announcements"}]
    additions = v4._workflow_v4_checks(manifest, observation, artifact)
    blocks = v5._pre_blocks(observation)
    if manifest["case"] == "hooks":
        expected = {v3._hook_fields(True, optional)[0] for optional in (True, False)}
        correct = len(blocks) == 2 and {b["heading"] for b in blocks} == expected
        next(c for c in additions if c["name"] == "hook-announcements")["passed"] &= correct
        additions.append(check("workflow", "configured-pre-hook-blocks-only", correct,
                               "Exactly the two configured pre blocks may be emitted; invented or duplicate blocks are not repaired by later correct blocks."))
    claims = v5._execution_error_claims(observation)
    additions.append(check("workflow", "recognized-execution-error-claims-supported",
                           all(c["status"] == "supported" for c in claims),
                           "Bounded completed commentary/final assertions require matching earlier command records/output. Missing support is unverified; retained raw narrative review is always pending."))
    additions.extend(_extension_checks(manifest, observation))
    additions.append(_separate_final_readback(manifest, observation, artifact))
    artifact_claims = _artifact_claims(manifest, observation, artifact)
    git_claims = _git_claims(manifest, observation)
    additions.append(check("workflow", "recognized-artifact-verification-claims-supported",
                           all(c["status"] == "supported" for c in artifact_claims),
                           "Recognized completed read/verification assertions require an earlier full exact-hash target read after every write. Correct saved bytes and collector snapshots cannot substitute."))
    additions.append(check("workflow", "recognized-git-comparison-claims-supported",
                           all(c["status"] == "supported" for c in git_claims),
                           "Recognized completed Git-history comparison/error assertions require earlier bounded relevant Git argv and corroborating results. Git commands are neither required nor recommended; absence of .git never proves an attempted comparison."))
    _replace_checks(report, "workflow", additions)
    report.update(schema_version=7, checker_version=7, historical_results_regraded=False)
    report["automated_checks_passed"] = all(c["passed"] for d in report["dimensions"].values() for c in d.get("checks", []))
    report["topic_screen"] = {"version": 4, "kind": "bounded-lexical-heuristic",
        "allocations": [{"id": number, "topics": sorted(e), "matched_cues": e} for (_, number, _), e in zip(items, evidence)],
        "semantic_review": "pending", "policy_neutrality": "requires semantic review; never inferred from cue matches"}
    report["narrative_screen"] = {"version": 6, "kind": "bounded-workflow-and-git-claims",
        "claims": v4._final_hook_claims(manifest, observation, artifact), "execution_error_claims": claims,
        "artifact_verification_claims": artifact_claims, "git_comparison_claims": git_claims,
        "pre_hook_blocks": blocks, "raw_review_status": "pending",
        "limitations": "Only documented affirmative forms and completed messages are screened. Normalized command records are assertions requiring retained raw verification. No match or passing screen establishes narrative accuracy; all other claims and paraphrases require manual raw review."}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="prepare one offline append case; no live calls")
    prepare.add_argument("--repository-root", type=Path, default=Path.cwd())
    prepare.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check", help="check a new v7 bundle")
    check.add_argument("manifest", type=Path)
    check.add_argument("observation", type=Path)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        print(json.dumps(prepare_pilot(args.repository_root, args.output), indent=2))
        return 0
    if args.output.exists():
        parser.error("report output already exists")
    report = check_workspace(args.manifest, json.loads(args.observation.read_text()))
    v1._json(args.output, report)
    print(str(args.output))
    return 0 if report["automated_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
