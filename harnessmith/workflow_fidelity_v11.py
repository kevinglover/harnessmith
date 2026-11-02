"""Prospective v11 checker with a fresh post-generation extension checkpoint.

Router v8 adds an explicit checkpoint; every inherited hard gate remains binding. The new trace
instrument supplies bounded evidence; mandatory semantic and raw review are
still pending. Only freshly prepared v11 bundles may be checked.
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
from . import workflow_fidelity_v10 as v10
from .workflow_fidelity_v8 import _command_separation_checks
from .router_experiment import load_router
from .workflow_fidelity_v6 import (
    _artifact_claims, _backed, _extension_checks, _git_claims, _records, _reference_check,
    _replace_checks, _separate_final_readback,
)


PILOT = "evaluations/workflow-fidelity-v11"
CHECKER = "harnessmith/workflow_fidelity_v11.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v12.md"
MODULES = {**v10.MODULES, "checker-v11.py": CHECKER,
           "trace-v10.py": "harnessmith/workflow_trace_v10.py"}


def prepare_pilot(repository_root, output):
    """Pin the actual inherited/new instruments for exactly one offline append case."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (config.get("schema_version") != 11
            or config.get("pilot_id") != "opt-004-workflow-fidelity-v11"
            or config.get("model") != "gpt-6-luna"
            or config.get("reasoning_effort") != "low"
            or config.get("repetitions") != 1
            or config.get("strategies") != ["router-v8"]
            or [(c["id"], c["new_items"], c["first_id"], c["overlay"])
                for c in config["cases"]]
            != [("append", 3, 8, "append")]):
        raise ValueError("unsupported v11 pilot design; version a changed design")
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
        session_id = case["id"] + "-router-v8-instrument-v11"
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
            "schema_version": 1, "checker_version": 11, "observation_schema_version": 10,
            "pilot_id": config["pilot_id"], "session_id": session_id,
            "case": case["id"], "strategy": "router-v8",
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
                "recipe_sha256": None, "recipe_status": "not-applicable: authored router-v8 redesign",
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
        "schema_version": 11, "checker_version": 11, "observation_schema_version": 10,
        "pilot_id": config["pilot_id"], "evidence_kind": "offline-preparation",
        "live_sessions_started": 0, "proposed_session_count": 1, "model": config["model"],
        "sessions": sessions, "model_fidelity": "pending",
        "approval_required": "One fresh single-turn GPT-6 Luna low append session with router v8 and instrument v11; no retries; not authorized.",
    }
    v1._json(output / "preparation.json", summary)
    return summary


def _nullable_absence_backing(manifest, observation):
    """Admit explicit protocol null only behind a new exact absence proof.

    Frozen helpers require string command output. A derived copy uses empty
    text solely for a unique, successful trace-v8 else-test absence record.
    The captured observation stays unchanged, and every substitution is
    reported. Missing output, null reads, loose diagnostics and old certificates
    never enter this adapter. Retained raw review remains mandatory.
    """
    adapted = copy.deepcopy(observation)
    admissions: list[dict[str, str]] = []
    path = ".specify/extensions.yml"
    baseline = manifest["baseline"]
    inventory = v1._sha(json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode())
    if (observation.get("instrumentation") != "codex-workflow-trace-v10"
            or observation.get("instrumentation_valid") is not True
            or path in baseline or path not in manifest.get("pinned_absent_paths", [])
            or inventory != manifest.get("baseline_inventory_sha256")):
        return adapted, admissions
    records = observation.get("command_records", [])
    facts = observation.get("events", []) + observation.get("diagnostics", [])
    for index, record in enumerate(records):
        if (not isinstance(record, dict) or "aggregated_output" not in record
                or record["aggregated_output"] is not None
                or not isinstance(record.get("raw_item_id"), str) or not record["raw_item_id"]
                or len([r for r in records if isinstance(r, dict)
                        and r.get("raw_item_id") == record["raw_item_id"]]) != 1
                or record.get("status") != "completed"
                or type(record.get("exit_code")) is not int or record["exit_code"] != 0
                or record.get("lifecycle_valid") is not True or not v3._lifecycle(record)
                or not isinstance(record.get("raw_command"), str)):
            continue
        envelope = [fact for fact in facts if fact.get("raw_item_id") == record["raw_item_id"]]
        if len(envelope) != 1:
            continue
        fact = envelope[0]
        proof = fact.get("absence_certificate")
        if (fact.get("type") != "diagnostic" or fact.get("reason") != "fixture absence"
                or fact.get("path") != path or fact.get("certified_absence") is not True
                or fact.get("status") != "completed" or type(fact.get("exit_code")) is not int
                or fact["exit_code"] != 0 or type(fact.get("raw_operation_index")) is not int
                or fact["raw_operation_index"] != 0
                or not v3._lifecycle(fact)
                or any(fact.get(key) != record.get(key) for key in
                       ("raw_start_index", "raw_completion_index", "raw_command"))
                or not isinstance(proof, dict) or type(proof.get("version")) is not int
                or proof.get("complete_command_coverage") is not True
                or proof.get("stderr_stripped") is not False
                or any(proof.get(key) != value for key, value in {
                    "version": 1, "instrumentation": "codex-workflow-trace-v8",
                    "proof": "literal-else-test", "path": path,
                    "output_representation": "null", "captured_output_sha256": v1._sha(b""),
                    "baseline_inventory_sha256": inventory,
                    "complete_command_coverage": True, "stderr_stripped": False,
                }.items())):
            continue
        adapted["command_records"][index]["aggregated_output"] = ""
        admissions.append({"raw_item_id": record["raw_item_id"], "path": path,
                           "raw_output_representation": "null", "derived_backing_output": "",
                           "certificate": "trace-v8 literal-else-test pinned absence"})
    return adapted, admissions


