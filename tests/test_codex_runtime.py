from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

from harnessmith.codex_runtime import (
    CodexRuntimeError,
    RpcClient,
    score_events,
    validate_request,
)
from harnessmith.runtime_evidence import (
    RuntimeEnvironment,
    RuntimeRequest,
    RuntimeTurnInput,
)


def event(method, **params):
    return {
        "method": method,
        "params": {"threadId": "thread", "turnId": "turn", **params},
    }


def completed(item):
    return event("item/completed", item=item)


def events():
    return [
        completed({"id": "answer", "type": "agentMessage", "text": "HSM-7391-ORCHID"}),
        event(
            "thread/tokenUsage/updated",
            tokenUsage={"total": {"inputTokens": 91, "outputTokens": 12}},
        ),
        event("turn/completed", turn={"id": "turn", "status": "completed"}),
    ]


class CodexScoringTests(unittest.TestCase):
    def score(self, values):
        return score_events(
            values,
            thread_id="thread",
            turn_id="turn",
            package_dir=Path("/probe"),
            latency_ms=15,
        )

    def test_measured_usage_and_actual_reference_read(self):
        read = completed(
            {
                "id": "read",
                "type": "commandExecution",
                "cwd": "/probe",
                "exitCode": 0,
                "status": "completed",
                "commandActions": [{"type": "read", "path": "references/lookup.md"}],
            }
        )
        sample = self.score([read] + events())
        self.assertEqual(("references/lookup.md",), sample.turns[0].reference_loads)
        self.assertEqual(91, sample.input_tokens)
        self.assertEqual((), sample.turns[0].actions)

    def test_output_claim_does_not_count_as_a_reference_read(self):
        values = events()
        values[0]["params"]["item"]["text"] = "I read references/lookup.md"
        self.assertEqual((), self.score(values).turns[0].reference_loads)

    def test_failed_and_unclassified_tools_cannot_disappear(self):
        for item, expected in [
            ({"type": "fileChange"}, "item:fileChange"),
            ({"type": "mcpToolCall"}, "item:mcpToolCall"),
            ({"type": "commandExecution", "exitCode": 1}, "unverified-command"),
            (
                {
                    "type": "commandExecution",
                    "status": "completed",
                    "exitCode": 0,
                    "commandActions": [{"type": "unknown"}],
                },
                "command:unknown",
            ),
        ]:
            with self.subTest(expected=expected):
                self.assertEqual(
                    (expected,),
                    self.score([completed({"id": "tool", **item})] + events())
                    .turns[0]
                    .actions,
                )

    def test_missing_usage_failed_completion_and_rerouting_abort(self):
        cases = [
            events()[:1],
            [events()[0], events()[-1]],
            events()[:-1],
            [event("model/rerouted")] + events(),
            events()[:-1]
            + [event("turn/completed", turn={"id": "turn", "status": "failed"})],
        ]
        for values in cases:
            with self.assertRaises(CodexRuntimeError):
                self.score(values)
        for invalid in (True, -1, None, 1.2):
            values = events()
            values[1]["params"]["tokenUsage"]["total"]["inputTokens"] = invalid
            with self.assertRaises(CodexRuntimeError):
                self.score(values)

    def test_duplicate_items_rejected_and_other_threads_ignored(self):
        with self.assertRaises(CodexRuntimeError):
            self.score([events()[0]] + events())
        extra = completed({"id": "other", "type": "fileChange"})
        extra["params"]["threadId"] = "different"
        self.assertEqual((), self.score([extra] + events()).turns[0].actions)

    def test_cumulative_usage_is_not_summed(self):
        earlier = event(
            "thread/tokenUsage/updated",
            tokenUsage={"total": {"inputTokens": 40, "outputTokens": 2}},
        )
        self.assertEqual(91, self.score([earlier] + events()).input_tokens)

    def test_preflight_rejects_unsupported_events_and_unsafe_paths(self):
        environment = RuntimeEnvironment(*(["test"] * 10))
        request = RuntimeRequest(
            "test",
            "codex",
            (RuntimeTurnInput("prompt", "test", "user"),),
            "canonical",
            1,
            "id",
            {"SKILL.md": b"test"},
            (),
            environment,
        )
        validate_request(request)
        for changed in [
            replace(request, target="generic"),
            replace(request, turns=request.turns * 2),
            replace(request, turns=(RuntimeTurnInput("compaction", "test", "user"),)),
            replace(request, turns=(RuntimeTurnInput("prompt", "test", "model"),)),
        ]:
            with self.assertRaises(CodexRuntimeError):
                validate_request(changed)
        for path in ("../escape", "/absolute", "a/../escape", "a\\b", "a//b"):
            with self.assertRaises(CodexRuntimeError):
                validate_request(replace(request, files={"SKILL.md": b"", path: b""}))


