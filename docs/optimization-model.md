# Optimization model

Harnessmith optimizes always-loaded instruction context through reviewed
progressive disclosure. It does not summarize, paraphrase, or delete arbitrary
prose.

## Static context paths

The compiler reports three useful instruction sizes:

- **Compiled root:** the generated `SKILL.md` loaded by the harness.
- **Normal path:** the root plus mandatory references. Exact section
  extractions are mandatory because the replacement instruction requires the
  agent to read them before continuing.
- **Packaged instructions:** the root plus every generated reference, including
  conditional fallback material.

Moving text into a mandatory reference may shrink the root without shrinking
the normal path. That is still useful for harnesses that discover skills from
the root, but it is not a claim of runtime token savings. Only a transform with
a real conditional load gate can reduce the static normal path.

## Audit before extraction

Audit classifies sections using size and heading cues and emits review
candidates. A candidate is not permission to extract it. Review the section for
global safety rules, prerequisites, invariants, and information needed to decide
whether to load the reference.

Duplicate headings require stable occurrence selectors such as `Examples[2]`.
Local fragment links currently block extraction because Markdown anchor rules
vary and Harnessmith will not guess at cross-document rewrites.

## Walkthrough: large skill to progressive disclosure

Suppose the canonical source contains:

```markdown
## Workflow

Follow these steps in order.

## Detailed examples

...reviewed supporting material...
```

After a reviewer selects `Detailed examples`, compile with:

```bash
harnessmith path/to/skill \
  --target cursor \
  --extract-section "Detailed examples" \
  --output generated/skill
```

The root becomes:

```markdown
## Detailed examples

**Before this stage:** Read &#91;`references/detailed-examples.md`&#93;(references/detailed-examples.md) completely; it remains authoritative. Do not continue until it is loaded.
```

The reference contains a generated comment followed by the exact original
section. The manifest records its source lines, source SHA-256, stable section
identity, and output path. Because this reference is mandatory, compare both
root and normal-path metrics before calling the change an optimization.

## Named optimizations

`spec-kit-extension-hooks` is currently the only named optimization. It moves
exact extension-hook fallback contracts into references and generates a
resolver script. The fallback remains available and its provenance is verified.
This pass is opt-in through a recipe or `--optimize-extension-hooks`.

## Budgets

Recipes and CLI flags can enforce maximum estimated root or normal-path tokens.
Compilation fails if a generated package exceeds either budget. Budgets use the
portable four-characters-per-token estimate, not a target tokenizer.
