"""O3 immutable mock stage runner: durable slots, pinned inputs, no retries.

This is offline transport qualification infrastructure, not live authorization.
A host normalizer is injected and its Python source is pinned with the stage.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import stat
import time

from .native_capture import AttemptJournal
from .native_contract import integrity_findings, parse_trajectory, usage_totals
from .native_transport import StdioCapture

INSTRUMENTATION = "native-stage-v1"
REQUIRED_ROLES = {"executable", "transport", "normalizer", "policy", "source",
                  "recipe", "package", "fixture", "contract", "capture", "stage"}


def inventory(path):
    """Exact local bytes/modes/link targets; directories include their entries."""
    root = Path(path)
    result = []

    def visit(item, name):
        info = item.lstat()
        row = dict(path=name, mode=stat.S_IMODE(info.st_mode))
        if stat.S_ISLNK(info.st_mode):
            row.update(kind="symlink", target=os.readlink(item))
        elif stat.S_ISREG(info.st_mode):
            row.update(kind="file", sha256=hashlib.sha256(item.read_bytes()).hexdigest())
        elif stat.S_ISDIR(info.st_mode):
            row.update(kind="directory")
        else:
            raise ValueError("unsupported pinned file")
        result.append(row)
        if row["kind"] == "directory":
            for child in sorted(item.iterdir()):
                visit(child, child.name if name == "." else name + "/" + child.name)
    visit(root, ".")
    return result


def pin(path, role):
    resolved = Path(path).resolve(strict=True)
    return dict(path=str(resolved), role=role, inventory=inventory(resolved))


def _blob(journal, value):
    return journal.blob((json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode())


def validate_stage(manifest, observer_factory, *, consumed_workspaces=()):
    if set(manifest) != {"schema_version", "stage_id", "mode", "trajectory", "pins",
                         "attempts", "ceilings", "normalization_policy", "environment"}:
        raise ValueError("stage has missing/unknown fields")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported stage version")
    if manifest["mode"] != "mock" or manifest["trajectory"].get("mode") != "mock":
        raise ValueError("native stages remain unqualified and disabled")
    if not isinstance(manifest["stage_id"], str) or not manifest["stage_id"].strip():
        raise ValueError("stage identity required")
    if not isinstance(manifest["normalization_policy"], dict):
        raise ValueError("normalization policy must be retained")
    environment = manifest["environment"]
    if (set(environment) != {"model", "effort", "permissions", "resources", "cache_policy"}
            or any(not environment[k] for k in environment)):
        raise ValueError("stage environment must be explicit")
    ceilings = manifest["ceilings"]
    if set(ceilings) != {"attempts", "threads", "task_turns", "deadline_seconds"}:
        raise ValueError("invalid stage ceilings")
    if any(type(ceilings[k]) is not int or ceilings[k] < 1 for k in ("attempts", "threads", "task_turns")):
        raise ValueError("invalid count ceiling")
    if (type(ceilings["deadline_seconds"]) not in (int, float)
            or not math.isfinite(ceilings["deadline_seconds"])
            or not 0 < ceilings["deadline_seconds"] <= 180):
        raise ValueError("invalid whole-trajectory deadline")
    attempts = manifest["attempts"]
    if not isinstance(attempts, list) or not attempts or len(attempts) > ceilings["attempts"]:
        raise ValueError("attempt ceiling exceeded")
    seen = set()
    workspaces: list[Path] = []
    for attempt in attempts:
        if set(attempt) != {"id", "workspace", "command", "env", "steps"}:
            raise ValueError("invalid attempt fields")
        identifier = attempt["id"]
        if (not isinstance(identifier, str) or not identifier
                or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in identifier)
                or identifier in seen):
            raise ValueError("attempt IDs must be unique safe names")
        seen.add(identifier)
        command = attempt["command"]
        if (not isinstance(command, list) or not command
                or not all(isinstance(s, str) and s for s in command)
                or not Path(command[0]).is_absolute()):
            raise ValueError("absolute executable and literal argv required")
        if not isinstance(attempt["env"], dict) or any(
                not isinstance(k, str) or not isinstance(v, str) for k, v in attempt["env"].items()):
            raise ValueError("explicit child environment required")
        if not Path(attempt["workspace"]).is_absolute() or not Path(attempt["workspace"]).is_dir():
            raise ValueError("existing absolute workspace required")
        workspace = Path(attempt["workspace"]).resolve()
        if any(workspace == old or workspace in old.parents or old in workspace.parents for old in workspaces):
            raise ValueError("each attempt requires a separate non-overlapping workspace")
        workspaces.append(workspace)
        if not isinstance(attempt["steps"], list) or not attempt["steps"]:
            raise ValueError("bounded protocol steps required")
        for step in attempt["steps"]:
            if set(step) != {"send", "until"} or not isinstance(step["send"], dict):
                raise ValueError("invalid protocol step")
            until = step["until"]
            if until is not None and (not isinstance(until, dict) or not until
                    or not set(until).issubset({"id", "method"})):
                raise ValueError("invalid protocol boundary")
    pins = manifest["pins"]
    if not isinstance(pins, list) or not REQUIRED_ROLES.issubset({p["role"] for p in pins}):
        raise ValueError("required stage pins missing")
    for item in pins:
        if set(item) != {"path", "role", "inventory"} or not Path(item["path"]).is_absolute():
            raise ValueError("invalid pin")
        consumed = item["role"] == "fixture" and str(Path(item["path"]).resolve()) in consumed_workspaces
        if not consumed and inventory(item["path"]) != item["inventory"]:
            raise ValueError("pinned input changed: " + item["role"])
        if item["role"] == "policy" and json.loads(Path(item["path"]).read_bytes()) != manifest["normalization_policy"]:
            raise ValueError("normalization policy pin does not match manifest")
    bound = {(p["role"], str(Path(p["path"]).resolve())) for p in pins}
    from . import native_capture, native_contract, native_transport
    for role, path in (("stage", __file__), ("capture", native_capture.__file__),
                       ("contract", native_contract.__file__), ("transport", native_transport.__file__),
                       ("normalizer", inspect.getsourcefile(observer_factory))):
        if path is None or (role, str(Path(path).resolve())) not in bound:
            raise ValueError("executed instrument is not pinned: " + role)
    for attempt in attempts:
        for role, path in (("executable", attempt["command"][0]), ("fixture", attempt["workspace"])):
            if (role, str(Path(path).resolve())) not in bound:
                raise ValueError("attempt input is not pinned: " + role)
    parse_trajectory(dict(manifest["trajectory"], trajectory_id="preflight",
                         capture_status="incomplete", capture_elapsed_ms=0, events=[], usage=[]))


def _collect(directory, manifest, attempt, observer_factory, remaining):
    trace = dict(manifest["trajectory"], trajectory_id=attempt["id"],
                 capture_status="incomplete", capture_elapsed_ms=0, events=[], usage=[])
    journal = AttemptJournal(directory, dict(stage=manifest, attempt=attempt))
    observer = None
    error = None
    stop = time.monotonic() + manifest["ceilings"]["deadline_seconds"]
    captured = set()

    def accept(direction, frame):
        captured.add(frame.raw_ref)
        decoded = observer.observe(direction, frame.message(), frame.raw_ref, frame.elapsed_ms)
        journal.append("decoded", {"blob_ref": _blob(journal, decoded)})
        if not isinstance(decoded, dict) or set(decoded) != {"events", "usage"}:
            raise ValueError("normalizer must return events and usage")
        candidate = dict(trace, events=trace["events"] + decoded["events"],
                         usage=trace["usage"] + decoded["usage"])
        parse_trajectory(candidate)
        for record in decoded["events"] + decoded["usage"]:
            if record["raw_ref"] != frame.raw_ref:
                raise ValueError("normalizer backing is not the captured frame")
        for event in decoded["events"]:
            if event["origin"] != "mock" or event["elapsed_ms"] != frame.elapsed_ms:
                raise ValueError("normalizer clock/origin mismatch")
        trace.update(candidate)
        # Retain an over-limit observation before failing the stage.
        threads = sum(e["kind"] in {"thread.started", "thread.forked", "thread.resumed"} for e in trace["events"])
        turns = sum(e["kind"] == "turn.started" and e["data"]["turn_role"] == "task" for e in trace["events"])
        if threads > remaining["threads"] or turns > remaining["task_turns"]:
            raise ValueError("observed stage count ceiling exceeded")

    try:
        journal.snapshot(attempt["workspace"], "before")
        observer = observer_factory(manifest["normalization_policy"])
        if time.monotonic() >= stop:
            raise TimeoutError("attempt deadline exceeded before transport startup")
        with StdioCapture(journal, attempt["command"], cwd=attempt["workspace"],
                          env=attempt["env"], timeout=max(.001, stop - time.monotonic())) as client:
            requested_threads = requested_turns = 0
            for step in attempt["steps"]:
                method = step["send"].get("method")
                requested_threads += method in {"thread/start", "thread/fork", "thread/resume"}
                requested_turns += method == "turn/start"
                if requested_threads > remaining["threads"] or requested_turns > remaining["task_turns"]:
                    raise ValueError("requested stage count ceiling exceeded")
                client.send(step["send"], before_write=lambda frame: accept("send", frame))
                until = step["until"]
                if until is not None:
                    while True:
                        frame = client.receive()
                        message = frame.message()
                        accept("receive", frame)
                        if "error" in message and "id" in message:
                            raise ValueError("host RPC error")
                        if all(message.get(k) == v for k, v in until.items()):
                            break
        # Reader threads have joined: consume every remaining retained frame,
        # including usage or contradictory actions after the requested boundary.
        while not client.frames.empty():
            accept("receive", client.frames.get_nowait())
        # Usage can select the last raw counter notification per work identity.
        # It may not manufacture lifecycle events or backing evidence.
        usage = observer.finish()
        journal.append("normalization.finalized", {"blob_ref": _blob(journal, usage)})
        if not isinstance(usage, list) or any(u["raw_ref"] not in captured for u in usage):
            raise ValueError("final usage lacks captured backing")
        trace["usage"].extend(usage)
        parse_trajectory(trace)
        if time.monotonic() >= stop:
            raise TimeoutError("attempt deadline exceeded during cleanup/normalization")
        trace["capture_status"] = "complete"
    except BaseException as exc:
        error = exc
        trace["capture_status"] = "interrupted" if isinstance(exc, (TimeoutError, KeyboardInterrupt)) else "incomplete"
        journal.append("capture.error", {"type": type(exc).__name__, "message": str(exc)})
    finally:
        try:
            journal.snapshot(attempt["workspace"], "after")
        except BaseException as exc:
            trace["capture_status"] = "incomplete"
            journal.append("snapshot.error", {"type": type(exc).__name__, "message": str(exc)})
            if error is None:
                error = exc
        trace["capture_elapsed_ms"] = journal.elapsed_ms()
        if time.monotonic() >= stop and error is None:
            trace["capture_status"] = "interrupted"
            error = TimeoutError("attempt deadline exceeded during final snapshot")
            journal.append("capture.error", {"type": type(error).__name__, "message": str(error)})
        parsed = parse_trajectory(trace)
        result = dict(instrumentation=INSTRUMENTATION, trajectory=trace,
                      findings=[asdict(f) for f in integrity_findings(parsed)],
                      usage_totals=usage_totals(parsed))
        journal.append("attempt.finished", {"status": trace["capture_status"],
                                             "result_ref": _blob(journal, result)})
        journal.closed = True
    if error is not None:
        raise error
    return result


def run_mock_stage(directory, manifest, observer_factory, *, enabled=False):
    """Run a frozen synthetic stage once; stop on the first incomplete attempt.

    A caller-supplied normalizer is trusted Python, not a sandbox. Its source
    file and the complete manifest are pinned. This cannot launch native stages.
    """
    if enabled is not True:
        raise RuntimeError("stage collection disabled")
    # Freeze caller-owned containers before any source/observer can mutate them.
    frozen = json.loads(json.dumps(manifest, allow_nan=False))
    validate_stage(frozen, observer_factory)
    destination = Path(directory).resolve()
    for attempt in frozen["attempts"]:
        workspace = Path(attempt["workspace"]).resolve()
        if destination == workspace or workspace in destination.parents or destination in workspace.parents:
            raise ValueError("stage evidence must be outside every workspace")
    stage = AttemptJournal(destination, frozen)
    remaining = {k: frozen["ceilings"][k] for k in ("threads", "task_turns")}
    result = {"status": "incomplete", "attempts": []}
    consumed_workspaces: set[str] = set()
    try:
        for attempt in frozen["attempts"]:
            # Recheck all input pins immediately before consuming a slot.
            # Workspaces must be distinct or restored in a separately prepared
            # manifest; silently resetting a measured workspace is prohibited.
            validate_stage(frozen, observer_factory, consumed_workspaces=consumed_workspaces)
            stage.append("stage.slot_consumed", {"attempt_id": attempt["id"]})
            collected = _collect(destination / attempt["id"], frozen, attempt,
                                 observer_factory, remaining)
            consumed_workspaces.add(str(Path(attempt["workspace"]).resolve()))
            result["attempts"].append(attempt["id"])
            stage.append("stage.attempt_retained", {"attempt_id": attempt["id"],
                         "result_ref": _blob(stage, collected)})
            validate_stage(frozen, observer_factory, consumed_workspaces=consumed_workspaces)
            for event in collected["trajectory"]["events"]:
                if event["kind"] in {"thread.started", "thread.resumed", "thread.forked"}:
                    remaining["threads"] -= 1
                if event["kind"] == "turn.started" and event["data"]["turn_role"] == "task":
                    remaining["task_turns"] -= 1
            if collected["findings"] or collected["usage_totals"] is None:
                raise ValueError("attempt integrity/measurement incomplete; stage stopped")
        result["status"] = "complete"
    except BaseException as exc:
        stage.append("stage.stopped", {"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        stage.append("attempt.finished", {"status": result["status"],
                                           "result_ref": _blob(stage, result)})
        stage.closed = True
    return result
