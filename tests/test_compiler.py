from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith import CompileOptions, SkillCompilerError, compile_skill, write_package


ROOT = Path(__file__).resolve().parents[1]
ANALYZE = ROOT / "skills" / "speckit-analyze" / "SKILL.md"


class CompilerTests(unittest.TestCase):
    def test_cursor_vertical_slice_is_lossless_and_smaller(self) -> None:
        package = compile_skill(
            ANALYZE,
            CompileOptions(
                target="cursor",
                source_id="skills/speckit-analyze/SKILL.md",
                extract_sections=(
                    "4. Detection Passes (Token-Efficient Analysis)",
                    "Specification Analysis Report",
                ),
                optimize_extension_hooks=True,
            ),
        )

        root = package.files["SKILL.md"]
        self.assertIn("disable-model-invocation: false", root)
        self.assertNotIn("argument-hint:", root)
        self.assertNotIn("user-invocable:", root)
        self.assertIn("**Before this stage:**", root)
        self.assertIn("scripts/resolve-extension-hooks.py", package.files)
        self.assertIn("references/extension-hooks-fallback.md", package.files)
        self.assertNotIn("When constructing command invocations", root)
        self.assertGreater(package.metrics["root_reduction_percent"], 40)
        self.assertGreater(package.metrics["normal_path_reduction_percent"], 0)
        self.assertGreater(package.metrics["conditional_reference_chars"], 0)
        self.assertEqual(3, len([p for p in package.files if p.startswith("references/")]))
        self.assertEqual(
            "skills/speckit-analyze/SKILL.md", package.manifest["source"]["path"]
        )
        for path, content in package.files.items():
            if path.endswith(".md"):
                self.assertTrue(content.endswith("\n"), path)
                self.assertFalse(content.endswith("\n\n"), path)
                self.assertNotIn("\n\n\n", content, path)

    def test_hook_optimization_is_explicit_and_fail_closed(self) -> None:
        baseline = ROOT / "skills" / "speckit-baseline" / "SKILL.md"
        with self.assertRaisesRegex(SkillCompilerError, "reviewed before"):
            compile_skill(
                baseline,
                CompileOptions(target="cursor", optimize_extension_hooks=True),
            )

    def test_context_budgets_fail_closed(self) -> None:
        with self.assertRaisesRegex(SkillCompilerError, "normal path token budget"):
            compile_skill(
                ANALYZE,
                CompileOptions(target="cursor", max_normal_path_tokens=1),
            )

    def test_cursor_explicit_invocation_uses_native_field(self) -> None:
        package = compile_skill(
            ANALYZE,
            CompileOptions(target="cursor", invocation="explicit"),
        )
        self.assertIn("disable-model-invocation: true", package.files["SKILL.md"])

    def test_generic_target_emits_standard_frontmatter(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="generic"))
        root = package.files["SKILL.md"]
        self.assertNotIn("argument-hint:", root)
        self.assertNotIn("user-invocable:", root)
        self.assertNotIn("disable-model-invocation:", root)

    def test_claude_target_preserves_native_invocation_fields(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="claude"))
        root = package.files["SKILL.md"]
        self.assertIn("argument-hint:", root)
        self.assertIn("user-invocable: true", root)
        self.assertIn("disable-model-invocation: false", root)

    def test_codex_explicit_invocation_uses_openai_metadata(self) -> None:
        package = compile_skill(
            ANALYZE,
            CompileOptions(target="codex", invocation="explicit"),
        )
        self.assertNotIn("disable-model-invocation:", package.files["SKILL.md"])
        self.assertEqual(
            "policy:\n  allow_implicit_invocation: false\n",
            package.files["agents/openai.yaml"],
        )

    def test_unsupported_user_invocation_semantics_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "SKILL.md"
            source.write_text(
                "---\n"
                "name: model-only\n"
                "description: Background model context.\n"
                "user-invocable: false\n"
                "---\n\n"
                "Never expose this as a user command.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SkillCompilerError, "cannot represent"):
                compile_skill(source, CompileOptions(target="cursor"))

    def test_regeneration_replaces_only_manifest_owned_files(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="cursor"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "skill"
            write_package(package, output)
            (output / "KEEP.txt").write_text("user data\n", encoding="utf-8")
            first = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            write_package(package, output)
            second = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first, second)
            self.assertEqual(
                "user data\n", (output / "KEEP.txt").read_text(encoding="utf-8")
            )
            manifest = json.loads((output / ".harnessmith.json").read_text())
            self.assertEqual(1, manifest["schema_version"])

    def test_non_compiler_directory_is_not_overwritten(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="cursor"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "skill"
            output.mkdir()
            (output / "KEEP.txt").write_text("user data\n")
            with self.assertRaisesRegex(SkillCompilerError, "refusing"):
                write_package(package, output)
            self.assertEqual("user data\n", (output / "KEEP.txt").read_text())

    def test_source_hash_pin_fails_closed(self) -> None:
        with self.assertRaisesRegex(SkillCompilerError, "source hash changed"):
            compile_skill(
                ANALYZE,
                CompileOptions(
                    target="cursor",
                    expected_source_sha256="0" * 64,
                ),
            )

    def test_skill_directory_resolves_skill_markdown(self) -> None:
        package = compile_skill(
            ANALYZE.parent,
            CompileOptions(target="generic"),
        )
        self.assertEqual("speckit-analyze", package.skill_name)
        self.assertTrue(package.manifest["source"]["path"].endswith("/SKILL.md"))


if __name__ == "__main__":
    unittest.main()
