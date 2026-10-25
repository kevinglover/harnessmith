"""Offline preparation and checks for the bounded OPT-004 workflow pilot.

No model client, credentials, project discovery, or live execution is provided.
Normalized observations are evaluator input, not independently verified traces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .router_experiment import load_router


PILOT = "evaluations/workflow-fidelity"
PACKAGE = ".agents/skills/speckit-checklist"
SETUP = ".specify/scripts/bash/check-prerequisites.sh"
SETUP_COMMAND = SETUP + " --json --template checklist-template"
MARKERS = ".pilot/events.jsonl"
RUBRIC = "evaluations/variants/router-quality-rubric-v2.md"
CHECKER = "harnessmith/workflow_fidelity.py"
ITEM = re.compile(r"^- \[([ xX])\] (CHK\d{3,}) (.+)$", re.M)
TRACEABILITY = re.compile(
    r"\[[^\]\n]*(?:Spec §|Gap|Ambiguity|Conflict|Assumption)[^\]\n]*\]"
)
QUALITY = re.compile(
    r"\[[^\]\n]*(?:Completeness|Clarity|Consistency|Measurability|Coverage|"
    r"Acceptance Criteria|Edge Case|Dependency|Dependencies|Ambiguity|"
    r"Conflict|Assumption|Traceability)[^\]\n]*\]"
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _relative(value):
    if not isinstance(value, str):
        raise ValueError("unsafe relative path")
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or str(path) != value
    ):
        raise ValueError("unsafe relative path")
    return value


def _files(root):
    """Reject links/nonregular files before reading a candidate tree."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("expected a real directory")
    paths = sorted(root.rglob("*"))
    if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths):
        raise ValueError("fixture/workspace contains a symlink or special file")
    return {
        p.relative_to(root).as_posix(): p.read_bytes() for p in paths if p.is_file()
    }


def _json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def prepare_pilot(repository_root, output):
    """Freeze six new workspaces; merely copy documents and synthetic adapters."""
    repository_root, output = Path(repository_root), Path(output)
    pilot_root = repository_root / PILOT
    config_bytes = (pilot_root / "pilot.json").read_bytes()
    config = json.loads(config_bytes)
    if (
        config.get("schema_version") != 1
        or config.get("model") != "gpt-6-luna"
        or config.get("repetitions") != 1
        or config.get("strategies") != ["canonical", "router"]
        or [c["id"] for c in config["cases"]] != ["create", "append", "hooks"]
    ):
        raise ValueError("unsupported pilot design; version a changed design")
    source = (repository_root / _relative(config["source"])).read_bytes()
    router, review = load_router(repository_root / _relative(config["router"]), source)
    fixtures = _files(pilot_root / "fixtures")
    instruments = {
        "checker.py": (repository_root / CHECKER).read_bytes(),
        "rubric.md": (repository_root / RUBRIC).read_bytes(),
        "pilot.json": config_bytes,
    }
    target = _relative(config["target"])
    packages = {"canonical": {"SKILL.md": source}, "router": router}
    prepared = []
    for index, case in enumerate(config["cases"]):
        prompt = (pilot_root / _relative(case["prompt"])).read_bytes()
        files = {
            p[len("common/") :]: data
            for p, data in fixtures.items()
            if p.startswith("common/")
        }
        if case["overlay"]:
            prefix = _relative(case["overlay"]) + "/"
            files.update(
                {
                    p[len(prefix) :]: data
                    for p, data in fixtures.items()
                    if p.startswith(prefix)
                }
            )
        order = ["canonical", "router"] if index % 2 == 0 else ["router", "canonical"]
        for strategy in order:
            package = packages[strategy]
            workspace_files = dict(files)
            workspace_files.update(
                {PACKAGE + "/" + p: data for p, data in package.items()}
            )
            prepared.append((case, strategy, prompt, workspace_files))
    # All source and review validation precedes output mutation.
    output.mkdir(parents=True, exist_ok=False)
    (output / "instrument").mkdir()
    for name, data in instruments.items():
        (output / "instrument" / name).write_bytes(data)
    sessions = []
    for case, strategy, prompt, files in prepared:
        session_id = case["id"] + "-" + strategy
        directory = output / session_id
        workspace = directory / "workspace"
        workspace.mkdir(parents=True)
        for name, data in files.items():
            path = workspace / _relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o755 if name == SETUP else 0o644)
        (directory / "prompt.md").write_bytes(prompt)
        manifest = {
            "schema_version": 1,
            "pilot_id": config["pilot_id"],
            "session_id": session_id,
            "case": case["id"],
            "strategy": strategy,
            "evidence_kind": "offline-preparation",
            "model": config["model"],
            "reasoning_effort": config["reasoning_effort"],
            "target": target,
            "new_items": case["new_items"],
            "first_id": case["first_id"],
            "baseline_target_hex": files.get(target, b"").hex(),
            "baseline": {p: _sha(data) for p, data in files.items()},
            "executable_files": [SETUP],
            "required_reads": [
                ".specify/memory/constitution.md",
                "specs/001-invitations/spec.md",
            ]
            + ([".specify/extensions.yml"] if case["id"] == "hooks" else [])
            + ([target] if case["id"] == "append" else []),
            "expected_references": ["references/project-generation.md"]
            if strategy == "router"
            else [],
            "provenance": {
                "source_path": config["source"],
                "source_sha256": _sha(source),
                "recipe_sha256": None,
                "recipe_status": "not-applicable: canonical source or authored router",
                "router_review_sha256": review["review_sha256"],
                "package": {p: _sha(data) for p, data in packages[strategy].items()},
                "fixtures": {p: _sha(data) for p, data in fixtures.items()},
                "pilot_config_sha256": _sha(config_bytes),
                "prompt_sha256": _sha(prompt),
                "instruments": {p: _sha(data) for p, data in instruments.items()},
            },
        }
        _json(directory / "manifest.json", manifest)
        sessions.append(
            {
                "id": session_id,
                "manifest": session_id + "/manifest.json",
                "prompt": session_id + "/prompt.md",
                "manifest_sha256": _sha((directory / "manifest.json").read_bytes()),
            }
        )
    summary = {
        "schema_version": 1,
        "pilot_id": config["pilot_id"],
        "evidence_kind": "offline-preparation",
        "live_sessions_started": 0,
        "proposed_session_count": len(sessions),
        "model": config["model"],
        "sessions": sessions,
        "model_fidelity": "pending",
        "approval_required": "Six fresh single-turn GPT-6 Luna sessions; no retries.",
    }
    _json(output / "preparation.json", summary)
    return summary


