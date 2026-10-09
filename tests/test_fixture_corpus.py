from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harnessmith.fixture_corpus import (
    FixtureValidationError,
    load_and_validate_manifest,
)
from harnessmith.compiler import CompileOptions, compile_skill
from harnessmith.errors import SkillCompilerError
from harnessmith.metrics import estimate_tokens


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "fixtures" / "manifest.json"


class FixtureCorpusTests(unittest.TestCase):
    def test_corpus_is_pinned_diverse_and_offline_valid(self) -> None:
        records = load_and_validate_manifest(MANIFEST, ROOT)
        self.assertGreaterEqual(len(records), 10)
        self.assertGreaterEqual(len({record.repository for record in records}), 5)
        self.assertTrue(all(record.revision for record in records))
        self.assertTrue(all(record.license for record in records))

    def test_manifest_covers_required_structural_cases(self) -> None:
        records = load_and_validate_manifest(MANIFEST, ROOT)
        fixture_ids = {record.fixture_id for record in records}
        self.assertTrue(
            {
                "anthropic-small",
                "anthropic-explicit-only",
                "github-copilot-frontmatter",
                "github-copilot-duplicate-headings",
                "huggingface-heavy-examples",
                "microsoft-fenced-headings",
                "microsoft-setext",
                "vercel-cross-links",
                "vercel-html-block",
                "speckit-over-budget",
            }.issubset(fixture_ids)
        )
        oversized = ROOT / "fixtures/sources/speckit-over-budget/SKILL.md"
        self.assertGreater(estimate_tokens(oversized.read_text(encoding="utf-8")), 5000)

    def test_expected_target_matrix_matches_compiler_behavior(self) -> None:
        records = load_and_validate_manifest(MANIFEST, ROOT)
        for record in records:
            actual = []
            for target in ("generic", "cursor", "claude", "codex"):
                try:
                    compile_skill(
                        ROOT / record.source_path,
                        CompileOptions(
                            target=target,
                            source_id=record.source_path,
                            expected_source_sha256=record.source_sha256,
                        ),
                    )
                except SkillCompilerError:
                    continue
                actual.append(target)
            self.assertEqual(record.expected_targets, tuple(actual), record.fixture_id)

    def test_hash_drift_is_rejected(self) -> None:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "fixtures/sources/example/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("changed", encoding="utf-8")
            record = document["fixtures"][0]
            record["source_path"] = "fixtures/sources/example/SKILL.md"
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(FixtureValidationError, "hash mismatch"):
                load_and_validate_manifest(manifest, root)

    def test_repository_escape_is_rejected_before_file_access(self) -> None:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
        document["fixtures"] = [document["fixtures"][0]]
        document["fixtures"][0]["source_path"] = "../SKILL.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(FixtureValidationError, "repository-relative"):
                load_and_validate_manifest(manifest, root)

    def test_duplicate_fixture_ids_are_rejected(self) -> None:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
        document["fixtures"].append(dict(document["fixtures"][0]))
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(FixtureValidationError, "unique"):
                load_and_validate_manifest(manifest, ROOT)


if __name__ == "__main__":
    unittest.main()
