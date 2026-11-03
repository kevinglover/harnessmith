# Fidelity rubric v11 — guarded literal absence marker

Prospective rules for unchanged router v7, normalizer v9 (observation schema 9)
and checker/collector v10 (report schema 10). All hard gates from
[v10](router-quality-rubric-v10.md) and promotion requirements from
[v2](router-quality-rubric-v2.md) remain. The [v9 result](../../docs/workflow-fidelity-v9-results.md)
stays frozen at **0/1** full automated and complete reviewed gates. Historical
traces, observations, artifacts, scores, packages and the original skill are not
modified or regraded.

## New bounded conditional proof

The new standalone grammar is
`if [ -f PATH ]; then cat PATH; else test ! -e PATH && echo ABSENT; fi`.
All three path tokens must be the same safe literal workspace path. Both branches
must be statically supported, including the unused branch. The exact successful
command lifecycle, source, cwd and scope must match. The present branch requires
complete nonempty pinned contents. Absence is restricted to the manifest-pinned
absent `.specify/extensions.yml` and exact `ABSENT` plus newline output after the
guarded test. A marker alone, missing/null output, altered marker, mismatched
path, extra command, unsafe branch, noisy/partial output, failure, symlink or
stale inventory never earns this proof. Captured commands are neither rewritten
nor executed by the normalizer.

Before setup, the entire preceding operational trace must be accounted for under
the inherited read-only and pinned synthetic-setup rules. The new proof does not
admit absence probes concurrent with another operation. Existing exact-read
concurrency requirements remain unchanged.

A post-append extension check may account for one completed native update to
the pinned checklist target only, with an exact preserved prefix and no changed
other file or mode. A distinct successful full final readback must complete after
that edit and before the check. This bounded exception supports the synthetic
append case; it does not declare arbitrary writes, shell commands, hooks or
unknown operations absence-preserving. Mutation of extension state, another
target, incomplete/ambiguous edits or unsafe overlap cannot gain a certificate.

Only exactly correlated inherited attribution failures may be superseded, with
their original facts and issues retained in new proof metadata. Newly proven
timely context reads may repair their corresponding dependency shadow; certified
prewrite operations may restore downstream terminal-discovery proof. Independent
full-read attribution blocked by those earlier unknowns may be reconsidered only
under the unchanged v8 intrinsic-read and connected-overlap safety requirements.
No new concurrency grammar or unsafe-peer exemption is added. Independent
failures and all command-separation requirements remain binding. This is bounded
static attribution, not shell emulation, executable attestation or OS tracing.

Inherited explicit-null absence support remains restricted to its original
matching v8 proof and derived backing copy. The new guarded-marker proof requires
text and must not admit null through that adapter. Captured observations remain
unchanged. Every new bundle pins its actual inherited and new dependencies;
older manifests and observation schemas cannot be regraded as v10.

## Separate dimensions and promotion

| Dimension | Passing requirement |
| --- | --- |
| Content correctness | Exactly three distinct requirements-quality questions about measurable expiration, expired/reused outcomes and retention, with traceability and no invented policy; separate semantic review. |
| Formatting | Unchecked CHK008–010, question/bracket syntax, existing template preserved and accurate path/count/append/focus/depth/reviewer report. |
| Reference behavior | Complete pinned generation reference finishes before project actions, including unknown operations; only relevant references loaded. |
| Workflow fidelity | Every inherited hard gate: certified extension state before separate setup, complete context before write, command separation, exact prefix and checkbox states, separate complete final readback and evidence-supported commentary/final/Git claims. |
| Efficiency | Input/cache/output/latency/read counts reported descriptively. No paired baseline or replication means no savings claim. |

Anonymous semantic-first review must be saved before opening the lookup key,
grades, usage and raw trace. Disclose reviewer identity, prior exposure and
blinding limits; then inspect all operations and material narration. Empty
bounded match arrays never prove truthful narration. Preserve pending collector
grades and separate review sidecars. Do not pool models or instrument versions.

The [v10 proposal](../../docs/workflow-fidelity-pilot-v10.md) is one fresh GPT-6
Luna low append session, one turn and repetition, no retries, replacements,
expansion, baseline, hooks rerun or extra judge session. It is **not authorized
or launched**. The unchanged prompt does not prescribe shell syntax or a
post-append probe. Any grammar the model does not choose stays unobserved live;
do not rerun to manufacture coverage. One pass establishes only that sample,
not reliability, hooks fidelity, efficiency, equivalence, promotion or OPT-004
completion. Leave inline remains the compiler default.
