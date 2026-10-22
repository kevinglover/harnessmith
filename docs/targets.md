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
| Preserve tool metadata | Space-separated string | Space-separated string | String or YAML list | Space-separated string |
| Exclusive allowlist | Unsupported | Unsupported | Unsupported | Unsupported |
| Runtime preapproval | No runtime | Unverified | Documented; unverified | Unverified |
| Runtime restriction | No runtime | Unverified | `disallowed-tools`, documented; unverified | Unverified |

For adaptation, “unsupported” means Harnessmith fails when a requested source
behavior cannot be represented. Runtime capability declarations describe evidence,
not a blanket rejection of metadata preservation. Presentation-only fields such as argument hints, icons, and colors
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

## Metadata validation

Each target declares a `MetadataPolicy`. All canonical packages still require
nonempty string `name` and `description` fields, even where a host offers defaults.
Generic, Cursor, and Codex use the portable policy: names up to 64 characters,
lowercase letters/digits and single interior hyphens, descriptions up to 1,024
characters, and compatibility strings up to 500 characters. These are compiler
acceptance rules, not claims that every host rejects all other inputs.

Claude permits command-style names and longer descriptions; the compiler rejects
control/format characters, angle brackets, and invalid whitespace in those names.
Its tool fields accept space/comma-separated strings and flat YAML string lists.
Other targets require portable space-separated tool strings; no list-to-string
conversion is attempted. `metadata` is a string-to-string map, and `license` is a
string. Validation retains original field text, including quotes and comments.

The dependency-free interpreter supports plain, quoted, literal/folded string
scalars, flat block maps, flat flow maps, and flat tool lists. It fails closed on
anchors, tags, nested collections, or other forms it cannot confidently type;
it is not a complete YAML validator. Diagnostics identify unsupported forms so
an author can review them rather than having the compiler normalize them.

`HS102` errors block compilation. `HS103` warns when a portable target's source
directory differs from its skill name. Output paths may be arbitrary staging
directories; install the result under its skill name. Offline corpus evaluations
use `audit_skill(..., check_directory=False)` because fixture IDs are storage
names, not installation names. Claude permits a different directory name.

These policies follow the [Agent Skills specification](https://agentskills.io/specification)
and [Claude Code skill documentation](https://code.claude.com/docs/en/skills),
reviewed October 22, 2026. Host documentation remains mutable.

## Tool capability contract version 2

Capability documents now use schema version 2 and add `unknown` status. Consumers
must select [the version 2 schema](../schemas/adapter-capabilities-v2.schema.json);
the [version 1 schema](../schemas/adapter-capabilities.schema.json) remains available
for historical documents. Diagnostic, recipe, fixture, and package schemas stay
at version 1.

- `tools.allowed_metadata` and Claude's `tools.disallowed_metadata` describe
  compiler preservation of accepted field representations.
- `tools.preapproval` describes permission grants; `tools.restriction` describes
  removal of tool access. Their runtime status is `unknown` for hosts because
  no versioned runtime evidence has been captured. Generic has no runtime.
- The legacy `tools.allowlist` key remains present but is `unsupported`: the
  compiler cannot express an exclusive tool restriction through `allowed-tools`.
  Claude's legacy `tools.denylist` changes to `unknown`.

Claude documents grants and restrictions that expire on the next user message;
managed-only permission rules can ignore grants from some skill sources starting
in v2.1.282. `disallowed-tools` also has an `EndConversation` exception. These are
documented semantics, not measured guarantees. `HS306` makes that distinction
visible whenever accepted tool fields are preserved. No adapter turns a grant
into a restriction, and unsupported restriction fields still fail closed.

## Body syntax policy

Non-Claude targets report Claude command injection and substitutions: dynamic
commands, `$ARGUMENTS`, indexed arguments, declared named arguments, and known
`${CLAUDE_*}` tokens. `HS307` warns about occurrences in ordinary body text;
`HS308` notes occurrences in code, block quotes, comments, or escaped text.
Those lexical categories help review examples but do not prove that a host skips
preprocessing. Unrecognized syntax and external reference files are outside this
initial scanner's coverage.

Body findings are advisory during compilation: text is preserved and no command
is executed, substituted, or automatically rewritten. The compile CLI exposes
findings in JSON and prints them on stderr in text mode. Audit CI can reject
warnings with `--fail-on warning`, or include possible literal examples using
`--fail-on note`. The Claude target is the documented-syntax control, not a claim
of live behavioral validation. Known unsupported frontmatter still blocks builds.
