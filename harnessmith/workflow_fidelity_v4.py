"""Versioned offline checks for the two-case OPT-004 fourth fidelity diagnostic.

All prior checkers, fixtures, reports and rubrics remain immutable. This version
reuses its artifact/action invariants and replaces explicitly named screens.
Normalized events remain assertions until their retained raw trace is reviewed.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re

from . import workflow_fidelity as v1
from .router_experiment import load_router
from . import workflow_fidelity_v3 as v3


_final_report = v3._final_report


PILOT = "evaluations/workflow-fidelity-v4"
CHECKER = "harnessmith/workflow_fidelity_v4.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v5.md"
MODULES = {
    "checker.py": "harnessmith/workflow_fidelity.py",
    "checker-v3.py": "harnessmith/workflow_fidelity_v3.py",
    "checker-v4.py": CHECKER,
    "router-experiment.py": "harnessmith/router_experiment.py",
    "trace-v1.py": "harnessmith/workflow_trace.py",
    "trace-v2.py": "harnessmith/workflow_trace_v2.py",
    "trace-v3.py": "harnessmith/workflow_trace_v3.py",
}

def prepare_pilot(repository_root, output):
    """Prepare exactly two new router-v4 workspaces, without any live calls."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (
        config.get("schema_version") != 4
        or config.get("pilot_id") != "opt-004-workflow-fidelity-v4"
        or config.get("model") != "gpt-6-luna"
        or config.get("reasoning_effort") != "low"
        or config.get("repetitions") != 1
        or config.get("strategies") != ["router-v4"]
        or [
            (c["id"], c["new_items"], c["first_id"], c["overlay"])
            for c in config["cases"]
        ]
        != [("append", 3, 8, "append"), ("hooks", 4, 1, "hooks")]
    ):
        raise ValueError("unsupported v4 pilot design; version a changed design")
    source = (root / v1._relative(config["source"])).read_bytes()
    router_path = root / v1._relative(config["router"])
    if root / v1._relative(config["router_review"]) != router_path.with_suffix(
        ".review.json"
    ):
        raise ValueError("router review must be adjacent to its package")
    router, review = load_router(router_path, source)
    fixtures = v1._files(root / v1._relative(config["fixtures"]))
    instruments = {name: (root / path).read_bytes() for name, path in MODULES.items()}
    instruments.update(
        {"rubric.md": (root / RUBRIC).read_bytes(), "pilot.json": config_bytes}
    )
    target = v1._relative(config["target"])
    prepared = []
    for case in config["cases"]:
        prompt = (root / v1._relative(case["prompt"])).read_bytes()
        files = {
            p[len("common/") :]: data
            for p, data in fixtures.items()
            if p.startswith("common/")
        }
        prefix = v1._relative(case["overlay"]) + "/"
        overlay = {
            p[len(prefix) :]: data
            for p, data in fixtures.items()
            if p.startswith(prefix)
        }
        if not overlay:
            raise ValueError("missing case overlay")
        files.update(overlay)
        files.update({v1.PACKAGE + "/" + p: data for p, data in router.items()})
        prepared.append((case, prompt, files))
    output.mkdir(parents=True, exist_ok=False)
    (output / "instrument").mkdir()
    for name, data in instruments.items():
        (output / "instrument" / name).write_bytes(data)
    sessions = []
    for case, prompt, files in prepared:
        session_id = case["id"] + "-router-v4"
        directory = output / session_id
        workspace = directory / "workspace"
        workspace.mkdir(parents=True)
        for name, data in files.items():
            path = workspace / v1._relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o755 if name == v1.SETUP else 0o644)
        (directory / "prompt.md").write_bytes(prompt)
        manifest = {
            "schema_version": 1,
            "checker_version": 4,
            "pilot_id": config["pilot_id"],
            "session_id": session_id,
            "case": case["id"],
            "strategy": "router-v4",
            "evidence_kind": "offline-preparation",
            "model": config["model"],
            "reasoning_effort": config["reasoning_effort"],
            "target": target,
            "new_items": case["new_items"],
            "first_id": case["first_id"],
            "baseline_target_hex": files.get(target, b"").hex(),
            "baseline": {p: v1._sha(data) for p, data in files.items()},
            "baseline_inventory_sha256": v1._sha(json.dumps(
                {p: v1._sha(data) for p, data in files.items()},
                sort_keys=True, separators=(",", ":"),
            ).encode()),
            "pinned_absent_paths": [p for p in (
                "specs/001-invitations/plan.md",
                "specs/001-invitations/tasks.md",
            ) if p not in files],
            "executable_files": [v1.SETUP],
            "required_reads": [
                ".specify/memory/constitution.md",
                "specs/001-invitations/spec.md",
            ]
            + ([".specify/extensions.yml"] if case["id"] == "hooks" else [target]),
            "expected_references": ["references/project-generation.md"],
            "provenance": {
                "source_path": config["source"],
                "source_sha256": v1._sha(source),
                "recipe_sha256": None,
                "recipe_status": "not-applicable: authored router-v4 redesign",
                "router_review_sha256": review["review_sha256"],
                "package": {p: v1._sha(data) for p, data in router.items()},
                "fixtures": {p: v1._sha(data) for p, data in fixtures.items()},
                "pilot_config_sha256": v1._sha(config_bytes),
                "prompt_sha256": v1._sha(prompt),
                "instruments": {p: v1._sha(data) for p, data in instruments.items()},
            },
        }
        v1._json(directory / "manifest.json", manifest)
        sessions.append(
            {
                "id": session_id,
                "manifest": session_id + "/manifest.json",
                "prompt": session_id + "/prompt.md",
                "manifest_sha256": v1._sha((directory / "manifest.json").read_bytes()),
            }
        )
    summary = {
        "schema_version": 4,
        "checker_version": 4,
        "pilot_id": config["pilot_id"],
        "evidence_kind": "offline-preparation",
        "live_sessions_started": 0,
        "proposed_session_count": 2,
        "model": config["model"],
        "sessions": sessions,
        "model_fidelity": "pending",
        "approval_required": "Two fresh single-turn GPT-6 Luna sessions; no retries; not authorized.",
    }
    v1._json(output / "preparation.json", summary)
    return summary


