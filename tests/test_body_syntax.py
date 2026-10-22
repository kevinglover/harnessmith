from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harnessmith.audit import audit_skill
from harnessmith.body_syntax import body_syntax_diagnostics
from harnessmith.compiler import CompileOptions, compile_skill
from harnessmith.parser import parse_skill
from harnessmith.targets import TARGET_NAMES


class BodySyntaxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "example" / "SKILL.md"
        self.source.parent.mkdir()

    def write(self, body: str, fields: str = "") -> None:
        self.source.write_text(
            "---\nname: example\ndescription: Example.\n" + fields + "---\n" + body
        )

    def findings(self, target="generic"):
        return body_syntax_diagnostics(parse_skill(self.source), target)

    def test_active_tokens_across_targets(self) -> None:
        body = (
            "Input: $ARGUMENTS and $ARGUMENTS[1], $0, $12.\n"
            "Run !`echo sample`.\n"
            "Path: ${CLAUDE_SKILL_DIR} ${CLAUDE_SESSION_ID} ${CLAUDE_PROJECT_DIR}\n"
            "${CLAUDE_EFFORT} ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_DATA}\n"
        )
        self.write(body)
        for target in TARGET_NAMES:
            findings = self.findings(target)
            self.assertEqual(0 if target == "claude" else 11, len(findings))
            self.assertTrue(all(d.rule_id == "HS307" for d in findings))
            self.assertTrue(all(d.severity.value == "warning" for d in findings))
            package = compile_skill(self.source, CompileOptions(target))
            self.assertIn(body, package.files["SKILL.md"])
            self.assertEqual(findings, package.diagnostics)
            report = audit_skill(self.source, target)
            self.assertTrue(report["target_compatible"])  # advisory policy
            self.assertEqual(len(findings), len(report["warnings"]))
        span = self.findings()[0].source_span
        self.assertEqual(
            (5, 8, 17), (span.start_line, span.start_column, span.end_column)
        )

    def test_literal_contexts_are_distinguished_and_not_declared_safe(self) -> None:
        self.write(
            "```text\n$ARGUMENTS\n```\n"
            "~~~markdown\n!`echo example`\n~~~\n"
            "Literal `$ARGUMENTS` and \\$ARGUMENTS.\n"
            "<!--\n${CLAUDE_SKILL_DIR}\n-->\n"
            "> $ARGUMENTS\n"
            "    $1\n"
            "Active $ARGUMENTS.\n"
        )
        findings = self.findings()
        self.assertEqual(["HS308"] * 7 + ["HS307"], [d.rule_id for d in findings])
        for finding in findings[:-1]:
            self.assertIn("not evidence", finding.rationale)
        self.assertIn("fenced code", findings[0].message)
        self.assertIn("inline code", findings[2].message)
        self.assertIn("escaped text", findings[3].message)
        self.assertIn("HTML comment", findings[4].message)

    def test_negative_controls_and_backslash_parity(self) -> None:
        self.write(
            "Use $HOME, $PATH, ${OTHER}, $ARGUMENTS_EXTRA, $12items, "
            "${CLAUDE_UNKNOWN}, ordinary ! punctuation and `code`.\n"
        )
        self.assertEqual([], self.findings())
        self.write("\\$ARGUMENTS\n\\\\$ARGUMENTS\n")
        self.assertEqual(["HS308", "HS307"], [d.rule_id for d in self.findings()])

    def test_long_fences_and_multiline_inline_code(self) -> None:
        self.write(
            "````md\n```\n$ARGUMENTS\n````\n"
            "Literal ``text\n$ARGUMENTS\ntext``\nActive $ARGUMENTS\n"
        )
        self.assertEqual(
            ["HS308", "HS308", "HS307"], [d.rule_id for d in self.findings()]
        )

    def test_named_arguments_are_scanned_only_when_declared(self) -> None:
        for arguments in ["issue branch", "[issue, branch]", "\n  - issue\n  - branch"]:
            self.write(
                "$issue $branch $other $issue_extra\n", "arguments: " + arguments + "\n"
            )
            findings = self.findings()
            self.assertEqual(2, len(findings))
            self.assertIn("$issue", findings[0].message)

    def test_no_embedded_commands_execute(self) -> None:
        sentinel = self.root / "must-not-exist"
        self.write("Command !`touch %s`\n" % sentinel)
        for target in TARGET_NAMES:
            audit_skill(self.source, target)
            compile_skill(self.source, CompileOptions(target))
        self.assertFalse(sentinel.exists())

    def test_cli_exposes_audit_and_compile_findings(self) -> None:
        self.write("Input $ARGUMENTS\n")
        command = [
            sys.executable,
            "-m",
            "harnessmith",
            str(self.source),
            "--target",
            "generic",
        ]
        audit = subprocess.run(
            command + ["--audit", "--json", "--fail-on", "warning"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, audit.returncode, audit.stderr)
        self.assertEqual("HS307", json.loads(audit.stdout)["diagnostics"][0]["rule_id"])
        output = self.root / "output"
        for json_output in [True, False]:
            compile_result = subprocess.run(
                command
                + ["--output", str(output), "--dry-run"]
                + (["--json"] if json_output else []),
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, compile_result.returncode, compile_result.stderr)
            if json_output:
                self.assertEqual(
                    "HS307",
                    json.loads(compile_result.stdout)["diagnostics"][0]["rule_id"],
                )
            else:
                self.assertIn("HS307", compile_result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
