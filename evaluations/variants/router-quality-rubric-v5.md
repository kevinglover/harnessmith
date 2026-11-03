# Fidelity rubric v5 — bounded topic and narrative evidence

This prospective rubric applies only to newly prepared router-v4 bundles,
checker/collector v4 and the unchanged trace normalizer v3. Observation schema
remains v3; checker and collector reports use v4. Every older rubric, package,
instrument, observation and score remains frozen. In particular, the completed
[v3 results](../../docs/workflow-fidelity-v3-results.md) stay at 1/2 frozen
automated passes and 0/2 complete reviewed passes.

The five dimensions remain separate: content correctness, formatting, reference
behavior, workflow fidelity and efficiency. All hard requirements in
[rubric v4](router-quality-rubric-v4.md) remain, including complete readback,
phase timing, final report after automatic hooks and evidence-grounded narration.
No passing keyword screen, artifact or usage figure compensates for a failed
dimension. The broader promotion requirements in
[rubric v2](router-quality-rubric-v2.md) are unchanged.

## Changes from v4

| Criterion | Prospective rule and limit |
| --- | --- |
| Topic allocation screen | Require one distinct item per requested topic. Recognize a bounded set of invitation/token/link use, acceptance or redemption paraphrases in addition to reuse wording, together with expiration and outcome cues. Retain matched cues for inspection. Bracketed labels, repeating a review, or resending an invitation cannot supply reuse coverage. This remains a lexical screen; unsupported paraphrases need review rather than an inferred pass. |
| Recognized final-hook claims | For the checker's documented affirmative optional-offer and automatic-completion forms, require support from timely configured message blocks or successful hook events before the final report. Retain the recognized clause, phase and supporting item IDs. Missing support is unverified, not automatically proven false. A failed supported-claim check fails workflow. |
| General narrative review | Always review all material claims against raw tool results, completed messages and artifacts. A hook-claim screen pass or no recognized claim does not establish narrative accuracy. Environmental availability claims, arbitrary paraphrases, negation/quotation meaning and policy assertions still require review. Unsupported factual narration fails reviewed workflow under the inherited rule. |

No new shell grammar is introduced. The known-existing feature directory can
be inventoried to discover checklist files before creating a missing target;
failed directory listing commands still fail. No directory-listing error,
denied write, masked failure, unclassified command or successful recovery is
waived. Pinned absence proof, literal-write support and final-readback proof
remain exactly as implemented in trace v3.

## Semantic and raw review protocol

Before exposing strategy/session labels, frozen grades or usage, prepare all
artifact packets with anonymous IDs, prompt, source spec/constitution, before
artifact, final artifact and final report. Keep the lookup key separate. Record
the reviewer's identity and exposure; an author who recognizes cases is neither
independent nor fully blinded. No extra live judge session is included.

Assess content first, with per-item citations and separate judgments for
requirements-quality phrasing, one-to-one topic allocation, traceability, and
no invented policy/quotation/exclusivity. Preserve that review before raw review.
Do not revise it merely to agree with a later keyword score.

The following are synthetic calibration controls, not model observations:

| Synthetic context and text | Expected review |
| --- | --- |
| Spec leaves cross-workspace handling unspecified. “Are workspace-boundary handling rules explicitly defined? [Completeness, Gap]” | Neutral missing-policy question. |
| Same context. “Are rules forbidding every cross-workspace invitation defined? [Completeness, Gap]” | Presupposes a prohibition; Gap does not neutralize the invented policy. |
| “Are outcomes for expired invitations and invitation tokens redeemed a second time specified?” | Reuse/outcome coverage is present by meaning; screen status remains a separate result. |
| “Are outcomes for expired invitations reviewed again before release?” | Repeating a review does not cover reuse of an invitation. |
| Final says an optional post hook was offered; completed messages contain only a promise to show it. | Unsupported offer claim and missing usable offer; a later final claim cannot satisfy either requirement. |
| Final says comparison was unavailable; only evidence is absent metadata and no attempted comparison. | Unverified environmental inference, not a proved failed comparison. Do not invent a failed command; fail the unsupported narrative claim. |
| Final identifies a particular cache diagnostic whose exact text is returned alongside successful setup JSON. | Supported diagnostic claim; do not describe setup as failed when the result supports success. |

Then inspect the full raw trace, not just normalized events. Build a claim/evidence
record for file operation/count/preservation, context reads, hooks offered,
invocations/completions and any stated errors or limitations. Cite raw item IDs
and start/completion lines, or artifact hashes. Distinguish supported,
contradicted and unverified claims, plus explicitly qualified uncertainty. Mark
missing review evidence pending; do not silently turn it into a pass.

Review both cases even when one has already failed. Keep completed collection
reports and their original pending-review fields unchanged; add review sidecars.
Any screen/review disagreement must retain both reasons. Deduplicate issue
counts by raw command identity without changing individual frozen failures.

## Targeted diagnostic and approval boundary

The [v4 proposal](../../docs/workflow-fidelity-pilot-v4.md) contains exactly two
fresh GPT-6 Luna low sessions: append, then creation with synthetic hooks, one
turn per session. All original prompts and project fixtures are reused. No
baseline, standalone create case, retries, replacement, resume, extra judge or
model override is included. Live collection remains disabled until separate
approval of this concrete proposal.

Both sessions must complete and pass every applicable automated content,
formatting, reference and workflow assertion **and** semantic/raw review to
clear this targeted repair gate. Ordinary fidelity failures remain retained;
instrumentation or isolation defects stop the remaining slot. A new rule or
candidate after collection requires another version, never retrospective repair
of these grades.

Efficiency remains descriptive: total/cached/uncached input, output, latency,
reference reads and failed actions, with no matched baseline or savings claim.
One sample per case cannot establish reliability. Do not pool models or cohorts.
A two-case pass would not meet broader replication, lifecycle/target, baseline
or independent-review requirements, promote the router, or complete OPT-004.
Leave inline remains the compiler default; router v4 is an authored redesign.
