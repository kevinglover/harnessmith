"""Prospective v6 adapter: append verification, extension ordering and Git claims.

Frozen v1 action gates and v3/v4 semantic screens remain dependencies. Normalized
records are assertions, not a substitute for mandatory retained raw review.
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
from .router_experiment import load_router
from .workflow_trace import _shell_body
from .workflow_trace_v3 import CACHE_WARNING, _literal_words


PILOT = "evaluations/workflow-fidelity-v6"
CHECKER = "harnessmith/workflow_fidelity_v6.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v7.md"
MODULES = {**v5.MODULES, "checker-v6.py": CHECKER,
           "trace-v5.py": "harnessmith/workflow_trace_v5.py"}


def prepare_pilot(repository_root, output):
    """Pin the actual inherited/new instruments for exactly one offline append case."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (config.get("schema_version") != 6
            or config.get("pilot_id") != "opt-004-workflow-fidelity-v6"
            or config.get("model") != "gpt-6-luna"
            or config.get("reasoning_effort") != "low"
            or config.get("repetitions") != 1
            or config.get("strategies") != ["router-v6"]
            or [(c["id"], c["new_items"], c["first_id"], c["overlay"])
                for c in config["cases"]]
            != [("append", 3, 8, "append")]):
        raise ValueError("unsupported v6 pilot design; version a changed design")
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
        session_id = case["id"] + "-router-v6"
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
            "schema_version": 1, "checker_version": 6, "observation_schema_version": 5,
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
        "schema_version": 6, "checker_version": 6, "observation_schema_version": 5,
        "pilot_id": config["pilot_id"], "evidence_kind": "offline-preparation",
        "live_sessions_started": 0, "proposed_session_count": 1, "model": config["model"],
        "sessions": sessions, "model_fidelity": "pending",
        "approval_required": "One fresh single-turn GPT-6 Luna append session; no retries; not authorized.",
    }
    v1._json(output / "preparation.json", summary)
    return summary


def _replace_checks(report, dimension, checks):
    selected = report["dimensions"][dimension]["checks"]
    names = {check["name"] for check in checks}
    selected[:] = [check for check in selected if check["name"] not in names] + checks
    report["dimensions"][dimension]["automated_status"] = "pass" if all(c["passed"] for c in selected) else "fail"


def _records(observation):
    records = observation.get("command_records", [])
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        raise ValueError("command_records must be a list of command objects")
    return [r for r in records if v3._lifecycle(r) and r.get("lifecycle_valid") is True
            and isinstance(r.get("raw_item_id"), str) and r["raw_item_id"]
            and r.get("status") in {"completed", "failed"}
            and type(r.get("exit_code")) is int
            and isinstance(r.get("raw_command"), str)
            and isinstance(r.get("aggregated_output"), str)]


def _backed(event, records):
    """A derived command event must match its successful captured envelope."""
    return v3._successful(event) and v3._lifecycle(event) and any(
        v3._successful(record) and all(event.get(key) == record.get(key) for key in
            ("raw_item_id", "raw_start_index", "raw_completion_index"))
        for record in records)


def _extension_checks(manifest, observation):
    records, events = _records(observation), observation.get("events", [])
    setups = [e for e in events if e.get("type") == "setup"]
    path = ".specify/extensions.yml"
    if path in manifest["baseline"]:
        proof = [e for e in events if e.get("type") == "read" and e.get("path") == path
                 and e.get("read_coverage", {}).get("complete") is True
                 and e.get("read_sha256") == manifest["baseline"][path]]
    else:
        proof = [e for e in observation.get("diagnostics", [])
                 if path in manifest.get("pinned_absent_paths", [])
                 and e.get("type") == "diagnostic" and e.get("path") == path
                 and e.get("certified_absence") is True and e.get("reason") == "fixture absence"]
    before = bool(setups) and all(_backed(s, records) and any(
        _backed(p, records) and p["raw_completion_index"] < s["raw_start_index"]
        for p in proof) for s in setups)
    reads = [e for e in events if e.get("type") == "read"]
    reads += [e for e in observation.get("diagnostics", []) if e.get("certified_absence") is True]
    isolated = bool(setups) and all(_backed(s, records) and not any(
        e.get("raw_item_id") == s.get("raw_item_id") for e in reads) for s in setups)
    return [{"dimension": "workflow", "name": "extension-config-before-setup", "passed": before,
             "detail": "Before setup starts, a separate successful command must finish a complete baseline-matching extension read or certified manifest-pinned absence. Missing, partial, inferred, overlapping or same-command discovery is insufficient."},
            {"dimension": "workflow", "name": "setup-isolated-from-file-reads", "passed": isolated,
             "detail": "Setup has a successful matching command lifecycle and shares no command envelope with file reads or certified absence probes."}]


