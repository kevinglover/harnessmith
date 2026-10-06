from __future__ import annotations

import unittest

from harnessmith.errors import SkillCompilerError
from harnessmith.frontmatter import render_frontmatter, scalar_value, split_frontmatter


class FrontmatterTests(unittest.TestCase):
    def test_nested_yaml_is_retained_losslessly(self) -> None:
        source = (
            "---\n"
            "name: sample-skill\n"
            "description: \"A sample.\"\n"
            "metadata:\n"
            "  author: example\n"
            "allowed-tools:\n"
            "  - Read\n"
            "  - Grep\n"
            "---\n\n"
            "# Sample\n"
        )
        fields, body, body_line = split_frontmatter(source)

        self.assertEqual("sample-skill", scalar_value(fields[0]))
        self.assertIn("  author: example\n", fields[2].raw)
        self.assertIn("  - Grep\n", fields[3].raw)
        self.assertEqual("\n# Sample\n", body)
        self.assertEqual(10, body_line)
        self.assertTrue(render_frontmatter(fields).startswith("---\nname: sample-skill\n"))

    def test_duplicate_top_level_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(SkillCompilerError, "duplicate"):
            split_frontmatter(
                "---\nname: one\nname: two\ndescription: sample\n---\nbody\n"
            )


if __name__ == "__main__":
    unittest.main()
