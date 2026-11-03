"""Prospective v8 adapter for schema-7 discovery and command separation.

Router v7 adds explicit command boundaries to the authored redesign. All frozen
hard gates remain; new checks distinguish attribution from workflow fidelity.
Only new v8 bundles can be checked; retained raw review remains mandatory.
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
from . import workflow_fidelity_v7 as v7
from .router_experiment import load_router
from .workflow_fidelity_v6 import (
    _artifact_claims, _extension_checks, _git_claims, _reference_check,
    _replace_checks, _separate_final_readback,
)


PILOT = "evaluations/workflow-fidelity-v8"
CHECKER = "harnessmith/workflow_fidelity_v8.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v9.md"
MODULES = {**v7.MODULES, "checker-v8.py": CHECKER,
           "trace-v7.py": "harnessmith/workflow_trace_v7.py"}


def prepare_pilot(repository_root, output):
    """Pin the actual inherited/new instruments for exactly one offline append case."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (config.get("schema_version") != 8
            or config.get("pilot_id") != "opt-004-workflow-fidelity-v8"
            or config.get("model") != "gpt-6-luna"
            or config.get("reasoning_effort") != "low"
            or config.get("repetitions") != 1
            or config.get("strategies") != ["router-v7"]
            or [(c["id"], c["new_items"], c["first_id"], c["overlay"])
                for c in config["cases"]]
            != [("append", 3, 8, "append")]):
        raise ValueError("unsupported v8 pilot design; version a changed design")
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
        session_id = case["id"] + "-router-v7-instrument-v8"
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
            "schema_version": 1, "checker_version": 8, "observation_schema_version": 7,
            "pilot_id": config["pilot_id"], "session_id": session_id,
            "case": case["id"], "strategy": "router-v7",
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
                "recipe_sha256": None, "recipe_status": "not-applicable: authored router-v7 redesign",
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
        "schema_version": 8, "checker_version": 8, "observation_schema_version": 7,
        "pilot_id": config["pilot_id"], "evidence_kind": "offline-preparation",
        "live_sessions_started": 0, "proposed_session_count": 1, "model": config["model"],
        "sessions": sessions, "model_fidelity": "pending",
        "approval_required": "One fresh single-turn GPT-6 Luna low append session with router v7 and instrument v8; no retries; not authorized.",
    }
    v1._json(output / "preparation.json", summary)
    return summary



def _command_separation_checks(manifest, observation):
    """Evaluate normalized envelope boundaries without inferring hidden actions.

    Parser attribution and workflow separation are independent. A successfully
    attributed discovery still cannot accompany any observed read. Only the two
    named passive diagnostic forms are allowed beside context reads. The
    retained raw trace must be reviewed for unrepresented operations.
    """
    records = v6._records(observation)
    captured = observation.get("command_records", [])
    facts = observation.get("events", []) + observation.get("diagnostics", [])

    def backed(fact):
        matches = [record for record in captured
                   if record.get("raw_item_id") == fact.get("raw_item_id")]
        return len(matches) == 1 and v6._backed(fact, records)

    def envelope(fact):
        return [other for other in facts
                if other.get("raw_item_id") == fact.get("raw_item_id")]

    def cache_noise(fact):
        return (fact.get("type") == "diagnostic"
                and fact.get("reason") == "corroborated read-only Python cache warning")

    def passive_context(fact):
        return cache_noise(fact) or (fact.get("type") == "diagnostic"
                                    and fact.get("reason") == "literal output label")

    path = ".specify/extensions.yml"
    extension = [fact for fact in facts if fact.get("path") == path]

    def extension_proof(fact):
        if path in manifest["baseline"]:
            return (fact.get("type") == "read"
                    and fact.get("read_coverage", {}).get("complete") is True
                    and fact.get("read_sha256") == manifest["baseline"][path])
        return (fact.get("type") == "diagnostic"
                and fact.get("reason") == "fixture absence"
                and fact.get("certified_absence") is True
                and path in manifest.get("pinned_absent_paths", []))

    extension_isolated = bool(extension) and all(
        backed(fact) and extension_proof(fact)
        and len([other for other in envelope(fact) if not cache_noise(other)]) == 1
        and all(backed(other) for other in envelope(fact))
        for fact in extension)
    required = set(manifest["required_reads"]) - {path}
    context = [fact for fact in facts
               if fact.get("type") == "read" and fact.get("path") != path]
    context_isolated = required <= {fact.get("path") for fact in context} and all(
        backed(fact) and all((other.get("type") == "read" or passive_context(other)) and backed(other)
                             for other in envelope(fact))
        for fact in context)
    discovery_reasons = {"file discovery", "directory discovery", "working-directory discovery"}

    def discovery(fact):
        return fact.get("type") == "diagnostic" and fact.get("reason") in discovery_reasons

    discoveries = [fact for fact in facts if discovery(fact)]
    discovery_isolated = all(
        backed(fact) and all((discovery(other) or passive_context(other)) and backed(other)
                             for other in envelope(fact))
        for fact in discoveries)
    return [
        {"dimension": "workflow", "name": "extension-check-isolated-from-other-operations",
         "passed": extension_isolated,
         "detail": "Every observed extension check must have a unique successful matching lifecycle and a complete pinned read or certified pinned absence. Its command may contain only that check and corroborated read-only Python cache diagnostics. Discovery, setup, other reads, labels, mutation and unknown companions fail. Retained raw review remains mandatory."},
        {"dimension": "workflow", "name": "context-reads-isolated-from-discovery-and-mutation",
         "passed": context_isolated,
         "detail": "Each required context path must have a successful lifecycle-backed read. Every observed read outside the separately checked extension config, including optional/template and package reads, must share its command only with successful lifecycle-backed reads, literal output labels and corroborated read-only Python cache diagnostics. Discovery, absence probes, setup, hooks, writes, unknowns and other diagnostics fail. Attribution of a mixed read/discovery command does not satisfy separation. Retained raw review remains mandatory."},
        {"dimension": "workflow", "name": "discovery-isolated-from-other-operations",
         "passed": discovery_isolated,
         "detail": "When discovery is observed, each successful lifecycle-backed discovery envelope may contain only successful discovery, literal output labels and corroborated read-only Python cache diagnostics. Reads, extension probes, setup, hooks, writes, unknowns and other diagnostics fail. No discovery is required by this gate, and retained raw review remains mandatory."},
    ]


def check_workspace(manifest_path, observation):
    """Apply new screens only to a new v8 bundle; never regrade old evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("checker_version") != 8 or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v8"
            or manifest.get("observation_schema_version") != 7):
        raise ValueError("v8 checker requires a newly prepared v8 bundle")
    root = Path(__file__).resolve().parents[1]
    for name, path in {**MODULES, "rubric.md": RUBRIC, "pilot.json": PILOT + "/pilot.json"}.items():
        if manifest["provenance"]["instruments"].get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError("checker dependency version differs; prepare a new v8 bundle")
    if observation.get("schema_version") != 7:
        raise ValueError("unsupported v7 observation schema")
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
    additions.extend(_command_separation_checks(manifest, observation))
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
    report.update(schema_version=8, checker_version=8, historical_results_regraded=False)
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
    check = commands.add_parser("check", help="check a new v8 bundle")
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
