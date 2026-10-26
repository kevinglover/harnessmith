"""Fresh synthetic traces for schema-5 reads; no historical replay or code execution."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from harnessmith.workflow_fidelity import PACKAGE, SETUP_COMMAND
from harnessmith.workflow_trace_v4 import normalize_events as normalize_v4
from harnessmith.workflow_trace_v5 import normalize_events


TARGET = "specs/001-invitations/checklists/security.md"
CONFIG = ".specify/extensions.yml"
CONSTITUTION = ".specify/memory/constitution.md"
REFERENCE = PACKAGE + "/references/project-generation.md"
CACHE = (
    "python3: warning: confstr() failed with code 5: couldn't get path of "
    "DARWIN_USER_TEMP_DIR; using /tmp instead\n"
    "python3: error: couldn't create cache file '/tmp/xcrun_db-AbC123' "
    "(errno=Operation not permitted)\n"
)


def event(method, **params):
    return {"method": method, "params": {"threadId": "t", "turnId": "u", **params}}


class WorkflowTraceV5Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name).resolve() / "workspace"
        self.workspace.mkdir()
        self.manifest = {"model": "gpt-6-luna", "target": TARGET, "baseline": {}}
        self.before = b"# Security\n- [x] CHK001 First\n- [X] CHK002 Second\n"
        self.addition = b"- [ ] CHK003 Is expiry specified? [Gap]\n"
        self.pin(TARGET, self.before)
        self.manifest["baseline_target_hex"] = self.before.hex()
        self.constitution = self.pin(CONSTITUTION, b"# Principles\nPreserve review states.\n")
        self.pin(REFERENCE, b"# Generation\nAsk requirements questions.\n")
        self.pin(".specify/templates/checklist-template.md", b"# Checklist\n")
        self.absent()

    def pin(self, path, data):
        destination = self.workspace / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        self.manifest["baseline"][path] = hashlib.sha256(data).hexdigest()
        self.inventory()
        return data

    def inventory(self):
        self.manifest["baseline_inventory_sha256"] = hashlib.sha256(
            json.dumps(self.manifest["baseline"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def absent(self):
        self.manifest["pinned_absent_paths"] = [CONFIG]
        self.inventory()

    def exists_script(self, path=CONSTITUTION):
        return (f"from pathlib import Path; p=Path({path!r}); print('EXISTS', p.exists()); "
                "print(p.read_text() if p.exists() else '')")

    def bytes_script(self, path=TARGET):
        return (f"from pathlib import Path; p=Path({path!r}); b=p.read_bytes(); "
                "print('BEFORE BYTES'); print(repr(b)); print('BEFORE TEXT'); print(b.decode())")

    def bytes_output(self, data):
        return "BEFORE BYTES\n" + repr(data) + "\nBEFORE TEXT\n" + data.decode() + "\n"

    def python(self, script):
        return "python3 -c " + shlex.quote(script)

    def command(self, command, output="", **overrides):
        item = {"id": "read", "type": "commandExecution", "status": "completed",
                "command": command, "cwd": str(self.workspace), "exitCode": 0,
                "aggregatedOutput": output, "commandActions": [], **overrides}
        return [event("item/started", item={**item, "status": "inProgress"}),
                event("item/completed", item=item)]

    def write(self, **overrides):
        item = {"id": "write", "type": "fileChange", "status": "completed",
                "changes": [{"path": TARGET, "kind": {"type": "update"}, "diff": "synthetic"}],
                **overrides}
        return [event("item/started", item={**item, "status": "inProgress"}),
                event("item/completed", item=item)]

    def normalize(self, events, **kwargs):
        return normalize_events(
            events + [event("thread/tokenUsage/updated", tokenUsage={"total": {
                "inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 1,
                "reasoningOutputTokens": 0, "totalTokens": 11}}),
                event("turn/completed", turn={"id": "u", "status": "completed"})],
            thread_id="t", turn_id="u", workspace=self.workspace, manifest=self.manifest,
            latency_ms=1, **kwargs)

    def reads(self, result):
        return [e for e in result["events"] if e["type"] == "read"]

    def assertUnverified(self, result):
        self.assertFalse(self.reads(result))
        self.assertTrue(any(e["type"] == "unknown" for e in result["events"]))

    def test_exists_reads_exact_pinned_input_with_complete_lifecycle(self):
        result = self.normalize(self.command(
            self.python(self.exists_script()), "EXISTS True\n" + self.constitution.decode() + "\n"))
        self.assertEqual([], result["issues"])
        self.assertEqual(5, result["schema_version"])
        self.assertEqual("codex-workflow-trace-v5", result["instrumentation"])
        read = self.reads(result)[0]
        self.assertEqual(hashlib.sha256(self.constitution).hexdigest(), read["read_sha256"])
        self.assertTrue(read["read_coverage"]["complete"])
        self.assertEqual((0, 1), (read["raw_start_index"], read["raw_completion_index"]))

    def test_absence_requires_pinned_inventory_and_precedes_mutations(self):
        result = self.normalize(self.command(self.python(self.exists_script(CONFIG)), "EXISTS False\n\n"))
        self.assertEqual([], result["issues"])
        certificate = result["diagnostics"][0]
        self.assertEqual(CONFIG, certificate["path"])
        self.assertTrue(certificate["certified_absence"])
        self.assertEqual("fixture absence", certificate["reason"])
        self.assertEqual((0, 1), (certificate["raw_start_index"], certificate["raw_completion_index"]))
        for field in ("pinned_absent_paths", "baseline_inventory_sha256"):
            value = self.manifest.pop(field)
            self.assertUnverified(self.normalize(self.command(
                self.python(self.exists_script(CONFIG)), "EXISTS False\n\n")))
            self.manifest[field] = value

    def test_presence_of_extension_is_read_not_absence(self):
        self.manifest["pinned_absent_paths"] = []
        data = self.pin(CONFIG, b"hooks: {}\n")
        result = self.normalize(self.command(
            self.python(self.exists_script(CONFIG)), "EXISTS True\n" + data.decode() + "\n"))
        self.assertEqual(CONFIG, self.reads(result)[0]["path"])
        self.assertFalse(any(e.get("certified_absence") for e in result["diagnostics"]))

    def test_absence_rejects_changed_present_inventory_and_other_paths(self):
        events = self.command(self.python(self.exists_script(CONFIG)), "EXISTS False\n\n")
        self.manifest["baseline_inventory_sha256"] = "wrong"
        self.assertUnverified(self.normalize(events))
        self.inventory()
        self.pin(CONFIG, b"hooks: {}\n")
        self.assertUnverified(self.normalize(events))
        self.manifest["pinned_absent_paths"] = ["other.md"]
        self.assertUnverified(self.normalize(self.command(
            self.python(self.exists_script("other.md")), "EXISTS False\n\n")))

    def test_absence_rejects_prior_unknown_write_and_setup(self):
        for preceding in (self.command("false", "", id="unknown", exitCode=1), self.write(),
                          self.command(SETUP_COMMAND, "", id="setup")):
            result = self.normalize(preceding + self.command(
                self.python(self.exists_script(CONFIG)), "EXISTS False\n\n"))
            self.assertFalse(any(e.get("certified_absence") for e in result["diagnostics"]))
            self.assertTrue(result["issues"])

    def test_labeled_byte_read_is_prewrite_when_artifact_has_later_changes(self):
        (self.workspace / TARGET).write_bytes(self.before + self.addition)
        result = self.normalize(self.command(self.python(self.bytes_script()), self.bytes_output(self.before)) + self.write())
        read = self.reads(result)[0]
        self.assertTrue(read["read_before_write"])
        self.assertNotIn("read_after_write", read)
        self.assertEqual(hashlib.sha256(self.before).hexdigest(), read["read_sha256"])

    def test_final_labeled_byte_read_requires_exact_final_bytes_after_write(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        result = self.normalize(self.write() + self.command(self.python(self.bytes_script()), self.bytes_output(after)))
        self.assertEqual([], result["issues"])
        read = self.reads(result)[0]
        self.assertTrue(read["read_after_write"])
        self.assertEqual(hashlib.sha256(after).hexdigest(), read["read_sha256"])
        self.assertEqual((2, 3), (read["raw_start_index"], read["raw_completion_index"]))

    def test_final_exists_read_has_exact_current_bytes(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        result = self.normalize(self.write() + self.command(
            self.python(self.exists_script(TARGET)), "EXISTS True\n" + after.decode() + "\n"))
        self.assertTrue(self.reads(result)[0]["read_after_write"])

    def test_final_read_rejects_before_bytes_or_changed_final_file(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        self.assertUnverified(self.normalize(self.write() + self.command(
            self.python(self.bytes_script()), self.bytes_output(self.before))))
        (self.workspace / TARGET).write_bytes(after + b"later\n")
        self.assertUnverified(self.normalize(self.write() + self.command(
            self.python(self.bytes_script()), self.bytes_output(after))))

    def test_read_cannot_acquire_final_proof_without_recorded_write(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        self.assertUnverified(self.normalize(self.command(
            self.python(self.bytes_script()), self.bytes_output(after))))

    def test_failed_write_or_intervening_unknown_blocks_final_read(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        for preceding in (self.write(status="failed"), self.write() + self.command("unknown", id="unknown")):
            self.assertUnverified(self.normalize(preceding + self.command(
                self.python(self.bytes_script()), self.bytes_output(after))))

    def test_overlapping_write_lifecycles_cannot_certify_read(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        write, read = self.write(), self.command(self.python(self.bytes_script()), self.bytes_output(after))
        self.assertUnverified(self.normalize([write[0], read[0], write[1], read[1]]))
        self.assertUnverified(self.normalize([write[0], read[0], read[1], write[1]]))

    def test_complete_cat_python_discovery_chain_with_exact_cache_pairs(self):
        command = ("cat " + REFERENCE + " && " + self.python(self.exists_script(CONFIG)) + " && "
                   + self.python(self.bytes_script()) + " && rg --files --hidden .specify")
        reference = (self.workspace / REFERENCE).read_text()
        output = reference + CACHE * 2 + "EXISTS False\n\n" + CACHE * 2 + self.bytes_output(self.before) + CONSTITUTION + "\n"
        result = self.normalize(self.command(command, output))
        self.assertEqual([], result["issues"])
        self.assertEqual([REFERENCE, TARGET], [e["path"] for e in self.reads(result)])
        cache = [e for e in result["diagnostics"] if "cache warning" in e.get("reason", "")]
        self.assertEqual(CACHE * 4, cache[0]["raw_warning_output"])
        discovery = [e for e in result["diagnostics"] if e.get("reason") == "file discovery"][0]
        self.assertFalse(discovery["certifies_absence"])
        self.assertFalse(discovery["certifies_file_contents"])

    def test_no_match_discovery_retains_proven_reads_and_failure(self):
        command = self.python(self.bytes_script()) + " && rg --files -g 'missing/**'"
        for status in ("completed", "failed"):
            result = self.normalize(self.command(command, self.bytes_output(self.before), exitCode=1, status=status))
            self.assertEqual(1, len(self.reads(result)))
            self.assertEqual(0, self.reads(result)[0]["exit_code"])
            self.assertTrue(any(e.get("status") == "failed" for e in result["events"]))

    def test_discovery_requires_scoped_real_complete_listing(self):
        prefix = self.python(self.bytes_script())
        for suffix, output in (("rg --files", CONSTITUTION + "\n"),
                               ("rg --files --hidden", CONSTITUTION + "\n"),
                               ("rg --files .specify", TARGET + "\n"),
                               ("rg --files .specify", "missing.md\n"),
                               ("rg --files .specify", CONSTITUTION),
                               ("rg --files .specify", CONSTITUTION + "\n" + CONSTITUTION + "\n"),
                               ("rg --files .specify --follow", CONSTITUTION + "\n")):
            self.assertUnverified(self.normalize(self.command(prefix + " && " + suffix,
                                                              self.bytes_output(self.before) + output)))

    def test_readonly_chain_rejects_unbounded_producers_masking_and_partial_output(self):
        prefix, output = self.python(self.bytes_script()), self.bytes_output(self.before)
        for command, text in ((prefix + " && touch sentinel", output),
                              (prefix + " || true", output),
                              (prefix + "; cat " + TARGET, output + self.before.decode()),
                              (prefix + " | cat", output), (prefix, output[:10]),
                              (prefix, output + "extra\n"), (prefix, output[:-1])):
            self.assertUnverified(self.normalize(self.command(command, text)))
        self.assertFalse((self.workspace / "sentinel").exists())

    def test_dynamic_or_side_effect_ast_never_executes(self):
        sentinel = self.workspace / "must-not-exist"
        scripts = [self.bytes_script().replace("p=Path", "p=input"),
                   self.bytes_script().replace("b=p.read_bytes()", "b=p.read_text().encode()"),
                   self.bytes_script().replace("print(repr(b))", "print(repr(b[:2]))"),
                   self.bytes_script().replace("print(b.decode())", "print(b.decode('utf-8'))"),
                   self.bytes_script().replace("print('BEFORE TEXT')", "print(input())"),
                   self.bytes_script().replace("from pathlib import Path", "from evil import Path"),
                   self.bytes_script() + f"; Path({str(sentinel)!r}).touch()",
                   self.exists_script().replace("p.exists() else ''", "p.exists() else input()"),
                   self.exists_script().replace("p.read_text()", "p.write_text('changed')")]
        for script in scripts:
            self.assertUnverified(self.normalize(self.command(self.python(script), self.bytes_output(self.before))))
        self.assertFalse(sentinel.exists())
        self.assertEqual(self.before, (self.workspace / TARGET).read_bytes())

    def test_byte_labels_names_unicode_and_unlabeled_forms(self):
        self.before = "# Café\n- [X] CHK001 Échéance\n".encode()
        self.pin(TARGET, self.before)
        self.manifest["baseline_target_hex"] = self.before.hex()
        for script, output in ((self.bytes_script().replace("p=Path", "target=Path").replace("b=p.read_bytes()", "data=target.read_bytes()").replace("repr(b)", "repr(data)").replace("b.decode()", "data.decode()"), self.bytes_output(self.before)),
                               (self.bytes_script().replace("print('BEFORE BYTES'); ", "").replace("print('BEFORE TEXT'); ", ""), repr(self.before) + "\n" + self.before.decode() + "\n"),
                               (self.bytes_script().replace("print('BEFORE BYTES')", "print(b'BEFORE BYTES')"), self.bytes_output(self.before).replace("BEFORE BYTES\n", "b'BEFORE BYTES'\n", 1))):
            self.assertEqual([], self.normalize(self.command(self.python(script), output))["issues"])

    def test_variable_shadowing_reordered_or_missing_prints_rejected(self):
        for script in (self.bytes_script().replace("b=p.read_bytes()", "p=p.read_bytes()"),
                       self.bytes_script().replace("b", "print"),
                       self.bytes_script().replace("print(repr(b)); ", ""),
                       self.bytes_script().replace("print(b.decode())", "print(repr(b))"),
                       self.bytes_script().replace("print(repr(b))", "print(b.decode())"),
                       self.bytes_script() + "; print('extra')"):
            self.assertUnverified(self.normalize(self.command(self.python(script), self.bytes_output(self.before))))

    def test_outside_symlink_and_relocated_paths(self):
        for path in ("../outside", "/tmp/outside"):
            result = self.normalize(self.command(self.python(self.exists_script(path)), "EXISTS False\n\n"))
            self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))
        (self.workspace / "alias").symlink_to(self.workspace / TARGET)
        result = self.normalize(self.command(self.python(self.bytes_script("alias")), self.bytes_output(self.before)))
        self.assertTrue(any(i["kind"] == "isolation" for i in result["issues"]))
        recorded = Path("/recorded/workspace")
        result = self.normalize(self.command(self.python(self.bytes_script(str(recorded / TARGET))),
                                             self.bytes_output(self.before), cwd=str(recorded)), recorded_workspace=recorded)
        self.assertEqual([], result["issues"])
        self.assertIn(str(recorded), self.reads(result)[0]["raw_command"])

    def test_read_requires_pinned_hash_declared_path_and_matching_lifecycle(self):
        command, output = self.python(self.bytes_script()), self.bytes_output(self.before)
        events = self.command(command, output)
        self.assertUnverified(self.normalize(events[1:]))
        events[0]["params"]["item"]["command"] = "different"
        self.assertUnverified(self.normalize(events))
        self.assertUnverified(self.normalize(self.command(command, output, commandActions=[{"type": "read", "path": CONFIG}])))
        self.manifest["baseline"][TARGET] = "wrong"
        self.assertUnverified(self.normalize(self.command(command, output)))

    def test_invalid_source_status_exit_and_non_utf8_are_unverified(self):
        command, output = self.python(self.bytes_script()), self.bytes_output(self.before)
        for overrides in ({"source": "unknown"}, {"status": "failed"}, {"exitCode": 1}, {"exitCode": False},
                          {"status": "interrupted"}, {"aggregatedOutput": None}):
            self.assertUnverified(self.normalize(self.command(command, output, **overrides)))
        self.pin(TARGET, b"\xff")
        self.manifest["baseline_target_hex"] = "ff"
        self.assertUnverified(self.normalize(self.command(command, output)))

    def test_cache_exceptions_require_whole_output_and_never_mask_real_error(self):
        command, output = self.python(self.bytes_script()), self.bytes_output(self.before)
        for copies in (1, 2, 3):
            result = self.normalize(self.command(command, CACHE * copies + output))
            self.assertEqual([], result["issues"])
            self.assertEqual(CACHE * copies, result["diagnostics"][0]["raw_warning_output"])
        for text in (CACHE + output[:10],
                     CACHE.replace("code 5", "code 6") + output,
                     CACHE * 2 + output + "SyntaxError: actual error\n",
                     CACHE + output + "Permission denied\n"):
            result = self.normalize(self.command(command, text))
            self.assertUnverified(result)
            self.assertTrue(any(e.get("status") == "failed" for e in result["events"]))

    def test_command_records_retain_validated_cwd_context(self):
        root = self.normalize(self.command("git diff -- " + TARGET))
        self.assertEqual(str(self.workspace), root["command_records"][0]["raw_cwd"])
        self.assertEqual(".", root["command_records"][0]["cwd_relative"])
        subdir = self.workspace / "specs"
        nested = self.normalize(self.command("git diff -- " + TARGET, cwd=str(subdir)))
        self.assertEqual("specs", nested["command_records"][0]["cwd_relative"])
        outside = self.normalize(self.command("git diff -- " + TARGET, cwd=str(self.workspace.parent)))
        self.assertIsNone(outside["command_records"][0]["cwd_relative"])
        recorded = Path("/recorded/workspace")
        relocated = self.normalize(self.command("git diff -- " + TARGET, cwd=str(recorded)),
                                   recorded_workspace=recorded)
        self.assertEqual(".", relocated["command_records"][0]["cwd_relative"])

    def test_standalone_cat_reference_has_exact_baseline_hash_and_coverage(self):
        data = (self.workspace / REFERENCE).read_bytes()
        for command in ("cat " + REFERENCE, "/bin/cat -- " + REFERENCE):
            result = self.normalize(self.command(command, data.decode()))
            self.assertEqual([], result["issues"])
            read = self.reads(result)[0]
            self.assertEqual(REFERENCE, read["path"])
            self.assertTrue(read["read_coverage"]["complete"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), read["read_sha256"])

    def test_standalone_cat_rejects_partial_mismatch_and_unpinned_outputs(self):
        data = (self.workspace / REFERENCE).read_text()
        for output in (data[:10], data + "extra\n", data[:-1], CACHE + data):
            self.assertUnverified(self.normalize(self.command("cat " + REFERENCE, output)))
        self.manifest["baseline"][REFERENCE] = "wrong"
        self.assertUnverified(self.normalize(self.command("cat " + REFERENCE, data)))
        del self.manifest["baseline"][REFERENCE]
        self.assertUnverified(self.normalize(self.command("cat " + REFERENCE, data)))

    def test_standalone_cat_preserves_before_and_after_write_distinction(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        result = self.normalize(self.command("cat " + TARGET, self.before.decode(), id="before")
                                + self.write() + self.command("cat " + TARGET, after.decode(), id="after"))
        self.assertEqual([], result["issues"])
        before, final = self.reads(result)
        self.assertTrue(before["read_before_write"])
        self.assertEqual(hashlib.sha256(self.before).hexdigest(), before["read_sha256"])
        self.assertTrue(final["read_after_write"])
        self.assertEqual(hashlib.sha256(after).hexdigest(), final["read_sha256"])
        self.assertUnverified(self.normalize(self.command("cat " + TARGET, after.decode())))

    def test_standalone_cat_requires_literal_path_lifecycle_and_success(self):
        data = (self.workspace / REFERENCE).read_text()
        for command in ("cat -n " + REFERENCE, "cat " + REFERENCE + " " + TARGET, "cat -"):
            self.assertUnverified(self.normalize(self.command(command, data)))
        for overrides in ({"exitCode": 1}, {"status": "failed"},
                          {"commandActions": [{"type": "read", "path": CONFIG}]}):
            self.assertUnverified(self.normalize(self.command("cat " + REFERENCE, data, **overrides)))
        self.assertUnverified(self.normalize(self.command("cat " + REFERENCE, data)[1:]))
        (self.workspace / "cat-alias").symlink_to(self.workspace / REFERENCE)
        self.assertUnverified(self.normalize(self.command("cat cat-alias", data)))

    def test_inherited_internal_append_and_failure_retention_still_work(self):
        after = self.before + self.addition
        (self.workspace / TARGET).write_bytes(after)
        script = (f"from pathlib import Path; p=Path({TARGET!r}); old=p.read_bytes(); "
                  f"add={self.addition!r}; p.open('ab').write(add); new=p.read_bytes(); "
                  "assert new == old + add; print(new.decode())")
        result = self.normalize(self.command(self.python(script), CACHE + after.decode() + "\n"))
        self.assertEqual([], result["issues"])
        self.assertEqual(["read", "write", "read"], [e["type"] for e in result["events"]])
        result = self.normalize(self.command(f"cat >> {TARGET} <<'EOF'\nnew\nEOF\n", "AssertionError: failure\n"))
        self.assertTrue(any(e.get("status") == "failed" for e in result["events"]))

    def test_objects_and_frozen_v4_module_unchanged(self):
        events = self.command(self.python(self.bytes_script()), self.bytes_output(self.before))
        saved_events, saved_manifest = copy.deepcopy(events), copy.deepcopy(self.manifest)
        self.normalize(events)
        self.assertEqual(saved_events, events)
        self.assertEqual(saved_manifest, self.manifest)
        old = normalize_v4(events, thread_id="t", turn_id="u", workspace=self.workspace,
                           manifest=self.manifest, latency_ms=1)
        self.assertEqual(4, old["schema_version"])
        self.assertFalse(self.reads(old))


if __name__ == "__main__":
    unittest.main()