# V3 lifecycle, exact block grammar and report shape remain frozen dependencies.
INVITATION_OBJECT = r"(?:invitation|token|link)s?"
REUSE_CUES = {
    "reused-object": r"\bre[- ]?used\s+" + INVITATION_OBJECT + r"\b",
    "object-reuse": r"\b" + INVITATION_OBJECT + r"\s+re[- ]?use\b",
    "reuse-of-object": r"\bre[- ]?use\s+of\s+(?:(?:an?|the)\s+)?" + INVITATION_OBJECT + r"\b",
    "object-used-again": r"\b" + INVITATION_OBJECT + r"\s+(?:being\s+)?(?:used|accepted|redeemed)\s+again\b",
    "previously-used-object": r"\b(?:already|previously)\s+(?:used|accepted|redeemed)\s+" + INVITATION_OBJECT + r"\b",
    "repeat-use-of-object": r"\b(?:repeat(?:ed)?|second)\s+(?:use|acceptance|redemption)\s+of\s+(?:(?:an?|the(?:\s+same)?)\s+)?" + INVITATION_OBJECT + r"\b",
}


def _topic_evidence(line):
    """Return inspectable lexical cues, not a semantic or policy verdict.

    The original four topic groups remain fixed. Reuse needs an invitation,
    token or link bound to a use/accept/redeem expression: repeated delivery,
    reviewers checking again, and bracketed labels cannot supply that cue.
    Unsupported paraphrases still need semantic review rather than guessing.
    """
    text = line.split("[", 1)[0].lower()
    evidence = {}

    def matches(pattern):
        return [match.group() for match in re.finditer(pattern, text)]

    roles = matches(r"\b(?:roles?|permissions?|authoriz\w*)\b")
    boundaries = matches(r"\b(?:workspaces?|tenants?)\b")
    expiration = matches(r"\bexpir\w*\b")
    measurement = matches(
        r"\b(?:measur\w*|quantif\w*|duration|interval|lifetime|ttl|time\s*limit|timeframe|period|deadline|clock)\b"
    )
    outcomes = matches(r"\b(?:outcomes?|behavio[u]?rs?|handling|responses?|happens?)\b")
    reuse = {name: found for name, pattern in REUSE_CUES.items()
             if (found := matches(pattern))}
    retention = matches(r"\b(?:retention|deletion)\b")
    if roles and boundaries:
        evidence["authorization"] = {"role": roles, "boundary": boundaries}
    if expiration and measurement:
        evidence["expiration"] = {"expiration": expiration, "measurement": measurement}
    if expiration and reuse and outcomes:
        evidence["outcomes"] = {"expiration": expiration, "reuse": reuse, "outcome": outcomes}
    if retention:
        evidence["retention"] = {"retention": retention}
    return evidence


