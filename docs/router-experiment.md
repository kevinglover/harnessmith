# Compact-router experiment

This fourth variant tests a reviewed skill redesign alongside canonical, mandatory
extraction, and conditional extraction. It is an experimental authored baseline,
not a compiler optimization or a claim of semantic equivalence.

The design follows the official recommendation to retain shared purpose and
constraints in the root and load substantial task-specific guidance as needed:
https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

## Package

`evaluations/variants/speckit-checklist-router/SKILL.md` keeps requirements-quality
rules, reviewer ownership, unchecked/append behavior, traceability and routing.
Original discovery metadata is unchanged to isolate body organization.

`references/project-generation.md` retains the original pre-execution, execution,
and post-execution sections verbatim, including setup, templates, clarification,
file structure, reporting, and extension hooks. The two example references also
retain their source sections verbatim. Consultations need not load project setup.

The sibling `.review.json` pins source and package hashes, maps exact source spans,
and lists semantic changes. Loading fails on drift, changed files, symlinks or
executable files. Hashes prove identity, not quality or semantic equivalence.

## Experiment

Use the same three frozen consultation prompts from the preceding pilot. Four
repetitions rotate all four strategies through every run position: 48 sessions
across the three scenarios. This reruns all baselines contemporaneously; it does
not compare only new router runs with older baseline means.

```bash
python3 -m harnessmith.runtime_comparison \
  evaluations/scenarios/checklist-core-security-codex.json \
  --recipe recipes/speckit-checklist.conditional.codex.json \
  --router-package evaluations/variants/speckit-checklist-router \
  --samples 4 --output /tmp/checklist-four-way
```

The default prepares packages without credentials or model calls. Add
`--enabled --model gpt-6-luna` for 16 live sessions for this one scenario. Repeat
with `checklist-optional-some-codex` and `checklist-optional-most-codex` for the
48-session batch. Live execution consumes usage and sends package content/prompts
to the provider. Existing output directories are never overwritten.

Version-2 comparison reports record the router review hash and all package hashes.
Version-1 three-way reports and default behavior remain unchanged. Enhanced
structural/quotation checks apply equally to every strategy in four-way runs.
The frozen [semantic rubric](../evaluations/variants/router-quality-rubric.md)
is evaluator-only and is never included in runtime requests. Semantic review
must be completed separately before claiming fidelity.

## Boundaries

This isolates architecture on comparable consultations; it does not yet test
artifact creation, append operations, hooks, or implicit selection. The source
skill remains unchanged. Do not promote the redesign based on consultation
results alone. Stronger checks cannot turn this pilot into comprehensive workflow
validation. No live savings are claimed before the new batch completes.

On 2026-10-24 the user requested cheaper benchmark models. The comparison CLI
now defaults to GPT-6 Luna; expensive models require an explicit override. The
Astra batch was stopped after one completed session and one interrupted session.
Its evidence is retained separately and is not pooled with Luna measurements.

The 48-session Luna batch is complete. See [results and limitations](router-luna-results.md).
