# Harness-aware Agent Skill compilation

## Conclusion

One canonical behavioral definition can produce harness-aware packages without
creating a manually maintained fork, but only if compilation is conservative:

- keep normative workflow instructions lossless;
- make progressive-disclosure extraction explicit and reversible;
- model invocation policy independently from any runtime's frontmatter;
- fail when a target cannot represent a behavior-bearing capability;
- record source-section and output hashes after all formatting;
- evaluate behavior as well as root-file size.

The implemented vertical slice proves those mechanics for
`skills/speckit-analyze/SKILL.md` and Cursor. The reviewed optimization reduces
the root from an estimated 3,066 tokens to 1,604 tokens (48%). More importantly,
the normal static path—root plus mandatory references—falls to 2,437 tokens,
21% below the canonical skill. The package also retains the exact original hook
contracts as a conditional fallback. Estimates use a reproducible four
characters per token; behavioral agent evals are still required before treating
the package as production-equivalent.

## How this repository currently generates and synchronizes skills

### Source and update flow

The checked-in Spec Kit version is `specify 1.0.8` in `VERSION.md`. The CI entry
point is `.github/workflows/ci.yml`, which calls
`.github/workflows/speckit-init.yml` for `codex`, `agy`, `cursor-agent`,
`copilot`, `opencode`, and `claude`.

The reusable workflow:

1. resolves the latest GitHub Spec Kit release;
2. installs that exact release of `specify-cli`;
3. writes `specify --version` to `VERSION.md`;
4. skips regeneration when that file is unchanged;
5. runs `specify init --force --here --ignore-agent-tools --script sh --integration <runtime>` for each configured integration;
6. formats Markdown and JSON;
7. commits regenerated output.

