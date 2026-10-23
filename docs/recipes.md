# Recipes

A recipe is a strict, versioned JSON record of reviewed compiler choices. Keep
recipes beside source control rather than encoding maintained optimizations in
ad hoc command lines.

```json
{
  "schema_version": 1,
  "target": "cursor",
  "source_sha256": "<64 lowercase hexadecimal characters>",
  "invocation": "source",
  "extract_sections": ["Detailed examples"],
  "optimizations": [],
  "budgets": {
    "root_tokens": 5000,
    "normal_path_tokens": 7000
  }
}
```

All fields other than `schema_version` are optional, but maintained recipes
should normally set a target and source hash. Unknown keys, transforms, targets,
and budget names are rejected.

## Fields

- `target`: `generic`, `cursor`, `claude`, or `codex`.
- `source_sha256`: hash of the complete canonical `SKILL.md`. A mismatch stops
  compilation and requires re-audit.
- `invocation`: `source` preserves source policy; `explicit` disables model
  invocation but permits user invocation; `automatic` permits both. The target
  must be able to represent the result.
- `extract_sections`: exact heading selectors. Duplicate headings use the stable
  `Heading[n]` form.
- `optimizations`: currently only `spec-kit-extension-hooks`.
- `budgets.root_tokens` and `budgets.normal_path_tokens`: positive integer
  static-estimate ceilings.

The canonical schema is
[`schemas/recipe.schema.json`](../schemas/recipe.schema.json). The checked-in
[`speckit-analyze.cursor.json`](../recipes/speckit-analyze.cursor.json) is a
complete working example.

## Review lifecycle

1. Audit the current source and inspect candidate sections and target warnings.
2. Confirm that selected sections keep their load gate and global constraints
   in the root.
3. Copy the audited source hash into the recipe.
4. Preview with `--diff`.
5. Compile and run `harnessmith verify`.
6. When upstream changes, re-audit and review the recipe before updating its
   pinned hash.

The manifest separately records the recipe path and content hash, making both
source drift and policy drift detectable.

## Reviewed root-budget recipes

The [checklist recipe](../recipes/speckit-checklist.cursor.json) extracts
`Example Checklist Types & Sample Items` and `Anti-Examples: What NOT To Do`.
The root retains the requirements-quality purpose, execution steps, prohibited
implementation-test patterns, required patterns, and both hook contracts.
The [clarify recipe](../recipes/speckit-clarify.cursor.json) extracts only
`Completion Report`; the root retains question limits, termination rules,
incremental writes, validation, mandatory hooks before reporting, and Done When.
Both recipes are pinned to exact canonical source hashes and target Cursor.
They do not edit canonical skills or opt into hook optimization.

| Skill | Canonical | Compiled root | Normal path | All packaged instructions |
| --- | ---: | ---: | ---: | ---: |
| speckit-checklist | 5,674 | 4,918 | 5,820 | 5,820 |
| speckit-clarify | 5,040 | 4,818 | 5,099 | 5,099 |

All values are static token estimates. These are optional **root-budget**
recipes, not efficiency recommendations: normal-path cost increases by 3% and
1%, respectively. Every extracted reference remains mandatory. No conditional
fallback or generated script is introduced, so the fallback instruction total
is the same as the normal path. Use the unextracted source when full-path cost
matters more than the 5,000-token root ceiling.

Conditional extraction was not approved: the source does not define an optional
load gate for these sections. The existing hook optimizer is also unsuitable
for these recipes: it does not recognize checklist's `Post-Execution Checks`,
and its after-hook directive says to run after reporting, whereas clarify
explicitly requires hooks before reporting. Extending it requires a separate
review of ordering and fallback behavior.

Validation covers byte-preserving extraction, retained root constraints, source
hash rejection, budgets, independent package verification, and paired **mock**
turn contracts with workflow ordering, abort, and reference reloads after
compaction. These tests detect package/contract regressions; they do not prove
live behavioral equivalence or runtime savings. Run them with:

```bash
python3 -m unittest tests.test_reviewed_recipes -v
```
