"""Fake stdio integration for the write collector; no provider access."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

from harnessmith.codex_runtime import CodexRuntimeError, RpcClient
from harnessmith.workflow_runtime import (
    MODEL,
    ORDER,
    collect_session,
    run_batch,
    sandbox_policy,
    validate_permissions,
)

ROOT = Path(__file__).resolve().parents[1]

FAKE_SERVER = r"""
import json, os, subprocess, sys, time
from pathlib import Path
if '--version' in sys.argv:
    print('mock-codex-workflow-1')
    raise SystemExit(0)
workspace = Path.cwd().resolve()
home = Path(os.environ['CODEX_HOME'])
assert (home/'auth.json').read_text() == '{}'
assert (home/'auth.json').stat().st_mode & 0o777 == 0o600
assert not (home/'config.toml').exists()
assert 'sandbox_workspace_write.network_access=false' in sys.argv
assert 'sandbox_workspace_write.exclude_slash_tmp=true' in sys.argv
manifest = json.loads((workspace.parent/'manifest.json').read_text())
target = workspace/manifest['target']
def send(v):
    print(json.dumps(v), flush=True)
def event(method, **params):
    send({'method':method,'params':{'threadId':'thread','turnId':'turn',**params}})
seq = 0
def item(value, action=None):
    global seq
    seq += 1
    value = {'id':str(seq), **value}
    event('item/started', item={**value, 'status':'inProgress'})
    if action:
        action()
    event('item/completed', item=value)
def command(cmd, reads=(), action=None):
    item({'type':'commandExecution','command':cmd,'cwd':str(workspace),
          'status':'completed','exitCode':0,'source':'agent',
          'commandActions':[{'type':'read','path':p} for p in reads]}, action)
def hook(name):
    command('python3 .pilot/marker_hook.py '+name, action=lambda:subprocess.run(
        [sys.executable,'.pilot/marker_hook.py',name],cwd=workspace,check=True,capture_output=True))
for line in sys.stdin:
    q=json.loads(line); method=q['method']; p=q.get('params',{})
    if method=='initialized': continue
    result={}
    if method=='skills/list':
        result={'data':[{'errors':[],'skills':[{'path':str(workspace/'.agents/skills/speckit-checklist/SKILL.md')},
                                              {'path':'/ambient/SKILL.md'}]}]}
    elif method=='thread/start':
        assert p['ephemeral'] is True
        assert p['approvalPolicy']=='never'
        assert p['config']['skills.config']==[{'path':'/ambient/SKILL.md','enabled':False}]
        result={'model':'gpt-6-astra' if MODE=='wrong-model' else p['model'],'cwd':str(workspace),
                'reasoningEffort':'low','approvalPolicy':'never','instructionSources':[], 'testAuthHome':str(home),
                'sandbox':{'type':'workspaceWrite','writableRoots':[], 'networkAccess':False,
                           'excludeSlashTmp':True,'excludeTmpdirEnvVar':True},'thread':{'id':'thread'}}
    elif method=='turn/start':
        assert p['effort']=='low' and p['model']=='gpt-6-luna'
        assert p['sandboxPolicy']['writableRoots']==[str(workspace)]
        assert p['sandboxPolicy']['networkAccess'] is False
        result={'turn':{'id':'turn'}}
    send({'id':q['id'],'result':result})
    if method!='turn/start': continue
    event('turn/started',turn={'id':'turn','status':'inProgress'})
    if MODE=='timeout':
        event('item/started',item={'id':'unfinished','type':'commandExecution','command':'cat spec.md','cwd':str(workspace)})
        time.sleep(3)
        continue
    for reference in manifest['expected_references']:
        path='.agents/skills/speckit-checklist/'+reference
        command('cat '+path,[path])
    if manifest['case']=='hooks':
        command('cat .specify/extensions.yml',['.specify/extensions.yml'])
        hook('pilot-pre-marker')
    command('.specify/scripts/bash/check-prerequisites.sh --json --template checklist-template',
            action=lambda:subprocess.run(['.specify/scripts/bash/check-prerequisites.sh','--json','--template','checklist-template'],
                                        cwd=workspace,check=True,capture_output=True))
    for path in manifest['required_reads']:
        if path!='.specify/extensions.yml': command('cat '+path,[path])
    questions=[
        'Are authorization roles and workspace boundaries documented? [Completeness, Spec §FR-1]',
        'Is invitation expiration quantified in requirements? [Clarity, Spec §FR-2]',
        'Are expired and reused invitation outcomes defined in requirements? [Coverage, Gap]',
        'Are record retention requirements documented? [Completeness, Gap]']
    if manifest['case']=='append': questions=questions[1:]
    base=target.read_text() if target.exists() else (
        '# Security Requirements Checklist\n\n**Purpose**: Review.\n**Created**: 2026-10-24\n'
        '**Ownership**: Reviewer approval of requirements quality.\n'
        '## Notes\n/specit is unused; /speckit-implement reads state but does not modify markers.\n').replace('\\n','\n')
    # Source is a raw string: translate test literals into actual Markdown lines.
    base=base.replace(chr(92)+'n',chr(10))
    content=base+'\n## Requirement Clarity\n\n'.replace(chr(92)+'n',chr(10))
    content+='\n'.replace(chr(92)+'n',chr(10)).join('- [ ] CHK%03d %s'%(manifest['first_id']+n,v) for n,v in enumerate(questions))+'\n'.replace(chr(92)+'n',chr(10))
    def write():
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content)
    item({'type':'fileChange','status':'completed','changes':[{'path':str(target),
          'kind':{'type':'update' if target.exists() else 'add'},'diff':content}]}, write)
    if manifest['case']=='hooks': hook('pilot-post-marker')
    if MODE=='unknown': command('echo diagnostic')
    output=('Appended to' if manifest['case']=='append' else 'Created')+' '+str(target)+'; '+str(len(questions))+' new items. Security standard reviewer PR review.'
    if manifest['case']=='hooks':
        output+=' Automatic Pre-Hook Automatic Hook EXECUTE_COMMAND: pilot-pre-marker EXECUTE_COMMAND: pilot-post-marker Optional Pre-Hook Optional Hook To execute: `/pilot-optional-pre` To execute: `/pilot-optional-post`'
    item({'type':'agentMessage','text':output})
    if MODE=='rerouted': event('model/rerouted',fromModel='gpt-6-luna',toModel='gpt-6-astra')
    if MODE!='missing-usage': event('thread/tokenUsage/updated',tokenUsage={'total':{'inputTokens':5000,'cachedInputTokens':3000,'outputTokens':80,'reasoningOutputTokens':0,'totalTokens':5080}})
    event('turn/completed',turn={'id':'turn','status':'completed'})
