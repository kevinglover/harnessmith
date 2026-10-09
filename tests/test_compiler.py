from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from harnessmith import CompileOptions, SkillCompilerError, compile_skill, write_package
from harnessmith.verification import verify_compiled_package


ROOT = Path(__file__).resolve().parents[1]
ANALYZE = ROOT / "skills" / "speckit-analyze" / "SKILL.md"


class CompilerTests(unittest.TestCase):
    def test_bundled_text_binary_and_executable_resources_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "source"
            (skill / "references").mkdir(parents=True)
            (skill / "scripts").mkdir()
            (skill / "assets").mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: bundled\ndescription: Bundled resources.\n---\n\n"
                "## Guide\n\nRead [the guide](references/guide.md).\n",
                encoding="utf-8",
            )
            (skill / "references" / "guide.md").write_text(
                "# Existing guide\n", encoding="utf-8"
            )
            script = skill / "scripts" / "run.sh"
            script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
            script.chmod(0o755)
            binary = b"\x89PNG\r\n\x1a\n\xff"
            (skill / "assets" / "logo.bin").write_bytes(binary)

            package = compile_skill(skill, CompileOptions(target="generic"))

            self.assertEqual(
                "# Existing guide\n", package.files["references/guide.md"]
            )
            self.assertEqual(binary, package.binary_files["assets/logo.bin"])
            self.assertIn("scripts/run.sh", package.executable_files)
            self.assertEqual(
                3,
                sum(
                    item.get("type") == "preserve-resource"
                    for item in package.transformations
                ),
            )

            output = root / "compiled"
            write_package(package, output)
            self.assertEqual(binary, (output / "assets" / "logo.bin").read_bytes())
            self.assertTrue((output / "scripts" / "run.sh").stat().st_mode & 0o111)
            self.assertTrue(verify_compiled_package(output).valid)

    def test_generated_resource_collision_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "source"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: collision\ndescription: Collision.\n---\n\n"
                "## Guide\n\nCanonical guide.\n",
                encoding="utf-8",
            )
            (skill / "references" / "guide.md").write_text(
                "Existing guide.\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(SkillCompilerError, "collides"):
                compile_skill(
                    skill,
                    CompileOptions(target="generic", extract_sections=("Guide",)),
                )

    def test_bundled_resource_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "source"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: symlink\ndescription: Symlink.\n---\n\nBody.\n",
                encoding="utf-8",
            )
            external = root / "external.md"
            external.write_text("External.\n", encoding="utf-8")
            (skill / "references" / "external.md").symlink_to(external)
            with self.assertRaisesRegex(SkillCompilerError, "must not be a symlink"):
                compile_skill(skill, CompileOptions(target="generic"))

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

    def test_modified_owned_file_is_not_overwritten(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="cursor"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "skill"
            write_package(package, output)
            (output / "SKILL.md").write_text("user modification\n", encoding="utf-8")
            with self.assertRaisesRegex(SkillCompilerError, "was modified"):
                write_package(package, output)
            self.assertEqual(
                "user modification\n",
                (output / "SKILL.md").read_text(encoding="utf-8"),
            )

    def test_new_generated_path_does_not_overwrite_unowned_file(self) -> None:
        cursor_package = compile_skill(ANALYZE, CompileOptions(target="cursor"))
        codex_package = compile_skill(
            ANALYZE, CompileOptions(target="codex", invocation="explicit")
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "skill"
            write_package(cursor_package, output)
            policy = output / "agents" / "openai.yaml"
            policy.parent.mkdir()
            policy.write_text("user data\n", encoding="utf-8")

            with self.assertRaisesRegex(SkillCompilerError, "unowned file"):
                write_package(codex_package, output)

            self.assertEqual("user data\n", policy.read_text(encoding="utf-8"))

    def test_failed_atomic_publish_restores_previous_package(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="cursor"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "skill"
            write_package(package, output)
            before = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            real_replace = os.replace
            calls = 0

            def fail_publish(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated publish failure")
                return real_replace(source, destination)

            with mock.patch("harnessmith.compiler.os.replace", side_effect=fail_publish):
                with self.assertRaisesRegex(OSError, "simulated publish failure"):
                    write_package(package, output)

            after = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_symlinked_output_directory_is_rejected(self) -> None:
        package = compile_skill(ANALYZE, CompileOptions(target="cursor"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "external"
            external.mkdir()
            output = root / "skill"
            output.symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(SkillCompilerError, "symlinked output"):
                write_package(package, output)

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
