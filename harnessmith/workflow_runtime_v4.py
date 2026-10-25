"""Bounded opt-in collection for the proposed two-session Luna follow-up.

No resume, retry, sample-count or model override. All prior instruments stay unchanged.
The v4 collector uses the unchanged, pinned v3 trace normalizer.
This module is disabled by default; live use requires separate user approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import subprocess

from .codex_runtime import CodexRuntimeError, RpcClient
from .workflow_fidelity import PACKAGE
from .workflow_fidelity_v4 import check_workspace, prepare_pilot
from .workflow_trace_v3 import normalize_events


MODEL = "gpt-6-luna"
INSTRUMENTATION = "codex-workflow-stdio-v4"
ORDER = ("append-router-v4", "hooks-router-v4")
CONFIG = {
    "approval_policy": "never",
    "sandbox_mode": "workspace-write",
    "sandbox_workspace_write.network_access": False,
    "sandbox_workspace_write.exclude_slash_tmp": True,
    "sandbox_workspace_write.exclude_tmpdir_env_var": True,
    "web_search": "disabled",
    "model_reasoning_effort": "low",
    "shell_environment_policy.inherit": "none",
    "shell_environment_policy.set.PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "allow_login_shell": False,
    "features.multi_agent": False,
}


class WorkflowClient(RpcClient):
    """Stop immediately on server errors/retries or model substitution."""

    def receive(self):
        message = super().receive()
        if message.get("method") in ("model/rerouted", "error"):
            raise CodexRuntimeError("workflow session stopped on " + message["method"])
        return message


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def journal(path, value):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def sandbox_policy(workspace):
    return {
        "type": "workspaceWrite",
        "writableRoots": [str(Path(workspace).resolve())],
        "networkAccess": False,
        "excludeSlashTmp": True,
        "excludeTmpdirEnvVar": True,
    }


def validate_permissions(result, workspace):
    expected = sandbox_policy(workspace)
    actual = result.get("sandbox", {})
    # The cwd is always writable; explicit roots may be empty or name only cwd.
    roots = actual.get("writableRoots", [])
    if (
        not isinstance(roots, list)
        or any(Path(p).resolve() != Path(workspace).resolve() for p in roots)
        or any(actual.get(k) != v for k, v in expected.items() if k != "writableRoots")
        or result.get("model") != MODEL
        or result.get("reasoningEffort") != "low"
        or result.get("approvalPolicy") != "never"
        or Path(result.get("cwd", "/")).resolve() != Path(workspace).resolve()
        or result.get("instructionSources")
    ):
        raise CodexRuntimeError(
            "returned model/permissions/instructions differ from isolated pilot"
        )
    for root in result.get("runtimeWorkspaceRoots", [str(workspace)]):
        if Path(root).resolve() != Path(workspace).resolve():
            raise CodexRuntimeError("unexpected runtime workspace root")


def command_line(executable):
    args = [str(executable), "app-server", "--listen", "stdio://"]
    for key, value in CONFIG.items():
        args.extend(["-c", key + "=" + json.dumps(value)])
    return args


def process_env(home):
    env = {
        k: v
        for k, v in os.environ.items()
        if k in ("PATH", "HOME", "TMPDIR", "SYSTEMROOT")
    }
    env["CODEX_HOME"] = str(home)
    return env


def snapshot(workspace, destination):
    # Preserve symlinks as links, never dereference a model-created escape.
    shutil.copytree(workspace, destination, symlinks=True)
    inventory = {}
    for p in sorted(destination.rglob("*")):
        name = p.relative_to(destination).as_posix()
        if p.is_symlink():
            inventory[name] = {"type": "symlink", "target": os.readlink(p)}
        elif p.is_file():
            inventory[name] = {
                "sha256": digest(p.read_bytes()),
                "mode": p.stat().st_mode & 0o777,
            }
        elif not p.is_dir():
            raise ValueError("special file in workspace snapshot")
    return inventory


def collect_session(
    directory,
    *,
    executable,
    auth_file,
    timeout=180,
    client_type=WorkflowClient,
    evidence_kind="runtime",
):
    directory = Path(directory).resolve()
    workspace = directory / "workspace"
    manifest = json.loads((directory / "manifest.json").read_bytes())
    prompt = (directory / "prompt.md").read_text()
    session = manifest["session_id"]
    # This file is the durable one-attempt guard, even when the process crashes.
    write_new(
        directory / "attempt.json",
        {
            "session_id": session,
            "model": MODEL,
            "started_at_unix": time.time(),
            "retry_allowed": False,
        },
    )
    before = snapshot(workspace, directory / "before")
    write_new(directory / "before-inventory.json", before)
    raw = directory / "raw"
    raw.mkdir()
    client = None
    thread_id = turn_id = None
    error = None
    returned = None
    events = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="opt004-auth-") as temporary:
        home = Path(temporary)
        home.chmod(0o700)
        shutil.copyfile(auth_file, home / "auth.json")
        (home / "auth.json").chmod(0o600)
        try:
            client = client_type(
                command_line(executable),
                cwd=workspace,
                env=process_env(home),
                log=raw / "events.jsonl",
                timeout=timeout,
                start_new_session=True,
            )
            client.call(
                "initialize",
                {"clientInfo": {"name": "harnessmith_workflow", "version": "4"}},
            )
            client.send({"method": "initialized", "params": {}})
            listing = client.call(
                "skills/list", {"cwds": [str(workspace)], "forceReload": True}
            )
            selected = (workspace / PACKAGE / "SKILL.md").resolve()
            disabled = []
            found = False
            for entry in listing["data"]:
                if entry.get("errors"):
                    raise CodexRuntimeError("skill discovery errors")
                for skill in entry["skills"]:
                    if Path(skill["path"]).resolve() == selected:
                        found = True
                    else:
                        disabled.append({"path": skill["path"], "enabled": False})
            if not found:
                raise CodexRuntimeError("prepared skill was not discovered")
            returned = client.call(
                "thread/start",
                {
                    "cwd": str(workspace),
                    "model": MODEL,
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "ephemeral": True,
                    "config": {"skills.config": disabled},
                },
            )
            validate_permissions(returned, workspace)
            thread_id = returned["thread"]["id"]
            journal(
                directory / "attempt-events.jsonl",
                {"phase": "turn-start-sending", "thread_id": thread_id},
            )
            turn = client.call(
                "turn/start",
                {
                    "threadId": thread_id,
                    "model": MODEL,
                    "effort": "low",
                    "approvalPolicy": "never",
                    "sandboxPolicy": sandbox_policy(workspace),
                    "input": [
                        {"type": "text", "text": "$speckit-checklist " + prompt},
                        {
                            "type": "skill",
                            "name": "speckit-checklist",
                            "path": str(selected),
                        },
                    ],
                },
            )
            turn_id = turn["turn"]["id"]
            journal(
                directory / "attempt-events.jsonl",
                {"phase": "turn-started", "turn_id": turn_id},
            )
            while not any(
                e.get("method") == "turn/completed"
                and e.get("params", {}).get("threadId") == thread_id
                and e["params"].get("turn", {}).get("id") == turn_id
                for e in client.events
            ):
                client.receive()
        except (Exception, KeyboardInterrupt) as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
        finally:
            if client is not None:
                events = client.events
                try:
                    client.close()
                except (OSError, KeyboardInterrupt) as exc:
                    error = {"type": type(exc).__name__, "message": str(exc)}
    latency = int((time.monotonic() - started) * 1000)
    # Artifact retention must not depend on successful event normalization.
    integrity_error = None
    try:
        after = snapshot(workspace, directory / "after")
        write_new(directory / "after-inventory.json", after)
    except (OSError, ValueError) as exc:
        integrity_error = {"type": type(exc).__name__, "message": str(exc)}
    try:
        observation = normalize_events(
            events,
            thread_id=thread_id,
            turn_id=turn_id,
            workspace=workspace,
            manifest=manifest,
            latency_ms=latency,
        )
    except (Exception, KeyboardInterrupt) as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        observation = {
            "schema_version": 3,
            "evidence_kind": "externally-captured-observation",
            "model": MODEL,
            "completed": False,
            "instrumentation_valid": False,
            "events": [],
            "output": "",
            "final_output": "",
            "commentary": [],
            "messages": [],
            "usage": None,
            "issues": [
                {
                    "kind": "instrumentation",
                    "detail": "normalization failed; inspect raw trace",
                }
            ],
        }
    observation["raw_trace"] = "raw/events.jsonl"
    if evidence_kind == "mock":
        observation["evidence_kind"] = "offline-simulation"
    observation["collector_error"] = error
    observation["returned_configuration"] = returned
    write_new(directory / "observation.json", observation)
    checks = None
    try:
        checks = check_workspace(directory / "manifest.json", observation)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        integrity_error = {"type": type(exc).__name__, "message": str(exc)}
    if checks is not None:
        write_new(directory / "checks.json", checks)
    protected_ok = checks is not None and all(
        c["passed"]
        for c in checks["dimensions"]["workflow"]["checks"]
        if c["name"]
        in ("preserved-inputs", "preserved-modes", "file-inventory", "read-scope")
    )
    isolation = any(i.get("kind") == "isolation" for i in observation.get("issues", []))
    stop = bool(
        error
        or integrity_error
        or not observation.get("instrumentation_valid")
        or not protected_ok
        or isolation
    )
    result = {
        "schema_version": 4,
        "session_id": session,
        "model": MODEL,
        "completed": observation.get("completed", False),
        "automated_checks_passed": checks is not None
        and checks["automated_checks_passed"],
        "stop_batch": stop,
        "collector_error": error,
        "integrity_error": integrity_error,
        "usage": observation.get("usage"),
        "latency_ms": latency,
        "model_fidelity": "pending-review",
        "observation": "observation.json",
        "checks": "checks.json" if checks else None,
    }
    write_new(directory / "result.json", result)
    return result


def run_batch(
    repository_root,
    output,
    *,
    executable,
    auth_file,
    enabled=False,
    timeout=180,
    client_type=WorkflowClient,
    evidence_kind="runtime",
):
    if not enabled:
        raise ValueError("live workflow collection requires explicit --enabled")
    if timeout <= 0 or timeout > 180:
        raise ValueError("timeout must be positive and at most 180 seconds")
    output = Path(output).resolve()
    prepared = prepare_pilot(repository_root, output)
    output.chmod(0o700)
    if tuple(s["id"] for s in prepared["sessions"]) != ORDER:
        raise ValueError("prepared batch differs from proposed two-session order")
    executable = Path(executable).resolve()
    version = subprocess.check_output(
        [str(executable), "--version"], text=True, timeout=10
    ).strip()
    collector_files = (
        "workflow_runtime_v4.py", "workflow_trace_v3.py", "workflow_trace_v2.py", "workflow_trace.py",
        "workflow_fidelity_v4.py", "workflow_fidelity_v3.py", "workflow_fidelity.py", "router_experiment.py",
        "codex_runtime.py",
    )
    hashes = {}
    for name in collector_files:
        content = Path(__file__).with_name(name).read_bytes()
        (output / "instrument" / name).write_bytes(content)
        hashes[name] = digest(content)
    environment = {
        "schema_version": 4,
        "evidence_kind": evidence_kind,
        "harness_version": version,
        "model": MODEL,
        "backend_model_version": "unreported",
        "mode": "app-server-stdio",
        "mode_version": version,
        "instrumentation": INSTRUMENTATION,
        "collector_files": hashes,
        "configuration": CONFIG,
        "configuration_sha256": digest(json.dumps(CONFIG, sort_keys=True).encode()),
        "cache_policy": "fresh-session;provider-cache-uncontrolled",
        "timeout_seconds": timeout,
        "approved_sessions": list(ORDER),
        "retries": 0,
        "read_isolation": "legacy sandbox permits host reads; recorded out-of-workspace reads fail; not an OS container",
    }
    write_new(output / "environment.json", environment)
    results = []
    for session_id in ORDER:
        journal(
            output / "batch-events.jsonl",
            {"event": "attempt", "session_id": session_id},
        )
        try:
            result = collect_session(
                output / session_id,
                executable=executable,
                auth_file=auth_file,
                timeout=timeout,
                client_type=client_type,
                evidence_kind=evidence_kind,
            )
        except (Exception, KeyboardInterrupt) as exc:
            result = {
                "schema_version": 4,
                "session_id": session_id,
                "model": MODEL,
                "completed": False,
                "automated_checks_passed": False,
                "stop_batch": True,
                "collector_error": {"type": type(exc).__name__, "message": str(exc)},
                "raw_trace": "raw/events.jsonl",
                "model_fidelity": "pending-review",
            }
            result_path = output / session_id / "result.json"
            if not result_path.exists():
                write_new(result_path, result)
        results.append(result)
        journal(output / "batch-events.jsonl", {"event": "result", **result})
        print(
            json.dumps(
                {
                    "session": session_id,
                    "completed": result["completed"],
                    "checks_passed": result["automated_checks_passed"],
                    "stop_batch": result["stop_batch"],
                }
            ),
            flush=True,
        )
        if result["stop_batch"]:
            break
    report = {
        "schema_version": 4,
        "evidence_kind": evidence_kind,
        "model": MODEL,
        "approved_session_count": len(ORDER),
        "attempted_session_count": len(results),
        "retries": 0,
        "unattempted": list(ORDER[len(results) :]),
        "results": results,
        "model_fidelity": "pending-review",
        "eligible_for_promotion": False,
    }
    write_new(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--auth-file",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        / "auth.json",
    )
    args = parser.parse_args(argv)
    if not args.enabled:
        parser.error("live workflow collection requires --enabled")
    executable = shutil.which(args.codex)
    if not executable or not args.auth_file.is_file():
        parser.error("Codex executable and existing local authentication required")
    report = run_batch(
        args.repository_root,
        args.output,
        executable=executable,
        auth_file=args.auth_file,
        enabled=True,
        timeout=args.timeout,
    )
    return (
        0
        if len(report["results"]) == len(ORDER)
        and all(r["automated_checks_passed"] for r in report["results"])
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
