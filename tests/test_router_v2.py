"""Offline package contracts; these do not test model instruction compliance."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from harnessmith.router_experiment import load_router


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills/speckit-checklist/SKILL.md"
PREVIOUS = ROOT / "evaluations/variants/speckit-checklist-router"
ROUTER = ROOT / "evaluations/variants/speckit-checklist-router-v2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frontmatter(raw):
    return raw.split(b"---", 2)[1]


class RouterV2Tests(unittest.TestCase):
    def test_versioned_review_pins_previous_and_current_packages(self):
        files, review = load_router(ROUTER, SOURCE.read_bytes())
        record = json.loads(ROUTER.with_suffix(".review.json").read_text())
        self.assertEqual(2, record["version"])
        self.assertEqual("reviewed-semantic-redesign", review["kind"])
        previous = record["previous_package"]
        self.assertEqual(PREVIOUS, ROOT / previous["path"])
        self.assertEqual(sha(PREVIOUS.with_suffix(".review.json")), previous["review_sha256"])
        self.assertEqual(
            {p.relative_to(PREVIOUS).as_posix(): sha(p)
             for p in PREVIOUS.rglob("*") if p.is_file()},
            previous["files"],
        )
        changed = {
            name for name, data in files.items()
            if hashlib.sha256(data).hexdigest() != previous["files"][name]
        }
        self.assertEqual({"SKILL.md", "references/project-generation.md"}, changed)

    def test_discovery_metadata_and_optional_examples_retain_original_bytes(self):
        files, _ = load_router(ROUTER, SOURCE.read_bytes())
        self.assertEqual(frontmatter(SOURCE.read_bytes()), frontmatter(files["SKILL.md"]))
        self.assertEqual(
            frontmatter((PREVIOUS / "SKILL.md").read_bytes()),
            frontmatter(files["SKILL.md"]),
        )
        for name in (
            "references/example-checklist-types-sample-items.md",
            "references/anti-examples-what-not-to-do.md",
        ):
            self.assertEqual((PREVIOUS / name).read_bytes(), files[name])

    def test_retention_mapping_does_not_claim_revised_generation_is_verbatim(self):
        record = json.loads(ROUTER.with_suffix(".review.json").read_text())
        self.assertEqual(
            {
                "references/example-checklist-types-sample-items.md",
                "references/anti-examples-what-not-to-do.md",
            },
            set(record["verbatim_source_spans"]),
        )
        self.assertEqual(0, record["validation_scope"]["live_sessions"])

    def test_every_routed_reference_is_an_existing_package_document(self):
        files, _ = load_router(ROUTER, SOURCE.read_bytes())
        links = re.findall(r"\]\((references/[^)]+)\)", files["SKILL.md"].decode())
        self.assertEqual(3, len(links))
        self.assertEqual(set(files) - {"SKILL.md"}, set(links))
        for path in ROUTER.rglob("*"):
            self.assertFalse(path.is_symlink())
            if path.is_file():
                self.assertEqual(0, path.stat().st_mode & 0o111)

    def test_revised_package_rejects_source_drift_and_unreviewed_edits(self):
        with self.assertRaises(ValueError):
            load_router(ROUTER, SOURCE.read_bytes() + b"\n")
        for edit in ("changed-reference", "extra-file"):
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "router-v2"
                shutil.copytree(ROUTER, target)
                shutil.copyfile(
                    ROUTER.with_suffix(".review.json"), target.with_suffix(".review.json")
                )
                if edit == "changed-reference":
                    path = target / "references/project-generation.md"
                    path.write_bytes(path.read_bytes() + b"unreviewed revision\n")
                else:
                    (target / "extra.md").write_text("unreviewed resource\n")
                with self.assertRaises(ValueError):
                    load_router(target, SOURCE.read_bytes())


if __name__ == "__main__":
    unittest.main()
