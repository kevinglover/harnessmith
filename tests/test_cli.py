from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def _write_diagnostic_skill(self, directory: str) -> Path:
        skill = Path(directory) / "SKILL.md"
        skill.write_text(
            "---\nname: cli-diagnostics\ndescription: CLI diagnostics fixture.\n---\n\n"
            "# Workflow\n\nFollow the workflow.\n\n"
            "## Examples\n\n"
            + ("Detailed supporting example text. " * 45)
            + "\n\n## Duplicate\n\nFirst.\n\n## Duplicate\n\nSecond.\n",
            encoding="utf-8",
        )
        return skill

    def test_cli_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "harnessmith", "--version"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertRegex(result.stdout, r"harnessmith \d+\.\d+\.\d+")

    def test_cli_emits_machine_readable_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speckit-analyze"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harnessmith",
                    "skills/speckit-analyze/SKILL.md",
                    "--target",
                    "cursor",
                    "--output",
                    str(output),
                    "--extract-section",
                    "4. Detection Passes (Token-Efficient Analysis)",
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual("speckit-analyze", report["skill"])
            self.assertTrue((output / "SKILL.md").is_file())

    def test_cli_audits_without_writing_output(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "harnessmith",
                "skills/speckit-analyze",
                "--target",
                "cursor",
                "--audit",
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("speckit-analyze", report["skill"])
        self.assertIn("recipe_template", report)
        self.assertGreater(report["metrics"]["section_count"], 0)

    def test_cli_audit_supports_diagnostic_json_and_sarif(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = self._write_diagnostic_skill(directory)
            json_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harnessmith",
                    str(skill),
                    "--target",
                    "generic",
                    "--audit",
                    "--format",
                    "json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, json_result.returncode, json_result.stderr)
            diagnostics = json.loads(json_result.stdout)
            self.assertTrue(any(item["rule_id"] == "HS101" for item in diagnostics))

            sarif_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harnessmith",
                    str(skill),
                    "--target",
                    "generic",
                    "--audit",
                    "--format",
                    "sarif",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, sarif_result.returncode, sarif_result.stderr)
            document = json.loads(sarif_result.stdout)
            self.assertEqual("2.1.0", document["version"])
            self.assertEqual(
                "Harnessmith", document["runs"][0]["tool"]["driver"]["name"]
            )

    def test_cli_audit_fail_on_uses_severity_threshold_and_exit_code_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = self._write_diagnostic_skill(directory)
            base = [
                sys.executable,
                "-m",
                "harnessmith",
                str(skill),
                "--target",
                "generic",
                "--audit",
                "--format",
                "json",
            ]
            warning = subprocess.run(
                [*base, "--fail-on", "warning"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, warning.returncode, warning.stderr)
            self.assertIsInstance(json.loads(warning.stdout), list)

            note = subprocess.run(
                [*base, "--fail-on", "note"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, note.returncode, note.stderr)

            error = subprocess.run(
                [*base, "--fail-on", "error"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, error.returncode, error.stderr)

    def test_cli_json_keeps_complete_legacy_audit_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = self._write_diagnostic_skill(directory)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harnessmith",
                    str(skill),
                    "--target",
                    "generic",
                    "--audit",
                    "--json",
                    "--fail-on",
                    "warning",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual("cli-diagnostics", report["skill"])
            self.assertIn("metrics", report)
            self.assertIn("diagnostics", report)

    def test_cli_compiles_from_a_pinned_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speckit-analyze"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harnessmith",
                    "skills/speckit-analyze",
                    "--recipe",
                    "recipes/speckit-analyze.cursor.json",
                    "--output",
                    str(output),
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = json.loads(
                (output / ".harnessmith.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                "recipes/speckit-analyze.cursor.json",
                manifest["recipe"]["path"],
            )

    def test_cli_dry_run_and_diff_do_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "preview"
            for flag in ("--dry-run", "--diff"):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "harnessmith",
                        "skills/speckit-analyze",
                        "--target",
                        "cursor",
                        "--output",
                        str(output),
                        flag,
                        "--json",
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(json.loads(result.stdout)["written"])

    def test_cli_verify_uses_distinct_invalid_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "compiled"
            compile_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harnessmith",
                    "skills/speckit-analyze",
                    "--recipe",
                    "recipes/speckit-analyze.cursor.json",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, compile_result.returncode, compile_result.stderr)
            valid = subprocess.run(
                [sys.executable, "-m", "harnessmith", "verify", str(output), "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, valid.returncode, valid.stderr)
            (output / "SKILL.md").write_text("changed\n", encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, "-m", "harnessmith", "verify", str(output), "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, invalid.returncode, invalid.stderr)
            self.assertFalse(json.loads(invalid.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
