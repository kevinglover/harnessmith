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

    def test_folded_block_scalar_is_interpreted_and_preserved(self) -> None:
        source = (
            "---\n"
            "name: sample-skill\n"
            "description: >-\n"
            "  First line of the description.\n"
            "  Second line of the description.\n"
            "---\n\n"
            "# Sample\n"
        )

        fields, _, _ = split_frontmatter(source)

        self.assertEqual(
            "First line of the description. Second line of the description.",
            scalar_value(fields[1]),
        )
        self.assertEqual(
            source.split("---\n\n", 1)[0] + "---\n",
            render_frontmatter(fields),
        )

    def test_literal_block_scalar_preserves_line_breaks(self) -> None:
        fields, _, _ = split_frontmatter(
            "---\n"
            "name: sample\n"
            "description: |\n"
            "  First line.\n"
            "  Second line.\n"
            "---\n"
        )

        self.assertEqual(
            "First line.\nSecond line.\n",
            scalar_value(fields[1]),
        )

    def test_invalid_block_scalar_header_is_rejected(self) -> None:
        fields, _, _ = split_frontmatter(
            "---\nname: sample\ndescription: >bad\n  text\n---\n"
        )
        with self.assertRaisesRegex(SkillCompilerError, "block scalar header"):
            scalar_value(fields[1])

    def test_duplicate_top_level_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(SkillCompilerError, "duplicate"):
            split_frontmatter(
                "---\nname: one\nname: two\ndescription: sample\n---\nbody\n"
            )


if __name__ == "__main__":
    unittest.main()
