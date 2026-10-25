"""Opt-in Codex App Server evidence for explicit, single-turn skill probes.

No lifecycle or implicit-invocation claims: unsupported requests fail preflight.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import queue
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time

from .evaluation import load_scenario
from .evaluation_turns import TurnTrace
from .frontmatter import split_frontmatter
from .metadata import string_value
from .runtime_evidence import (
    RuntimeEnvironment,
    RuntimeRequest,
    RuntimeSample,
    run_runtime_evidence,
)

INSTRUMENTATION = "codex-app-server-explicit-v3"
CONFIG = {
    "approval_policy": "never",
    "sandbox_mode": "read-only",
    "web_search": "disabled",
    "model_reasoning_effort": "low",
    "shell_environment_policy": {"inherit": "none"},
    "shell_environment_policy.set.PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
}


class CodexRuntimeError(RuntimeError):
    """Incomplete or unsupported evidence; never a successful sample."""


class RpcClient:
    """Bounded stdio client; persist observations even when collection fails."""

    def __init__(self, command, *, cwd, env, log, timeout, start_new_session=False):
        self.log = log
        self.start_new_session = start_new_session
        self.deadline = time.monotonic() + timeout
        self.messages: queue.Queue = queue.Queue()
        self.events = []
        self.sequence = 0
        self.stderr = log.with_suffix(".stderr").open("xb")
        self.raw_stdout = (
            log.with_suffix(".stdout").open("x", encoding="utf-8")
            if start_new_session
            else None
        )
        self.transcript = log.open("x", encoding="utf-8")
        self.process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.stderr,
            text=True,
            start_new_session=start_new_session,
        )
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        assert self.process.stdout is not None
        for line in self.process.stdout:
            if self.raw_stdout:
                self.raw_stdout.write(line)
                self.raw_stdout.flush()
            self.messages.put(line)
        self.messages.put(None)

    def send(self, message):
        self.transcript.write(
            json.dumps({"direction": "send", "message": message}) + "\n"
        )
        self.transcript.flush()
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def receive(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise CodexRuntimeError("Codex session timed out")
        try:
            line = self.messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise CodexRuntimeError("Codex session timed out") from exc
        if line is None:
            raise CodexRuntimeError("Codex closed stdout; inspect retained stderr")
        try:
            message = json.loads(line)
        except ValueError as exc:
            self.transcript.write(
                json.dumps({"direction": "receive", "unparsed_stdout": line}) + "\n"
            )
            self.transcript.flush()
            raise CodexRuntimeError("invalid Codex JSON event") from exc
        self.transcript.write(
            json.dumps({"direction": "receive", "message": message}) + "\n"
        )
        self.transcript.flush()
        if "method" in message and "id" in message:
            self.send(
                {
                    "id": message["id"],
                    "error": {
                        "code": -32601,
                        "message": "Unsupported by evidence adapter",
                    },
                }
            )
            raise CodexRuntimeError("unexpected server request: " + message["method"])
        if "method" in message:
            self.events.append(message)
        return message

    def call(self, method, params):
        self.sequence += 1
        identifier = self.sequence
        self.send({"id": identifier, "method": method, "params": params})
        while True:
            message = self.receive()
            if message.get("id") == identifier:
                if "error" in message:
                    raise CodexRuntimeError(
                        "Codex RPC failed: " + json.dumps(message["error"])
                    )
                return message["result"]

    def close(self):
        if self.start_new_session:
            # The workflow collector must stop tool descendants before snapshots.
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        if self.start_new_session:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.reader.join(timeout=1)
        for stream in (
            self.process.stdin,
            self.process.stdout,
            self.stderr,
            self.transcript,
            self.raw_stdout,
        ):
            if stream:
                stream.close()


def validate_request(request: RuntimeRequest):
    if request.target != "codex" or len(request.turns) != 1:
        raise CodexRuntimeError("only single-turn Codex probes are supported")
    turn = request.turns[0]
    if turn.event != "prompt" or turn.invocation != "user":
        raise CodexRuntimeError("only explicit user prompt probes are instrumented")
    for name in request.files:
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in name
            or str(path) != name
        ):
            raise CodexRuntimeError("unsafe package path")
    if "SKILL.md" not in request.files:
        raise CodexRuntimeError("package has no SKILL.md")


def score_events(events, *, thread_id, turn_id, package_dir, latency_ms):
    """Count completed reads only; unfamiliar actions stay visible and fail checks.

    Explicit invocation means the server accepted a skill input item. It is not
    evidence of implicit discovery. Command read classification comes from Codex.
    """
    output, actions, references = [], [], []
    usage = None
    completed = False
    seen = set()
    for event in events:
        method = event.get("method")
        params = event.get("params", {})
        if params.get("threadId") != thread_id:
            continue
        if method == "model/rerouted":
            raise CodexRuntimeError(
                "model rerouted; requested model provenance invalid"
            )
        if params.get("turnId", params.get("turn", {}).get("id")) != turn_id:
            continue
        if method == "thread/tokenUsage/updated":
            usage = params["tokenUsage"]["total"]
        elif method == "turn/completed":
            if params["turn"]["status"] != "completed":
                raise CodexRuntimeError(
                    "Codex turn failed: " + json.dumps(params["turn"].get("error"))
                )
            completed = True
        elif method == "item/completed":
            item = params["item"]
            if item["id"] in seen:
                raise CodexRuntimeError("duplicate completed item")
            seen.add(item["id"])
            kind = item["type"]
            if kind == "agentMessage":
                output.append(item["text"])
            elif kind == "commandExecution":
                reads = item.get("commandActions", [])
                if (
                    item.get("exitCode") != 0
                    or item.get("status") != "completed"
                    or not reads
                ):
                    actions.append("unverified-command")
                    continue
                for read in reads:
                    if read.get("type") != "read":
                        actions.append("command:" + read.get("type", "unknown"))
                        continue
                    path = Path(read["path"])
                    if not path.is_absolute():
                        path = Path(item["cwd"]) / path
                    try:
                        relative = (
                            path.resolve().relative_to(package_dir.resolve()).as_posix()
                        )
                    except ValueError:
                        actions.append("read-outside-package")
                        continue
                    if relative != "SKILL.md":
                        references.append(relative)
            elif kind not in ("userMessage", "reasoning"):
                actions.append("item:" + kind)
    if not completed or usage is None:
        raise CodexRuntimeError("missing completed turn or measured usage")
    for key in ("inputTokens", "outputTokens"):
        if type(usage.get(key)) is not int or usage[key] < 0:
            raise CodexRuntimeError("invalid measured usage")
    return RuntimeSample(
        (TurnTrace(True, "\n".join(output), tuple(actions), tuple(references)),),
        usage["inputTokens"],
        usage["outputTokens"],
        latency_ms,
    )


class CodexEvaluator:
    def __init__(self, *, executable, auth_file, output_dir, timeout=120):
        self.executable = str(Path(executable).resolve())
        self.auth_file = Path(auth_file)
        self.output_dir = Path(output_dir)
        self.timeout = timeout
        self.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def evaluate(self, request):
        validate_request(request)
        fields, _, _ = split_frontmatter(request.files["SKILL.md"].decode("utf-8"))
        field = next((field for field in fields if field.key == "name"), None)
        name = string_value(field) if field else None
        if not isinstance(name, str) or not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", name
        ):
            raise CodexRuntimeError("probe requires a portable skill name")
        log_id = hashlib.sha256(request.session_id.encode()).hexdigest()[:24]
        with tempfile.TemporaryDirectory(prefix="harnessmith-codex-") as temporary:
            root = Path(temporary)
            home, workspace = root / "codex-home", root / "workspace"
            home.mkdir(mode=0o700)
            workspace.mkdir()
            # Auth is copied locally, never put into prompts, arguments or logs.
            shutil.copyfile(self.auth_file, home / "auth.json")
            (home / "auth.json").chmod(0o600)
            package_dir = workspace / ".agents" / "skills" / name
            for relative, content in request.files.items():
                path = package_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                path.chmod(0o755 if relative in request.executable_files else 0o644)
            env = {
                key: value
                for key, value in os.environ.items()
                if key in ("PATH", "HOME", "TMPDIR", "SYSTEMROOT")
            }
            env["CODEX_HOME"] = str(home)
            command = [self.executable, "app-server", "--listen", "stdio://"]
            for key, value in CONFIG.items():
                if isinstance(value, dict):
                    for child, nested in value.items():
                        command.extend(
                            ["-c", key + "." + child + "=" + json.dumps(nested)]
                        )
                else:
                    command.extend(["-c", key + "=" + json.dumps(value)])
            client = RpcClient(
                command,
                cwd=workspace,
                env=env,
                log=self.output_dir / (log_id + ".jsonl"),
                timeout=self.timeout,
            )
            started = time.monotonic()
            try:
                client.call(
                    "initialize",
                    {"clientInfo": {"name": "harnessmith_evidence", "version": "1"}},
                )
                client.send({"method": "initialized", "params": {}})
                listing = client.call(
                    "skills/list", {"cwds": [str(workspace)], "forceReload": True}
                )
                disabled = []
                for entry in listing["data"]:
                    if entry.get("errors"):
                        raise CodexRuntimeError("skill discovery errors")
                    for skill in entry["skills"]:
                        if (
                            Path(skill["path"]).resolve()
                            != (package_dir / "SKILL.md").resolve()
                        ):
                            disabled.append({"path": skill["path"], "enabled": False})
                result = client.call(
                    "thread/start",
                    {
                        "cwd": str(workspace),
                        "model": request.environment.model,
                        "approvalPolicy": "never",
                        "sandbox": "read-only",
                        "ephemeral": True,
                        "config": {"skills.config": disabled},
                    },
                )
                if (
                    result["model"] != request.environment.model
                    or result["sandbox"]["type"] != "readOnly"
                ):
                    raise CodexRuntimeError(
                        "runtime model or permissions differ from requested configuration"
                    )
                thread_id = result["thread"]["id"]
                turn = client.call(
                    "turn/start",
                    {
                        "threadId": thread_id,
                        "input": [
                            {
                                "type": "text",
                                "text": "$" + name + " " + request.turns[0].prompt,
                            },
                            {
                                "type": "skill",
                                "name": name,
                                "path": str(package_dir / "SKILL.md"),
                            },
                        ],
                    },
                )
                turn_id = turn["turn"]["id"]
                while not any(
                    e.get("method") == "turn/completed"
                    and e.get("params", {}).get("threadId") == thread_id
                    and e["params"]["turn"]["id"] == turn_id
                    for e in client.events
                ):
                    client.receive()
                return score_events(
                    client.events,
                    thread_id=thread_id,
                    turn_id=turn_id,
                    package_dir=package_dir,
                    latency_ms=int((time.monotonic() - started) * 1000),
                )
            finally:
                client.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--enabled", action="store_true", help="allow real model usage")
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--output", required=True, type=Path, help="new evidence directory"
    )
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=120, help="seconds per session")
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--auth-file",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        / "auth.json",
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if not args.enabled:
        parser.error("runtime evidence requires --enabled")
    if args.samples < 2 or args.timeout <= 0:
        parser.error("at least two samples and a positive timeout are required")
    scenario = load_scenario(args.scenario)
    if (
        scenario.target != "codex"
        or len(scenario.turns) != 1
        or scenario.turns[0].event != "prompt"
        or scenario.turns[0].invocation != "user"
    ):
        parser.error("only single-turn explicit Codex prompt scenarios are supported")
    executable = shutil.which(args.codex)
    if not executable or not args.auth_file.is_file():
        parser.error("Codex executable and a local auth.json are required")
    version = subprocess.check_output(
        [executable, "--version"], text=True, timeout=10
    ).strip()
    environment = RuntimeEnvironment(
        harness="codex",
        harness_version=version,
        model=args.model,
        model_version="requested-id:" + args.model + ";backend-snapshot-unreported",
        mode="app-server-stdio",
        mode_version=version,
        instrumentation_version=INSTRUMENTATION,
        permission_policy="read-only;approval=never",
        cache_policy="fresh-session;provider-cache-uncontrolled",
        configuration_id=hashlib.sha256(
            json.dumps(CONFIG, sort_keys=True).encode()
        ).hexdigest(),
    )
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    evaluator = CodexEvaluator(
        executable=executable,
        auth_file=args.auth_file,
        output_dir=args.output / "raw",
        timeout=args.timeout,
    )
    try:
        report = run_runtime_evidence(
            scenario,
            evaluator,
            repository_root=args.repository_root,
            environment=environment,
            samples=args.samples,
            enabled=True,
        )
    except (CodexRuntimeError, OSError, ValueError, KeyError) as exc:
        (args.output / "incomplete.json").write_text(
            json.dumps({"completed": False, "error": str(exc)}, indent=2) + "\n"
        )
        print("Incomplete runtime evidence: " + str(exc))
        return 2
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(str(args.output / "report.json"))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