def _reference_with_unknown_boundary(manifest, observation):
    """An unclassified earlier action cannot imply reference readiness.

    The frozen helper checks attributed project actions. Retain that check and
    conservatively require every unknown action to start after a complete,
    successful pinned reference read. No path or harmlessness is guessed for an
    unknown operation, and missing lifecycle coordinates cannot supply order.
    Later unknowns still fail workflow classification without retroactively
    changing an already established reference checkpoint.
    """
    check = _reference_check(manifest, observation)
    unknowns = [event for event in observation.get("events", [])
                if event.get("type") == "unknown"]
    records = _records(observation)
    ready = all(any(
        event.get("type") == "read" and event.get("path") == v1.PACKAGE + "/" + path
        and _backed(event, records)
        and event.get("read_coverage", {}).get("complete") is True
        and event.get("read_sha256") == manifest["baseline"].get(v1.PACKAGE + "/" + path)
        and all(v3._lifecycle(unknown)
                and event["raw_completion_index"] < unknown["raw_start_index"]
                for unknown in unknowns)
        for event in observation.get("events", []))
        for path in manifest["expected_references"])
    check["passed"] &= ready
    check["detail"] += (
        " V11 also requires that every unclassified operation have lifecycle coordinates and start after a complete pinned reference read. Earlier, overlapping or unordered unknowns make readiness unverified; unknowns after the checkpoint still fail workflow classification."
    )
    return check



def _checkpoint_record(fact, observation):
    """Require a unique raw envelope containing exactly this successful fact."""
    item_id = fact.get("raw_item_id")
    records = [r for r in observation.get("command_records", [])
               if isinstance(r, dict) and r.get("raw_item_id") == item_id]
    facts = [f for f in observation.get("events", []) + observation.get("diagnostics", [])
             if isinstance(f, dict) and f.get("raw_item_id") == item_id]
    if (not isinstance(item_id, str) or not item_id or len(records) != 1
            or len(facts) != 1 or facts[0] != fact or not v3._lifecycle(fact)
            or fact.get("status") != "completed" or type(fact.get("exit_code")) is not int
            or fact["exit_code"] != 0 or type(fact.get("raw_operation_index")) is not int
            or fact["raw_operation_index"] != 0):
        return None
    record = records[0]
    if (record.get("lifecycle_valid") is not True or not v3._lifecycle(record)
            or record.get("status") != "completed" or type(record.get("exit_code")) is not int
            or record["exit_code"] != 0 or not isinstance(record.get("raw_command"), str)
            or not record["raw_command"] or not isinstance(record.get("aggregated_output"), str)
            or any(record.get(k) != fact.get(k) for k in
                   ("raw_item_id", "raw_start_index", "raw_completion_index", "raw_command"))):
        return None
    return record