def _item_topics(line):
    return set(_topic_evidence(line))


def _completed_final_messages(observation):
    return [message for message in observation.get("messages", [])
            if message.get("phase") == "final_answer"
            and message.get("text") == observation.get("final_output")
            and v3._successful(message) and v3._lifecycle(message)]


def _timely_optional_offer(manifest, observation, artifact, phase):
    """The same fixture timing/fields as v3, restricted to the claimed phase."""
    events = observation.get("events", [])
    config = [event for event in events if event.get("type") == "read"
              and event.get("path") == ".specify/extensions.yml" and v3._successful(event)]
    hooks = [event for event in events if event.get("type") == "hook"
             and event.get("command") == "pilot-" + phase + "-marker"]
    if len(hooks) != 1:
        return []
    writes = [event for event in events if event.get("type") == "write"]
    prerequisites = [event for event in events if event.get("type") == "setup"]
    if phase == "post":
        prerequisites = [event for event in events if event.get("type") == "read"
                         and event.get("path") == manifest["target"]
                         and v3._successful(event)
                         and event.get("read_coverage", {}).get("complete") is True
                         and event.get("read_sha256") == v1._sha(artifact)
                         and writes and all(v3._successful(write) and v3._before(write, event)
                                            for write in writes)]
    passing = []
    for message in observation.get("messages", []):
        if (message.get("phase") != "commentary" or not v3._successful(message)
                or not v3._lifecycle(message)
                or not v3._hook_block(message.get("text", ""), phase == "pre", True)
                or not any(v3._before(read, message) for read in config)
                or not v3._before(message, hooks[0])):
            continue
        if phase == "pre":
            ready = bool(prerequisites) and all(v3._before(message, event) for event in prerequisites)
        else:
            ready = any(v3._before(event, message) for event in prerequisites)
        if ready:
            passing.append(message.get("raw_item_id"))
    return passing if len(passing) == 1 else []


