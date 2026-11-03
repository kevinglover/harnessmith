# Follow-up: identify where extraction saves runtime usage

## Prepared batch

Use the unchanged 23 KB `speckit-checklist` source, the existing two-section
extraction configuration, gpt-6-astra at low reasoning effort, and the existing
explicit-v3 adapter. Four scenarios with two canonical/compiled pairs each make
sixteen live sessions. Do not overwrite or merge previous batches.

| Case | Scenario | Task | Expected optional reads |
| --- | --- | --- | --- |
| Security | [Scenario](../evaluations/scenarios/checklist-core-security-codex.json) | Draft four requirements-quality items for workspace invitations | None |
| Append policy | [Scenario](../evaluations/scenarios/checklist-core-append-policy-codex.json) | Preserve reviewer state and draft CHK015–CHK016 for an existing checklist | None |
| Some | [Scenario](../evaluations/scenarios/checklist-optional-some-codex.json) | Select API examples for two gaps | Examples |
| Most | [Scenario](../evaluations/scenarios/checklist-optional-most-codex.json) | Combine API/security examples and corrected anti-example analysis | Examples, then anti-examples |

The new core tasks do not instruct the model to avoid optional references. Extra
reads remain observable and may fail the exact reference contract. All prompts
are read-only consultations; this is not the full project-generation workflow.
The latter two scenarios are unchanged from the earlier approved benchmark.

The adapter's two-pair order is canonical/compiled then compiled/canonical.
Use new output directories under `/tmp/harnessmith-checklist-savings-v2/` with
case names `security`, `append-policy`, `some`, `most`. Each command uses
`--model gpt-6-astra --samples 2 --timeout 180 --enabled`. Stop on incomplete
collection or usage limits. Do not discard unfavorable completed samples.

## Measurement requirements

Report the following separately for every session and within-scenario pair:

- Total input tokens, including cached input.
- Cached input tokens from the final cumulative runtime usage event.
- Uncached input tokens, computed as input minus cached input.
- Output tokens and session latency.
- Reference reads, command count, fidelity checks, and manual answer inspection.

Do not call reduced total input a billing saving. Do not attribute a larger cache
hit fraction to extraction without further evidence. Do not compare server turn
duration in partial logs with full adapter session latency. Small sample counts,
provider cache reuse, and varying output lengths limit causal conclusions.

## What the existing evidence already tells us

The earlier completed no-reference case yielded these means across two pairs:

| Variant | Total input | Cached input | Uncached input | Output |
| --- | ---: | ---: | ---: | ---: |
| Canonical | 28,850.5 | 16,320 | 12,530.5 | 259 |
| Compiled | 28,092.5 | 21,184 | 6,908.5 | 251.5 |

The 2.63% total-input reduction is much smaller than the uncached-input reduction.
The latter is heavily affected by the first canonical session's lower cache hit
count. It must not be presented as a compiler-caused saving.

For the single completed pair of the interrupted one-reference case:

| Variant | Total input | Cached input | Uncached input | Output |
| --- | ---: | ---: | ---: | ---: |
| Canonical | 28,798 | 21,120 | 7,678 | 165 |
| Compiled | 44,327 | 36,992 | 7,335 | 261 |

The compiled run used 53.92% more total input but 4.47% less uncached input and
96 more output tokens. It also took longer. This mixed result is not enough to
claim either a monetary saving or a monetary regression; cache treatment and
output charges matter, and no pricing or billing measurement was performed.
The original reports and logs remain in the private local evidence directory.

## Completed live batch

All sixteen authorized sessions completed on October 23, 2026. All four reports
passed schema validation. All sixteen output checks passed; twelve full contracts
passed. The four failures were compiled security/append-policy sessions that read
both references when the scenarios expected neither. Manual inspection found
comparable requirements-quality answers; it was not blinded quality scoring.

| Case | Compiled total input change | Compiled uncached input change | Compiled latency change |
| --- | ---: | ---: | ---: |
| Security | +58.4% | +10.3% | +19.4% |
| Append policy | +58.5% | +68.4% | +28.9% |
| Some | +75.7% | +49.7% | +29.3% |
| Most | +113.4% | +120.4% | +27.9% |

Each row compares the two-sample compiled mean against the two-sample canonical
mean for that scenario. Output tokens were also higher for every compiled mean.
No runtime saving was demonstrated in this batch. Small samples and uncontrolled
provider caches preclude a general performance conclusion or monetary claim.

The generated extraction sites instruct the model to read the reference
completely and not continue until it is loaded. This is a plausible contributor
to unnecessary loading: all four compiled core-task runs read both references.
The one-reference task explicitly excluded the other section and loaded only the
requested reference. A controlled comparison is needed to attribute causality to
load wording. No load gates or expected traces were changed during the experiment.

The next design experiment should use reviewed conditional loading for genuinely
optional sections, retaining mandatory load gates for requirements. Compare
canonical, current compilation and conditional compilation on both skip and
must-load tasks. Prefer a larger optional fraction and measure round-trip costs.
Do not declare success merely because the static root becomes smaller.

The private `evaluations/local-evidence/2026-10-23-checklist-savings-v2/` bundle
contains original reports and raw logs, individual metrics and cache splits,
answer review, calculation script, source snapshots, and a compiled-package copy
verified against the report's file hashes. Previous batches remain intact.
The two new scenario contracts and repository schema/documentation checks pass.
