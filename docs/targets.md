# Target capabilities

Harnessmith supports four target names. Capability declarations live in
`harnessmith.targets` and contract tests keep them aligned with adapter
behavior.

| Capability | generic | cursor | claude | codex |
| --- | --- | --- | --- | --- |
| Disable model/implicit invocation | Unsupported | `disable-model-invocation` | `disable-model-invocation` | `agents/openai.yaml` |
| Disable user invocation | Unsupported | Unsupported | `user-invocable` | Unsupported |
| Argument metadata | Unsupported | Unsupported | Native | Unsupported |
| Target-specific frontmatter | Unsupported | Cursor fields | Claude fields | Unsupported in `SKILL.md` |
| References | Supported | Supported | Supported | Supported |
| Scripts | Supported | Supported | Supported | Supported |
| Tool allowlist | Supported | Supported | Supported | Supported |
| Tool denylist | Not declared | Not declared | `disallowed-tools` | Not declared |

“Unsupported” means Harnessmith fails when the source behavior cannot be
preserved. Presentation-only fields such as argument hints, icons, and colors
may be omitted for targets that do not support them; this is recorded as a
frontmatter-filter transformation.

## Walkthrough: cross-harness invocation adaptation

Given a source that is user-invocable but must not be invoked implicitly by the
model:

```yaml
---
name: deploy-reviewed
description: Deploy only when explicitly requested.
disable-model-invocation: true
user-invocable: true
---
```

- Claude preserves both fields in `SKILL.md`.
- Cursor preserves `disable-model-invocation` and omits the redundant default
  user-invocation field.
- Codex emits standard `SKILL.md` frontmatter plus
  `agents/openai.yaml` with `policy.allow_implicit_invocation: false`.
- Generic compilation fails because the portable format has no invocation
  control for this non-default policy.

## Walkthrough: intentional fail-closed behavior

This source requires a skill to be hidden from users:

```yaml
---
name: internal-only
description: Internal routing skill.
user-invocable: false
---
```

Claude can represent it. Cursor and Codex cannot, so compilation stops with an
error instead of dropping the restriction. An unknown behavior-bearing field
also fails on every target. The operator must select a compatible target or
deliberately revise the canonical semantics.

For contributor details, see [Adding an adapter](adding-an-adapter.md).