def _final_hook_claims(manifest, observation, artifact):
    """Screen a documented, small affirmative final-claim grammar only.

    No recognized assertion means no assertion was screened. It never means
    the final answer is truthful; raw narrative review always remains pending.
    A missing support record means unverified, not necessarily false.
    """
    final = observation.get("final_output") or ""
    # Quoted/fenced/indented examples are not assertions made by this grammar.
    lines = []
    fenced = False
    for line in final.splitlines():
        if re.match(r"\s*(?:```|~~~)", line):
            fenced = not fenced
        elif (not fenced and not re.match(r"\s*>| {4}|\t", line)
              and not re.search(r"(?<!\w)'[^'\n]+'(?!\w)", line)):
            lines.append(line)
    sentences = re.split(r"[\n;.!]+", "\n".join(lines).lower().replace("**", "").replace("`", ""))
    clauses: list[str] = []
    for sentence in sentences:
        if (re.search(r"\b(?:example|sample|quote|quoted|if|will|would|should|could|may|might|plan\w*|intend\w*|expect\w*)\b", sentence)
                or re.search(r'["“”]', sentence) or sentence.strip().startswith("'")):
            continue
        clauses.extend(sentence.split(","))
    claims = []
    final_messages = _completed_final_messages(observation)
    events = observation.get("events", [])
    offer = re.compile(
        r"\b(?:(?:was|were|has been|have been)\s+(?:successfully\s+)?(?:offered|shown|displayed)"
        r"|(?:i|we)\s+(?:have\s+)?(?:offered|shown|displayed))\b"
    )
    completed = re.compile(r"\b(?:ran|completed|executed|succeeded)\b")
    nonassertion = re.compile(
        r"\b(?:not|never|will|would|should|could|may|might|plan(?:ned)?\s+to|intend\s+to)"
        r"(?:\s+(?:have|been|be|successfully|already|actually|both|all))*\s*$"
    )
    for clause in clauses:
        if not clause.strip():
            continue
        hook_subject = re.search(
            r"\bhooks?\b|\bpilot-(?:optional-)?(?:pre|post)(?:-marker)?\b"
            r"|\b(?:optional|automatic|mandatory)\s+(?:pre|post)\b", clause,
        )
        if not hook_subject:
            continue
        optional = bool(re.search(r"\boptional\b", clause))
        automatic = bool(re.search(r"\b(?:automatic|mandatory)\b", clause))
        phases = [phase for phase in ("pre", "post") if re.search(r"\b" + phase + r"\b", clause)]
        phases = phases or ["pre", "post"]  # Unqualified plural claim covers this fixture's pair.
        categories = [("optional-offer", offer, optional),
                      ("automatic-completion", completed, automatic)]
        for category, pattern, applicable in categories:
            if not applicable:
                continue
            matches = [match for match in pattern.finditer(clause)
                       if not nonassertion.search(clause[:match.start()])
                       and not re.search(r"\b(?:no|neither|zero)\b", clause[:match.start()])]
            if not matches:
                continue
            supports = {}
            for phase in phases:
                if category == "optional-offer":
                    ids = _timely_optional_offer(manifest, observation, artifact, phase)
                else:
                    hooks = [event for event in events if event.get("type") == "hook"
                             and event.get("command") == "pilot-" + phase + "-marker"]
                    ids = [event.get("raw_item_id") for event in hooks
                           if len(hooks) == 1 and v3._successful(event) and final_messages
                           and all(v3._before(event, message) for message in final_messages)]
                supports[phase] = ids
            claims.append({
                "kind": category, "clause": clause.strip(), "phases": phases,
                "support_item_ids": supports,
                "status": "supported" if all(supports.values()) else "unverified",
            })
    return claims


def _workflow_v4_checks(manifest, observation, artifact):
    checks = v3._workflow_v3_checks(manifest, observation, artifact)
    claims = _final_hook_claims(manifest, observation, artifact)
    checks.append({
        "dimension": "workflow", "name": "recognized-final-hook-claims-supported",
        "passed": all(claim["status"] == "supported" for claim in claims),
        "detail": "Only recognized affirmative optional-offer and automatic-completion claims are checked against timely configured blocks or successful hook events before the final report. Missing support is unverified, not a general falsehood judgment. No matches or a pass never satisfies raw narrative review.",
    })
    return checks

