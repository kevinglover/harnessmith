"""Bounded Codex 0.164 protocol observer for synthetic O3 qualification.

No permission snapshot is inferred from configuration, and no live launch is
provided. Unsupported lifecycle operations fail closed. Invocation requires an
explicit input AND a successful exact full root read; text answers never count.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shlex

INSTRUMENTATION = "codex-native-observer-v1"
COUNTERS = {"input_tokens": "inputTokens", "cached_input_tokens": "cachedInputTokens",
            "cache_write_input_tokens": "cacheWriteInputTokens", "output_tokens": "outputTokens",
            "reasoning_output_tokens": "reasoningOutputTokens"}


def package_digest(directory):
    """Use the prospective O2 package byte/mode inventory encoding."""
    directory = Path(directory)
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlinked package not supported by this binding")
        if path.is_file():
            payload = path.read_bytes()
            files.append(dict(path=path.relative_to(directory).as_posix(),
                sha256=hashlib.sha256(payload).hexdigest(), mode=oct(path.stat().st_mode & 0o777),
                bytes=len(payload)))
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class CodexObserver:
    def __init__(self, policy):
        if set(policy) != {"version", "accounting", "packages"} or policy["version"] != INSTRUMENTATION:
            raise ValueError("unknown Codex normalization policy")
        if policy["accounting"] != "fresh-cumulative-only":
            raise ValueError("resume/fork/compaction accounting is unqualified")
        self.packages = {}
        for entry in policy["packages"]:
            path = Path(entry["root"]).resolve(strict=True)
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != entry["root_sha256"]:
                raise ValueError("package root drift")
            if package_digest(path.parent) != entry["package_sha256"]:
                raise ValueError("package inventory drift")
            self.packages[str(path)] = dict(entry, payload=payload)
        self.sequence = 0
        self.threads = set()
        self.pending = {}
        self.prompts = {}
        self.turns = {}
        self.completed = set()
        self.items = {}
        self.approvals = {}
        self.decisions = {}
        self.latest_usage = {}
        self.usage_turns = set()
        self.activated = set()
        self.last_raw = None

    @staticmethod
    def _rpc_id(identifier):
        if type(identifier) not in (str, int):
            raise ValueError("invalid RPC identity")
        return json.dumps(identifier)

    def observe(self, direction, message, reference, elapsed):
        events = []
        self.last_raw = reference

        def emit(kind, thread, turn=None, data=None, cause=None):
            identity = "codex-event-" + str(self.sequence)
            events.append(dict(kind=kind, event_id=identity, sequence=self.sequence,
                elapsed_ms=elapsed, thread_id=thread, turn_id=turn,
                causal_event_id=cause, origin="mock", raw_ref=reference, data=data or {}))
            self.sequence += 1
            return identity

        method = message.get("method")
        params = message.get("params", {})
        if direction == "send":
            if method in {"thread/resume", "thread/fork", "thread/compact/start", "turn/interrupt"}:
                raise ValueError("native lifecycle binding is not qualified")
            if method is not None and "id" in message:
                key = self._rpc_id(message["id"])
                if key in self.pending:
                    raise ValueError("duplicate client request ID")
                self.pending[key] = method
            if method == "turn/start":
                thread = params["threadId"]
                if thread in self.prompts:
                    raise ValueError("overlapping pending prompts")
                self.prompts[thread] = dict(raw_ref=reference, input=params["input"])
            elif method is None and "id" in message:
                key = self._rpc_id(message["id"])
                request = self.approvals.get(key)
                decision = message.get("result", {}).get("decision")
                if request is None or key in self.decisions or decision not in {"accept", "decline"}:
                    raise ValueError("unsupported or uncorrelated approval decision")
                self.decisions[key] = decision
            return dict(events=events, usage=[])
        if direction != "receive":
            raise ValueError("unknown observation direction")
        if method is None:
            key = self._rpc_id(message.get("id"))
            if key not in self.pending:
                raise ValueError("uncorrelated RPC response")
            self.pending.pop(key)
            if "error" in message:
                raise ValueError("host rejected request")
        elif method == "thread/started":
            thread = params["thread"]["id"]
            if params["thread"].get("forkedFromId") or params["thread"].get("parentThreadId"):
                raise ValueError("inherited or subagent thread is outside fresh-thread binding")
            if thread in self.threads:
                raise ValueError("duplicate native thread identity")
            self.threads.add(thread)
            emit("thread.started", thread)
        elif method == "turn/started":
            thread, turn = params["threadId"], params["turn"]["id"]
            prompt = self.prompts.pop(thread, None)
            if prompt is None or (thread, turn) in self.turns:
                raise ValueError("turn lacks unique submitted prompt")
            start = emit("turn.started", thread, turn, dict(turn_role="task", prompt_ref=prompt["raw_ref"]))
            self.turns[(thread, turn)] = dict(start=start, prompt=prompt)
        elif method == "turn/completed":
            thread, turn = params["threadId"], params["turn"]["id"]
            key = (thread, turn)
            if key not in self.turns or key in self.completed:
                raise ValueError("unmatched/duplicate native turn completion")
            emit("turn.completed", thread, turn, dict(status=params["turn"]["status"]), self.turns[key]["start"])
            self.completed.add(key)
        elif method == "item/commandExecution/requestApproval":
            thread, turn, item = params["threadId"], params["turnId"], params["itemId"]
            key = self._rpc_id(message["id"])
            if key in self.approvals:
                raise ValueError("duplicate approval RPC ID")
            # RPC identity remains distinct from optional host approvalId. The
            # full request retains both; its typed identity uses the RPC ID.
            aid = "rpc:" + key
            event = emit("approval.requested", thread, turn, dict(approval_id=aid, action_id=item))
            self.approvals[key] = dict(thread=thread, turn=turn, item=item, event=event,
                                       approval_id=aid, grant=None)
        elif method == "serverRequest/resolved":
            key = self._rpc_id(params["requestId"])
            request = self.approvals.get(key)
            if request is None or key not in self.decisions or request.get("resolved"):
                raise ValueError("approval resolution lacks a unique request/decision")
            if params.get("threadId") != request["thread"]:
                raise ValueError("approval resolution has wrong thread")
            decision = "grant" if self.decisions[key] == "accept" else "deny"
            request["grant"] = emit("approval.decided", request["thread"], request["turn"],
                dict(approval_id=request["approval_id"], decision=decision), request["event"])
            request["resolved"] = True
        elif method in {"item/started", "item/completed"}:
            item = params["item"]
            if item["type"] == "contextCompaction":
                raise ValueError("compaction usage binding is unqualified")
            if item["type"] == "commandExecution":
                thread, turn, identity = params["threadId"], params["turnId"], item["id"]
                key = (thread, turn, identity)
                if method == "item/started":
                    if key in self.items:
                        raise ValueError("duplicate command item")
                    event = emit("action.proposed", thread, turn, dict(action_id=identity,
                        operation=item["command"], input_ref=reference))
                    self.items[key] = dict(proposal=event, input_ref=reference, command=item["command"], started=None)
                else:
                    state = self.items.get(key)
                    if state is None or state.get("completed"):
                        raise ValueError("unmatched/duplicate command completion")
                    state["completed"] = True
                    if item["command"] != state["command"]:
                        raise ValueError("command changed between proposal and completion")
                    if item["status"] == "declined":
                        if state["started"] is not None:
                            raise ValueError("declined command already executed")
                    elif item["status"] in {"completed", "failed"} and type(item.get("exitCode")) is int:
                        if state["started"] is None:
                            state["started"] = self._start(emit, state, thread, turn, identity)
                        output = item.get("aggregatedOutput")
                        result = emit("action.completed", thread, turn, dict(action_id=identity,
                            status="succeeded" if item["exitCode"] == 0 else "failed", exit_code=item["exitCode"],
                            output_ref=reference if isinstance(output, str) else None), state["started"])
                        self._root_read(emit, state, item, thread, turn, result, reference)
                    else:
                        raise ValueError("command completion lacks execution/exit proof")
            elif item["type"] in {"fileChange", "mcpToolCall", "dynamicToolCall", "hook"}:
                raise ValueError("tool attribution not implemented for " + item["type"])
            elif item["type"] not in {"agentMessage", "userMessage", "reasoning", "plan"}:
                raise ValueError("unsupported native item type: " + item["type"])
        elif method == "item/commandExecution/outputDelta":
            thread, turn, identity = params["threadId"], params["turnId"], params["itemId"]
            state = self.items.get((thread, turn, identity))
            if state is None or state.get("completed"):
                raise ValueError("output outside command lifecycle")
            if not isinstance(params["delta"], str) or not params["delta"]:
                raise ValueError("empty output is not execution proof")
            if state["started"] is None:
                state["started"] = self._start(emit, state, thread, turn, identity)
        elif method == "thread/tokenUsage/updated":
            thread, turn = params["threadId"], params["turnId"]
            if (thread, turn) not in self.turns:
                raise ValueError("usage lacks a known turn")
            latest_turn = [key[1] for key in self.turns if key[0] == thread][-1]
            if turn != latest_turn:
                raise ValueError("usage for an earlier turn after subsequent work started")
            total = params["tokenUsage"]["total"]
            counters = {field: total.get(native) for field, native in COUNTERS.items()}
            if any(value is not None and (type(value) is not int or value < 0) for value in counters.values()):
                raise ValueError("invalid usage counter")
            old = self.latest_usage.get(thread)
            if old and any(counters[k] is not None and old["final"][k] is not None
                           and counters[k] < old["final"][k] for k in counters):
                raise ValueError("counter reset without qualified new epoch")
            self.latest_usage[thread] = dict(raw_ref=reference, final=counters, turn=turn)
            self.usage_turns.add((thread, turn))
        elif method in {"thread/compacted", "hook/started", "hook/completed"}:
            raise ValueError("unqualified lifecycle/hook notification")
        elif method not in {"item/agentMessage/delta", "item/reasoning/textDelta",
                            "item/reasoning/summaryTextDelta", "item/reasoning/summaryPartAdded",
                            "turn/plan/updated", "turn/diff/updated", "thread/status/changed"}:
            raise ValueError("unsupported notification: " + str(method))
        return dict(events=events, usage=[])

    def _start(self, emit, state, thread, turn, identity):
        approvals = [a for a in self.approvals.values()
                     if (a["thread"], a["turn"], a["item"]) == (thread, turn, identity)]
        if len(approvals) > 1:
            raise ValueError("multiple callbacks need a separately qualified execution binding")
        approval = approvals[0] if approvals else None
        return emit("action.started", thread, turn, dict(action_id=identity,
            approval_id=approval["approval_id"] if approval else None,
            operation=state["command"], path=None, input_ref=state["input_ref"], dispatch="tool"),
            approval["grant"] if approval else state["proposal"])

    def _root_read(self, emit, state, item, thread, turn, result, reference):
        if item["exitCode"] != 0 or not isinstance(item.get("aggregatedOutput"), str):
            return
        for path, package in self.packages.items():
            if state["command"] not in {"cat " + shlex.quote(path), "cat -- " + shlex.quote(path)}:
                continue
            if item["aggregatedOutput"].encode() != package["payload"]:
                return
            emit("read.observed", thread, turn, dict(action_id=item["id"], path=path,
                blob_sha256=package["root_sha256"], byte_start=0, byte_end=len(package["payload"]),
                complete=True, category="other"), result)
            inputs = self.turns[(thread, turn)]["prompt"]["input"]
            explicit = any(i.get("type") == "skill" and i.get("path") == path
                           and i.get("name") == package["skill_id"] for i in inputs)
            key = (thread, turn, path)
            if explicit and key not in self.activated:
                emit("invocation.observed", thread, turn, dict(skill_id=package["skill_id"],
                    package_sha256=package["package_sha256"], channel="explicit", evidence_ref=reference), result)
                self.activated.add(key)

    def finish(self):
        if self.pending or self.prompts or set(self.turns) != self.completed:
            raise ValueError("unfinished request/turn lifecycle")
        if any(not item.get("completed") for item in self.items.values()):
            raise ValueError("unfinished command lifecycle")
        if any(not request.get("resolved") for request in self.approvals.values()):
            raise ValueError("unfinished approval lifecycle")
        result = []
        for thread, usage in self.latest_usage.items():
            work = [value["start"] for key, value in self.turns.items() if key[0] == thread]
            missing = any(key not in self.usage_turns for key in self.turns if key[0] == thread)
            result.append(dict(interval_id="usage:" + thread, thread_id=thread,
                meter_id=INSTRUMENTATION, counter_epoch="fresh", basis="cumulative", baseline_reason="fresh",
                work_ids=work, raw_ref=usage["raw_ref"], normalization_ref=INSTRUMENTATION,
                unavailable_reason="missing per-turn usage" if missing else None,
                baseline={key: 0 for key in COUNTERS}, final=usage["final"]))
        return result
