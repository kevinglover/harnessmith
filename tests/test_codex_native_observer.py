from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from harnessmith.codex_native_observer import CodexObserver, INSTRUMENTATION, package_digest


class CodexObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'SKILL.md'
        self.root.write_text('Synthetic skill instructions\n')
        self.policy = dict(version=INSTRUMENTATION, accounting='fresh-cumulative-only', packages=[
            dict(root=str(self.root), root_sha256=hashlib.sha256(self.root.read_bytes()).hexdigest(),
                 skill_id='synthetic', package_sha256=package_digest(self.root.parent))])
        self.observer = CodexObserver(self.policy)
        self.sequence = 0
        self.events = []

    def observe(self, method, params=None, *, direction='receive', **fields):
        self.sequence += 1
        message = dict(fields)
        if method is not None:
            message.update(method=method, params=params or {})
        result = self.observer.observe(direction, message, 'raw-' + str(self.sequence), self.sequence)
        self.events.extend(result['events'])
        return result['events']

    def begin(self, explicit=True):
        self.observe('thread/start', {}, direction='send', id=1)
        self.observe('thread/started', {'thread': {'id': 'thread'}})
        self.observe(None, id=1, result={'thread': {'id': 'thread'}})
        inputs = [{'type': 'skill', 'name': 'synthetic', 'path': str(self.root)}] if explicit else [{'type': 'text', 'text': 'review'}]
        self.observe('turn/start', dict(threadId='thread', input=inputs), direction='send', id=2)
        self.observe('turn/started', dict(threadId='thread', turn={'id': 'turn'}))
        self.observe(None, id=2, result={'turn': {'id': 'turn'}})

    def command(self, phase, **changes):
        import shlex
        item = dict(type='commandExecution', id='command', command='cat ' + shlex.quote(str(self.root)),
                    status='inProgress' if phase == 'started' else 'completed',
                    exitCode=None if phase == 'started' else 0,
                    aggregatedOutput=None if phase == 'started' else self.root.read_text())
        item.update(changes)
        return self.observe('item/' + phase, dict(threadId='thread', turnId='turn', item=item))

    def usage(self, input_tokens=10, cache=True):
        total = dict(inputTokens=input_tokens, cachedInputTokens=2, outputTokens=3, reasoningOutputTokens=1)
        if cache:
            total['cacheWriteInputTokens'] = 0
        self.observe('thread/tokenUsage/updated', dict(threadId='thread', turnId='turn',
                     tokenUsage={'total': total, 'last': {'inputTokens': 999999}}))

    def finish_turn(self):
        self.observe('turn/completed', dict(threadId='thread', turn={'id': 'turn', 'status': 'completed'}))

    def test_pending_command_is_not_execution_and_full_read_backs_explicit_use(self):
        self.begin()
        self.assertEqual(['action.proposed'], [e['kind'] for e in self.command('started')])
        kinds = [e['kind'] for e in self.command('completed')]
        self.assertEqual(['action.started', 'action.completed', 'read.observed', 'invocation.observed'], kinds)
        self.assertFalse(any(e['kind'] == 'permission.snapshot' for e in self.events))

    def test_prompt_or_answer_alone_does_not_prove_invocation(self):
        self.begin()
        self.observe('item/completed', dict(threadId='thread', turnId='turn',
            item={'type': 'agentMessage', 'id': 'answer', 'text': 'I used synthetic'}))
        self.assertFalse(any(e['kind'] == 'invocation.observed' for e in self.events))

    def test_wrong_null_noisy_and_failed_reads_do_not_prove_invocation(self):
        for output, code in ((None, 0), ('wrong', 0), (self.root.read_text() + 'noise', 0), (self.root.read_text(), 1)):
            with self.subTest(output=output, code=code):
                self.observer = CodexObserver(self.policy)
                self.events = []
                self.begin()
                self.command('started')
                kinds = [e['kind'] for e in self.command('completed', aggregatedOutput=output, exitCode=code)]
                self.assertNotIn('read.observed', kinds)
                self.assertNotIn('invocation.observed', kinds)

    def test_read_without_explicit_input_does_not_invent_implicit_activation(self):
        self.begin(explicit=False)
        self.command('started')
        kinds = [e['kind'] for e in self.command('completed')]
        self.assertIn('read.observed', kinds)
        self.assertNotIn('invocation.observed', kinds)

    def test_latest_cumulative_usage_once_without_last_double_count(self):
        self.begin()
        self.usage(10)
        self.usage(20)
        self.finish_turn()
        result = self.observer.finish()
        self.assertEqual(1, len(result))
        self.assertEqual(20, result[0]['final']['input_tokens'])
        self.assertEqual(0, result[0]['baseline']['input_tokens'])

    def test_missing_cache_write_stays_null_and_reset_is_rejected(self):
        self.begin()
        self.usage(10, cache=False)
        self.finish_turn()
        self.assertIsNone(self.observer.finish()[0]['final']['cache_write_input_tokens'])
        with self.assertRaisesRegex(ValueError, 'counter reset'):
            self.usage(5)

    def test_denied_request_has_rpc_identity_and_no_execution(self):
        self.begin()
        self.command('started')
        request = self.observe('item/commandExecution/requestApproval',
            dict(threadId='thread', turnId='turn', itemId='command', approvalId='host-callback'), id=77)
        self.observe(None, direction='send', id=77, result={'decision': 'decline'})
        resolved = self.observe('serverRequest/resolved', {'threadId': 'thread', 'requestId': 77})
        self.command('completed', status='declined', exitCode=None, aggregatedOutput=None)
        self.assertEqual('rpc:77', request[0]['data']['approval_id'])
        self.assertEqual(request[0]['event_id'], resolved[0]['causal_event_id'])
        self.assertFalse(any(e['kind'] == 'action.started' for e in self.events))

    def test_grant_causal_binding_requires_resolution(self):
        self.begin()
        self.command('started')
        self.observe('item/commandExecution/requestApproval',
            dict(threadId='thread', turnId='turn', itemId='command'), id='approval')
        self.observe(None, direction='send', id='approval', result={'decision': 'accept'})
        grant = self.observe('serverRequest/resolved', {'threadId': 'thread', 'requestId': 'approval'})[0]
        start = self.observe('item/commandExecution/outputDelta',
            dict(threadId='thread', turnId='turn', itemId='command', delta='output'))[0]
        self.assertEqual(grant['event_id'], start['causal_event_id'])

    def test_session_wide_approval_and_unqualified_lifecycle_fail_closed(self):
        self.begin()
        for method in ('thread/resume', 'thread/fork', 'thread/compact/start', 'turn/interrupt'):
            with self.assertRaises(ValueError):
                self.observe(method, {}, direction='send', id=10)
        with self.assertRaises(ValueError):
            self.observe(None, direction='send', id='unknown', result={'decision': 'acceptForSession'})

    def test_missing_duplicate_and_reordered_lifecycles_fail(self):
        self.begin()
        with self.assertRaises(ValueError):
            self.command('completed')
        self.command('started')
        with self.assertRaises(ValueError):
            self.command('started')
        self.finish_turn()
        with self.assertRaisesRegex(ValueError, 'unfinished command'):
            self.observer.finish()

    def test_package_mode_and_bytes_are_pinned(self):
        self.root.chmod(0o700)
        with self.assertRaisesRegex(ValueError, 'inventory drift'):
            CodexObserver(self.policy)
        self.root.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'root drift'):
            CodexObserver(self.policy)

    def test_wrong_thread_resolution_and_inherited_threads_are_rejected(self):
        self.begin()
        self.command('started')
        self.observe('item/commandExecution/requestApproval',
            dict(threadId='thread', turnId='turn', itemId='command'), id='approval')
        self.observe(None, direction='send', id='approval', result={'decision': 'accept'})
        with self.assertRaisesRegex(ValueError, 'wrong thread'):
            self.observe('serverRequest/resolved', {'threadId': 'other', 'requestId': 'approval'})
        for field in ('forkedFromId', 'parentThreadId'):
            with self.assertRaisesRegex(ValueError, 'fresh-thread'):
                self.observe('thread/started', {'thread': {'id': 'child', field: 'thread'}})


if __name__ == '__main__':
    unittest.main()
