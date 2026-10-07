from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
