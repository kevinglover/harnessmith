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