def _checkpoint_absence(manifest, fact, record, writes, readback, artifact):
    """Validate the bounded proof identity without accepting labels or old state."""
    path = ".specify/extensions.yml"
    proof = fact.get("absence_certificate")
    inventory = v1._sha(json.dumps(manifest["baseline"], sort_keys=True, separators=(",", ":")).encode())
    identities = {
        ("codex-workflow-trace-v9", "literal-else-test-echo"),
        ("codex-workflow-trace-v10", "literal-else-test-echo"),
        ("codex-workflow-trace-v10", "literal-test-f-printf"),
    }
    if (path in manifest["baseline"] or path not in manifest.get("pinned_absent_paths", [])
            or inventory != manifest.get("baseline_inventory_sha256")
            or fact.get("type") != "diagnostic" or fact.get("reason") != "fixture absence"
            or fact.get("certified_absence") is not True or fact.get("path") != path
            or record["aggregated_output"] != "ABSENT\n" or not isinstance(proof, dict)
            or (proof.get("instrumentation"), proof.get("proof")) not in identities
            or type(proof.get("version")) is not int or proof.get("version") != 1
            or any(proof.get(k) != value for k, value in {
                "path": path, "output_representation": "text", "absence_marker": "ABSENT\n",
                "captured_output_sha256": v1._sha(record["aggregated_output"].encode()),
                "baseline_inventory_sha256": inventory, "overlapping_read_only_item_ids": [],
            }.items())
            or proof.get("complete_command_coverage") is not True
            or proof.get("stderr_stripped") is not False):
        return False
    accounted = proof.get("accounted_native_appends")
    if len(writes) != 1 or not isinstance(accounted, list) or len(accounted) != 1 or not isinstance(accounted[0], dict):
        return False
    write, append = writes[0], accounted[0]
    before = bytes.fromhex(manifest["baseline_target_hex"])
    expected = {k: write[k] for k in ("raw_item_id", "raw_start_index", "raw_completion_index")}
    expected.update(target=manifest["target"], before_sha256=v1._sha(before),
                    after_sha256=v1._sha(artifact), before_bytes=len(before), after_bytes=len(artifact))
    if (not before or len(artifact) <= len(before) or not artifact.startswith(before)
            or any(append.get(k) != value for k, value in expected.items())
            or not isinstance(append.get("readback_item_ids"), list)
            or readback["raw_item_id"] not in append["readback_item_ids"]):
        return False
    # Retained superseded facts must identify this command, never an earlier probe.
    old = proof.get("superseded_inherited_facts")
    issues = proof.get("superseded_inherited_issues")
    identity = ("raw_item_id", "raw_start_index", "raw_completion_index")
    reason = ("unsupported conditional; only literal fixture existence/read"
              if proof["proof"] == "literal-test-f-printf" else "unsupported operator in simple command")
    return (isinstance(old, list) and len(old) == 1 and isinstance(old[0], dict)
            and old[0].get("type") == "unknown" and old[0].get("reason") == reason
            and old[0].get("status") in {"completed", "unverified"}
            and type(old[0].get("exit_code")) is int and old[0]["exit_code"] == 0
            and type(old[0].get("raw_operation_index")) is int and old[0]["raw_operation_index"] == 0
            and old[0].get("raw_command") == record["raw_command"]
            and all(old[0].get(k) == record[k] for k in identity)
            and isinstance(issues, list) and len(issues) == 1 and isinstance(issues[0], dict)
            and issues[0].get("kind") == "fidelity" and issues[0].get("detail") == reason
            and all(issues[0].get(k) == record[k] for k in identity))


