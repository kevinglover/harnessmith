"""Offline package and mocked turn checks; no claim of model fidelity."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from harnessmith.compiler import CompileOptions, compile_skill, write_package
from harnessmith.errors import SkillCompilerError
from harnessmith.evaluation_turns import EvaluationTurn, TurnTrace, check_turns
from harnessmith.parser import parse_skill
from harnessmith.recipe import load_recipe
from harnessmith.transforms import resolve_section
from harnessmith.verification import verify_compiled_package

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "checklist": {
        "constraints": (
            "**🚫 ABSOLUTELY PROHIBITED**",
            "**✅ REQUIRED PATTERNS**",
            "hooks.before_checklist",
            "hooks.after_checklist",
        ),
        "actions": (
            "check-before-hooks",
            "read-spec",
            "write-requirements-checklist",
            "report-checklist",
            "wait-after-hooks",
        ),
        "output": "Requirements quality checklist created.",
        "forbidden": ("test-implementation",),
        "metrics": (5674, 4918, 5820),
    },
    "clarify": {
        "constraints": (
            "Maximum of 5 total questions across the whole session.",
            "Respect user early termination signals",
            "**You MUST complete this section before reporting completion to the user.**",
            "hooks.before_clarify",
            "hooks.after_clarify",
        ),
        "actions": (
            "check-before-hooks",
            "read-spec",
            "ask-one-question",
            "integrate-answer",
            "wait-after-hooks",
            "report-coverage",
        ),
        "output": "Questions answered: 1. Coverage reported.",
        "forbidden": ("ask-sixth-question", "report-before-hooks"),
        "metrics": (5040, 4818, 5099),
    },
}


class ReviewedRecipeTests(unittest.TestCase):
    def package(self, name):
        source = ROOT / ("skills/speckit-" + name + "/SKILL.md")
        recipe = load_recipe(ROOT / ("recipes/speckit-" + name + ".cursor.json"))
        options = CompileOptions(
            target=recipe.target,
            extract_sections=recipe.extract_sections,
            expected_source_sha256=recipe.source_sha256,
            max_root_tokens=recipe.max_root_tokens,
            max_normal_path_tokens=recipe.max_normal_path_tokens,
            recipe_id=recipe.path.relative_to(ROOT).as_posix(),
            recipe_sha256=recipe.sha256,
        )
        return source, options, compile_skill(source, options)

    def test_exact_content_workflow_constraints_and_metrics(self):
        for name, case in CASES.items():
            with self.subTest(name=name):
                source, options, package = self.package(name)
                ir = parse_skill(source)
                for constraint in case["constraints"]:
                    self.assertIn(constraint, package.files["SKILL.md"])
                for transform in package.transformations:
                    if transform["type"] == "extract-section":
                        section = resolve_section(ir, transform["section_id"])
                        self.assertIn(
                            section.text.rstrip("\n") + "\n",
                            package.files[transform["output"]],
                        )
                        self.assertIn(transform["output"], package.files["SKILL.md"])
                metrics = package.metrics
                self.assertEqual(
                    case["metrics"],
                    tuple(
                        metrics[k]
                        for k in (
                            "source_skill_token_estimate",
                            "compiled_root_token_estimate",
                            "normal_path_instruction_token_estimate",
                        )
                    ),
                )
                self.assertEqual(0, metrics["conditional_reference_chars"])
                self.assertEqual(
                    metrics["normal_path_instruction_token_estimate"],
                    metrics["packaged_instruction_token_estimate"],
                )
                with tempfile.TemporaryDirectory() as directory:
                    output = Path(directory) / name
                    write_package(package, output)
                    self.assertTrue(verify_compiled_package(output).valid)
                    reference = next(output.glob("references/*.md"))
                    reference.write_text(reference.read_text() + "changed\n")
                    self.assertFalse(verify_compiled_package(output).valid)
                with self.assertRaisesRegex(SkillCompilerError, "source hash changed"):
                    compile_skill(
                        source, replace(options, expected_source_sha256="0" * 64)
                    )
                with self.assertRaises(SkillCompilerError):
                    compile_skill(source, replace(options, max_root_tokens=1))

    def test_paired_mock_workflows_and_reload_after_compaction(self):
        for name, case in CASES.items():
            _, _, package = self.package(name)
            refs = tuple(
                sorted(p for p in package.files if p.startswith("references/"))
            )
            canonical = TurnTrace(True, case["output"], case["actions"], ())
            compiled = replace(canonical, reference_loads=refs)
            first = EvaluationTurn(
                "prompt",
                "Run speckit-" + name,
                "user",
                True,
                case["actions"],
                (),
                refs,
                (case["output"],),
                (),
                canonical,
                compiled,
            )
            reload_turn = replace(
                first, event="compaction", prompt="Resume and reload references"
            )
            abort = EvaluationTurn(
                "abort",
                "Stop",
                "none",
                False,
                ("stop",),
                (),
                (),
                ("Stopped",),
                (),
                TurnTrace(False, "Stopped", ("stop",), ()),
                TurnTrace(False, "Stopped", ("stop",), ()),
            )
            turns = (first, reload_turn, abort)
            for variant in ("canonical", "compiled"):
                traces = tuple(getattr(t, "mock_" + variant) for t in turns)
                kwargs = dict(
                    variant=variant,
                    allow_model=True,
                    allow_user=True,
                    forbidden_actions=case["forbidden"],
                    available_files=tuple(package.files)
                    if variant == "compiled"
                    else (),
                )
                checks = check_turns(turns, traces, **kwargs)
                self.assertTrue(all(passed for _, passed, _ in checks), checks)
                # Missing a required read or changing workflow order must fail.
                bad = replace(traces[0], actions=tuple(reversed(traces[0].actions)))
                self.assertFalse(
                    all(
                        p
                        for _, p, _ in check_turns(turns, (bad, *traces[1:]), **kwargs)
                    )
                )
                if variant == "compiled":
                    bad = replace(traces[1], reference_loads=())
                    self.assertFalse(
                        all(
                            p
                            for _, p, _ in check_turns(
                                turns, (traces[0], bad, traces[2]), **kwargs
                            )
                        )
                    )
