from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from harnessmith.audit import audit_skill


class AuditTests(unittest.TestCase):
    def test_audit_accepts_an_arbitrary_skill_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "example-skill"
            skill.mkdir()
            details = "Supporting example and configuration guidance. " * 35
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: example-skill\n"
                "description: A non-Spec Kit fixture for generic auditing.\n"
                "---\n\n"
                "# Example Skill\n\n"
                "## Safety Rules\n\n"
                "You MUST confirm before destructive work.\n\n"
                "## Detailed Examples\n\n"
                + details
                + "\n",
                encoding="utf-8",
            )
            references = skill / "references"
            references.mkdir()
            (references / "notes.md").write_text("Notes.\n", encoding="utf-8")

            report = audit_skill(skill, "cursor")

            self.assertEqual("example-skill", report["skill"])
            self.assertTrue(report["target_compatible"])
            self.assertEqual(1, report["bundled_resources"]["references"]["files"])
            self.assertEqual(
                report["source"]["sha256"],
                report["recipe_template"]["source_sha256"],
            )
            classifications = {
                section["heading"]: section["classification"]
                for section in report["sections"]
            }
            self.assertEqual("keep-in-root", classifications["Safety Rules"])
            self.assertEqual(
                "review-for-reference", classifications["Detailed Examples"]
            )


if __name__ == "__main__":
    unittest.main()