The behavioral source is upstream Spec Kit command content, identified in each
skill by metadata such as `templates/commands/analyze.md`. Current upstream
generation is implemented by the
[Spec Kit skills integration](https://github.com/github/spec-kit/blob/main/src/specify_cli/integrations/base.py),
with runtime post-processing in adapters such as
[Claude](https://github.com/github/spec-kit/blob/main/src/specify_cli/integrations/claude/__init__.py),
[Codex](https://github.com/github/spec-kit/blob/main/src/specify_cli/integrations/codex/__init__.py),
and
[Cursor](https://github.com/github/spec-kit/blob/main/src/specify_cli/integrations/cursor_agent/__init__.py).

There is no `AGENTS.md` or repository-local contribution guide in this checkout.
The applicable contribution guidance therefore comes from the upstream
[GitHub Spec Kit contribution guide](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md)
when a change belongs in generation, and from this repository's README and CI
when a change is repository-specific.

### Canonical versus generated material

| Material                                                                          | Role                                                   | Maintenance rule                                                 |
| --------------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------- |
| Upstream `templates/commands/*.md`                                                | Behavioral source for Spec Kit commands                | Change upstream when behavior should change for all integrations |
| `skills/speckit-*/SKILL.md`                                                       | Generated shared output                                | Do not hand-edit; regenerate                                     |
| `.cursor/skills/speckit-*/SKILL.md`                                               | Generated Cursor copies                                | Do not hand-edit; regenerate or compile                          |
| `.github/agents`, `.github/prompts`, `.opencode/commands`, `.gemini/commands`     | Generated runtime entry points                         | Treat as outputs                                                 |
| `.specify/scripts`, `.specify/templates`, `.specify/integrations/*.manifest.json` | Generated project infrastructure and integration state | Regenerate from Spec Kit                                         |
| `skills/speckit-baseline/SKILL.md`                                                | Repository-specific skill                              | Maintained here                                                  |
| `skills/claude-command-converter/SKILL.md`                                        | Repository-specific conversion guidance                | Maintained here                                                  |
| `harnessmith/`                                                                    | Experimental compiler implementation                   | Maintained here until an upstream home is chosen                 |

### What `claude-command-converter` actually does

`skills/claude-command-converter/SKILL.md` is an instruction-only skill, not an
executable converter. It tells an agent to read a `.claude/commands/*.md` file,
derive a kebab-case skill name, move `$ARGUMENTS` into an Inputs section, move
handoffs into prose, remove slash-command syntax, and retain only portable
frontmatter. It contains important fidelity guidance, but it has no parser,
provenance model, deterministic renderer, or tests. The new compiler does not
replace it yet; it establishes those missing mechanical layers.

### Runtime exposure today

- `.claude/skills` is a symlink to `../skills`.
- `.agents/skills` is a symlink to `../skills` and is used by Codex.
- Cursor receives physical copies under `.cursor/skills`.

This gives Claude and Codex the same bytes even when their native metadata
capabilities differ. It also makes generation order observable: Codex, Agy, and
Claude manifests all claim the same physical `skills/...` paths with different
hashes. The final shared files include Claude-specific `argument-hint`,
`user-invocable`, and `disable-model-invocation` fields, while Cursor copies do
not include all of them.

The manifest hashes are not final integrity hashes. For example, the checked-in
`skills/speckit-analyze/SKILL.md` hash does not match the value recorded in any
of the Agy, Codex, or Claude manifests. Later integrations overwrite the shared
path, and formatting occurs after generation. A compiler manifest should
therefore hash the normalized canonical input and the final rendered files,
which this vertical slice does.

## Verified harness capability matrix

The standard defines the portable package; harness documentation defines
discovery, invocation, and extensions. An empty cell below means the primary
documentation does not establish the capability, not that the runtime can
never implement it.

| Capability                           | Agent Skills standard                                                          | Cursor                                                                                                    | Claude Code                                                                                                                        | Codex                                                                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Discovery paths                      | Not specified by the format                                                    | Project `.agents/skills`, `.cursor/skills`; matching user locations; compatibility paths for Claude/Codex | Project, nested, personal, enterprise `.claude/skills`; plugin `skills/`                                                           | Scans `.agents/skills` from CWD to repo root; user `$HOME/.agents/skills`; `/etc/codex/skills`; system skills; follows symlinks     |
| Required frontmatter                 | `name`, `description`                                                          | `name`, `description`                                                                                     | `description` recommended; `name` optional in Claude, though portable packages should keep both                                    | `name`, `description`; standard-compatible                                                                                          |
| Portable optional frontmatter        | `license`, `compatibility`, `metadata`, experimental `allowed-tools`           | Documents `metadata`; runtime handling of other portable optional fields is not described                 | Accepts `license`, `metadata`, `allowed-tools`; also many native extensions                                                        | Uses the open standard; runtime-specific invocation policy lives outside frontmatter                                                |
| Runtime frontmatter/extensions       | None                                                                           | `paths`, `disable-model-invocation`, `icon`, `color`; legacy `globs` fallback                             | `when_to_use`, arguments, invocation controls, tool controls, model/effort, `context: fork`, agent/background, hooks, paths, shell | `agents/openai.yaml` can declare presentation, dependencies, and `policy.allow_implicit_invocation`                                 |
| Explicit invocation                  | Not specified                                                                  | `/skill-name`                                                                                             | `/skill-name`                                                                                                                      | `/skills` selector or `$skill-name` mention                                                                                         |
| Model-driven invocation              | Description-based activation is the common model, not a portable control field | Default; disabled by `disable-model-invocation: true`                                                     | Default; disabled by `disable-model-invocation: true`                                                                              | Default; disabled by `agents/openai.yaml` with `allow_implicit_invocation: false`                                                   |
| Progressive disclosure               | Metadata, then full `SKILL.md`, then resources as needed                       | Yes; manual use attaches to one message, Custom Mode keeps it for the session                             | Description first; invoked body stays in conversation; supporting files should be loaded on demand                                 | Name/description/path list first; full skill when selected; initial list is context-budgeted                                        |
| `references/`, `scripts/`, `assets/` | All defined as optional conventions                                            | All documented                                                                                            | Supporting files and bundled scripts documented                                                                                    | Scripts, references, and assets documented                                                                                          |
| Context-specific constraint          | Root instructions under 5,000 tokens recommended; under 500 lines              | `paths` and nested skill directories can scope discovery                                                  | Loaded skill persists across turns; compaction reattaches up to 5,000 tokens per skill within a 25,000-token combined budget       | Initial skill list uses at most 2% of context or 8,000 characters when context is unknown; descriptions may be shortened or omitted |

Primary sources:

- [Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)

### Portability implications

Invocation is the clearest adapter boundary. `disable-model-invocation` is a
Cursor and Claude field, while Codex expresses the equivalent model-selection
restriction in `agents/openai.yaml`. `user-invocable: false` has no documented
Cursor or Codex equivalent. A compiler must reject that conversion rather than
silently exposing a command the source intended to hide.

Likewise, `paths`, `context: fork`, skill hooks, model selection, and tool
controls are not portable standard features. They belong in target adapters or
in a declared compatibility error, not in scattered conditional rewrites.

## Concrete inefficiencies in the current skills

The 11 shared `speckit-*` root files contain 143,545 characters, 2,685 lines,
and an estimated 35,890 tokens. Ten have Cursor counterparts whose bodies are
byte-for-byte identical; only frontmatter differs.

Representative cases:

| Skill               | Lines | Estimated root tokens | Observation                                                                                                                      |
| ------------------- | ----: | --------------------: | -------------------------------------------------------------------------------------------------------------------------------- |
| `speckit-baseline`  |   114 |                 1,121 | Small repository-specific skill and a useful control; splitting it would add navigation without meaningful savings               |
| `speckit-analyze`   |   271 |                 3,066 | Global read-only constraints must stay in root, but the detailed detection rubric and report/remediation/hook tail can be staged |
| `speckit-implement` |   238 |                 3,300 | Contains approval gates, checklist branching, mutation rules, and mandatory pre/post hooks; unsafe to summarize mechanically     |
| `speckit-checklist` |   395 |                 5,674 | Exceeds the standard's recommended 5,000-token root size and contains long stage-specific rubrics                                |
| `speckit-clarify`   |   308 |                 5,040 | Also crosses the recommended root token budget and mixes orchestration with detailed procedure                                   |
| `speckit-specify`   |   360 |                 4,662 | Near the budget and combines top-level safety with large detailed stages                                                         |

Ten skills repeat extension-hook instructions; five repeat a full Mandatory
Post-Execution Hooks section. The repetition may still be necessary in a fully
self-contained package, but it is a candidate for lossless reference
extraction or upstream reusable generation—not ad hoc summarization.

The frontmatter also demonstrates harness leakage: the shared files contain
Claude-specific keys because Claude writes last through a symlink, while the
Cursor copies have a different subset. Codex currently sees those Claude keys
even though its documented invocation control is `agents/openai.yaml`.

## Architecture

The implemented flow is:

```text
Canonical SKILL.md
        |
        v
Lossless parser + SkillIR
  - raw top-level YAML fields
  - body sections and line ranges
  - source path + SHA-256
        |
        v
Explicit optimization passes
  - selected section extraction
  - reviewed Spec Kit hook resolution
        |
        v
Harness adapter
  - capability validation
  - frontmatter filtering/mapping
  - invocation policy rendering
        |
        v
Skill package
  - SKILL.md
  - references/
  - scripts/
  - target metadata
  - .harnessmith.json
```

The parser retains raw frontmatter blocks instead of serializing YAML, so nested
maps, lists, comments, and quoting survive unchanged. It interprets only the
scalar fields needed for compiler decisions. The IR records every heading's
source offsets and line range.

Section extraction is opt-in by exact heading. The pass copies the complete
source section to a reference and leaves the original heading in place with a
mandatory load-before-continuing instruction. Duplicate, missing, ambiguous,
or overlapping selectors fail. A second explicit pass can replace the reviewed
Spec Kit pre/post hook contracts with a read-only resolver. Exact replaced prose
is retained in a conditional fallback. Verification reconstructs nested
transformations and confirms normative lines containing terms such as MUST,
NEVER, REQUIRED, STOP, or "do not" remain in the package.

Target adapters share no transformation conditionals with the extraction pass.
They receive an `InvocationPolicy` and render it natively:

- Cursor: `disable-model-invocation` in `SKILL.md`;
- Claude: `disable-model-invocation` and `user-invocable` in `SKILL.md`;
- Codex: `policy.allow_implicit_invocation` in `agents/openai.yaml` when needed;
- generic: only the standard default policy is representable.

## Deterministic transformations versus semantic judgment

| Transformation                                                                    | Classification                                                        | Reason                                                                                                                                                            |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Parse frontmatter and ATX sections                                                | Deterministic                                                         | Structural and lossless                                                                                                                                           |
| Map an explicitly declared invocation policy                                      | Deterministic                                                         | Capability mapping with documented equivalents                                                                                                                    |
| Copy a selected complete section to a reference                                   | Deterministic after selection                                         | Bytes and load directive are fixed; section choice still needs a human/configured recipe                                                                          |
| Record source/output hashes and line provenance                                   | Deterministic                                                         | Content-derived, no timestamps                                                                                                                                    |
| Extract known parsing, validation, normalization, or filtering into a script      | Deterministic only when the source already defines complete mechanics | The compiler must not invent edge-case behavior                                                                                                                   |
| Resolve the reviewed Spec Kit hook contract                                       | Deterministic with lossless fallback                                  | The helper filters disabled/conditional hooks, formats target invocation, never executes commands, and routes unsupported YAML to the exact original instructions |
| Decide which prose is globally necessary                                          | Semantic judgment                                                     | Depends on safety, branching, and workflow meaning                                                                                                                |
| Summarize or rewrite a long procedure                                             | Semantic judgment and out of scope                                    | Can silently weaken requirements                                                                                                                                  |
| Infer that a command is explicit-only from `user-invocable: true` or `$ARGUMENTS` | Unsafe inference                                                      | Those signals do not disable model invocation                                                                                                                     |
| Convert prose hooks to native runtime hooks                                       | Semantic judgment                                                     | Native lifecycle, permissions, and failure behavior differ                                                                                                        |

This is why the CLI requires exact `--extract-section` selectors. A future recipe
file can version reviewed extraction choices without teaching the compiler to
guess from length.

## Evaluation criteria

### Static fidelity gates

Every compile should pass:

- source hash and final output hashes recorded after formatting;
- every extracted reference contains the exact source section;
- no selected section is missing, duplicated, ambiguous, or nested under
  another selected section;
- normative statement multiset retained across root plus references;
- source heading order retained in the root orchestration layer;
- invocation policy either mapped exactly or rejected;
- target-unsupported behavior fields rejected;
- regeneration changes only manifest-owned files;
- identical input and options produce byte-identical output.

The current unit suite covers those core properties, including fail-closed
invocation conversion and safe regeneration.

### Context efficiency

Track separately:

- source root characters and token estimate;
- compiled root characters and token estimate;
- total reference size;
- mandatory versus conditional reference size;
- root-plus-mandatory normal-path size;
- packaged instruction and script size;
- root reduction percentage;
- path-loaded characters for representative runs;
- actual runtime input-token usage when traces are available.

Root reduction alone is not success. For a path that always needs every
reference immediately, total loaded context may stay flat or grow slightly.
The value is strongest when detailed branches or remediation guidance are not
needed on every invocation.

### Behavioral evaluation

Use a small fixture matrix for each skill:

- positive explicit invocation;
- positive implicit invocation where supported;
- negative trigger control;
- missing prerequisite/abort path;
- approval-boundary path;
- normal successful path;
- hook-present, hook-absent, invalid-hook-config, and mandatory-hook paths;
- expected output structure and write set.

Compare canonical and compiled runs on workflow selection, command order,
files read/written, abort behavior, approvals, hook dispatch, output sections,
and token usage. OpenAI's
[skill eval guidance](https://developers.openai.com/blog/eval-skills) recommends
capturing `codex exec --json` traces and combining deterministic checks with a
small rubric-based grade. Equivalent runtime runners can use the same fixture
contract.

## Implemented smallest useful slice

The repository evidence supports a local proof rather than replacing Spec Kit
generation immediately. The slice includes:

1. a dependency-free Python parser and provenance-aware IR;
2. capability definitions and adapters for generic, Cursor, Claude, and Codex;
3. a lossless, exact-heading extraction pass;
4. deterministic `.harnessmith.json` provenance;
5. a dependency-free, read-only hook resolver with an exact fallback contract;
6. root, normal-path, packaged, conditional, and script metrics plus enforceable
   token budgets;
7. normative-retention and exact-section verification;
8. safe regeneration that refuses non-compiler output directories;
9. unit, CLI, and generated-script tests;
10. one checked-in Cursor example for `speckit-analyze`.

Example command:

```bash
python3 -m harnessmith skills/speckit-analyze/SKILL.md \
  --target cursor \
  --output examples/compiled/cursor/speckit-analyze \
  --source-id skills/speckit-analyze/SKILL.md \
  --optimize-extension-hooks \
  --extract-section '4. Detection Passes (Token-Efficient Analysis)' \
  --extract-section 'Specification Analysis Report' \
  --max-root-tokens 1700 \
  --max-normal-path-tokens 2500 \
  --json
```

Measured output:

| Metric                     | Characters | Estimated tokens |                                Versus canonical |
| -------------------------- | ---------: | ---------------: | ----------------------------------------------: |
| Canonical root             |     12,263 |            3,066 |                                               — |
| Compiled root              |      6,416 |            1,604 |                                     48% smaller |
| Mandatory references       |      3,331 |              833 |                       Loaded by the normal path |
| Normal static path         |      9,747 |            2,437 |                                     21% smaller |
| Conditional exact fallback |      4,703 |            1,176 | Loaded only when resolver reports `unavailable` |
| All packaged Markdown      |     14,450 |            3,613 |             18% larger, not normally all loaded |
| Resolver script            |     10,541 |            2,636 |     Executed without loading its implementation |

The compiler reports both path-loaded and packaged size so a smaller root cannot
hide a larger mandatory path. Runtime script output and actual tokenizer counts
still require behavioral traces.

## Generalization beyond Spec Kit

A second real-world fixture should come from a different domain and exercise the
same compiler-relevant shape as the larger Spec Kit workflows:

- global invariants and approval boundaries;
- ordered stages with semantically meaningful sequencing;
- conditional branches and supporting references;
- deterministic validation or normalization mechanics;
- detailed remediation material needed only after a specific failure.

An editorial or publishing workflow would be a useful candidate because it
combines qualitative judgment with mechanical validation. A conservative recipe
would keep identity, scope, selection rules, approval boundaries, and the
top-level procedure in `SKILL.md`; move branch-specific guidance and detailed
failure remediation to references; and consider scripts only for mechanical
checks.

A particularly useful portability test is a source skill that combines
`disable-model-invocation: true` with `user-invocable: false`. Claude documents
those as separate model- and user-invocation controls, while Codex does not use
those `SKILL.md` fields for invocation policy. The intended policy must therefore
be explicit before compilation. The compiler correctly refuses to map
`user-invocable: false` to Cursor or Codex when no documented equivalent exists;
that fail-closed behavior is the generalizable result.

## What belongs upstream

### GitHub Spec Kit

The following should be proposed upstream if the proof holds:

- a canonical command/skill IR with provenance to `templates/commands/*.md`;
- target adapters that emit runtime-native metadata after one canonical parse;
- post-format manifests that hash final bytes;
- elimination of order-dependent writes through shared symlink targets;
- reusable generation for repeated hook prose;
- fixture-based semantic preservation checks across integrations.

Spec Kit already owns the command sources and runtime integrations, so permanent
support for generated optimized packages belongs there rather than in a
downstream fork.

### Agent Skills specification

Potential standardization topics are narrower:

- a portable declaration of model/user invocation policy;
- a conventional provenance manifest for generated skills;
- normative guidance for required reference loading;
- optional conformance fixtures for package-level semantic preservation.

Runtime-specific UI, custom modes, model choice, subagent execution, and native
hooks should remain extensions unless multiple implementations converge on the
same semantics.

## Current limitations

- Section selection is reviewed/operator-supplied, not inferred.
- The parser preserves arbitrary YAML blocks but only interprets simple scalar
  fields needed for adapter decisions.
- Static normative checks are a guardrail, not a proof of behavioral
  equivalence.
- There is no live Cursor/Claude/Codex behavioral runner in this repository yet.
- Generated scripts are supported for the reviewed hook transform; copying
  arbitrary scripts/assets from a multi-file canonical input is not yet.
- The hook resolver handles the generated Spec Kit YAML shape without a
  dependency, uses PyYAML when available, and loads the exact prose fallback for
  valid YAML features outside its safe subset.
- Only `speckit-analyze` has a checked-in compiled demonstration.

These constraints are intentional. The slice establishes evidence and
reversibility before any bulk conversion or source rewrite.
