from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith.compiler import CompileOptions, compile_skill, write_package
from harnessmith.verification import compare_package, verify_compiled_package


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "speckit-analyze" / "SKILL.md"
RECIPE = ROOT / "recipes" / "speckit-analyze.cursor.json"


class VerificationTests(unittest.TestCase):
    def _compiled(self, root: Path) -> Path:
        package = compile_skill(
            SOURCE,
            CompileOptions(
                target="cursor",
                extract_sections=(
                    "4. Detection Passes (Token-Efficient Analysis)",
                    "Specification Analysis Report",
                ),
                optimize_extension_hooks=True,
                source_id=SOURCE.as_posix(),
                expected_source_sha256=json.loads(RECIPE.read_text())["source_sha256"],
                recipe_id=RECIPE.as_posix(),
                recipe_sha256=__import__("hashlib").sha256(RECIPE.read_bytes()).hexdigest(),
            ),
        )
        output = root / "compiled"
        write_package(package, output)
        return output

    def test_valid_package_passes_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = verify_compiled_package(self._compiled(Path(directory)))
            self.assertTrue(report.valid, report.issues)
            self.assertEqual("passed", report.checks["regeneration"])

    def test_hash_tampering_and_missing_files_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self._compiled(Path(directory))
            (output / "SKILL.md").write_text("tampered\n", encoding="utf-8")
            (output / "scripts" / "resolve-extension-hooks.py").unlink()
            report = verify_compiled_package(output)
            self.assertFalse(report.valid)
            self.assertIn("HS505", {issue.code for issue in report.issues})
            self.assertIn("HS506", {issue.code for issue in report.issues})

    def test_manifest_traversal_and_owned_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self._compiled(Path(directory))
            manifest_path = output / ".harnessmith.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["../outside"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = verify_compiled_package(output)
            self.assertIn("HS504", {issue.code for issue in report.issues})

            del manifest["files"]["../outside"]
            skill = output / "SKILL.md"
            skill.unlink()
            skill.symlink_to(SOURCE)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = verify_compiled_package(output)
            self.assertIn("HS504", {issue.code for issue in report.issues})

    def test_symlinked_owned_parent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = self._compiled(root)
            external = root / "external"
            external.mkdir()
            references = output / "references"
            for child in references.iterdir():
                child.unlink()
            references.rmdir()
            references.symlink_to(external, target_is_directory=True)
            report = verify_compiled_package(output)
            self.assertIn("HS504", {issue.code for issue in report.issues})

    def test_compare_reports_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = self._compiled(root)
            before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
            desired = compile_skill(SOURCE, CompileOptions(target="cursor")).files
            diff = compare_package(desired, output)
            after = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
            self.assertTrue(diff.changed)
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
