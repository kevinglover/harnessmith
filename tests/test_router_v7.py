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
PREVIOUS = ROOT / "evaluations/variants/speckit-checklist-router-v6"
ROUTER = ROOT / "evaluations/variants/speckit-checklist-router-v7"
FROZEN_SOURCE_SHA256 = "1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45"
FROZEN_V6_REVIEW_SHA256 = "8f8f386a2f421dbc8eebc303db4d8bbc217c1c5409bffd9972917fe5b84a9315"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frontmatter(raw):
    return raw.split(b"---", 2)[1]


class RouterV7Tests(unittest.TestCase):
    def test_versioned_review_pins_previous_and_current_packages(self):
        files, review = load_router(ROUTER, SOURCE.read_bytes())
        record = json.loads(ROUTER.with_suffix(".review.json").read_text())
        self.assertEqual(7, record["version"])
        self.assertEqual("reviewed-semantic-redesign", review["kind"])
        self.assertEqual(sha(ROUTER.with_suffix(".review.json")), review["review_sha256"])
        previous = record["previous_package"]
        self.assertEqual(PREVIOUS, ROOT / previous["path"])
        self.assertEqual(FROZEN_V6_REVIEW_SHA256, previous["review_sha256"])
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
        for edit in ("changed-root", "changed-reference", "extra-file", "missing-file"):
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "router-v7"
                shutil.copytree(ROUTER, target)
                shutil.copyfile(
                    ROUTER.with_suffix(".review.json"), target.with_suffix(".review.json")
                )
                if edit == "changed-root":
                    path = target / "SKILL.md"
                    path.write_bytes(path.read_bytes() + b"unreviewed instruction\n")
                elif edit == "changed-reference":
                    path = target / "references/project-generation.md"
                    path.write_bytes(path.read_bytes() + b"unreviewed revision\n")
                elif edit == "extra-file":
                    (target / "extra.md").write_text("unreviewed resource\n")
                else:
                    (target / "references/project-generation.md").unlink()
                with self.assertRaises(ValueError):
                    load_router(target, SOURCE.read_bytes())

    def test_candidate_is_isolated_from_original_and_retains_v6_source_identity(self):
        record = json.loads(ROUTER.with_suffix(".review.json").read_text())
        previous = json.loads(PREVIOUS.with_suffix(".review.json").read_text())
        self.assertEqual(previous["source_sha256"], record["source_sha256"])
        self.assertEqual(FROZEN_SOURCE_SHA256, record["source_sha256"])
        self.assertEqual(sha(SOURCE), record["source_sha256"])
        self.assertFalse(ROUTER.is_relative_to(ROOT / "skills"))
        self.assertEqual(
            {p.relative_to(PREVIOUS).as_posix() for p in PREVIOUS.rglob("*") if p.is_file()},
            set(record["files"]),
        )

    def test_revised_generation_cannot_be_mislabeled_as_verbatim_source(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "router-v7"
            shutil.copytree(ROUTER, target)
            record = json.loads(ROUTER.with_suffix(".review.json").read_text())
            record["verbatim_source_spans"]["references/project-generation.md"] = [
                ["## Pre-Execution Checks", "## Example Checklist Types & Sample Items"]
            ]
            target.with_suffix(".review.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "source retention failed"):
                load_router(target, SOURCE.read_bytes())

    def test_document_only_package_rejects_executable_and_symlink_mutations(self):
        for mutation in ("executable", "symlink"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "router-v7"
                shutil.copytree(ROUTER, target)
                shutil.copyfile(
                    ROUTER.with_suffix(".review.json"), target.with_suffix(".review.json")
                )
                path = target / "references/project-generation.md"
                if mutation == "executable":
                    path.chmod(0o755)
                else:
                    path.unlink()
                    path.symlink_to(ROUTER / "references/project-generation.md")
                with self.assertRaises(ValueError):
                    load_router(target, SOURCE.read_bytes())

    def test_repinning_modified_examples_does_not_bypass_source_retention(self):
        for name in (
            "references/example-checklist-types-sample-items.md",
            "references/anti-examples-what-not-to-do.md",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "router-v7"
                shutil.copytree(ROUTER, target)
                record = json.loads(ROUTER.with_suffix(".review.json").read_text())
                example = target / name
                example.write_bytes(example.read_bytes() + b"changed example\n")
                record["files"][name] = sha(example)
                target.with_suffix(".review.json").write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, "source retention failed"):
                    load_router(target, SOURCE.read_bytes())

    def test_package_root_symlink_is_rejected_even_with_valid_review(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "router-v7"
            target.symlink_to(ROUTER, target_is_directory=True)
            shutil.copyfile(
                ROUTER.with_suffix(".review.json"), target.with_suffix(".review.json")
            )
            with self.assertRaisesRegex(ValueError, "cannot be a symlink"):
                load_router(target, SOURCE.read_bytes())


    def test_hook_selection_blocks_and_post_checkpoint_remain_byte_identical(self):
        old = (PREVIOUS / "references/project-generation.md").read_bytes()
        new = (ROUTER / "references/project-generation.md").read_bytes()
        for start, end in (
            (b"- If the YAML cannot be parsed",
             b"## Execution Steps"),
            (b"8. **Post-hook checkpoint**:", b"9. **Report**:"),
        ):
            with self.subTest(start=start):
                self.assertEqual(old[old.index(start):old.index(end)],
                                 new[new.index(start):new.index(end)])

    def test_content_and_clarification_guidance_remain_byte_identical(self):
        old = (PREVIOUS / "references/project-generation.md").read_bytes()
        new = (ROUTER / "references/project-generation.md").read_bytes()
        for start, end in (
            (b"1. **Setup**:", b"2. **Project principles**:"),
            (b"3. **Clarify intent (dynamic)**:", b"8. **Post-hook checkpoint**:"),
            (b"   **CORE PRINCIPLE - Test the Requirements, Not the Implementation**:",
             b"8. **Post-hook checkpoint**:"),
        ):
            with self.subTest(start=start):
                self.assertEqual(old[old.index(start):old.index(end)],
                                 new[new.index(start):new.index(end)])
        start = b"**Important**:"
        self.assertEqual(old[old.index(start):], new[new.index(start):])

    def test_shared_rules_and_optional_routes_remain_byte_identical(self):
        old = (PREVIOUS / "SKILL.md").read_bytes()
        new = (ROUTER / "SKILL.md").read_bytes()
        end = b"For creating or appending an actual project checklist, read"
        self.assertEqual(old[:old.index(end)], new[:new.index(end)])
        start = b"For requests for domain sample questions"
        self.assertEqual(old[old.index(start):], new[new.index(start):])

if __name__ == "__main__":
    unittest.main()
