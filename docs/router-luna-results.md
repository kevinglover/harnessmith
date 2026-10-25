# Compact-router pilot on GPT-6 Luna — 2026-10-24

The user requested cheaper benchmark models. The Astra batch was stopped after
one completed session and one interrupted session. Both raw logs remain in
`evaluations/local-evidence/2026-10-24-router-live/`, with a STOPPED marker.
They are not pooled with the Luna evidence.

All 48 Luna sessions completed: four variants × four repetitions × three frozen
consultations. No retries or observations were dropped. The comparison CLI now
defaults to `gpt-6-luna`; using Astra requires an explicit model override.

## Efficiency

Mean total input tokens per session, with changes relative to canonical **on Luna**:

| Scenario | Canonical | Mandatory | Conditional | Compact router |
| --- | ---: | ---: | ---: | ---: |
| Skip optional references | 25,627 | 25,883 (+1.0%) | 18,286 (−28.6%) | 16,810 (−34.4%) |
| Load examples | 26,390 | 41,558 (+57.5%) | 41,135 (+55.9%) | 34,771 (+31.8%) |
| Load examples and anti-examples | 26,830 | 42,461 (+58.3%) | 41,643 (+55.2%) | 35,265 (+31.4%) |

Mean latency in seconds:

| Scenario | Canonical | Mandatory | Conditional | Router |
| --- | ---: | ---: | ---: | ---: |
| Skip | 7.15 | 6.92 | 6.27 | 6.61 |
| One reference | 5.60 | 7.00 | 6.87 | 6.48 |
| Both references | 6.50 | 8.36 | 7.88 | 8.15 |

Mean uncached input tokens:

| Scenario | Canonical | Mandatory | Conditional | Router |
| --- | ---: | ---: | ---: | ---: |
| Skip | 12,603 | 12,347 | 11,502 | 4,618 |
| One reference | 16,054 | 13,686 | 8,879 | 8,371 |
| Both references | 9,262 | 11,997 | 10,219 | 6,593 |

Caches were uncontrolled. Uncached differences cannot be attributed entirely to
skill architecture. The entire Luna batch measured 1,506,627 input tokens and
10,991 output tokens. Applying published Standard credit rates to cached,
uncached, and output tokens gives approximately 1.65 credits, excluding Astra.
This is an estimate, not observed billing or subscription-limit consumption.
[Official rates, checked 2026-10-24](https://learn.chatgpt.com/docs/pricing).

## Quality and fidelity

Full frozen automated checks, including process and enhanced structural checks:

| Scenario | Canonical | Mandatory | Conditional | Router |
| --- | ---: | ---: | ---: | ---: |
| Skip | 4/4 | 2/4 | 0/4 | 2/4 |
| One reference | 4/4 | 4/4 | 4/4 | 4/4 |
| Both references | 0/4 | 1/4 | 2/4 | 2/4 |
| Total | 8/12 | 7/12 | 6/12 | 8/12 |

The skip-case failures include bolded IDs and noncanonical traceability notation;
the exact-format checker treats those as failures even when the questions remain
readable. One mandatory run also loaded unexpected references. In the both-reference
case, many outputs quoted the corrected question without its complete checkbox/ID
prefix, failing the frozen verbatim-item assertion. No checks were relaxed.

The primary assistant reviewed all 48 answers with strategy labels omitted from
the review input; this was not an independent or fully blinded evaluation, since
some labeled outputs had already been inspected. Content review found appropriate
requirements-quality coverage and explanations in all router answers. One mandatory
security answer added an unsupported exclusivity restriction ("only" administrators
can invite) and was marked as a content failure. Exact quotation and structural
failures remain failures regardless of content-review findings. Per-output evidence
and rationales are retained in `semantic-review.json`.

## Interpretation

The 802-token root improves on the extraction variants' roughly 5,000-token roots.
It still does not beat the original on total input for the reference-heavy tasks.
This supports treating routing as a workload-dependent architectural choice rather
than automatically equating a smaller root with lower total usage.

Luna's behavior differs materially from the prior Astra pilot. These measurements
cannot establish the same savings or quality on Astra. Four observations per cell
are descriptive evidence, not a statistical guarantee. This pilot covers supplied-
context consultations only; project generation, append operations, hooks, and
implicit skill discovery remain untested. The redesign is not promoted to a
compiler transformation or substituted for the original skill.

## Evidence

`evaluations/local-evidence/2026-10-24-router-luna/` contains immutable scenario
reports, package snapshots, raw events, `analysis.json`, the reusable `analyze.py`,
review inputs/key, `semantic-review.json`, and `usage-summary.json`. All three
reports passed the version-2 comparison schema; all package hashes matched their
recorded provenance. Evidence is gitignored. Six focused router tests and lint
passed after the default-model change; the preceding full suite passed 162 tests.