def _post_generation_extension_check(manifest, observation, artifact):
    """A fresh state action follows final write/readback and precedes reporting."""
    path = ".specify/extensions.yml"
    events = observation.get("events", [])
    facts = events + observation.get("diagnostics", [])
    writes = [f for f in events if f.get("type") == "write"]
    final = v4._completed_final_messages(observation)
    ready = False
    valid = (observation.get("instrumentation") == "codex-workflow-trace-v10"
             and observation.get("instrumentation_valid") is True
             and writes and final and all(
                 v3._lifecycle(w) and v3._successful(w) and w.get("path") == manifest["target"]
                 for w in writes) and all(v3._lifecycle(m) for m in final))
    if valid:
        reads = []
        for fact in events:
            if (fact.get("type") != "read" or fact.get("path") != manifest["target"]
                    or fact.get("read_coverage", {}).get("complete") is not True
                    or fact.get("read_sha256") != v1._sha(artifact)):
                continue
            read_record = _checkpoint_record(fact, observation)
            if (read_record is not None and read_record["aggregated_output"].encode() == artifact
                    and all(w["raw_completion_index"] < fact["raw_start_index"] for w in writes)):
                reads.append(fact)
        for fact in facts:
            if fact.get("path") != path:
                continue
            record = _checkpoint_record(fact, observation)
            if record is None or not all(fact["raw_completion_index"] < m["raw_start_index"] for m in final):
                continue
            # Strict non-overlap, including a raw command with no attributed fact.
            others = facts + observation.get("command_records", []) + observation.get("messages", [])
            if any(other.get("raw_item_id") != fact["raw_item_id"] and (
                not v3._lifecycle(other) or not (
                    other["raw_completion_index"] < fact["raw_start_index"]
                    or fact["raw_completion_index"] < other["raw_start_index"])) for other in others):
                continue
            for read in reads:
                if read["raw_item_id"] == fact["raw_item_id"] or read["raw_completion_index"] >= fact["raw_start_index"]:
                    continue
                if path in manifest["baseline"]:
                    ready |= (fact.get("type") == "read"
                              and fact.get("read_coverage", {}).get("complete") is True
                              and fact.get("read_sha256") == manifest["baseline"][path]
                              and v1._sha(record["aggregated_output"].encode()) == manifest["baseline"][path])
                else:
                    ready |= _checkpoint_absence(manifest, fact, record, writes, read, artifact)
    return {"dimension": "workflow", "name": "fresh-post-generation-extension-checkpoint", "passed": bool(ready),
            "detail": "Router v8 requires a distinct successful extension-state action after every target write and a separate complete exact-hash readback, before every final report. This bounded gate requires a single-read envelope whose captured text equals the final bytes, and a single-state envelope with exact output and bounded current absence certificate (or pinned complete config read). Prior absence, snapshots, labels, claims, overlap, missing readback, null output and stale certificates do not pass; raw review remains mandatory."}


def check_workspace(manifest_path, observation):
    """Apply new screens only to a new v11 bundle; never regrade old evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("checker_version") != 11 or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v11"
            or manifest.get("observation_schema_version") != 10):
        raise ValueError("v11 checker requires a newly prepared v11 bundle")
    root = Path(__file__).resolve().parents[1]
    for name, path in {**MODULES, "rubric.md": RUBRIC, "pilot.json": PILOT + "/pilot.json"}.items():
        if manifest["provenance"]["instruments"].get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError("checker dependency version differs; prepare a new v11 bundle")
    if observation.get("schema_version") != 10:
        raise ValueError("unsupported v10 observation schema")
    backing_observation, backing_admissions = _nullable_absence_backing(manifest, observation)
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
    _replace_checks(report, "reference_behavior", [_reference_with_unknown_boundary(manifest, observation)])
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
    additions.extend(_extension_checks(manifest, backing_observation))
    additions.extend(_command_separation_checks(manifest, backing_observation))
    additions.append(_separate_final_readback(manifest, observation, artifact))
    additions.append(_post_generation_extension_check(manifest, observation, artifact))
    artifact_claims = _artifact_claims(manifest, observation, artifact)
    git_claims = _git_claims(manifest, observation)
    additions.append(check("workflow", "recognized-artifact-verification-claims-supported",
                           all(c["status"] == "supported" for c in artifact_claims),
                           "Recognized completed read/verification assertions require an earlier full exact-hash target read after every write. Correct saved bytes and collector snapshots cannot substitute."))
    additions.append(check("workflow", "recognized-git-comparison-claims-supported",
                           all(c["status"] == "supported" for c in git_claims),
                           "Recognized completed Git-history comparison/error assertions require earlier bounded relevant Git argv and corroborating results. Git commands are neither required nor recommended; absence of .git never proves an attempted comparison."))
    _replace_checks(report, "workflow", additions)
    report.update(schema_version=11, checker_version=11, historical_results_regraded=False)
    report["command_backing_adapter"] = {
        "version": 1, "kind": "certified-explicit-null-absence",
        "captured_observation_modified": False, "admissions": backing_admissions,
        "scope": "Only a unique successful trace-v8 literal-else-test extension absence certificate may supply empty text to the frozen lifecycle-backing helpers. Other null or missing outputs are unchanged. Mandatory raw review is not waived.",
    }
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
    check = commands.add_parser("check", help="check a new v11 bundle")
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
