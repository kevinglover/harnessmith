# Larger-skill Codex benchmark

This benchmark uses the existing `skills/speckit-checklist/SKILL.md` unchanged,
pinned in the fixture manifest as `local-speckit-checklist`. Its source is 22,786
bytes (5,674 estimated tokens). The compiled Codex root is 4,910 estimated tokens,
with two optional references totaling 902 estimated tokens. These are static
character-based estimates, not runtime measurements.

Extraction uses the same two section selectors as the reviewed checklist recipe,
but targets Codex through the collector's direct-extraction configuration. It is
not a recipe-backed runtime run. The source's local Git revision and byte hash are
pinned; this is an existing repository skill, not a new synthetic equivalent.

## Frozen comparison

All cases use gpt-6-astra, low reasoning effort, instrumentation explicit-v3,
read-only permissions, fresh ephemeral sessions, and the same canonical/compiled
packages. Two paired samples per case mean twelve sessions in total. Pair order
alternates canonical/compiled then compiled/canonical. Provider caches remain
uncontrolled. These exploratory sample counts do not support significance claims.

| Scenario | User task | Expected compiled reference reads |
| --- | --- | --- |
| `checklist-optional-none-codex` | Draft three requirements-quality questions from a supplied invoice-export spec | None |
| `checklist-optional-some-codex` | Select API sample questions for dependency outages and versioning gaps | Examples |
| `checklist-optional-most-codex` | Select API/security examples, inspect the corrected anti-example, and rewrite an implementation-test item | Examples, then anti-examples |

The latter two prompts explicitly request the relevant sections; the first leaves
reference selection to the model. This controls task demand while observing the
model's actual reads. It does not estimate how frequently these tasks occur in a
real workload. Cross-variant comparisons should be made within each scenario;
tasks differ in output length and reasoning requirements.

All feature context is provided in the prompts. They request read-only
consultations and explicitly exclude setup scripts, hooks, project-file searches,
and filesystem edits. Consequently this benchmark exercises realistic instruction
content and requirements-review tasks, but does not validate the full checklist
file-generation workflow, hook execution or project integration.

## Acceptance and inspection

Before any live call, the collector checks source hashes and the mock contracts.
Mock results establish that the scenarios are internally consistent; they are not
behavioral observations. Live scoring checks invocation, exact reference-read
order, unexpected actions, and required/forbidden output substrings. Broad semantic
quality is not established by those checks.

Inspect the raw answers as well:

- None: exactly three unchecked CHK001–CHK003 questions, focused on requirement
  measurability, error completeness and export scope/authorization, with traceability.
- Some: correct verbatim API questions and a sound distinction between requirement
  quality and implementation testing.
- Most: correct quoted examples and a rewritten export item that asks about
  documented requirements rather than testing running software.

Retain every failed sample. Do not change expectations after seeing results or
silently rescore unknown reads as successful. Compare measured input/output tokens,
cached input tokens, session latency, reference loads and observed command counts.
A smaller static root is not evidence of reduced runtime usage.

## Live commands

Each command makes four real sessions and consumes model usage. These send the
selected repository skill and task prompt to OpenAI's Codex service using local
Codex authentication. Output directories must not already exist.

```bash
python3 -m harnessmith.codex_runtime \
  evaluations/scenarios/checklist-optional-none-codex.json \
  --model gpt-6-astra --samples 2 --timeout 180 \
  --output /tmp/harnessmith-checklist-live-v1/none --enabled

python3 -m harnessmith.codex_runtime \
  evaluations/scenarios/checklist-optional-some-codex.json \
  --model gpt-6-astra --samples 2 --timeout 180 \
  --output /tmp/harnessmith-checklist-live-v1/some --enabled

python3 -m harnessmith.codex_runtime \
  evaluations/scenarios/checklist-optional-most-codex.json \
  --model gpt-6-astra --samples 2 --timeout 180 \
  --output /tmp/harnessmith-checklist-live-v1/most --enabled
```

## Status

All three offline scenario contracts pass, as do the 145-test repository suite,
schema checks, lint and type checks. Instrumentation v3 accepts portable quoted
skill names using the compiler's metadata parser. The evaluator now compares
unique audit rule IDs to the fixture contract, allowing real skills to trigger
the same diagnostic at multiple source spans.

The authorized October 23, 2026 batch started seven of twelve sessions before
Codex returned `usageLimitExceeded`. Six sessions completed; one failed mid-turn.
The runner stopped without retries or a model change. Five sessions never started.

The no-reference case completed both pairs, passed all 24 current checks, and
validated against the runtime evidence schema. Canonical/compiled mean input usage
was 28,850.5/28,092.5 tokens (2.63% lower compiled); mean session latency was
11.326/10.7905 seconds (4.73% lower compiled). Both compiled sessions avoided the
optional references. Manual answer inspection found comparable three-item,
traceable requirements-quality checklists.

The one-reference case completed only its first pair. Both answers selected the
correct questions; the compiled trace showed the expected examples read. Input
usage was 28,798 canonical versus 44,327 compiled (53.92% higher). This is a partial
observation, not a completed repeated-pair report. The both-reference case did not
start. All raw logs, the incomplete marker and a source snapshot are retained in
the private, git-ignored `evaluations/local-evidence/2026-10-23-checklist-live-v1/`
bundle. The interrupted case has no completed evidence report.

These results suggest a tradeoff, not a general optimization win: a small saving
when optional material is unused, potentially outweighed by another model/tool
round trip when it is required. Provider caches were uncontrolled; the matrix is
incomplete and samples are too few for significance claims. Further live runs
must wait until account usage is available. A new complete one-reference batch
should remain separate from this interrupted batch.

A subsequent separately authorized [follow-up batch](checklist-savings-followup.md)
completed the one- and two-reference cases alongside two new core tasks. Its
results are kept separate from this interrupted initial batch.
