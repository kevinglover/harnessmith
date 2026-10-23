from __future__ import annotations

import unittest
from pathlib import Path

from harnessmith.adapters import adapt_frontmatter
from harnessmith.contracts import CapabilityStatus
from harnessmith.errors import SkillCompilerError
from harnessmith.frontmatter import split_frontmatter
from harnessmith.model import InvocationPolicy, SkillIR
from harnessmith.targets import (
    CODEX,
    GENERIC,
    TARGET_NAMES,
    capability_documents,
    get_target,
    iter_targets,
)


def _ir(frontmatter: str) -> SkillIR:
    source = "---\n" + frontmatter + "---\n\nBody\n"
    fields, body, body_start_line = split_frontmatter(source)
    return SkillIR(
        source_path=Path("SKILL.md"),
        source_id="SKILL.md",
        source_text=source,
        source_sha256="0" * 64,
        frontmatter=fields,
        body=body,
        body_start_line=body_start_line,
        sections=(),
    )


class AdapterContractTests(unittest.TestCase):
    def test_registry_has_stable_unique_targets_and_contracts(self) -> None:
        self.assertEqual(("generic", "cursor", "claude", "codex"), TARGET_NAMES)
        definitions = tuple(iter_targets())
        self.assertEqual(TARGET_NAMES, tuple(item.name for item in definitions))
        self.assertEqual(set(TARGET_NAMES), set(capability_documents()))
        for definition in definitions:
            self.assertEqual(definition.name, definition.capabilities.target)
            names = [item.name for item in definition.capabilities.capabilities]
            self.assertEqual(len(names), len(set(names)))

    def test_target_lookup_is_case_insensitive_and_unknown_fails_closed(self) -> None:
        self.assertIs(get_target("CoDeX"), CODEX)
        with self.assertRaisesRegex(SkillCompilerError, "unknown target"):
            get_target("invented")

    def test_generic_and_codex_field_contracts_are_independent(self) -> None:
        self.assertEqual(GENERIC.frontmatter_fields, CODEX.frontmatter_fields)
        self.assertIsNot(GENERIC.frontmatter_fields, CODEX.frontmatter_fields)
        self.assertEqual(
            CapabilityStatus.UNSUPPORTED,
            GENERIC.capability("invocation.model").status,
        )
        self.assertEqual(
            CapabilityStatus.SUPPORTED,
            CODEX.capability("invocation.model").status,
        )

    def test_every_target_declares_required_cross_target_capabilities(self) -> None:
        required = {
            "invocation.model",
            "invocation.user",
            "arguments",
            "frontmatter.extensions",
            "content.references",
            "content.scripts",
            "tools.allowlist",
        }
        for definition in iter_targets():
            names = {item.name for item in definition.capabilities.capabilities}
            self.assertTrue(required <= names, definition.name)

    def test_declared_user_invocation_support_matches_adapter_behavior(self) -> None:
        ir = _ir("name: hidden\ndescription: Hidden\nuser-invocable: false\n")
        for definition in iter_targets():
            status = definition.capability("invocation.user").status
            if status is CapabilityStatus.SUPPORTED:
                adapt_frontmatter(ir, definition.name, InvocationPolicy(False, False))
            else:
                with self.assertRaises(SkillCompilerError, msg=definition.name):
                    adapt_frontmatter(
                        ir, definition.name, InvocationPolicy(False, False)
                    )

    def test_behavior_bearing_unknown_fields_still_fail_closed(self) -> None:
        ir = _ir("name: test\ndescription: Test\nunknown-policy: strict\n")
        for target in TARGET_NAMES:
            with self.assertRaisesRegex(SkillCompilerError, "cannot preserve"):
                adapt_frontmatter(ir, target, InvocationPolicy())


class ToolCapabilityTests(unittest.TestCase):
    def test_v2_distinguishes_representation_from_runtime_claims(self) -> None:
        for definition in iter_targets():
            self.assertEqual(2, definition.capabilities.schema_version)
            self.assertIs(CapabilityStatus.SUPPORTED,
                          definition.capability('tools.allowed_metadata').status)
            self.assertIs(CapabilityStatus.UNSUPPORTED,
                          definition.capability('tools.allowlist').status)
            expected = (CapabilityStatus.UNSUPPORTED if definition.name == 'generic'
                        else CapabilityStatus.UNKNOWN)
            self.assertIs(expected, definition.capability('tools.preapproval').status)
            self.assertIs(expected, definition.capability('tools.restriction').status)
        self.assertIs(CapabilityStatus.UNKNOWN,
                      get_target('claude').capability('tools.denylist').status)

    def test_permission_fields_are_never_converted_to_restrictions(self) -> None:
        ir = _ir('name: example\ndescription: Example\nallowed-tools: Read Grep\n')
        for definition in iter_targets():
            adapted = adapt_frontmatter(ir, definition.name, InvocationPolicy())
            fields = {field.key: field.raw for field in adapted.fields}
            self.assertEqual('allowed-tools: Read Grep\n', fields['allowed-tools'])
            self.assertNotIn('disallowed-tools', fields)
        restricted = _ir('name: example\ndescription: Example\ndisallowed-tools: Write\n')
        for target in ('generic', 'cursor', 'codex'):
            with self.assertRaisesRegex(SkillCompilerError, 'cannot preserve'):
                adapt_frontmatter(restricted, target, InvocationPolicy())
        adapted = adapt_frontmatter(restricted, 'claude', InvocationPolicy())
        self.assertIn('disallowed-tools: Write\n', [f.raw for f in adapted.fields])

    def test_unrecognized_restrictive_policy_fails_closed(self) -> None:
        ir = _ir('name: example\ndescription: Example\ntools-policy: exclusive\n')
        for target in TARGET_NAMES:
            with self.assertRaisesRegex(SkillCompilerError, 'cannot preserve'):
                adapt_frontmatter(ir, target, InvocationPolicy())


if __name__ == "__main__":
    unittest.main()