"""


class WorkflowRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.auth = self.root / "auth.json"
        self.auth.write_text("{}")

    def run_fake(self, mode="good", timeout=10):
        executable = self.root / ("fake-" + mode)
        executable.write_text(
            "#!" + sys.executable + "\nMODE=" + repr(mode) + "\n" + FAKE_SERVER
        )
        executable.chmod(0o755)
        output = self.root / mode
        report = run_batch(
            ROOT,
            output,
            executable=executable,
            auth_file=self.auth,
            enabled=True,
            timeout=timeout,
            evidence_kind="mock",
        )
        return report, output, executable

    def test_exact_six_no_retries_and_private_auth_cleanup(self):
        report, output, executable = self.run_fake()
        self.assertEqual(list(ORDER), [r["session_id"] for r in report["results"]])
        self.assertEqual([], report["unattempted"])
        self.assertEqual(0, report["retries"])
        self.assertTrue(
            all(r["automated_checks_passed"] for r in report["results"]), report
        )
        for session in ORDER:
            directory = output / session
            raw = [
                json.loads(line)
                for line in (directory / "raw/events.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                1,
                sum(
                    r["direction"] == "send"
                    and r["message"].get("method") == "turn/start"
                    for r in raw
                ),
            )
            self.assertTrue((directory / "before-inventory.json").exists())
            self.assertTrue((directory / "after-inventory.json").exists())
            observation = json.loads((directory / "observation.json").read_text())
            self.assertFalse(
                Path(observation["returned_configuration"]["testAuthHome"]).exists()
            )
            self.assertEqual("offline-simulation", observation["evidence_kind"])
            self.assertEqual(
                5000,
                json.loads((directory / "observation.json").read_text())["usage"][
                    "inputTokens"
                ],
            )
        with self.assertRaises(FileExistsError):
            collect_session(
                output / ORDER[0], executable=executable, auth_file=self.auth
            )
        self.assertFalse(list(output.rglob("auth.json")))

    def test_fidelity_failure_retained_and_batch_not_retried(self):
        report, output, _ = self.run_fake("unknown")
        self.assertEqual(6, report["attempted_session_count"])
        self.assertFalse(any(r["automated_checks_passed"] for r in report["results"]))
        self.assertEqual(6, len(list(output.glob("*/result.json"))))

    def test_instrumentation_failure_retains_first_and_stops_remaining(self):
        for mode in ("missing-usage", "wrong-model", "rerouted", "timeout"):
            with self.subTest(mode=mode):
                report, output, _ = self.run_fake(
                    mode, timeout=0.3 if mode == "timeout" else 10
                )
                self.assertEqual(1, report["attempted_session_count"])
                self.assertEqual(list(ORDER[1:]), report["unattempted"])
                self.assertTrue((output / ORDER[0] / "raw/events.jsonl").is_file())
                self.assertTrue((output / ORDER[0] / "after-inventory.json").is_file())
                self.assertFalse((output / ORDER[1] / "attempt.json").exists())
                observation = json.loads(
                    (output / ORDER[0] / "observation.json").read_text()
                )
                self.assertFalse(
                    Path(observation["returned_configuration"]["testAuthHome"]).exists()
                )
                if mode == "wrong-model":
                    trace = (output / ORDER[0] / "raw/events.jsonl").read_text()
                    self.assertNotIn('"method": "turn/start"', trace)

    def test_normalizer_failure_still_retains_artifacts_and_raw_output(self):
        with mock.patch(
            "harnessmith.workflow_runtime.normalize_events",
            side_effect=ValueError("mock decoder failure"),
        ):
            report, output, _ = self.run_fake()
        self.assertEqual(1, report["attempted_session_count"])
        directory = output / ORDER[0]
        self.assertTrue(
            (directory / "after/specs/001-invitations/checklists/security.md").exists()
        )
        self.assertIn("Created", (directory / "raw/events.stdout").read_text())
        self.assertEqual("ValueError", report["results"][0]["collector_error"]["type"])

    def test_process_group_close_prevents_delayed_descendant_write(self):
        marker = self.root / "late-marker"
        child = (
            "import time,pathlib;time.sleep(0.5);pathlib.Path(%r).write_text('late')"
            % str(marker)
        )
        source = (
            "import subprocess,sys,json,time;subprocess.Popen([sys.executable,'-c',%r]);"
            "q=json.loads(sys.stdin.readline());print(json.dumps({'id':q['id'],'result':{}}),flush=True);time.sleep(5)"
        ) % child
        client = RpcClient(
            [sys.executable, "-u", "-c", source],
            cwd=self.root,
            env={},
            log=self.root / "process.jsonl",
            timeout=3,
            start_new_session=True,
        )
        client.call("test", {})
        client.close()
        time.sleep(0.7)
        self.assertFalse(marker.exists())

    def test_malformed_stdout_is_retained_verbatim(self):
        source = "import sys;sys.stdin.readline();print('not-json-output',flush=True)"
        client = RpcClient(
            [sys.executable, "-u", "-c", source],
            cwd=self.root,
            env={},
            log=self.root / "invalid.jsonl",
            timeout=3,
            start_new_session=True,
        )
        try:
            with self.assertRaises(CodexRuntimeError):
                client.call("test", {})
        finally:
            client.close()
        self.assertIn("not-json-output", (self.root / "invalid.stdout").read_text())
        self.assertIn("unparsed_stdout", (self.root / "invalid.jsonl").read_text())

    def test_disabled_by_default_no_files_created(self):
        output = self.root / "disabled"
        with self.assertRaises(ValueError):
            run_batch(ROOT, output, executable="/unused", auth_file=self.auth)
        self.assertFalse(output.exists())

    def test_every_permission_boundary_checked_before_turn(self):
        good = {
            "model": MODEL,
            "reasoningEffort": "low",
            "approvalPolicy": "never",
            "cwd": str(self.root),
            "sandbox": sandbox_policy(self.root),
            "instructionSources": [],
        }
        validate_permissions(good, self.root)
        changes = [
            ("model", "gpt-6-astra"),
            ("reasoningEffort", "high"),
            ("approvalPolicy", "on-request"),
            ("cwd", "/"),
            ("instructionSources", [{"path": "/ambient/AGENTS.md"}]),
        ]
        for key, value in changes:
            changed = copy.deepcopy(good)
            changed[key] = value
            with self.assertRaises(CodexRuntimeError):
                validate_permissions(changed, self.root)
        for key, value in [
            ("networkAccess", True),
            ("excludeSlashTmp", False),
            ("excludeTmpdirEnvVar", False),
            ("writableRoots", ["/tmp"]),
            ("type", "dangerFullAccess"),
        ]:
            changed = copy.deepcopy(good)
            changed["sandbox"][key] = value
            with self.assertRaises(CodexRuntimeError):
                validate_permissions(changed, self.root)


if __name__ == "__main__":
    unittest.main()
