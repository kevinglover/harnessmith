"""Prospective v5 adapter: bounded reports, pre blocks and narration evidence.

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
from .router_experiment import load_router
from .workflow_trace import _shell_body
from .workflow_trace_v3 import CACHE_WARNING, _literal_words


PILOT = "evaluations/workflow-fidelity-v5"
CHECKER = "harnessmith/workflow_fidelity_v5.py"
RUBRIC = "evaluations/variants/router-quality-rubric-v6.md"
MODULES = {**v4.MODULES, "checker-v5.py": CHECKER,
           "trace-v4.py": "harnessmith/workflow_trace_v4.py"}


def prepare_pilot(repository_root, output):
    """Pin the actual inherited/new instruments for exactly two offline cases."""
    root, output = Path(repository_root), Path(output)
    config_bytes = (root / PILOT / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (config.get("schema_version") != 5
            or config.get("pilot_id") != "opt-004-workflow-fidelity-v5"
            or config.get("model") != "gpt-6-luna"
            or config.get("reasoning_effort") != "low"
            or config.get("repetitions") != 1
            or config.get("strategies") != ["router-v5"]
            or [(c["id"], c["new_items"], c["first_id"], c["overlay"])
                for c in config["cases"]]
            != [("append", 3, 8, "append"), ("hooks", 4, 1, "hooks")]):
        raise ValueError("unsupported v5 pilot design; version a changed design")
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
        session_id = case["id"] + "-router-v5"
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
            "schema_version": 1, "checker_version": 5, "observation_schema_version": 4,
            "pilot_id": config["pilot_id"], "session_id": session_id,
            "case": case["id"], "strategy": "router-v5",
            "evidence_kind": "offline-preparation", "model": config["model"],
            "reasoning_effort": config["reasoning_effort"], "target": target,
            "new_items": case["new_items"], "first_id": case["first_id"],
            "baseline_target_hex": files.get(target, b"").hex(), "baseline": baseline,
            "baseline_inventory_sha256": v1._sha(json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()),
            "pinned_absent_paths": [p for p in ("specs/001-invitations/plan.md", "specs/001-invitations/tasks.md") if p not in files],
            "executable_files": [v1.SETUP],
            "required_reads": [".specify/memory/constitution.md", "specs/001-invitations/spec.md"]
            + ([".specify/extensions.yml"] if case["id"] == "hooks" else [target]),
            "expected_references": ["references/project-generation.md"],
            "provenance": {
                "source_path": config["source"], "source_sha256": v1._sha(source),
                "recipe_sha256": None, "recipe_status": "not-applicable: authored router-v5 redesign",
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
        "schema_version": 5, "checker_version": 5, "observation_schema_version": 4,
        "pilot_id": config["pilot_id"], "evidence_kind": "offline-preparation",
        "live_sessions_started": 0, "proposed_session_count": 2, "model": config["model"],
        "sessions": sessions, "model_fidelity": "pending",
        "approval_required": "Two fresh single-turn GPT-6 Luna sessions; no retries; not authorized.",
    }
    v1._json(output / "preparation.json", summary)
    return summary


def _final_report(output, target, count, append):
    # Only this singular adjectival form is added to the frozen count grammar.
    # Transforming every occurrence preserves its wrong/contradictory count gate.
    output = re.sub(r"\b(" + v3.NUMBER + r")[ -](?:item|question)[ -]checklist\b",
                    r"\1 items checklist", output, flags=re.I)
    return v3._final_report(output, target, count, append)


def _plain_lines(text):
    fenced = False
    for line in text.splitlines():
        if re.match(r"\s*(?:```|~~~)", line):
            fenced = not fenced
        elif not fenced and not re.match(r"\s*>| {4}|\t", line):
            yield line


def _completed_messages(observation):
    return [m for m in observation.get("messages", [])
            if m.get("phase") in {"commentary", "final_answer"}
            and isinstance(m.get("text"), str) and v3._successful(m) and v3._lifecycle(m)]


def _pre_blocks(observation):
    blocks = []
    expected = {v3._hook_fields(True, optional)[0] for optional in (True, False)}
    for message in _completed_messages(observation):
        for line in _plain_lines(message["text"]):
            heading = line.strip().replace("**", "").replace("`", "")
            heading = re.sub(r"^(?:[-+*]|\d+[.)])\s+", "", heading)
            heading = re.sub(r"^#{1,6}\s+", "", heading)
            if re.match(r"(?:(?:Automatic|Optional)\s+)?Pre[- ]Hooks?\s*:", heading, re.I):
                blocks.append({"raw_item_id": message.get("raw_item_id"), "heading": heading,
                               "configured": heading in expected})
    return blocks


DIAGNOSTICS = {
    "unknown-synthetic-command": r"unknown synthetic command",
    "syntax-error": r"\bsyntaxerror\b",
    "permission-denied": r"permission denied",
    "operation-not-permitted": r"operation not permitted",
    "missing-file": r"no such file or directory",
    "missing-command": r"command not found",
    "traceback": r"traceback",
    "cache-diagnostic": r"(?:cache(?:[- ]write)?\s+(?:warning|diagnostic|error)s?|couldn't create cache file|xcrun_db)",
}
ERROR_ASSERTION = re.compile(
    r"\b(?:adapter|invocation|command|setup|script|python3?|shell|tool|attempt)\b"
    r"[^;.!?\n]{0,120}?\b(?P<verb>returned|reported|produced|raised|failed|errored)\b"
    r"|\b(?:i|we)\s+(?P<received>received|observed|saw|got)\b", re.I,
)
EXECUTION_ASSERTION = re.compile(
    r"\b(?:i|we)\s+(?:have\s+)?(?:successfully\s+)?(?:ran|executed|invoked)\s+"
    r"(?:`(?P<backtick>[^`\n]+)`|\"(?P<quoted>[^\"\n]+)\"|(?P<slash>/[\w.-]+))", re.I,
)
NONASSERTION = re.compile(
    r"\b(?:if|would|will|should|could|may|might|example|sample|quote[ds]?)\b"
    r"|\b(?:plan(?:s|ned|ning)?|intend(?:s|ed)?|expect(?:s|ed)?)\s+(?:to|that)\b"
    r"|\b(?:am|is|are|was|were)\s+expected\s+to\b", re.I,
)
NEGATION = re.compile(r"\b(?:not|never|no|neither|didn't|did not|hasn't|haven't)\b", re.I)


def _unquoted(text):
    # Keep offsets: quoted diagnostics may support an assertion outside quotes,
    # but a quoted entire assertion is not the agent asserting that proposition.
    return re.sub(r'`[^`]*`|"[^"\n]*"|“[^”\n]*”|(?<!\w)\x27[^\x27\n]+\x27(?!\w)',
                  lambda match: " " * len(match.group()), text)


def _command_subject(clause, command):
    """Require literal invocation argv, never a subject name in an argument.

    Only simple commands and the inherited bounded shell wrapper are supported.
    Unsupported compounds remain unverified even when they contain the name.
    """
    try:
        words = _literal_words(_shell_body(command))
        outer = _literal_words(command)
    except ValueError:
        return False
    lower = clause.lower()
    python = {"python", "python3", "/usr/bin/python", "/usr/bin/python3"}
    shell = {"sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh"}
    requirements = []
    if re.search(r"\b(?:setup|prerequisite)\b", lower):
        requirements.append(words[0] == v1.SETUP or (
            len(words) >= 2 and words[0] in python | shell and words[1] == v1.SETUP))
    if re.search(r"\badapter\b", lower):
        requirements.append(len(words) == 3 and words[0] in python
                            and words[1] == ".pilot/marker_hook.py")
    if re.search(r"\bpython3?\b", lower):
        requirements.append(words[0] in python)
    if re.search(r"\bshell\b", lower):
        requirements.append(outer[0] in shell)
    if re.search(r"\bscript\b", lower):
        script = words[1] if len(words) >= 2 and words[0] in python | shell else words[0]
        requirements.append(bool(re.search(r"\.(?:py|sh)$", script)))
    return all(requirements)


def _nonasserted(text, assertion):
    # Modal/example context before the predicate scopes the assertion. A later
    # factual qualification ("as expected") or future recovery does not erase it.
    return (bool(NONASSERTION.search(text[:assertion.end()]))
            or bool(re.search(r"\bif\b", text[assertion.end():], re.I)))


def _executed_literal(claimed, command):
    """Only exact simple argv or the fixture's exact adapter invocation counts.

    Literal output arguments, filenames, compound shells and dynamic command
    forms cannot prove that the named command itself was executed.
    """
    try:
        words = _literal_words(_shell_body(command))
        if claimed.startswith("/pilot-"):
            return (len(words) == 3 and words[0] in {"python3", "/usr/bin/python3"}
                    and words[1] == ".pilot/marker_hook.py" and words[2] == claimed[1:])
        return words == _literal_words(claimed)
    except ValueError:
        return False


def _execution_error_claims(observation):
    """Screen only documented affirmative clauses against earlier command output.

    Missing matching evidence is unverified, not a generalized falsehood verdict.
    Completed messages alone are screened; deltas/promises/quotes cannot supply
    assertions or supporting execution results. Raw review remains mandatory.
    """
    records = observation.get("command_records", [])
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        raise ValueError("command_records must be a list of command objects")
    claims = []
    for message in _completed_messages(observation):
        clauses = re.split(r"[;\n]|\.(?:\s|$)|,\s*(?:but|and)\s+|\s+but\s+",
                           "\n".join(_plain_lines(message["text"])))
        earlier = [r for r in records if v3._lifecycle(r)
                   and r.get("lifecycle_valid") is True
                   and r.get("status") in {"completed", "failed"}
                   and type(r.get("exit_code")) is int
                   and isinstance(r.get("raw_command"), str)
                   and isinstance(r.get("aggregated_output"), str)
                   and v3._before(r, message)]
        for clause in clauses:
            unquoted = _unquoted(clause)
            if clause.strip().endswith("?"):
                continue
            assertion = ERROR_ASSERTION.search(unquoted)
            diagnostics = {name: match for name, pattern in DIAGNOSTICS.items()
                           if (match := re.search(pattern, clause, re.I))}
            if (assertion and diagnostics and not _nonasserted(unquoted, assertion)
                    and not NEGATION.search(unquoted[:assertion.end()])
                    and not NEGATION.search(unquoted[assertion.end():min(m.start() for m in diagnostics.values())])):
                failed = (assertion.group("verb") or "").lower() in {"failed", "errored"}
                support = []
                for record in earlier:
                    output = record["aggregated_output"]
                    clean = CACHE_WARNING.sub("", output)
                    matches = all(re.search(DIAGNOSTICS[name], output, re.I) for name in diagnostics)
                    failure = record["exit_code"] != 0 or any(
                        name != "cache-diagnostic" and re.search(DIAGNOSTICS[name], clean, re.I)
                        for name in diagnostics)
                    if (matches and (not failed or failure)
                            and _command_subject(unquoted[assertion.start():assertion.end()], record["raw_command"])):
                        support.append(record["raw_item_id"])
                claims.append({"kind": "execution-error", "clause": clause.strip(),
                               "diagnostics": sorted(diagnostics), "support_item_ids": support,
                               "raw_item_id": message.get("raw_item_id"), "phase": message["phase"],
                               "status": "supported" if support else "unverified"})
            execution = EXECUTION_ASSERTION.search(clause)
            if (execution and re.search(r"\b(?:ran|executed|invoked)\b", unquoted[execution.start():execution.end()], re.I)
                    and not _nonasserted(unquoted, execution)
                    and not NEGATION.search(unquoted[:execution.start()])):
                command = next(value for value in execution.groupdict().values() if value)
                successful = bool(re.search(r"\bsuccessfully\b", execution.group(), re.I))
                support = [r["raw_item_id"] for r in earlier
                           if _executed_literal(command, r["raw_command"])
                           and (not successful or (r["status"] == "completed" and r["exit_code"] == 0
                                and not any(re.search(pattern, CACHE_WARNING.sub("", r["aggregated_output"]), re.I)
                                            for name, pattern in DIAGNOSTICS.items() if name != "cache-diagnostic")))]
                claims.append({"kind": "explicit-execution", "clause": clause.strip(),
                               "command": command, "support_item_ids": support,
                               "raw_item_id": message.get("raw_item_id"), "phase": message["phase"],
                               "status": "supported" if support else "unverified"})
    return claims


def _replace_checks(report, dimension, checks):
    selected = report["dimensions"][dimension]["checks"]
    names = {check["name"] for check in checks}
    selected[:] = [check for check in selected if check["name"] not in names] + checks
    report["dimensions"][dimension]["automated_status"] = "pass" if all(c["passed"] for c in selected) else "fail"


def check_workspace(manifest_path, observation):
    """Apply new screens only to a new v5 bundle; never regrade old evidence."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("checker_version") != 5 or manifest.get("pilot_id") != "opt-004-workflow-fidelity-v5"
            or manifest.get("observation_schema_version") != 4):
        raise ValueError("v5 checker requires a newly prepared v5 bundle")
    root = Path(__file__).resolve().parents[1]
    for name, path in MODULES.items():
        if manifest["provenance"]["instruments"].get(name) != v1._sha((root / path).read_bytes()):
            raise ValueError("checker dependency version differs; prepare a new v5 bundle")
    if observation.get("schema_version") != 4:
        raise ValueError("unsupported v4 observation schema")
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
        check("formatting", "final-report", _final_report(final, str(target.resolve()), manifest["new_items"], bool(before)), "Frozen completed-report grammar plus bounded singular item/question checklist modifiers; wrong, planned, negated and contradictory counts cannot supply a pass."),
    ])
    workflow = report["dimensions"]["workflow"]["checks"]
    workflow[:] = [c for c in workflow if c["name"] not in {"final-report", "hook-announcements"}]
    additions = v4._workflow_v4_checks(manifest, observation, artifact)
    blocks = _pre_blocks(observation)
    if manifest["case"] == "hooks":
        expected = {v3._hook_fields(True, optional)[0] for optional in (True, False)}
        correct = len(blocks) == 2 and {b["heading"] for b in blocks} == expected
        next(c for c in additions if c["name"] == "hook-announcements")["passed"] &= correct
        additions.append(check("workflow", "configured-pre-hook-blocks-only", correct,
                               "Exactly the two configured pre blocks may be emitted; invented or duplicate blocks are not repaired by later correct blocks."))
    claims = _execution_error_claims(observation)
    additions.append(check("workflow", "recognized-execution-error-claims-supported",
                           all(c["status"] == "supported" for c in claims),
                           "Bounded completed commentary/final assertions require matching earlier command records/output. Missing support is unverified; retained raw narrative review is always pending."))
    _replace_checks(report, "workflow", additions)
    report.update(schema_version=5, checker_version=5, historical_results_regraded=False)
    report["automated_checks_passed"] = all(c["passed"] for d in report["dimensions"].values() for c in d.get("checks", []))
    report["topic_screen"] = {"version": 4, "kind": "bounded-lexical-heuristic",
        "allocations": [{"id": number, "topics": sorted(e), "matched_cues": e} for (_, number, _), e in zip(items, evidence)],
        "semantic_review": "pending", "policy_neutrality": "requires semantic review; never inferred from cue matches"}
    report["narrative_screen"] = {"version": 5, "kind": "bounded-hook-and-execution-error-claims",
        "claims": v4._final_hook_claims(manifest, observation, artifact), "execution_error_claims": claims,
        "pre_hook_blocks": blocks, "raw_review_status": "pending",
        "limitations": "Only documented affirmative forms and completed messages are screened. Normalized command records are assertions requiring retained raw verification. No match or passing screen establishes narrative accuracy; all other claims and paraphrases require manual raw review."}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="prepare two offline cases; no live calls")
    prepare.add_argument("--repository-root", type=Path, default=Path.cwd())
    prepare.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check", help="check a new v5 bundle")
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
