from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

from harnessmith.catalog import audit_catalog, load_catalog_profile
from harnessmith.cli import main
from harnessmith.errors import SkillCompilerError

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def skill(
        self,
        directory,
        name="review",
        description="Review requirements, not implementation.",
    ):
        path = self.root / directory / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "---\nname: %s\ndescription: %s\n---\nBody\n"
            % (
                json.dumps(name, ensure_ascii=False),
                json.dumps(description, ensure_ascii=False),
            )
        )
        return path

    def profile(self, budget, reserved=0):
        value = audit_catalog(self.root, "codex")["profile"]
        value.update(
            profile_id="test-v1",
            budget_characters=budget,
            reserved_characters=reserved,
            evidence="Synthetic test; not a host limit.",
        )
        path = self.root / "profile.json"
        path.write_text(json.dumps(value))
        return path

    def test_measured_components_include_paths_escapes_and_unicode(self):
        self.skill("nested/é", description='A "quoted" café description')
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = audit_catalog(self.root, "codex")
        entry = report["entries"][0]
        line = (
            json.dumps(
                {k: entry[k] for k in ("name", "description", "path")},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )
        self.assertEqual(len(line), report["listing_characters"])
        self.assertEqual(len(line), sum(report["components_characters"].values()))
        self.assertEqual(
            len(entry["description"]), report["components_characters"]["description"]
        )
        self.assertIsNone(report["overflow_characters"])
        self.assertIsNone(report["runtime_metrics"])
        self.assertEqual(report, audit_catalog(self.root, "codex"))
        self.assertEqual(
            before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        )

    def test_crowded_catalog_duplicates_and_exact_overflow_boundary(self):
        for index in range(30):
            self.skill(
                "skill-%02d" % index,
                name="duplicate" if index < 2 else "skill-%d" % index,
                description="Shared scope" if index < 2 else "Unique scope %d" % index,
            )
        report = audit_catalog(self.root, "codex")
        self.assertEqual(
            ["HS401", "HS403"], [d["rule_id"] for d in report["diagnostics"]]
        )
        size = report["listing_characters"]
        path = self.profile(size + 100, 100)
        self.assertEqual(
            0, audit_catalog(self.root, "codex", path)["overflow_characters"]
        )
        path = self.profile(size + 99, 100)
        report = audit_catalog(self.root, "codex", path)
        self.assertEqual(1, report["overflow_characters"])
        self.assertIn("HS402", [d["rule_id"] for d in report["diagnostics"]])

    def test_profile_validation_and_provenance(self):
        path = self.profile(100)
        original = json.loads(path.read_text())
        first = audit_catalog(self.root, "codex", path)["profile_sha256"]
        for key, value in [
            ("schema_version", True),
            ("budget_characters", True),
            ("reserved_characters", -1),
            ("target", "claude"),
            ("listing_format", "native"),
            ("host_version", ""),
            ("extra", 1),
        ]:
            with self.subTest(key=key):
                path.write_text(json.dumps({**original, key: value}))
                with self.assertRaises(SkillCompilerError):
                    load_catalog_profile(path, "codex")
        path.write_text(json.dumps({**original, "host_version": "test-v2"}))
        self.assertNotEqual(
            first, audit_catalog(self.root, "codex", path)["profile_sha256"]
        )
        path.write_text("{")
        with self.assertRaises(SkillCompilerError):
            load_catalog_profile(path, "codex")

    def test_empty_catalog_and_invalid_inputs(self):
        self.assertEqual(0, audit_catalog(self.root, "claude")["listing_characters"])
        with self.assertRaises(SkillCompilerError):
            audit_catalog(self.root, "cursor")
        with self.assertRaises(SkillCompilerError):
            audit_catalog(self.root / "absent", "codex")
        path = self.skill("bad")
        path.write_text("---\nname: bad\n---\nBody\n")
        with self.assertRaises(SkillCompilerError):
            audit_catalog(self.root, "codex")
        path.unlink()
        path.symlink_to(ROOT / "skills/speckit-analyze/SKILL.md")
        with self.assertRaises(SkillCompilerError):
            audit_catalog(self.root, "codex")

    def test_cli_formats_thresholds_and_errors(self):
        self.skill("first")
        self.skill("second")
        for flags in (["--json"], ["--format", "json"], ["--format", "sarif"], []):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                result = main(
                    [
                        "catalog",
                        str(self.root),
                        "--target",
                        "codex",
                        "--fail-on",
                        "warning",
                        *flags,
                    ]
                )
            self.assertEqual(1, result)
            self.assertIn("HS401", out.getvalue())
            if flags:
                json.loads(out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                2,
                main(
                    [
                        "catalog",
                        str(self.root),
                        "--target",
                        "codex",
                        "--json",
                        "--format",
                        "sarif",
                    ]
                ),
            )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["catalog", str(self.root), "--target", "claude"]))

    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "requires .[dev]")
    def test_reports_and_profiles_match_published_schemas(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource

        registry = Registry().with_resources(
            (
                (path.name, Resource.from_contents(json.loads(path.read_text())))
                for path in (ROOT / "schemas").glob("*.schema.json")
            )
        )
        self.skill("first")
        self.skill("second")
        report = audit_catalog(self.root, "codex", self.profile(1))
        for name, value in [
            ("catalog-report", report),
            ("catalog-profile", report["profile"]),
        ]:
            schema = json.loads(
                (ROOT / ("schemas/" + name + ".schema.json")).read_text()
            )
            Draft202012Validator(schema, registry=registry).validate(value)
