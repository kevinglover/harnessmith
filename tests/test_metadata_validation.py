from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith.audit import audit_skill
from harnessmith.compiler import CompileOptions, compile_skill, write_package
from harnessmith.errors import SkillCompilerError
from harnessmith.metadata import metadata_diagnostics, string_value
from harnessmith.parser import parse_skill
from harnessmith.targets import TARGET_NAMES
from harnessmith.verification import verify_compiled_package

ROOT = Path(__file__).resolve().parents[1]


class MetadataValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "valid-name" / "SKILL.md"
        self.source.parent.mkdir()

    def write(self, fields: str) -> Path:
        self.source.write_text("---\n" + fields + "---\n\n# Workflow\nBody.\n")
        return self.source

    def check_invalid(self, fields: str, targets=TARGET_NAMES) -> None:
        self.write(fields)
        original = self.source.read_bytes()
        for target in targets:
            with self.subTest(target=target, fields=fields[:90]):
                result = audit_skill(self.source, target)
                self.assertFalse(result["target_compatible"])
                errors = [d for d in result["diagnostics"] if d["rule_id"] == "HS102"]
                self.assertTrue(errors)
                self.assertTrue(all(d["severity"] == "error" for d in errors))
                self.assertTrue(
                    all(d["source_span"]["start_line"] >= 1 for d in errors)
                )
                with self.assertRaisesRegex(SkillCompilerError, "HS102"):
                    compile_skill(self.source, CompileOptions(target))
        self.assertEqual(original, self.source.read_bytes())

    def test_portable_name_boundaries(self) -> None:
        for name in ["A-name", "bad--name", "-bad", "bad-", "bad_name", "a" * 65]:
            self.check_invalid(
                "name: %s\ndescription: valid\n" % name, ("generic", "cursor", "codex")
            )
        for name in ["a", "a" * 64, "café", '"123"']:
            self.write("name: %s\ndescription: valid\n" % name)
            for target in TARGET_NAMES:
                compile_skill(self.source, CompileOptions(target))

    def test_string_types_and_required_values(self) -> None:
        for key in ["name", "description"]:
            for value in [
                "true",
                "false",
                "null",
                "42",
                "1.5",
                "2026-10-22",
                "[]",
                "{}",
                "{version: 1.2.3}",
                '{"key":"literal # value"}',
                "[text]",
                "{value: text}",
                '""',
                '"   "',
                "&ref text",
                "*ref",
                "!!str text",
                "- item",
                "key: value",
                "'bad' quote'",
            ]:
                fields = {"name": "valid-name", "description": "valid"}
                fields[key] = value
                self.check_invalid(
                    "".join("%s: %s\n" % item for item in fields.items())
                )
        self.check_invalid("description: valid\n")
        self.check_invalid("name: valid-name\n")
        self.check_invalid("name: valid-name\ndescription:\n  - item\n")
        self.check_invalid("name: valid-name\ndescription: |-\nunindented\n")
        self.check_invalid("name: valid-name\ndescription: value\nunindented\n")

    def test_plain_strings_are_typed_after_folding(self) -> None:
        for description in [
            "2026-10-22 release notes",
            "42\n  release instructions.",
            "2026-10-22\n  release notes",
            "true\n  story",
        ]:
            fields = "name: valid-name\ndescription: " + description + "\n"
            self.write(fields)
            for target in TARGET_NAMES:
                with self.subTest(description=description, target=target):
                    package = compile_skill(self.source, CompileOptions(target))
                    self.assertIn(fields, package.files["SKILL.md"])
        for value in [
            "42",
            "2026-10-22",
            "2026-10-22T12:30:45Z",
            "2026-10-22 12:30:45.123 -05:00",
        ]:
            self.check_invalid("name: valid-name\ndescription: " + value + "\n")

    def test_flow_scalars_preserve_embedded_quotes(self) -> None:
        for metadata in [
            "{author: O'Reilly}",
            '{author: Say"Hello}',
            "{author: O'Reilly, label: 'hello, world'}",
            '{author: Say"Hello, label: "hello, world"}',
        ]:
            fields = (
                "name: valid-name\ndescription: valid\nmetadata: " + metadata + "\n"
            )
            self.write(fields)
            for target in TARGET_NAMES:
                with self.subTest(metadata=metadata, target=target):
                    package = compile_skill(self.source, CompileOptions(target))
                    self.assertIn(fields, package.files["SKILL.md"])
        for tools in [
            "[Bash(O'Reilly), Read]",
            '[Bash(say"hello), Read]',
            "['Bash(one,two)', Read]",
            '["Bash(one,two)", Read]',
        ]:
            fields = (
                "name: valid-name\ndescription: valid\nallowed-tools: " + tools + "\n"
            )
            self.write(fields)
            package = compile_skill(self.source, CompileOptions("claude"))
            self.assertIn(fields, package.files["SKILL.md"])

    def test_folded_plain_scalar_rejects_colon_separators(self) -> None:
        for value in [
            "first\n  second:",
            "first\n  second: # comment",
            "first\n\n  second:",
            "first\n  second:\n  third",
            "first\n  second: third",
        ]:
            self.check_invalid("name: valid-name\ndescription: " + value + "\n")
        for value in [
            "first\n  https://example.com",
            "'first second:'",
            '"first second:"',
            ">-\n  first\n  second:",
            "|-\n  first\n  second:",
        ]:
            fields = "name: valid-name\ndescription: " + value + "\n"
            self.write(fields)
            for target in TARGET_NAMES:
                with self.subTest(value=value, target=target):
                    package = compile_skill(self.source, CompileOptions(target))
                    self.assertIn(fields, package.files["SKILL.md"])

    def test_plain_scalar_quotes_do_not_hide_comments(self) -> None:
        self.write("name: Review '90s # keep this comment\ndescription: valid\n")
        package = compile_skill(self.source, CompileOptions("claude"))
        self.assertEqual("Review '90s", package.skill_name)
        for description in [
            "Review '90s",
            'Review "90s',
            "'quoted # text'",
            '"quoted # text"',
        ]:
            self.write(
                "name: valid-name\ndescription: "
                + description
                + " # "
                + "x" * 1100
                + "\n"
            )
            for target in TARGET_NAMES:
                compile_skill(self.source, CompileOptions(target))

    def test_reserved_plain_scalar_indicators(self) -> None:
        for indicator in "@`%]},":
            self.check_invalid(
                "name: valid-name\ndescription: " + indicator + "example\n"
            )
            self.write("name: valid-name\ndescription: '" + indicator + "example'\n")
            for target in TARGET_NAMES:
                compile_skill(self.source, CompileOptions(target))

    def test_paragraph_folding_and_length_limits(self) -> None:
        self.check_invalid("name: alpha\n\n  beta\ndescription: valid\n", ("claude",))
        for raw, expected in [
            ("alpha\n  beta", "alpha beta"),
            ("alpha\n\n  beta", "alpha\nbeta"),
            ("alpha\n\n\n  beta", "alpha\n\nbeta"),
            ("alpha\n# comment\n  beta", "alpha beta"),
        ]:
            self.write("name: valid-name\ndescription: " + raw + "\n")
            self.assertEqual(
                expected, string_value(parse_skill(self.source).field("description"))
            )
        for key, limit in [("description", 1024), ("compatibility", 500)]:
            base = "name: valid-name\n" + (
                "description: valid\n" if key == "compatibility" else ""
            )
            for block in [False, True]:
                prefix = ">-\n  " if block else ""
                value = prefix + "a" * (limit // 2) + "\n\n  " + "b" * (limit // 2 - 1)
                self.write(base + key + ": " + value + "\n")
                compile_skill(self.source, CompileOptions("generic"))
                self.check_invalid(base + key + ": " + value + "b\n", ("generic",))

    def test_length_boundaries_and_claude_extensions(self) -> None:
        for key, limit in [("description", 1024), ("compatibility", 500)]:
            fields = "name: valid-name\n" + (
                "" if key == "description" else "description: valid\n"
            )
            self.write(fields + "%s: %s\n" % (key, "x" * limit))
            compile_skill(self.source, CompileOptions("generic"))
            targets = (
                TARGET_NAMES
                if key == "compatibility"
                else ("generic", "cursor", "codex")
            )
            self.check_invalid(fields + "%s: %s\n" % (key, "x" * (limit + 1)), targets)
        self.write("name: Team:Review\ndescription: " + "x" * 1600 + "\n")
        compile_skill(self.source, CompileOptions("claude"))
        for name in ['" bad"', '"bad  name"', '"bad<name"', '"bad\\u200bname"']:
            self.check_invalid("name: %s\ndescription: valid\n" % name, ("claude",))

    def test_metadata_mapping_types(self) -> None:
        for metadata in [
            "true",
            "[]",
            "[one]",
            "42",
            "\n  count: 2",
            "\n  key: [value]",
            "\n  key:\n    nested: value",
            "\n  one: text\n  one: again",
            "{key: true}",
            "{key:value}",
            "{1: text}",
        ]:
            self.check_invalid(
                "name: valid-name\ndescription: valid\nmetadata: " + metadata + "\n"
            )
        for metadata in [
            "{}",
            "{version: 1.2.3}",
            '{"key":"literal # value"}',
            '{"author":"Test", version: "1.0"}',
            '\n  author: Test\n  version: "1.0"',
        ]:
            self.write(
                "name: valid-name\ndescription: valid\nmetadata: " + metadata + "\n"
            )
            compile_skill(self.source, CompileOptions("generic"))

    def test_tools_are_target_specific_and_preserved(self) -> None:
        base = "name: valid-name\ndescription: valid\nallowed-tools: "
        for tools in ['[Read, "Bash(git *)"]', "\n  - Read\n  - Grep", "Read, Grep"]:
            self.check_invalid(base + tools + "\n", ("generic", "cursor", "codex"))
            self.write(base + tools + "\n")
            package = compile_skill(self.source, CompileOptions("claude"))
            self.assertIn("allowed-tools: " + tools + "\n", package.files["SKILL.md"])
        for tools in [
            "",
            "true",
            "[Read, 2]",
            "\n  - true",
            "{tool: Read}",
            '\n  - ""',
            "\n  - Read\n    - Write",
        ]:
            self.check_invalid(base + tools + "\n")
        self.write(base + "Bash(git:*) Read\n")
        for target in TARGET_NAMES:
            compile_skill(self.source, CompileOptions(target))

    def test_comments_quoting_and_folded_values_keep_bytes_and_verify(self) -> None:
        fields = (
            'name: "valid-name" # keep comment\n'
            "description: >-\n  A multiline\n  description.\n"
            "license: 'MIT' # preserved\nmetadata:\n  version: \"1.0\"\n"
        )
        self.write(fields)
        source_bytes = self.source.read_bytes()
        package = compile_skill(self.source, CompileOptions("generic"))
        self.assertEqual("valid-name", package.skill_name)
        self.assertIn(fields, package.files["SKILL.md"])
        self.assertEqual(source_bytes, self.source.read_bytes())
        output = self.root / "arbitrary-staging-directory"
        write_package(package, output)
        result = verify_compiled_package(output)
        self.assertTrue(result.valid, result.as_dict())
        self.assertTrue(audit_skill(self.source, "generic")["target_compatible"])

    def test_crlf_metadata_and_source_hash_are_preserved(self) -> None:
        import hashlib

        raw = b"---\r\nname: valid-name\r\ndescription: Example.\r\n---\r\nBody.\r\n"
        self.source.write_bytes(raw)
        ir = parse_skill(self.source)
        self.assertEqual(raw.decode(), ir.source_text)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ir.source_sha256)
        package = compile_skill(self.source, CompileOptions("generic"))
        self.assertIn(
            "name: valid-name\r\ndescription: Example.\r\n", package.files["SKILL.md"]
        )
        output = self.root / "crlf-output"
        write_package(package, output)
        result = verify_compiled_package(output)
        self.assertTrue(result.valid, result.as_dict())

    def test_directory_policy_warns_without_blocking_staging(self) -> None:
        self.write("name: different-name\ndescription: valid\n")
        for target in TARGET_NAMES:
            report = audit_skill(self.source, target)
            self.assertTrue(report["target_compatible"])
            ids = [d["rule_id"] for d in report["diagnostics"]]
            self.assertEqual(target != "claude", "HS103" in ids)
            compile_skill(self.source, CompileOptions(target))
            self.assertNotIn(
                "HS103",
                [
                    d["rule_id"]
                    for d in audit_skill(self.source, target, check_directory=False)[
                        "diagnostics"
                    ]
                ],
            )

    def test_every_pinned_fixture_has_valid_standard_metadata(self) -> None:
        records = json.loads((ROOT / "fixtures/manifest.json").read_text())["fixtures"]
        for record in records:
            ir = parse_skill(ROOT / record["source_path"])
            for target in TARGET_NAMES:
                with self.subTest(fixture=record["fixture_id"], target=target):
                    self.assertEqual([], metadata_diagnostics(ir, target))


if __name__ == "__main__":
    unittest.main()
