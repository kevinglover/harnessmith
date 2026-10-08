from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import harnessmith


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_version_has_three_numeric_components(self) -> None:
        self.assertRegex(harnessmith.__version__, r"^\d+\.\d+\.\d+$")

    def test_module_entry_point_displays_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "harnessmith", "--help"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage: harnessmith", result.stdout)

    def test_packaging_uses_module_version_as_single_source(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('dynamic = ["version"]', pyproject)
        self.assertIn('version = { attr = "harnessmith.__version__" }', pyproject)
        self.assertNotIn('\nversion = "0.1.0"', pyproject)


if __name__ == "__main__":
    unittest.main()
