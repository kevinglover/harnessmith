from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith import SkillCompilerError
from harnessmith.recipe import load_recipe


class RecipeTests(unittest.TestCase):
    def test_loads_a_strict_versioned_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recipe.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "target": "codex",
                        "source_sha256": "a" * 64,
                        "invocation": "explicit",
                        "extract_sections": ["Examples"],
                        "optimizations": [],
                        "budgets": {
                            "root_tokens": 1000,
                            "normal_path_tokens": 1500,
                        },
                    }
                ),
                encoding="utf-8",
            )

            recipe = load_recipe(path)

            self.assertEqual("codex", recipe.target)
            self.assertEqual(("Examples",), recipe.extract_sections)
            self.assertEqual(1000, recipe.max_root_tokens)
            self.assertEqual(64, len(recipe.sha256))

    def test_rejects_unknown_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recipe.json"
            path.write_text(
                json.dumps({"schema_version": 1, "surprise": True}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SkillCompilerError, "unknown keys"):
                load_recipe(path)

    def test_rejects_invalid_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recipe.json"
            path.write_text(
                json.dumps(
                    {"schema_version": 1, "source_sha256": "not-a-hash"}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SkillCompilerError, "source_sha256"):
                load_recipe(path)


if __name__ == "__main__":
    unittest.main()