def _reference_check(manifest, observation):
    events, records = observation.get("events", []), _records(observation)
    prefix = v1.PACKAGE + "/"
    project = [e for e in events if e.get("type") in {"setup", "hook", "write"}
               or (e.get("type") == "read" and not str(e.get("path", "")).startswith(prefix))]
    project += [e for e in observation.get("diagnostics", []) if e.get("certified_absence") is True]
    references = [prefix + name for name in manifest["expected_references"]]
    ready = bool(project) and all(any(
        e.get("type") == "read" and e.get("path") == path and _backed(e, records)
        and e.get("read_coverage", {}).get("complete") is True
        and e.get("read_sha256") == manifest["baseline"].get(path)
        and all(v3._lifecycle(action) and e["raw_completion_index"] < action["raw_start_index"]
                for action in project) for e in events) for path in references)
    return {"dimension": "reference_behavior", "name": "reference-before-project-actions",
            "passed": ready, "detail": "A successful complete baseline-hash generation-reference read must finish in a separate command before every project action starts, including extension absence checks. Same-envelope sequencing does not supply this checkpoint."}


def _clauses(message):
    return re.split(r"[;\n]|\.(?:\s|$)|,\s*(?:but|and)\s+|\s+but\s+",
                    "\n".join(v5._plain_lines(message["text"])))


def _asserted(clause, match, *, failure=False):
    text = v5._unquoted(clause)
    # "could not run" is a factual failed-attempt assertion, not a hypothetical.
    scoped = re.sub(r"\bcould not run\b", "failed to run", text, flags=re.I) if failure else text
    if clause.strip().endswith("?") or v5._nonasserted(scoped, match):
        return False
    prefix = scoped[:match.end()]
    if failure:
        prefix = re.sub(r"\b(?:not recognized|not a git repository|could not run)\b", "failure", prefix, flags=re.I)
    return not v5.NEGATION.search(prefix)


READ_ASSERTION = re.compile(
    r"\b(?:the\s+)?final\s+(?:file\s+read|(?:file|checklist|artifact)\s+(?:read|readback|verification)|readback)\s+"
    r"(?:shows?|showed|confirms?|confirmed|proves?|proved|verified|demonstrates?)\b"
    r"|\b(?:i|we)\s+(?:have\s+)?(?:successfully\s+)?(?:read|reread|re-read|verified|checked)\s+"
    r"(?:the\s+)?(?:final\s+(?:file|artifact|checklist)|(?:existing\s+)?(?:prefix|checkbox states|original content))\b",
    re.I,
)


def _artifact_claims(manifest, observation, artifact):
    """Screen explicit final-read/verification statements, never imply completeness."""
    events, records = observation.get("events", []), _records(observation)
    writes = [e for e in events if e.get("type") == "write"]
    reads = [e for e in events if e.get("type") == "read"
             and e.get("path") == manifest["target"] and _backed(e, records)
             and e.get("read_coverage", {}).get("complete") is True
             and e.get("read_sha256") == v1._sha(artifact)
             and writes and all(v3._successful(w) and v3._before(w, e) for w in writes)]
    claims = []
    for message in v5._completed_messages(observation):
        for clause in _clauses(message):
            match = READ_ASSERTION.search(v5._unquoted(clause))
            if not match or not _asserted(clause, match):
                continue
            preserved = not re.search(r"\b(?:intact|preserv\w*|unchanged)\b", clause, re.I) or artifact.startswith(bytes.fromhex(manifest["baseline_target_hex"]))
            support = [e["raw_item_id"] for e in reads if preserved and v3._before(e, message)]
            claims.append({"kind": "final-artifact-read-verification", "clause": clause.strip(),
                           "raw_item_id": message.get("raw_item_id"), "phase": message["phase"],
                           "support_item_ids": support, "status": "supported" if support else "unverified"})
    return claims


def _separate_final_readback(manifest, observation, artifact):
    events, records = observation.get("events", []), _records(observation)
    writes = [e for e in events if e.get("type") == "write"]
    final = v4._completed_final_messages(observation)
    ready = bool(writes) and bool(final) and any(
        e.get("type") == "read" and e.get("path") == manifest["target"] and _backed(e, records)
        and e.get("read_coverage", {}).get("complete") is True
        and e.get("read_sha256") == v1._sha(artifact)
        and all(v3._successful(w) and v3._lifecycle(w)
                and w["raw_completion_index"] < e["raw_start_index"] for w in writes)
        and all(v3._before(e, message) for message in final) for e in events)
    return {"dimension": "workflow", "name": "separate-final-artifact-readback", "passed": ready,
            "detail": "Router v6 requires a distinct completed full exact-hash read command after every write finishes and before the final report. Proven internal append/readback still supports truthful read narration and the inherited gate, but does not fulfill this separate-tool-action checkpoint."}