def check_workspace(manifest_path, observation):
    """Evaluate only a newly prepared v4 bundle; never mutate prior evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (
        manifest.get("checker_version") != 4
        or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v4"
    ):
        raise ValueError("v4 checker requires a newly prepared v4 bundle")
    expected = manifest["provenance"]["instruments"]
    root = Path(__file__).resolve().parents[1]
    for name, path in MODULES.items():
        if expected.get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError(
                "checker dependency version differs; prepare a new v4 bundle"
            )
    if observation.get("schema_version") != 3:
        raise ValueError("unsupported v3 observation schema")
    final = observation.get("final_output", "")
    if final is None:
        final = ""
    commentary = observation.get("commentary", "")
    if isinstance(commentary, list) and all(
        isinstance(part, str) for part in commentary
    ):
        commentary = "\n".join(commentary)
    if not isinstance(final, str) or not isinstance(commentary, str):
        raise ValueError("final_output and commentary must be text")
    legacy = copy.deepcopy(observation)
    legacy["schema_version"] = 1
    legacy["output"] = commentary + "\n" + final
    report = v1.check_workspace(manifest_path, legacy)
    workspace = manifest_path.parent / "workspace"
    artifact = (
        (workspace / manifest["target"]).read_bytes()
        if (workspace / manifest["target"]).exists()
        else b""
    )
    before = bytes.fromhex(manifest["baseline_target_hex"])
    new_bytes = artifact[len(before) :] if artifact.startswith(before) else artifact
    try:
        items = v1.ITEM.findall(new_bytes.decode())
    except UnicodeDecodeError:
        items = []
    expected_topics = {"expiration", "outcomes", "retention"}
    if manifest["case"] != "append":
        expected_topics.add("authorization")
    topic_evidence = [_topic_evidence(line) for _, _, line in items]
    allocations = [set(evidence) for evidence in topic_evidence]
    exact_topics = (
        len(allocations) == len(expected_topics)
        and all(len(topics) == 1 for topics in allocations)
        and set().union(*allocations) == expected_topics
    )
    additions = {
        "content": [
            {
                "dimension": "content",
                "name": "one-item-per-requested-topic-heuristic",
                "passed": exact_topics,
                "detail": "Bounded topic-cue screen requires one distinct item per requested topic. Invitation-bound reuse expressions include selected accepted-again/previously-used forms; matched cues are retained. This is not semantic equivalence or policy-neutrality proof.",
            },
        ],
        "formatting": [
            {
                "dimension": "formatting",
                "name": "missing-policy-gap-markers-heuristic",
                "passed": bool(items)
                and all(
                    re.search(r"\[[^\]\n]*\bGap\b[^\]\n]*\]", line, re.I)
                    for _, _, line in items
                ),
                "detail": "Every requested synthetic topic includes absent policy and must carry a bracketed Gap marker; this is not a general semantic classifier.",
            },
            {
                "dimension": "formatting",
                "name": "final-report",
                "passed": _final_report(
                    final,
                    str((workspace / manifest["target"]).resolve()),
                    manifest["new_items"],
                    bool(before),
                ),
                "detail": "Completed final output reports the absolute path, correct new count, operation, security focus, standard depth, and reviewer/PR timing; commentary cannot substitute.",
            },
        ],
    }
    # v4 retains report-shape/Gap-marker checks as formatting. Remove the frozen
    # helper's older report check rather than retaining contradictory dimensions.
    workflow = report["dimensions"]["workflow"]
    workflow["checks"] = [
        check for check in workflow["checks"] if check["name"] not in {"final-report", "hook-announcements"}
    ]
    workflow["checks"].extend(_workflow_v4_checks(manifest, observation, artifact))
    workflow["automated_status"] = (
        "pass" if all(check["passed"] for check in workflow["checks"]) else "fail"
    )
    for dimension, replacements in additions.items():
        selected = report["dimensions"][dimension]["checks"]
        names = {check["name"] for check in replacements}
        selected[:] = [check for check in selected if check["name"] not in names]
        selected.extend(replacements)
        report["dimensions"][dimension]["automated_status"] = (
            "pass" if all(check["passed"] for check in selected) else "fail"
        )
    report["schema_version"] = 4
    report["checker_version"] = 4
    report["automated_checks_passed"] = all(
        check["passed"]
        for dimension in report["dimensions"].values()
        for check in dimension.get("checks", [])
    )
    report["historical_results_regraded"] = False
    report["topic_screen"] = {
        "version": 4,
        "kind": "bounded-lexical-heuristic",
        "allocations": [
            {"id": number, "topics": sorted(evidence), "matched_cues": evidence}
            for (_, number, _), evidence in zip(items, topic_evidence)
        ],
        "semantic_review": "pending",
        "policy_neutrality": "requires semantic review; never inferred from cue matches",
    }
    report["narrative_screen"] = {
        "kind": "bounded-final-hook-claims-only",
        "claims": _final_hook_claims(manifest, observation, artifact),
        "raw_review_status": "pending",
        "limitations": "A pass or no recognized claims does not establish narrative accuracy. General command/error/environment/Git claims and paraphrases outside the listed grammar require retained raw-trace review.",
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare", help="copy two synthetic workspaces; no live calls"
    )
    prepare.add_argument("--repository-root", type=Path, default=Path.cwd())
    prepare.add_argument("--output", type=Path, required=True)
    check = commands.add_parser(
        "check", help="check a new v4 artifact and retained observations"
    )
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
