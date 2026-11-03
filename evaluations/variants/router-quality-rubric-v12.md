# Fidelity rubric v12 — test-form conditionals and a fresh final checkpoint

Prospective rules for authored router v8, normalizer v10 (observation schema 10)
and checker/collector v11 (report schema 11). All hard gates from
[v11](router-quality-rubric-v11.md) and promotion requirements from
[v2](router-quality-rubric-v2.md) remain. The [v10 result](../../docs/workflow-fidelity-v10-results.md)
stays frozen at **0/1** automated and complete reviewed gates. Historical traces,
observations, artifacts, scores, packages and the original skill are unchanged;
no historical trace is replayed or regraded with these instruments.

## Bounded conditional proof

The new standalone form is
`if test -f PATH; then cat PATH; else printf 'ABSENT\n'; fi`.
The test and read must name the same safe literal workspace path. Both branches
must be supported, including the unused branch. A present file must return
complete nonempty pinned contents. Absence is restricted to the manifest-pinned
absent `.specify/extensions.yml` and exact `ABSENT` plus newline output. A marker
alone is insufficient. Missing/null/noisy/partial output, wrong paths, unsafe
branches, extra operations, failed commands, symlinks and stale pins fail closed.

Only bounded non-login shell wrappers with safe literal quoting are admitted.
Shell expansion and command substitution cannot be treated as literal content.
Captured commands remain data; normalization does not rewrite or execute them.
Every proof requires the exact complete successful lifecycle, scope, cwd and
pinned inventory. Absence probes cannot overlap another operation. Prior unknown
or mutating operations block proof unless the inherited narrow append contract
accounts for the sole target update and its separate complete final readback.

Exactly correlated inherited attribution failures may be superseded only with
the original facts/issues retained in the certificate. Downstream discovery and
complete-read dependencies may recover under the existing strict proof rules.
Independent failures and command boundaries remain binding. This is bounded
static attribution, not general shell evaluation, executable attestation or
operating-system file-access tracing. Inherited explicit-null support remains
limited to its original matching v8 proof; the new printf proof requires text.

## Mandatory fresh post-generation extension checkpoint

The new append-case workflow gate requires a distinct successful, fully backed
extension-state action after the last target write and a separate complete
readback of the final artifact, and before the final report starts. It must be
isolated from other reads, discovery, setup, hooks and writes. The pinned absent
fixture requires a qualifying absence certificate; an early check, marker,
collector snapshot, final-file hash or narrative assertion cannot substitute.

The gate rejects missing, before-only, incomplete, failed, overlapping, unbacked
or late checks. Every existing reference, context, command-separation, append,
final-readback and evidence-supported narration/Git gate still applies. A correct
artifact does not waive the new checkpoint. No additional criterion is inserted
into an old report. Fresh v11 manifests and observation schemas are required.

For this bounded synthetic append proof, the final target readback and extension
check each occupy their own single-fact captured command. The readback's captured
text must equal the final artifact bytes; a normalized hash without matching
returned text is insufficient. This deliberately narrow checkpoint contract is
separate from the inherited general readback check. Multiple edits, mixed
readback envelopes and other absence grammars require their own future proof;
they cannot be inferred safe from a correct final artifact.

Router v8 makes the later action explicit in the generation route and step 8,
including when the initial configuration was absent. It preserves all earlier
hook selection, announcement/offer, permission and condition rules. This is an
authored workflow clarification, not a proven content-preserving compiler
transformation. Offline tests establish instrument behavior, not live obedience.

## Separate dimensions and promotion

| Dimension | Passing requirement |
| --- | --- |
| Content correctness | Exactly three distinct requirements-quality questions about measurable expiration, expired/reused outcomes and retention, with traceability and no invented policy; separate semantic review. |
| Formatting | Unchecked CHK008–010, question/bracket syntax, existing template preserved and accurate path/count/append/focus/depth/reviewer report. |
| Reference behavior | Complete pinned generation reference before every project action, including unknown operations; only relevant references loaded. |
| Workflow fidelity | All inherited hard gates plus the fresh isolated post-generation extension checkpoint after final write/readback and before reporting. |
| Efficiency | Input/cache/output/latency/read counts reported descriptively. No paired baseline or replication means no savings claim. |

Save anonymous semantic-first judgments before opening the lookup key, grades,
usage and raw trace. Disclose reviewer identity, prior exposure and blinding
limits. Then inspect every raw operation and material narration; empty bounded
match arrays do not prove truthful claims. Leave original pending grades intact
and retain separate reviews. Do not pool models, routers or instrument versions.

The [v11 proposal](../../docs/workflow-fidelity-pilot-v11.md) is exactly one fresh
GPT-6 Luna low append session, one turn and repetition, no retry, replacement,
expansion, baseline, hooks rerun or extra judge session. **No live session is
authorized or queued.** The original prompt and fixtures stay unchanged; the
prompt prescribes neither shell grammar nor the new checkpoint. Any grammar the
model does not choose remains unobserved live. Do not rerun to manufacture
coverage. One pass would establish only that reviewed sample, not reliability,
configured-hook fidelity, savings, equivalence, promotion or OPT-004 completion.
Leave inline remains the compiler default.
