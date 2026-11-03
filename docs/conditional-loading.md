# Reviewed conditional loading

The default compiler still extracts sections behind mandatory read gates. Recipe
version 2 can explicitly classify an extracted section as optional and define
when it must be read. The compiler never guesses optionality from a heading.

## Recipe contract

See [the checklist recipe](../recipes/speckit-checklist.conditional.codex.json).
Each `conditional_sections` key must exactly match an `extract_sections` selector.
Its value requires:

- `optional: true`: the author's explicit classification;
- `when`: a nonempty single-line load condition;
- `rationale`: the review justification explaining why skipping is safe.

A source SHA-256 is required. Hash drift, missing policy fields, unselected
sections, duplicate selectors and unsupported hook-optimization combinations
fail before output. Recipe v1 cannot contain this policy. Unmarked sections stay
mandatory; omitting extraction remains supported.

The policy is a reviewed semantic choice, not a semantic-equivalence proof.
The author must establish that no unique mandatory requirement disappears on a
skip path. Exact section bytes remain in references, and normative-retention and
heading-order checks still run. These checks cannot prove that a natural-language
load condition is correct or that a model will obey it.

The generated gate says to read the reference completely when its condition
applies, and otherwise skip it and continue with the core instructions. It
explicitly says not to load a reference merely because it is linked.

## Provenance and compatibility

Conditional packages use manifest version 2 and record the condition and
rationale on each affected extraction transformation. Ordinary compilation still
emits manifest version 1 and retains its previous directives and reference bytes.
Both versions are supported by the current verifier. Older verifiers should fail
closed on version 2, rather than silently interpret its load behavior as mandatory.

The verifier checks generated policy text, exact source retention, output hashes,
metrics, and deterministic regeneration when source and recipe resolve. Version 2
has its own [recipe schema](../schemas/recipe-v2.schema.json) and
[package schema](../schemas/package-manifest-v2.schema.json).

`normal_path_instruction_token_estimate` excludes conditionally loaded references.
For conditional recipes, interpret this as the **skip-path estimate**, not an
expected workload average. Packaged estimates still include all references. No
automatic cost estimator, section bundler, or workload-based extraction chooser
is implemented in this change.

## Compile and verify

```bash
python3 -m harnessmith skills/speckit-checklist \
  --recipe recipes/speckit-checklist.conditional.codex.json \
  --output /tmp/checklist-conditional
python3 -m harnessmith verify /tmp/checklist-conditional
```

The reviewed checklist policies keep the core workflow in the root. Examples load
when requested or when core rules are insufficient. Anti-examples load when
requested or when comparing/correcting implementation-test wording. Their
classification is justified by the root already covering the requirements-quality
rules, item format, traceability and reviewer ownership.

## Three-way experiment

`harnessmith.runtime_comparison` prepares canonical, current mandatory extraction,
and conditional extraction from the same source. It only accepts a recipe whose
target and extraction selectors match the frozen scenario, with source invocation
and no unrelated optimizations. Scenario prompts, reference expectations and
output assertions are identical for both compiled strategies.

By default the command only prepares exact packages and provenance; it does not
read credentials, launch Codex, or contact a provider:

```bash
python3 -m harnessmith.runtime_comparison \
  evaluations/scenarios/checklist-core-security-codex.json \
  --recipe recipes/speckit-checklist.conditional.codex.json \
  --output /tmp/checklist-three-way-prepared
```

Adding `--enabled --model gpt-6-astra --samples 3` makes nine live sessions for
that scenario and consumes account usage. Use a new output directory. It uses
local Codex sign-in by default; `--auth-file` selects a local authentication file.
Three repetitions rotate strategy order so each strategy occupies each position
once. Fresh sessions do not control provider caches. Raw logs retain cache usage,
commands and model outputs. Failed checks remain in completed reports; provider
errors produce incomplete markers and retained raw logs. No aggregate efficiency
win is inferred. The distinct [comparison schema](../schemas/runtime-comparison.schema.json)
keeps these three-way reports separate from older paired evidence.

The prepared pilot uses three existing tasks:

1. `checklist-core-security-codex`: skip case, no optional reads expected.
2. `checklist-optional-some-codex`: must load the examples reference only.
3. `checklist-optional-most-codex`: must load examples followed by anti-examples.

This is **27 sessions** total at three strategies × three repetitions × three
scenarios. Keep the previously measured mandatory strategy's failures; do not
weaken assertions to obtain a pass. Compare total/cached/uncached input, output,
latency and answer quality within each task. Require correct skip and must-load
behavior before treating lower usage as a useful improvement.

## Verification status

The conditional package has passed independent verification, including
regeneration. Targeted tests cover malformed policies, source drift, unchanged
mandatory behavior, exact reference content, directive tampering, version
boundaries, rotated ordering, request isolation, invalid measurements and
prepare-only operation without credentials. The three-way runner has mock coverage and a completed 27-session live pilot.
Conditional loading passed all nine live observations, but only the skip case
reduced total input versus canonical. See [the live results](conditional-loading-results.md)
for measurements, failures, and limitations.
