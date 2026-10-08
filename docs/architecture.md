# Architecture

Harnessmith separates a skill's meaning from reviewed optimization policy,
target representation, and generated output.

## Compilation pipeline

1. `harnessmith.parser` reads `SKILL.md` into a lossless intermediate
   representation with source spans and stable section identities.
2. `harnessmith.recipe` optionally validates a versioned recipe and its pinned
   source hash.
3. `harnessmith.adapters` maps frontmatter and invocation policy through the
   machine-readable declarations in `harnessmith.targets`.
4. Ordered transforms analyze, apply, and verify their own invariants.
5. `harnessmith.compiler.verify_package` checks normative-statement retention,
   exact extraction provenance, and root-heading order.
6. The writer replaces only files owned by a valid earlier Harnessmith
   manifest.

```text
SKILL.md + optional recipe
          |
          v
 parser -> IR -> adapter -> verified transforms -> package + manifest
                                                   |
                                                   v
                                      independent package verifier
```

The current general transform moves explicitly selected sections into mandatory
references without rewriting their text. The `spec-kit-extension-hooks`
optimization is a named, narrow pass for the repository's Spec Kit input; it is
not a general Markdown heuristic.

## Core boundaries

- `harnessmith.model` contains parser and compiler data structures.
- `harnessmith.contracts` defines versioned, target-neutral diagnostic,
  capability, and fixture vocabulary.
- `harnessmith.targets` is the machine-readable target registry.
- `harnessmith.transforms` defines the pass protocol and lossless extraction.
- `harnessmith.compiler` builds packages and performs in-process invariants.
- `harnessmith.verification` verifies packages from disk and compares previews.
- `schemas/` defines version 1 JSON contracts for durable artifacts.

Recipes record reviewed intent. Manifests record what happened. Audit reports
are advisory observations and never mutate the source.

## Determinism and ownership

The same source, recipe, and compiler version must produce the same file
contents and hashes. Generated packages include `.harnessmith.json`; its
`compiler.name` and `files` map establish ownership. Harnessmith refuses to
overwrite a populated directory without a valid owned manifest and rejects
unsafe relative paths and symlink traversal.

`harnessmith verify` independently checks the on-disk manifest, output hashes,
source and recipe drift when those paths are available, invariant retention,
budgets, and deterministic regeneration. Verification never repairs a package.

## Metrics boundary

All current token values are deterministic static estimates using
`ceil(characters / 4)`. They are useful for budgets and before/after comparison,
but they are not tokenizer counts, model billing, runtime context usage,
latency, reference-read frequency, or behavioral equivalence evidence. See
[Evaluation](evaluation.md).

## Versioning

Schema versions are independent of the Python package version. Consumers must
reject unsupported schema versions instead of guessing. See
[ADR 0002](decisions/0002-versioned-contracts.md).

The governing safety invariants are documented in the
[Safety model](safety-model.md).