def check_workspace(manifest_path, observation):
    """Check artifacts plus asserted trace facts; never certify model fidelity.

    The caller must separately audit raw trace completeness and semantic quality.
    An external observation can name a retained trace, but a hash does not validate
    normalization or prove that its events caused the observed filesystem changes.
    """
    manifest_path = Path(manifest_path)
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    preparation = json.loads(
        (manifest_path.parent.parent / "preparation.json").read_bytes()
    )
    recorded = [s for s in preparation["sessions"] if s["id"] == manifest["session_id"]]
    if len(recorded) != 1 or recorded[0]["manifest_sha256"] != _sha(manifest_bytes):
        raise ValueError("manifest differs from prepared session")
    for name, expected in manifest["provenance"]["instruments"].items():
        actual = (
            manifest_path.parent.parent / "instrument" / _relative(name)
        ).read_bytes()
        if _sha(actual) != expected:
            raise ValueError("prepared evaluation instrument changed")
    if (
        _sha(Path(__file__).read_bytes())
        != manifest["provenance"]["instruments"]["checker.py"]
    ):
        raise ValueError("checker version differs; prepare a new pilot bundle")
    if (
        _sha((manifest_path.parent / "prompt.md").read_bytes())
        != manifest["provenance"]["prompt_sha256"]
    ):
        raise ValueError("prepared prompt changed")
    if manifest.get("schema_version") != 1 or observation.get("schema_version") != 1:
        raise ValueError("unsupported manifest/observation schema")
    kind = observation.get("evidence_kind")
    if kind not in ("offline-simulation", "externally-captured-observation"):
        raise ValueError("observation must explicitly declare its provenance")
    workspace = manifest_path.parent / "workspace"
    files = _files(workspace)
    target = _relative(manifest["target"])
    before = bytes.fromhex(manifest["baseline_target_hex"])
    artifact = files.get(target, b"")
    preserved = artifact.startswith(before)
    new_bytes = artifact[len(before) :] if preserved else artifact
    decode_ok = True
    try:
        text, new_text = artifact.decode("utf-8"), new_bytes.decode("utf-8")
    except UnicodeDecodeError:
        decode_ok = False
        text, new_text = "", ""
    items = ITEM.findall(new_text)
    all_items = ITEM.findall(text)
    events = observation.get("events", [])
    if not isinstance(events, list) or any(not isinstance(e, dict) for e in events):
        raise ValueError("observation events must be objects")
    checks = []

    def add(dimension, name, passed, detail):
        checks.append(
            {
                "dimension": dimension,
                "name": name,
                "passed": bool(passed),
                "detail": detail,
            }
        )

    baseline = manifest["baseline"]
    add(
        "workflow",
        "preserved-inputs",
        all(
            p == target or (p in files and _sha(files[p]) == sha)
            for p, sha in baseline.items()
        ),
        "All input fixture/package bytes remain unchanged.",
    )
    add(
        "workflow",
        "preserved-modes",
        all(
            bool((workspace / _relative(p)).stat().st_mode & 0o111)
            == (p in manifest["executable_files"])
            for p in files
        ),
        "Only the prepared setup stub has executable permission.",
    )
    allowed_new = {target} | ({MARKERS} if manifest["case"] == "hooks" else set())
    add(
        "workflow",
        "file-inventory",
        not (set(files) - set(baseline) - allowed_new),
        "Only the checklist and, for hooks, the marker log may be created.",
    )
    add(
        "workflow",
        "append-preserves-prefix",
        preserved,
        "Existing content, whitespace, IDs, and checkbox states are byte-preserved.",
    )
    add(
        "formatting",
        "item-count-and-ids",
        decode_ok
        and len(items) == manifest["new_items"]
        and [i[1] for i in items]
        == [
            "CHK%03d" % i
            for i in range(
                manifest["first_id"], manifest["first_id"] + manifest["new_items"]
            )
        ]
        and len({i[1] for i in all_items}) == len(all_items),
        "New items use exact unchecked-list syntax and consecutive unique IDs.",
    )
    checkbox_lines = re.findall(
        r"^\s*(?:[-*+]|\d+[.)])\s+\[[^\]]*\].*$", new_text, re.M
    )
    add(
        "formatting",
        "no-malformed-items",
        len(checkbox_lines) == len(items),
        "No extra/malformed checkbox items are hidden from the strict parser.",
    )
    add(
        "formatting",
        "new-items-unchecked",
        bool(items) and all(i[0] == " " for i in items),
        "New checkbox states belong to the reviewer.",
    )
    add(
        "formatting",
        "questions-and-dimensions",
        bool(items)
        and all("?" in line and QUALITY.search(line) for _, _, line in items),
        "Every new item is a question with a bracketed quality dimension.",
    )
    add(
        "formatting",
        "traceability",
        bool(items)
        and sum(bool(TRACEABILITY.search(line)) for _, _, line in items) / len(items)
        >= 0.8,
        "At least 80% of new items have traceability markers.",
    )
    lower_text = " ".join(text.lower().split())
    add(
        "formatting",
        "template-structure",
        all(
            token in lower_text
            for token in (
                "# security requirements checklist",
                "**purpose**:",
                "**created**:",
                "**ownership**:",
                "reviewer",
                "requirements quality",
                "## notes",
                "/speckit-implement",
                "does not modify markers",
            )
        )
        and bool(re.search(r"^## Requirement (?:Completeness|Clarity)$", text, re.M)),
        "Title, metadata, ownership, requirement category, and notes are retained.",
    )
    content = " ".join(i[2].lower() for i in items)
    topics = [r"expir", r"(?:expir|reus).*(?:reus|expir)", r"retention|deletion"]
    if manifest["case"] != "append":
        topics.extend([r"role|permission|authoriz", r"workspace|tenant"])
    add(
        "content",
        "requested-coverage-heuristic",
        all(re.search(t, content) for t in topics),
        "Keyword coverage is a screening heuristic; a reviewer must assess meaning.",
    )
    add(
        "content",
        "requirements-not-execution-heuristic",
        bool(items)
        and all(
            not re.match(
                r"(?:verify|test|confirm|check|click|run|execute)\b", line, re.I
            )
            and re.search(
                r"requirements?|spec(?:ification)?|documented|defined|specified|quantified",
                line,
                re.I,
            )
            and not re.search(
                r"works (?:properly|correctly)|functions as expected|returns? 200",
                line,
                re.I,
            )
            for _, _, line in items
        ),
        "Reject obvious execution tests; subtle invented policy still requires review.",
    )
    add(
        "workflow",
        "observation-completed",
        observation.get("completed") is True
        and observation.get("model") == manifest["model"],
        "Recorded session is completed on the proposed Luna model.",
    )
    supported = {"read", "setup", "hook", "write"}
    add(
        "workflow",
        "classified-events",
        all(e.get("type") in supported for e in events),
        "Unclassified operations fail; raw-trace completeness requires separate review.",
    )

    def complete(event):
        default_exit = 0 if event.get("type") == "write" else None
        return (
            event.get("status") == "completed"
            and event.get("exit_code", default_exit) == 0
        )

    add(
        "workflow",
        "successful-events",
        all(complete(e) for e in events),
        "Failed or incomplete reads, writes, setup and hooks cannot pass.",
    )
    reads = [e.get("path") for e in events if e.get("type") == "read" and complete(e)]
    prefix = PACKAGE + "/"
    references = [
        p[len(prefix) :]
        for p in reads
        if isinstance(p, str) and p.startswith(prefix) and p != prefix + "SKILL.md"
    ]
    add(
        "reference_behavior",
        "expected-reference-set",
        set(references) == set(manifest["expected_references"]),
        "Router reads project-generation only; canonical has no extracted references.",
    )
    add(
        "workflow",
        "required-context-reads",
        all(p in reads for p in manifest["required_reads"]),
        "Constitution, feature spec, and any configured hooks are read.",
    )
    allowed_reads = set(baseline) | allowed_new
    add(
        "workflow",
        "read-scope",
        all(p in allowed_reads for p in reads),
        "All recorded reads stay within fixture/package files.",
    )
    setups = [n for n, e in enumerate(events) if e.get("type") == "setup"]
    writes = [n for n, e in enumerate(events) if e.get("type") == "write"]
    setup_ok = (
        len(setups) == 1
        and complete(events[setups[0]])
        and (events[setups[0]].get("command") == SETUP_COMMAND)
    )
    add(
        "workflow",
        "setup-and-write-order",
        setup_ok
        and bool(writes)
        and all(events[n].get("path") == target for n in writes)
        and setups[0] < min(writes),
        "Read-only prerequisite/template setup precedes writes.",
    )
    add(
        "workflow",
        "context-before-write",
        bool(writes)
        and all(
            any(
                n < min(writes)
                and e.get("type") == "read"
                and complete(e)
                and e.get("path") == path
                for n, e in enumerate(events)
            )
            for path in manifest["required_reads"]
        ),
        "Required context and the existing append target are read before artifact writes.",
    )
    project_actions = [
        n
        for n, e in enumerate(events)
        if e.get("type") in {"setup", "hook", "write"}
        or (e.get("type") == "read" and not str(e.get("path", "")).startswith(prefix))
    ]
    for reference in manifest["expected_references"]:
        positions = [
            n
            for n, e in enumerate(events)
            if e.get("type") == "read"
            and complete(e)
            and e.get("path") == prefix + reference
        ]
        add(
            "reference_behavior",
            "reference-before-project-actions",
            bool(positions)
            and bool(project_actions)
            and min(positions) < min(project_actions),
            "Router generation guidance is loaded before any project action.",
        )
    hooks = [(n, e) for n, e in enumerate(events) if e.get("type") == "hook"]
    output = observation.get("output", "")
    if not isinstance(output, str):
        raise ValueError("output must be text")
    if manifest["case"] == "hooks":
        expected = ["pilot-pre-marker", "pilot-post-marker"]
        hook_ok = [e.get("command") for _, e in hooks] == expected and all(
            complete(e) for _, e in hooks
        )
        add(
            "workflow",
            "automatic-hook-order",
            hook_ok
            and setup_ok
            and bool(writes)
            and hooks[0][0] < setups[0] < min(writes) <= max(writes) < hooks[1][0],
            "Automatic pre finishes before setup; automatic post follows all writes.",
        )
        extension_positions = [
            n
            for n, e in enumerate(events)
            if e.get("type") == "read" and e.get("path") == ".specify/extensions.yml"
        ]
        add(
            "workflow",
            "hook-config-before-execution",
            hook_ok
            and bool(extension_positions)
            and min(extension_positions) < hooks[0][0],
            "Hook configuration is read before invocation.",
        )
        try:
            markers = [
                json.loads(line)
                for line in files.get(MARKERS, b"").decode().splitlines()
            ]
        except (ValueError, UnicodeDecodeError):
            markers = []
        expected_markers = [
            {"command": expected[0], "target_exists": False, "target_sha256": None},
            {
                "command": expected[1],
                "target_exists": True,
                "target_sha256": _sha(artifact),
            },
        ]
        add(
            "workflow",
            "hook-marker-artifacts",
            markers == expected_markers and bool(artifact),
            "Exactly pre-absence and post-final-hash markers corroborate the trace facts.",
        )
        add(
            "workflow",
            "hook-announcements",
            all(
                t in output
                for t in (
                    "Automatic Pre-Hook",
                    "Automatic Hook",
                    "EXECUTE_COMMAND: pilot-pre-marker",
                    "EXECUTE_COMMAND: pilot-post-marker",
                    "Optional Pre-Hook",
                    "Optional Hook",
                    "To execute: `/pilot-optional-pre`",
                    "To execute: `/pilot-optional-post`",
                )
            ),
            "Mandatory execution and optional offer blocks use normalized command IDs.",
        )
    else:
        add(
            "workflow",
            "no-unregistered-hooks",
            not hooks and MARKERS not in files,
            "No synthetic or real hook runs without configuration.",
        )
    absolute_target = str((workspace / target).resolve())
    # Paths can themselves contain case names and digits; they are not a report
    # of the operation or item count.
    lower_output = output.replace(absolute_target, "").lower()
    count_pattern = (
        r"\b%d\s+(?:new\s+)?(?:checklist\s+)?(?:items|questions)\b"
        r"|\b(?:new\s+)?(?:item|question)\s+count\s*:\s*%d\b"
    ) % (manifest["new_items"], manifest["new_items"])
    add(
        "workflow",
        "final-report",
        absolute_target in output
        and re.search(count_pattern, lower_output)
        and re.search(r"\bappended\b" if before else r"\bcreated\b", lower_output)
        and all(
            re.search(r"\b" + t + r"\b", lower_output)
            for t in ("standard", "reviewer", "security")
        )
        and re.search(r"\b(?:pr|pull request)\b", lower_output),
        "Report includes absolute path, new count, operation, focus, depth, actor/timing.",
    )
    dimensions = {}
    for dimension in ("content", "formatting", "reference_behavior", "workflow"):
        selected = [c for c in checks if c["dimension"] == dimension]
        dimensions[dimension] = {
            "automated_status": "pass"
            if all(c["passed"] for c in selected)
            else "fail",
            "review_status": "pending"
            if dimension in ("content", "workflow")
            else "not-performed",
            "checks": selected,
        }
    dimensions["efficiency"] = {
        "status": "not-evaluated",
        "usage": observation.get("usage"),
        "note": "One repetition is diagnostic, not a savings estimate.",
    }
    return {
        "schema_version": 1,
        "pilot_id": manifest["pilot_id"],
        "session_id": manifest["session_id"],
        "evidence_kind": kind,
        "automated_checks_passed": all(c["passed"] for c in checks),
        "model_fidelity": "pending",
        "eligible_for_promotion": False,
        "trace_review": "pending: normalized event facts are not independently verified",
        "raw_trace": observation.get("raw_trace"),
        "manifest_sha256": _sha(manifest_bytes),
        "artifact_sha256": _sha(artifact) if artifact else None,
        "dimensions": dimensions,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare", help="copy six synthetic workspaces; no live calls"
    )
    prepare.add_argument("--repository-root", type=Path, default=Path.cwd())
    prepare.add_argument("--output", type=Path, required=True)
    check = commands.add_parser(
        "check", help="check artifacts and evaluator-supplied observations"
    )
    check.add_argument("manifest", type=Path)
    check.add_argument("observation", type=Path)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare_pilot(args.repository_root, args.output)
        print(json.dumps(result, indent=2))
        return 0
    if args.output.exists():
        parser.error("report output already exists")
    report = check_workspace(args.manifest, json.loads(args.observation.read_text()))
    _json(args.output, report)
    print(str(args.output))
    return 0 if report["automated_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
