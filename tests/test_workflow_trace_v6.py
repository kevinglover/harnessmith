"""Fresh synthetic else-printf traces; never replay or execute model commands."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from harnessmith.workflow_fidelity import PACKAGE, SETUP_COMMAND
from harnessmith.workflow_trace_v5 import normalize_events as normalize_v5
from harnessmith.workflow_trace_v6 import normalize_events

CONFIG = ".specify/extensions.yml"
REFERENCE = PACKAGE + "/references/project-generation.md"
OUTPUT = "NO_EXTENSIONS_FILE\n"


def event(method, **params):
    return {"method": method, "params": {"threadId": "t", "turnId": "u", **params}}


class WorkflowTraceV6Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve() / "workspace"
        self.workspace.mkdir()
        self.manifest = {"model": "gpt-6-luna", "target": "checklists/security.md",
                         "baseline": {}, "pinned_absent_paths": [CONFIG]}
        self.pin(REFERENCE, b"# Generation\nAsk requirements-quality questions.\n")
        (self.workspace / ".specify").mkdir(exist_ok=True)

    def pin(self, path, data):
        target = self.workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        self.manifest["baseline"][path] = hashlib.sha256(data).hexdigest()
        self.inventory()

    def inventory(self):
        self.manifest["baseline_inventory_sha256"] = hashlib.sha256(json.dumps(
            self.manifest["baseline"], sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest()

    def conditional(self, path=CONFIG, yes=None, no="printf 'NO_EXTENSIONS_FILE\\n'", test="-f"):
        return f"if [ {test} {path} ]; then {yes or 'cat ' + path}; else {no}; fi"

    def command(self, command=None, output=OUTPUT, **overrides):
        item = {"id": "absence", "type": "commandExecution", "status": "completed",
                "command": command or self.conditional(), "cwd": str(self.workspace),
                "exitCode": 0, "aggregatedOutput": output, "commandActions": [], **overrides}
        return [event("item/started", item={**item, "status": "inProgress"}),
                event("item/completed", item=item)]

    def stream(self, items):
        return items + [event("thread/tokenUsage/updated", tokenUsage={"total": {
            "inputTokens": 10, "cachedInputTokens": 0, "outputTokens": 1,
            "reasoningOutputTokens": 0, "totalTokens": 11}}),
            event("turn/completed", turn={"id": "u", "status": "completed"})]

    def normalize(self, items, normalizer=normalize_events, **kwargs):
        return normalizer(self.stream(items), thread_id="t", turn_id="u",
                          workspace=self.workspace, manifest=self.manifest, latency_ms=1, **kwargs)

    def certificates(self, result):
        return [fact for fact in result["diagnostics"] if fact.get("absence_certificate")]

    def assertNoCertificate(self, items, **kwargs):
        result = self.normalize(items, **kwargs)
        self.assertEqual([], self.certificates(result))
        return result

    def test_exact_else_printf_repairs_only_synthetic_false_certificate(self):
        items = self.command()
        before_items, before_manifest = copy.deepcopy(items), copy.deepcopy(self.manifest)
        old = self.normalize(items, normalize_v5)
        self.assertFalse(old["diagnostics"][0]["certified_absence"])
        result = self.normalize(items)
        certificate = self.certificates(result)[0]
        self.assertTrue(certificate["certified_absence"])
        self.assertEqual(6, result["schema_version"])
        self.assertEqual("codex-workflow-trace-v6", result["instrumentation"])
        self.assertEqual("codex-workflow-trace-v5", result["base_normalizer"])
        self.assertEqual((0, 1), (certificate["raw_start_index"], certificate["raw_completion_index"]))
        proof = certificate["absence_certificate"]
        self.assertEqual("literal-else-printf", proof["proof"])
        self.assertEqual(hashlib.sha256(OUTPUT.encode()).hexdigest(), proof["captured_output_sha256"])
        self.assertEqual(self.manifest["baseline_inventory_sha256"], proof["baseline_inventory_sha256"])
        self.assertFalse(proof["stderr_stripped"])
        self.assertEqual(old["events"], result["events"])
        self.assertEqual(old["issues"], result["issues"])
        self.assertEqual(before_items, items)
        self.assertEqual(before_manifest, self.manifest)
        self.assertEqual(old, self.normalize(items, normalize_v5))

    def test_quoted_unquoted_and_absolute_literal_paths(self):
        for path in (CONFIG, shlex.quote("./" + CONFIG), '"' + CONFIG + '"',
                     shlex.quote(str(self.workspace / CONFIG))):
            with self.subTest(path=path):
                result = self.normalize(self.command(self.conditional(path)))
                self.assertEqual(1, len(self.certificates(result)))

    def test_supported_literal_printf_forms_and_shell_wrapper(self):
        for no, output in (("printf NO_EXTENSIONS_FILE", "NO_EXTENSIONS_FILE"),
                           ("printf '%s\\n' 'NO_EXTENSIONS_FILE'", OUTPUT),
                           ('printf "NO_EXTENSIONS_FILE\\n"', OUTPUT),
                           ("printf 'NONE\\tHERE\\r\\n'", "NONE\tHERE\r\n")):
            with self.subTest(no=no):
                command = "/bin/zsh -c " + shlex.quote(self.conditional(no=no))
                self.assertEqual(1, len(self.certificates(self.normalize(self.command(command, output)))))

    def test_login_interactive_and_extra_argument_candidate_wrappers_rejected(self):
        body = shlex.quote(self.conditional())
        for command in ("/bin/zsh -lc " + body, "/bin/bash -ic " + body,
                        "sh -c " + body + " ignored", "bash -l -c " + body):
            with self.subTest(command=command):
                self.assertNoCertificate(self.command(command))

    def test_login_shell_prefix_read_cannot_establish_read_only_prefix(self):
        reference = self.command("/bin/zsh -lc " + shlex.quote("cat " + REFERENCE),
                                 (self.workspace / REFERENCE).read_text(), id="reference")
        old = self.normalize(reference + self.command(), normalize_v5)
        self.assertEqual([], old["issues"])
        self.assertNoCertificate(reference + self.command())

    def test_recorded_absolute_root_is_mapped_without_rewriting_raw_command(self):
        recorded = Path("/recorded/isolated/workspace")
        command = self.conditional(shlex.quote(str(recorded / CONFIG)))
        result = self.normalize(self.command(command, cwd=str(recorded)), recorded_workspace=recorded)
        self.assertEqual(command, self.certificates(result)[0]["raw_command"])

    def test_known_complete_reference_prefix_and_later_mutation_are_allowed(self):
        reference = self.command("cat " + REFERENCE, (self.workspace / REFERENCE).read_text(), id="ref")
        write = {"id": "write", "type": "fileChange", "status": "completed",
                 "changes": [{"path": self.manifest["target"], "kind": {"type": "update"}, "diff": "synthetic"}]}
        later = [event("item/started", item={**write, "status": "inProgress"}),
                 event("item/completed", item=write)]
        result = self.normalize(reference + self.command() + later)
        self.assertEqual(1, len(self.certificates(result)))
        self.assertEqual((2, 3), (self.certificates(result)[0]["raw_start_index"],
                                self.certificates(result)[0]["raw_completion_index"]))

    def test_literal_label_without_test_cannot_certify_absence(self):
        self.assertNoCertificate(self.command("printf 'NO_EXTENSIONS_FILE\\n'"))

    def test_wrong_test_read_path_or_directory_test_cannot_certify(self):
        commands = [self.conditional("other.yml"), self.conditional(yes="cat other.yml"),
                    self.conditional(test="-d"), self.conditional(yes="rg --files .specify"),
                    self.conditional(yes="cat " + CONFIG + " " + CONFIG)]
        for command in commands:
            with self.subTest(command=command):
                self.assertNoCertificate(self.command(command))

    def test_present_file_and_directory_are_not_absence(self):
        target = self.workspace / CONFIG
        target.write_text("hooks: {}\n")
        self.assertNoCertificate(self.command())
        target.unlink()
        target.mkdir()
        self.assertNoCertificate(self.command())

    def test_pinned_absence_inventory_and_hash_are_mandatory(self):
        original = copy.deepcopy(self.manifest)
        for change in ({"pinned_absent_paths": []}, {"baseline_inventory_sha256": "wrong"},
                       {"baseline": {CONFIG: "present"}},
                       {"baseline": {CONFIG + "/child": "directory"}}):
            with self.subTest(change=change):
                self.manifest = {**original, **change}
                if "baseline" in change:
                    self.inventory()
                self.assertNoCertificate(self.command())
        self.manifest = original
        del self.manifest["baseline_inventory_sha256"]
        self.assertNoCertificate(self.command())

    def test_symlink_target_and_parent_are_rejected(self):
        target = self.workspace / CONFIG
        target.symlink_to("missing.yml")
        self.assertNoCertificate(self.command())
        target.unlink()
        (self.workspace / ".specify").rmdir()
        actual = self.workspace / "actual"
        actual.mkdir()
        (self.workspace / ".specify").symlink_to(actual, target_is_directory=True)
        self.assertNoCertificate(self.command())

    def test_outside_path_or_cwd_never_certifies(self):
        self.assertNoCertificate(self.command(self.conditional("/tmp/extensions.yml")))
        self.assertNoCertificate(self.command(cwd="/tmp"))
        self.assertNoCertificate(self.command(self.conditional("../outside.yml")))

    def test_hidden_side_effects_in_either_branch_and_extra_chains_rejected(self):
        commands = [self.conditional(yes="cat " + CONFIG + "; touch hidden"),
                    self.conditional(yes="cat " + CONFIG + " && touch hidden"),
                    self.conditional(no="printf 'NO_EXTENSIONS_FILE\\n'; touch hidden"),
                    self.conditional(no="printf 'NO_EXTENSIONS_FILE\\n' > hidden"),
                    self.conditional() + " && printf ''",
                    "printf ''; " + self.conditional(),
                    self.conditional() + " | cat", self.conditional() + " &"]
        for command in commands:
            with self.subTest(command=command):
                self.assertNoCertificate(self.command(command))

    def test_dynamic_output_unsupported_formats_arguments_and_empty_output_rejected(self):
        outputs = ["printf \"$LABEL\\n\"", "printf 'NO_EXTENSIONS_FILE\\n' extra",
                   "printf '%s%s' NO EXTENSIONS", "printf '%d' 0", "echo NO_EXTENSIONS_FILE",
                   "printf ''", "printf '%b' 'NO_EXTENSIONS_FILE\\n'",
                   "printf '%s' \"$(touch hidden)\"", "printf '-v'"]
        for no in outputs:
            with self.subTest(no=no):
                self.assertNoCertificate(self.command(self.conditional(no=no)))

    def test_exact_output_rejects_extra_mismatch_missing_and_runtime_errors(self):
        for output in (OUTPUT + "extra\n", "prefix\n" + OUTPUT, "NONE\n", "", None,
                       OUTPUT + "Permission denied\n", OUTPUT + "SyntaxError: bad\n"):
            with self.subTest(output=output):
                self.assertNoCertificate(self.command(output=output))

    def test_cache_warning_is_never_stripped_from_new_shell_certificate(self):
        cache = ("python3: warning: confstr() failed with code 5: couldn't get path of "
                 "DARWIN_USER_TEMP_DIR; using /tmp instead\n"
                 "python3: error: couldn't create cache file '/tmp/xcrun_db-AbC123' "
                 "(errno=Operation not permitted)\n")
        self.assertNoCertificate(self.command(output=cache + OUTPUT))

    def test_nonzero_failed_noninteger_exit_and_bad_source_rejected(self):
        for overrides in ({"exitCode": 1}, {"status": "failed"}, {"exitCode": False},
                          {"exitCode": "0"}, {"source": "untrusted"}, {"commandActions": None},
                          {"commandActions": [{"type": "read", "path": "other.yml"}]}):
            with self.subTest(overrides=overrides):
                self.assertNoCertificate(self.command(**overrides))

    def test_missing_duplicate_reversed_and_changed_lifecycle_rejected(self):
        original = self.command()
        traces = [[original[0]], [original[1]], original[::-1],
                  [original[0], original[0], original[1]], original + [original[1]]]
        for field, value in (("command", "printf fake"), ("cwd", str(self.workspace / ".specify")),
                             ("status", "completed"), ("type", "reasoning"), ("source", "untrusted")):
            changed = copy.deepcopy(original)
            changed[0]["params"]["item"][field] = value
            traces.append(changed)
        for trace in traces:
            with self.subTest(trace=trace):
                self.assertNoCertificate(trace)

    def test_prior_unknown_setup_hook_and_mutation_rejected(self):
        for command in ("false", SETUP_COMMAND, "sh .specify/hooks/pre.sh", "touch hidden"):
            with self.subTest(command=command):
                self.assertNoCertificate(self.command(command, "", id="prior") + self.command())
        write = {"id": "prior", "type": "fileChange", "status": "completed",
                 "changes": [{"path": self.manifest["target"], "kind": {"type": "update"}, "diff": "synthetic"}]}
        self.assertNoCertificate([event("item/started", item={**write, "status": "inProgress"}),
                                  event("item/completed", item=write)] + self.command())

    def test_unverified_earlier_absence_diagnostic_is_not_safe_prefix(self):
        earlier = self.command(self.conditional(no="echo NO_EXTENSIONS_FILE"), id="prior")
        self.assertNoCertificate(earlier + self.command())

    def test_prior_mkdir_diagnostic_with_later_write_does_not_count_as_read_only(self):
        reference = self.command("cat " + REFERENCE, (self.workspace / REFERENCE).read_text(), id="ref")
        write = {"id": "write", "type": "fileChange", "status": "completed",
                 "changes": [{"path": self.manifest["target"], "kind": {"type": "update"}, "diff": "synthetic"}]}
        later = [event("item/started", item={**write, "status": "inProgress"}),
                 event("item/completed", item=write)]
        for command in ("mkdir -p checklists", "mkdir -p checklists && printf 'created\\n'"):
            with self.subTest(command=command):
                prefix = self.command(command, "created\n" if "printf" in command else "", id="mkdir")
                items = reference + prefix + self.command() + later
                old = self.normalize(items, normalize_v5)
                self.assertEqual([], old["issues"])
                mkdir = [fact for fact in old["diagnostics"]
                         if fact.get("reason") == "artifact directory creation"]
                self.assertEqual(["write"], mkdir[0]["associated_write_item_ids"])
                result = self.assertNoCertificate(items)
                self.assertEqual(old["issues"], result["issues"])
                self.assertEqual(old["events"], result["events"])

    def test_reviewed_read_only_diagnostic_prefix_remains_admissible(self):
        for command, output in (("pwd", str(self.workspace) + "\n"),
                                ("ls .specify", ""), ("printf 'checkpoint\\n'", "checkpoint\n")):
            with self.subTest(command=command):
                result = self.normalize(self.command(command, output, id="prior") + self.command())
                self.assertEqual(1, len(self.certificates(result)))

    def test_overlapping_known_read_and_unknown_include_still_open_starts(self):
        absence = self.command()
        for command, output in (("cat " + REFERENCE, (self.workspace / REFERENCE).read_text()),
                                ("unknown", "")):
            other = self.command(command, output, id="other")
            arrangements = [[other[0], absence[0], other[1], absence[1]],
                            [other[0], absence[0], absence[1], other[1]],
                            [absence[0], other[0], other[1], absence[1]],
                            [absence[0], other[0], absence[1], other[1]],
                            [other[0], *absence], [absence[0], other[0], absence[1]]]
            for trace in arrangements:
                with self.subTest(command=command, trace=trace):
                    self.assertNoCertificate(trace)

    def test_prior_completion_without_start_and_malformed_item_block_certificate(self):
        earlier = self.command("printf label", "label", id="earlier")
        self.assertNoCertificate([earlier[1]] + self.command())
        self.assertNoCertificate([event("item/started", item={"type": "commandExecution"})] + self.command())

    def test_prior_read_source_mismatch_cannot_establish_read_only_prefix(self):
        for source in ("untrusted", "unifiedExecStartup"):
            reference = self.command("cat " + REFERENCE,
                                     (self.workspace / REFERENCE).read_text(), id="reference")
            reference[0]["params"]["item"]["source"] = source
            with self.subTest(source=source):
                old = self.normalize(reference + self.command(), normalize_v5)
                self.assertEqual([], old["issues"])
                self.assertNoCertificate(reference + self.command())

    def test_unaccounted_thread_or_turn_operation_before_checkpoint_blocks_certificate(self):
        for field in ("threadId", "turnId"):
            other = self.command("unknown", "", id="other")
            for item in other:
                item["params"][field] = "unaccounted"
            with self.subTest(field=field):
                self.assertNoCertificate(other + self.command())
                self.assertNoCertificate([other[0], *self.command()])

    def test_no_else_and_python_absence_remain_frozen(self):
        commands = [(f"if [ -f {CONFIG} ]; then cat {CONFIG}; fi", ""),
                    ("python3 -c " + shlex.quote(
                        f"from pathlib import Path; p=Path({CONFIG!r}); print('EXISTS', p.exists()); "
                        "print(p.read_text() if p.exists() else '')"), "EXISTS False\n\n")]
        for command, output in commands:
            with self.subTest(command=command):
                old = self.normalize(self.command(command, output), normalize_v5)
                result = self.normalize(self.command(command, output))
                self.assertEqual(old["diagnostics"], result["diagnostics"])
                self.assertEqual(old["events"], result["events"])
                self.assertEqual(old["issues"], result["issues"])
                self.assertEqual([], self.certificates(result))

    def test_failed_later_event_remains_a_failure(self):
        items = self.command() + self.command("false", "", id="later", exitCode=1)
        old = self.normalize(items, normalize_v5)
        result = self.normalize(items)
        self.assertEqual(1, len(self.certificates(result)))
        self.assertEqual(old["events"], result["events"])
        self.assertEqual(old["issues"], result["issues"])
        self.assertTrue(result["issues"])


if __name__ == "__main__":
    unittest.main()