GIT_ASSERTION = re.compile(
    r"\b(?:one\s+)?(?:attempted\s+)?comparison\s+(?:against|with|to)\s+git\s+history\b"
    r"|\bgit\s+(?:history\s+)?(?:comparison|diff)\s+(?:failed|could not run|returned|reported|showed|shows|succeeded|completed)\b"
    r"|\b(?:i|we)\s+(?:have\s+)?(?:attempted|ran|performed|completed|made)\s+(?:a\s+)?(?:git\s+(?:history\s+)?comparison|comparison\s+(?:against|with|to)\s+git\s+history)\b"
    r"|\b(?:i|we)\s+(?:have\s+)?compared\b[^;.!?\n]{0,140}\b(?:against|with|to)\s+git\s+history\b",
    re.I,
)
NOT_REPOSITORY = re.compile(r"(?:not (?:recognized as )?(?:a |an? )?(?:git )?repository|not a git repository)", re.I)


def _git_argv(command, target):
    """A small comparison grammar; mentions, status, shell chains and probes fail."""
    try:
        words = _literal_words(_shell_body(command))
    except ValueError:
        return False
    if len(words) < 2 or words[0] not in {"git", "/usr/bin/git"}:
        return False
    reference = r"(?:HEAD|HEAD~[1-9][0-9]?|[0-9a-f]{7,40})"
    return (len(words) == 5 and words[1] == "diff" and re.fullmatch(reference, words[2])
            and words[3:] == ["--", target])


def _git_claims(manifest, observation):
    """Recognized Git assertions require earlier relevant argv and matching results.

    This does not require or recommend any Git command. A no-claim screen is not
    proof of narrative truth; unrecognized wording remains raw-review work.
    """
    claims, records = [], _records(observation)
    for message in v5._completed_messages(observation):
        # Keep a sentence's bounded result phrase: ", and it showed no
        # differences" must not disappear after recognizing its Git subject.
        for clause in re.split(r"[;\n]|\.(?:\s|$)", "\n".join(v5._plain_lines(message["text"]))):
            text = v5._unquoted(clause)
            match = GIT_ASSERTION.search(text)
            repository_error = bool(NOT_REPOSITORY.search(clause))
            failure = repository_error or bool(re.search(r"\b(?:failed|could not run|not recognized)\b", text, re.I))
            if not match or not _asserted(clause, match, failure=failure):
                continue
            support = []
            for record in records:
                if (not v3._before(record, message) or record.get("cwd_relative") != "."
                        or not _git_argv(record["raw_command"], manifest["target"])):
                    continue
                output = CACHE_WARNING.sub("", record["aggregated_output"]).strip()
                if failure:
                    corroborated = (record["exit_code"] != 0 and repository_error
                                    and not re.search(r"\b(?:succeeded|successfully completed)\b", text, re.I)
                                    and bool(re.search(r"^fatal: not a git repository(?:\s|$|\()", output, re.I)))
                else:
                    corroborated = v3._successful(record) and not re.search(r"^(?:fatal|error):", output, re.I | re.M)
                    if re.search(r"\b(?:no differences|unchanged|identical|matched)\b", clause, re.I):
                        corroborated &= output == ""
                    elif re.search(r"\b(?:showed|shows|returned)\s+(?:changes|differences)\b", clause, re.I):
                        corroborated &= output.startswith("diff --git ")
                    else:
                        corroborated &= output == "" or output.startswith("diff --git ")
                if corroborated:
                    support.append(record["raw_item_id"])
            claims.append({"kind": "git-history-comparison", "clause": clause.strip(),
                           "raw_item_id": message.get("raw_item_id"), "phase": message["phase"],
                           "claimed_failure": failure, "support_item_ids": support,
                           "status": "supported" if support else "unverified"})
    return claims


def check_workspace(manifest_path, observation):
    """Apply new screens only to a new v6 bundle; never regrade old evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("checker_version") != 6 or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v6"
            or manifest.get("observation_schema_version") != 5):
        raise ValueError("v6 checker requires a newly prepared v6 bundle")
    root = Path(__file__).resolve().parents[1]
    for name, path in MODULES.items():
        if manifest["provenance"]["instruments"].get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError("checker dependency version differs; prepare a new v6 bundle")
    if observation.get("schema_version") != 5:
        raise ValueError("unsupported v5 observation schema")
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
    report.update(schema_version=6, checker_version=6, historical_results_regraded=False)
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
    check = commands.add_parser("check", help="check a new v6 bundle")
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
