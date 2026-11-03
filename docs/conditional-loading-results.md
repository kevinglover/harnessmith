# Conditional-loading live pilot — 2026-10-23

Conditional loading fixed unnecessary reference loading in the skip case, but did
not make extraction generally cheaper than leaving this skill intact. All 27
approved sessions completed: three strategies × three repetitions × three frozen
scenarios. No retries or observations were discarded.

## Results

Mean total input tokens per session; percentages compare with canonical.

| Scenario | Canonical | Mandatory extraction | Conditional extraction |
| --- | ---: | ---: | ---: |
| Security review: skip both references | 28,848 | 45,718 (+58.5%) | 28,194 (−2.3%) |
| API examples: load one reference | 28,386 | 45,178 (+59.2%) | 49,722 (+75.2%) |
| Review examples: load both references | 28,720 | 62,986 (+119.3%) | 50,681 (+76.5%) |

Mean latency in seconds:

| Scenario | Canonical | Mandatory | Conditional |
| --- | ---: | ---: | ---: |
| Skip both | 12.34 | 16.30 | 12.55 |
| Load one | 9.63 | 12.77 | 13.53 |
| Load both | 13.91 | 19.18 | 18.44 |

Mean uncached input tokens, calculated from the final raw usage event:

| Scenario | Canonical | Mandatory | Conditional |
| --- | ---: | ---: | ---: |
| Skip both | 12,293 | 8,129 | 7,031 |
| Load one | 12,258 | 14,287 | 13,924 |
| Load both | 8,155 | 8,373 | 7,886 |

Provider caching was uncontrolled. For example, skip-case canonical uncached input
ranged from 7,719 to 17,320. The apparent 42.8% uncached-input reduction for
conditional loading is not evidence of an intrinsic compiler saving of that size.
These are usage measurements, not dollar-cost estimates.

## Behavior and quality

- Conditional: 9/9 observations passed all frozen assertions. It skipped both
  references for security, loaded only examples for API questions, and loaded
  examples followed by anti-examples for the full review.
- Mandatory: 6/9 passed. All three security observations unnecessarily loaded both
  references and failed the expected-reference check. Their output checks passed.
- Canonical: 8/9 passed. One API observation used a read-only `sed` command that
  Codex classified as `unknown`, so the instrument failed its action check. The
  answer checks passed. This observation remains included in every mean.
- All 27 observations passed the existing output assertions. Those assertions are
  limited substring checks, not a comprehensive semantic quality evaluation.
  Manual inspection of all nine conditional answers found the requested checklist
  structure, supplied-spec coverage, quotes, and requirements-quality rewrites.

The conditional API outlier used 59,281 input tokens and read the root in two separate commands;
its other two runs used 44,507 and 45,377. Command/read variation remains visible
in the raw logs and analysis. The original-skill API action-classification failure
slightly lowers its mean input; conditional is still substantially more expensive
than either of the two passing canonical observations.

## Implication for compilation

Reviewed optionality is useful, but root-size reduction is not enough to choose an
extraction. This skill removes only about 654 measured input tokens on the skip
path while adding about 21,000–22,000 on the measured loaded paths. As a rough
illustration using these means, more than 97% of invocations would need to resemble
the skip path to break even on total input. This is not a production forecast:
three repetitions, different prompts, read-command variation and provider caching
limit the estimate.

The next compiler decision should be whether to extract at all. Keep a section
inline unless its size and expected skip rate justify the measured extra model
turns, repeated context, and read overhead. Conditional loading can be an available
strategy without being the default choice. Bundling needed reads may reduce the
penalty, but it was not isolated or proven by this experiment.

## Evidence and reproducibility

Local evidence is under
`evaluations/local-evidence/2026-10-23-conditional-three-way/` (gitignored):

- Each scenario has `report.json`, `preparation.json`, three exact package snapshots,
  and raw JSONL/stderr logs.
- `analyze.py` regenerates `analysis.json` from reports and raw usage; it verifies
  reported input/output usage against final provider usage events.
- All three reports passed the published comparison JSON schema; all package file
  hashes matched recorded provenance after collection.

Requested model: `gpt-6-astra`, low reasoning, fresh sessions with rotated strategy
order. Backend snapshot unreported. These read-only consultations do not exercise
the full checklist file-writing or extension-hook workflow. No prompts, policies,
scoring assertions, or compiler code changed during the batch.
