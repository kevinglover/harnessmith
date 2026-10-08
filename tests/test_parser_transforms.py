from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from harnessmith import CompileOptions, SkillCompilerError, compile_skill
from harnessmith.parser import parse_skill


def write_skill(directory: str, body: str) -> Path:
    path = Path(directory) / "SKILL.md"
    path.write_text(
        "---\nname: parser-test\ndescription: Parser test.\n---\n\n" + body,
        encoding="utf-8",
    )
    return path


class ParserTransformTests(unittest.TestCase):
    def test_fences_require_matching_character_and_length(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_skill(
                directory,
                "# Real\n\n````text\n## Not a heading\n```\n### Still fenced\n````\n\n"
                "~~~\n## Also hidden\n~~~\n\n## Visible\nBody.\n",
            )
            ir = parse_skill(path)
            self.assertEqual(["Real", "Visible"], [s.heading for s in ir.sections])
            self.assertIn("### Still fenced", ir.sections[0].text)

    def test_setext_sections_preserve_exact_heading_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_skill(
                directory,
                "Overview\n========\nIntro.\n\nDetails\n-------\nMust stay exact.\n",
            )
            ir = parse_skill(path)
            self.assertEqual(
                [("Overview", 1), ("Details", 2)],
                [(s.heading, s.level) for s in ir.sections],
            )
            self.assertEqual("Overview\n========\n", ir.sections[0].heading_text)
            package = compile_skill(
                path, CompileOptions(target="generic", extract_sections=("Details",))
            )
            self.assertIn("Details\n-------\n\n**Before this stage:**", package.files["SKILL.md"])
            self.assertIn("Details\n-------\nMust stay exact.\n", package.files["references/details.md"])

    def test_duplicate_heading_has_stable_occurrence_selector(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_skill(directory, "# Steps\nFirst.\n\n# Steps\nSecond.\n")
            ir = parse_skill(path)
            self.assertEqual(["Steps[1]", "Steps[2]"], [s.identity for s in ir.sections])
            with self.assertRaisesRegex(
                SkillCompilerError, "ambiguous.*Steps\[1\].*Steps\[2\]"
            ):
                compile_skill(path, CompileOptions(target="generic", extract_sections=("Steps",)))
            package = compile_skill(
                path, CompileOptions(target="generic", extract_sections=("Steps[2]",))
            )
            self.assertIn("references/steps-2.md", package.files)
            self.assertIn("Second.", package.files["references/steps-2.md"])
            self.assertEqual("Steps[2]", package.transformations[0]["section_id"])

    def test_html_blocks_do_not_create_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_skill(
                directory,
                "<div>\n# Not Markdown\n</div>\n\n# Real\nText.\n\n"
                "<!--\n## Also not Markdown\n-->\n\n## Child\nText.\n",
            )
            self.assertEqual(["Real", "Child"], [s.heading for s in parse_skill(path).sections])

    def test_local_fragment_links_fail_closed_during_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_skill(
                directory, "# Overview\nSee [details](#details).\n\n# Details\nRequired.\n"
            )
            with self.assertRaisesRegex(SkillCompilerError, "fragment links"):
                compile_skill(
                    path,
                    CompileOptions(target="generic", extract_sections=("Details",)),
                )

    def test_reference_links_remain_byte_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_skill(
                directory,
                "# Examples\nUse [the guide][guide].\n\n[guide]: https://example.com/a?q=1\n",
            )
            source_section = parse_skill(path).sections[0].text
            package = compile_skill(
                path, CompileOptions(target="generic", extract_sections=("Examples",))
            )
            self.assertIn(source_section, package.files["references/examples.md"])


if __name__ == "__main__":
    unittest.main()
