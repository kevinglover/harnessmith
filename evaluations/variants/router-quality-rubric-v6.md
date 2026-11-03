# Fidelity rubric v6 — constituent evidence and workflow checkpoints

This prospective rubric applies only to newly prepared router-v5 bundles,
checker/collector v5 and normalizer v4. Observations use schema v4; checks and
collector reports use v5. It does not regrade historical observations. The
[v4 results](../../docs/workflow-fidelity-v4-results.md) remain 0/2 full automated
passes and 2/2 separate semantic content passes, with the complete gate failing.

The five dimensions remain content correctness, formatting, reference behavior,
workflow fidelity and efficiency. All broader promotion requirements from
[rubric v2](router-quality-rubric-v2.md) and all unmodified requirements from
[rubric v5](router-quality-rubric-v5.md) remain in force. A correct artifact
cannot compensate for a failed workflow or establish efficiency.

## Prospective instrument changes

| Area | Rule and boundary |
| --- | --- |
| Internal append/readback | Recognize a bounded literal Python append sequence only when static syntax, pinned prewrite bytes, final artifact bytes, ordered read/write/read/assert/print and returned output corroborate it. Never execute trace code or accept dynamic writes. Missing, partial, denied or failed verification remains a failure. |
| Constituent read evidence | A bounded command can return a complete pinned file before a later constituent fails. Record the proven read separately while retaining the nonzero/failed command outcome. Success of one constituent never certifies a skipped read or clears the failed envelope. Unsupported shell control flow remains unclassified. |
| Count modifiers | Recognize supported singular modifiers such as “four item checklist” and “four-item checklist” in completed reports. Preserve rejection of wrong, contradictory, planned, negated or path-derived counts. |
| Configured hook announcements | Require exact configured IDs, descriptions and optional prompts at the existing phase checkpoints. The new extra-block screen rejects invented pre-hook blocks even if correct blocks also appear. Reading configuration after an announcement cannot authorize it retroactively. Arbitrary extra post-hook narration remains part of raw review. |
| Bounded error narration | Screen recognized factual execution/error claims in completed commentary as well as final messages against earlier completed command records. Retain claim text and supporting IDs, or mark unsupported claims unverified. Unsent deltas, later errors, quoted examples, negation and plans cannot serve as factual evidence. This is a bounded screen, not a general truthfulness classifier. |

No failed action is waived because a later recovery succeeds. Required context
must actually be returned before use. In particular, a shell script sent to
Python followed by `|| true` cannot certify a skipped constitution read, even
if later commands complete and the overall exit is zero. A no-match discovery
result does not erase its recorded nonzero outcome. Hidden-file discovery is
tested locally with synthetic directories; it is not proof about a future host.

## Mandatory review and promotion

The semantic-first anonymous packet protocol and disclosure requirements in
rubric v5 are unchanged. Then review retained raw traces, including completed
commentary and final messages, against artifacts and actual command outputs.
Distinguish unsupported claims, contradicted claims and confirmed outcomes.
Normalized command records and screen matches remain assertions requiring raw
review. A screen pass or no recognized claim never satisfies that review.

The targeted gate requires both cases to complete and pass every applicable
automated content, formatting, reference and workflow check plus semantic/raw
review. Preserve separate reasons when screening and review differ. Unknown
operations, failed actions and missing context remain failures. Semantic
neutrality, traceability meaning and arbitrary narrative accuracy remain manual
judgments; these offline repairs do not establish model compliance.

Efficiency remains descriptive usage accounting only. No matched baseline or
replication is part of the proposed two-case diagnostic. Models and versioned
cohorts remain separate. A passing future pilot would not establish general
equivalence, savings, router promotion or OPT-004 completion.

## Offline scope and live boundary

The [v5 repair plan](../../docs/workflow-fidelity-pilot-v5.md) reuses the original
synthetic append and hook-creation prompts and fixtures. Regression tests use
new synthetic observations and a local fake stdio server, with no provider,
credential or real project hook access. Historical traces are not rerun through
the new checker.

Any future live proposal remains exactly two fresh GPT-6 Luna low sessions,
append then hooks, one turn each, without retries, replacements, expansion or
an extra model judge. These files do not authorize launch. New user approval
is required after the concrete offline results are available.
