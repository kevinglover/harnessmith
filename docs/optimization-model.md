# Optimization model

Harnessmith offers reviewed choices for instruction placement, including leaving
all sections inline. It does not summarize, paraphrase, or delete arbitrary prose.
Static size reduction and measured runtime efficiency are different outcomes.

## Static context paths

The compiler reports three useful instruction sizes:

- **Compiled root:** the generated `SKILL.md` loaded by the harness.
- **Normal path:** the root plus mandatory references. Exact section
  extractions are mandatory because the replacement instruction requires the
  agent to read them before continuing.
- **Packaged instructions:** the root plus every generated reference, including
  conditional fallback material.

Moving text into a mandatory reference may shrink the root without shrinking
the normal path. This can satisfy an explicit root budget; it does not establish
runtime savings or better discovery. Conditional loading can reduce the static
normal path, but additional reads and model turns can still increase total runtime
input. These metrics omit repeated conversation context, read commands, and
provider caching. They are inventory estimates, not a runtime cost model.

## Audit before extraction

Audit classifies sections using size and heading cues and emits review
candidates. These are heuristics, not measured findings: the 5,000-token root
threshold, 1,000-token section threshold, and 250-token threshold for detail or
conditional headings do not predict reference-read cost or skip frequency.
A candidate is not permission to extract it. Review the section for global safety
rules, prerequisites, invariants, and information needed to decide whether to
load the reference.

The compiler does not automatically select candidates. CLI `--extract-section`
or a reviewed recipe selects extraction; an empty selection leaves sections inline.
Audit's starter recipe now keeps both `extract_sections` and `optimizations` empty
and sets no budgets, so it remains usable even above the advisory root threshold.
Existing explicitly supplied recipe/CLI budgets still fail compilation when
exceeded. The legacy audit metric names `recommended_root_token_budget` and
`over_recommended_root_budget` remain for compatibility; they describe advisory
static thresholds. `HS201` and `HS214` no longer emit `estimated_savings_tokens`
from root excess or section size. The optional diagnostic field remains supported
for compatibility, but these rules have no measured savings to populate it with.

Apply these decision rules in order:

1. Leave inline by default, including when runtime savings are unknown or fidelity
   requirements are unmet. This is a valid reviewed outcome, not an audit failure.
2. Select exact mandatory extraction only after reviewing ordering and load gates,
   for an explicit packaging or root-budget requirement. Record the resulting
   normal-path increase; do not label root reduction as runtime savings.
3. Consider conditional extraction only with source-pinned, reviewed optionality
   and a valid skip path. Heading cues cannot establish optionality. Treat it as an
   experiment until content, format, reference behavior, workflow, and efficiency
   pass the separate [promotion criteria](../evaluations/variants/router-quality-rubric-v2.md).
4. Promote extraction for efficiency only for the measured model/configuration and
   declared workload after fidelity passes. Compare total input and latency,
   retain cache and read behavior, and include leave-inline as the baseline.
   Do not hard-code a skip-rate break-even value from these small samples.

The [Astra conditional pilot](conditional-loading-results.md) measured a small
skip-path input reduction and substantially larger loaded-path input. The
[Luna router pilot](router-luna-results.md) measured larger skip-path reductions
but still higher input on loaded paths; format/reference failures remain.
These are separate model-specific findings. They justify the conservative default,
not universal size or skip-rate thresholds. The compact router is an authored
semantic redesign and has no automatic compiler promotion path. See
[OPT-004 status](opt-004-status.md) for evidence scope and outstanding requirements.

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
root and normal-path metrics and describe the change as a root-budget adjustment.
Runtime efficiency requires separate measurements.

## Named optimizations

`spec-kit-extension-hooks` is currently the only named optimization. It moves
exact extension-hook fallback contracts into references and generates a
resolver script. The resolver uses one dependency-free, strict YAML subset on
every host; unsupported syntax activates the exact fallback rather than changing
behavior according to installed Python packages. The fallback remains available
and its provenance is verified.
This pass is opt-in through a recipe or `--optimize-extension-hooks`.

## Budgets

Recipes and CLI flags can enforce maximum estimated root or normal-path tokens.
Compilation fails if a generated package exceeds either budget. Budgets use the
portable four-characters-per-token estimate, not a target tokenizer. Budgets are
explicit operator constraints; audit does not insert one into its starter recipe.
