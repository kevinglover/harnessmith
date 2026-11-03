"""Documentation links stay portable without publishing private evidence."""

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import check_repository


class RepositoryDocumentationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.private = self.root / "evaluations/local-evidence"
        self.readme = self.root / "README.md"
        patcher = mock.patch.object(check_repository, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def check(self, target):
        self.readme.write_text("[Evidence](" + target + ")\n", encoding="utf-8")
        return check_repository.check_docs()

    def test_existing_public_and_private_targets_pass(self):
        for relative in ("docs/public.md", "evaluations/local-evidence/run/report.json"):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("retained", encoding="utf-8")
            self.assertEqual([], self.check(relative))

    def test_entirely_absent_private_root_allows_private_links(self):
        for target in ("evaluations/local-evidence", "evaluations/local-evidence/run/report.json"):
            with self.subTest(target=target):
                self.assertEqual([], self.check(target))
                self.assertFalse(self.private.exists())

    def test_present_private_root_requires_each_linked_target(self):
        self.private.mkdir(parents=True)
        errors = self.check("evaluations/local-evidence/run/missing.json")
        self.assertEqual(1, len(errors))
        self.assertIn("missing link target", errors[0])

    def test_missing_public_targets_are_never_exempt(self):
        for private_present in (False, True):
            if private_present:
                self.private.mkdir(parents=True)
            errors = self.check("docs/missing.md")
            self.assertEqual(1, len(errors))
            self.assertIn("missing link target", errors[0])

    def test_lookalike_prefixes_and_traversal_do_not_gain_exemption(self):
        for target in (
            "evaluations/local-evidence-extra/run/report.json",
            "evaluations/local-evidence/../public/missing.json",
            "evaluations/local-evidence/%2e%2e/public/missing.json",
        ):
            with self.subTest(target=target):
                errors = self.check(target)
                self.assertEqual(1, len(errors))
                self.assertIn("missing link target", errors[0])

    def test_private_spelling_cannot_escape_repository(self):
        for target in (
            "evaluations/local-evidence/../../../outside.json",
            "evaluations/local-evidence/%2e%2e/%2e%2e/%2e%2e/outside.json",
        ):
            with self.subTest(target=target):
                errors = self.check(target)
                self.assertEqual(1, len(errors))
                self.assertIn("link escapes repository", errors[0])

    def test_dangling_private_root_symlink_is_not_absent_evidence(self):
        self.private.parent.mkdir()
        self.private.symlink_to("not-retained")
        errors = self.check("evaluations/local-evidence/run/report.json")
        self.assertEqual(1, len(errors))
        self.assertIn("missing link target", errors[0])

    def test_existing_private_root_symlink_does_not_bypass_containment(self):
        self.private.parent.mkdir()
        self.private.symlink_to(self.root.parent, target_is_directory=True)
        errors = self.check("evaluations/local-evidence/outside.json")
        self.assertEqual(1, len(errors))
        self.assertIn("link escapes repository", errors[0])


if __name__ == "__main__":
    unittest.main()
