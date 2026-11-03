"""Versioned offline checks for the two-case OPT-004 fidelity follow-up.

The v1 checker, fixtures, reports and rubric remain immutable. This version
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


PILOT = "evaluations/workflow-fidelity-v2"
CHECKER = "harnessmith/workflow_fidelity_v2.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v3.md"
MODULES = {
    "checker.py": "harnessmith/workflow_fidelity.py",
    "checker-v2.py": CHECKER,
    "router-experiment.py": "harnessmith/router_experiment.py",
    "trace-v1.py": "harnessmith/workflow_trace.py",
    "trace-v2.py": "harnessmith/workflow_trace_v2.py",
}
NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
NUMBER = r"(?:\d+|" + "|".join(NUMBER_WORDS) + r")"
DESCRIPTORS = r"(?:(?:new|unchecked|checklist|requirements[- ]quality|security)\s+)*"
COUNT = re.compile(
    r"\b(?P<count>" + NUMBER + r")\s+" + DESCRIPTORS + r"(?:items|questions)\b"
    r"|\b(?:new\s+)?(?:items?|questions?)(?:\s+count)?\s*:\s*(?P<label>"
    + NUMBER
    + r")\b",
    re.I,
)
NON_COMPLETION = re.compile(
    r"\b(?:not|never|no|unable|cannot|can't|didn't|haven't|hasn't|failed|fail|"
    r"will|would|should|could|may|might|plan|plans|planned|planning|intend|"
    r"intended|expect|expected|want|requested|request|must|need|needs|if)\b",
    re.I,
)


def prepare_pilot(repository_root, output):
    """Prepare exactly two new router-v2 workspaces, without any live calls."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (
        config.get("schema_version") != 2
        or config.get("pilot_id") != "opt-004-workflow-fidelity-v2"
        or config.get("model") != "gpt-6-luna"
        or config.get("reasoning_effort") != "low"
        or config.get("repetitions") != 1
        or config.get("strategies") != ["router-v2"]
        or [
            (c["id"], c["new_items"], c["first_id"], c["overlay"])
            for c in config["cases"]
        ]
        != [("append", 3, 8, "append"), ("hooks", 4, 1, "hooks")]
    ):
        raise ValueError("unsupported v2 pilot design; version a changed design")
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
        session_id = case["id"] + "-router-v2"
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
            "checker_version": 2,
            "pilot_id": config["pilot_id"],
            "session_id": session_id,
            "case": case["id"],
            "strategy": "router-v2",
            "evidence_kind": "offline-preparation",
            "model": config["model"],
            "reasoning_effort": config["reasoning_effort"],
            "target": target,
            "new_items": case["new_items"],
            "first_id": case["first_id"],
            "baseline_target_hex": files.get(target, b"").hex(),
            "baseline": {p: v1._sha(data) for p, data in files.items()},
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
                "recipe_status": "not-applicable: authored router-v2 redesign",
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
        "schema_version": 2,
        "checker_version": 2,
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


def _final_report(output, target, count, append):
    """Recognize a bounded completed-report grammar, never numbers in a path."""
    if target not in output:
        return False
    cleaned = output.replace(target, " artifactpath ").lower()
    cleaned = re.sub(r"[`*_]", "", cleaned)
    # A label or count in another sentence is allowed after a completed action;
    # a plan, conditional or negated clause cannot supply either fact.
    clauses = [part.strip() for part in re.split(r"[\n;.!]+", cleaned) if part.strip()]
    completed = [part for part in clauses if not NON_COMPLETION.search(part)]
    operation = r"\bappended\b" if append else r"\bcreated\b"
    if not any(re.search(operation, part) for part in completed) or not any(
        "artifactpath" in part for part in completed
    ):
        return False
    wrong_operation = r"\bcreated\b" if append else r"\bappended\b"
    if any(
        re.search(wrong_operation, part)
        and ("artifactpath" in part or COUNT.search(part))
        for part in completed
    ):
        return False
    counts = []
    for part in completed:
        for match in COUNT.finditer(part):
            value = match.group("count") or match.group("label")
            counts.append(int(value) if value.isdigit() else NUMBER_WORDS[value])
    return (
        bool(counts)
        and all(value == count for value in counts)
        and all(
            re.search(r"\b" + word + r"\b", cleaned)
            for word in ("standard", "reviewer", "security")
        )
        and bool(re.search(r"\b(?:pr|pull request)\b", cleaned))
    )


def _item_topics(line):
    # Traceability/quality labels do not supply the question's subject.
    text = line.split("[", 1)[0].lower()
    topics = set()
    if re.search(r"role|permission|authoriz", text) and re.search(
        r"workspace|tenant", text
    ):
        topics.add("authorization")
    if re.search(r"expir", text) and re.search(
        r"measur|quantif|duration|interval|lifetime|ttl|time\s*limit|timeframe|period|deadline|clock",
        text,
    ):
        topics.add("expiration")
    if (
        re.search(r"expir", text)
        and re.search(r"reus", text)
        and re.search(r"outcome|behavio[u]?r|handling|response|happen", text)
    ):
        topics.add("outcomes")
    if re.search(r"retention|deletion", text):
        topics.add("retention")
    return topics


def check_workspace(manifest_path, observation):
    """Evaluate only a newly prepared v2 bundle; never mutate prior evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (
        manifest.get("checker_version") != 2
        or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v2"
    ):
        raise ValueError("v2 checker requires a newly prepared v2 bundle")
    expected = manifest["provenance"]["instruments"]
    root = Path(__file__).resolve().parents[1]
    for name, path in MODULES.items():
        if expected.get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError(
                "checker dependency version differs; prepare a new v2 bundle"
            )
    if observation.get("schema_version") not in (1, 2):
        raise ValueError("unsupported v2 observation schema")
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
    allocations = [_item_topics(line) for _, _, line in items]
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
                "detail": "Synthetic keyword screen requires one distinct item per requested topic; meaning and invented policy still require review.",
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
    # v2 reports report-shape/Gap-marker checks as formatting. Remove the frozen
    # helper's older report check rather than retaining contradictory dimensions.
    workflow = report["dimensions"]["workflow"]
    workflow["checks"] = [
        check for check in workflow["checks"] if check["name"] != "final-report"
    ]
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
    report["schema_version"] = 2
    report["checker_version"] = 2
    report["automated_checks_passed"] = all(
        check["passed"]
        for dimension in report["dimensions"].values()
        for check in dimension.get("checks", [])
    )
    report["historical_results_regraded"] = False
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
        "check", help="check a new v2 artifact and retained observations"
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