class RpcTests(unittest.TestCase):
    def client(self, root, source, timeout=2):
        return RpcClient(
            [sys.executable, "-u", "-c", source],
            cwd=root,
            env={},
            log=Path(root) / "trace.jsonl",
            timeout=timeout,
        )

    def test_interleaved_notifications_preserved(self):
        source = "import sys,json\nr=json.loads(sys.stdin.readline())\nprint(json.dumps({'method':'notice','params':{}}))\nprint(json.dumps({'id':r['id'],'result':{'ok':True}}))\n"
        with tempfile.TemporaryDirectory() as root:
            client = self.client(root, source)
            try:
                self.assertEqual({"ok": True}, client.call("test", {}))
                self.assertEqual("notice", client.events[0]["method"])
            finally:
                client.close()
            self.assertEqual(3, len(Path(root, "trace.jsonl").read_text().splitlines()))

    def test_timeout_and_eof_retain_partial_log(self):
        for source, timeout in [("import time; time.sleep(5)", 0.05), ("pass", 2)]:
            with tempfile.TemporaryDirectory() as root:
                client = self.client(root, source, timeout)
                try:
                    with self.assertRaises(CodexRuntimeError):
                        client.call("test", {})
                finally:
                    client.close()
                self.assertIsNotNone(client.process.poll())
                self.assertEqual(
                    "send",
                    json.loads(Path(root, "trace.jsonl").read_text())["direction"],
                )


class CodexAdapterIntegrationTests(unittest.TestCase):
    def test_paired_collector_through_fake_stdio_server(self):
        from harnessmith.codex_runtime import CodexEvaluator
        from harnessmith.evaluation import load_scenario
        from harnessmith.runtime_evidence import run_runtime_evidence

        root = Path(__file__).resolve().parents[1]
        source = r"""
import json, os, sys
from pathlib import Path

def send(value):
    print(json.dumps(value), flush=True)

# Preserve a deterministic system-tool PATH without inheriting other variables.
assert 'shell_environment_policy.inherit="none"' in sys.argv
assert 'shell_environment_policy.set.PATH="/usr/bin:/bin:/usr/sbin:/sbin"' in sys.argv
home = Path(os.environ['CODEX_HOME'])
assert (home / 'auth.json').read_text() == '{}'
assert (home / 'auth.json').stat().st_mode & 0o777 == 0o600
assert not (home / 'config.toml').exists()
for line in sys.stdin:
    request = json.loads(line)
    method, params = request['method'], request.get('params', {})
    if method == 'initialized':
        continue
    result = {}
    if method == 'skills/list':
        result = {'data': [{'skills': [{'path': '/ambient/SKILL.md'}], 'errors': []}]}
    elif method == 'thread/start':
        assert params['ephemeral'] is True
        assert params['approvalPolicy'] == 'never'
        assert params['config']['skills.config'] == [{'path': '/ambient/SKILL.md', 'enabled': False}]
        result = {'model': params['model'], 'sandbox': {'type': 'readOnly'}, 'thread': {'id': 'thread'}}
    elif method == 'turn/start':
        skill = Path(params['input'][1]['path'])
        assert skill.is_file()
        assert 'HSM-7391-ORCHID' not in params['input'][0]['text']
        result = {'turn': {'id': 'turn'}}
    send({'id': request['id'], 'result': result})
    if method == 'turn/start':
        items = []
        reference = skill.parent / 'references/lookup.md'
        if reference.exists():
            items.append({'id': 'read', 'type': 'commandExecution', 'cwd': str(skill.parent),
                          'status': 'completed', 'exitCode': 0,
                          'commandActions': [{'type': 'read', 'path': str(reference)}]})
        items.append({'id': 'answer', 'type': 'agentMessage', 'text': 'HSM-7391-ORCHID'})
        for item in items:
            send({'method': 'item/completed', 'params': {'threadId': 'thread', 'turnId': 'turn', 'item': item}})
        send({'method': 'thread/tokenUsage/updated', 'params': {'threadId': 'thread', 'turnId': 'turn',
              'tokenUsage': {'total': {'inputTokens': 123, 'outputTokens': 10}}}})
        send({'method': 'turn/completed', 'params': {'threadId': 'thread',
              'turn': {'id': 'turn', 'status': 'completed'}}})
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            executable = path / "fake-codex"
            executable.write_text("#!" + sys.executable + "\n" + source)
            executable.chmod(0o755)
            auth = path / "auth.json"
            auth.write_text("{}")
            evaluator = CodexEvaluator(
                executable=executable, auth_file=auth, output_dir=path / "raw"
            )
            # Exercise quoted YAML names through package installation and RPC.
            original_evaluate = evaluator.evaluate

            def quoted_name(request):
                files = dict(request.files)
                files["SKILL.md"] = files["SKILL.md"].replace(
                    b"name: runtime-probe", b'name: "runtime-probe"'
                )
                return original_evaluate(replace(request, files=files))

            evaluator.evaluate = quoted_name
            report = run_runtime_evidence(
                load_scenario(root / "evaluations/scenarios/runtime-probe-codex.json"),
                evaluator,
                repository_root=root,
                environment=RuntimeEnvironment(*(["test"] * 10)),
                samples=2,
                enabled=True,
                evidence_kind="mock",
            )
            self.assertTrue(report["passed"])
            self.assertEqual(4, len(list((path / "raw").glob("*.jsonl"))))
            self.assertEqual(
                ["canonical", "compiled", "compiled", "canonical"],
                [item["variant"] for item in report["observations"]],
            )


if __name__ == "__main__":
    unittest.main()
