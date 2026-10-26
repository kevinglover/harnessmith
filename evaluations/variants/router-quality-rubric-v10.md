# Fidelity rubric v10 — same-path conditionals and concurrent reads

Prospective instrumentation rules for unchanged router v7, checker/collector v9
and normalizer v8 (observation schema 8; report schema 9). All hard gates from
[v9](router-quality-rubric-v9.md) and promotion requirements from
[v2](router-quality-rubric-v2.md) remain. The [v8 result](../../docs/workflow-fidelity-v8-results.md)
stays frozen at **0/1** full automated and complete reviewed gates. No historical
trace is replayed or regraded.

## New bounded proofs

A standalone literal `if [ -f PATH ]; then cat PATH; else test ! -e PATH; fi`
may supply a full read when the nonempty pinned file exists, or a pinned absence
fact for the explicitly absent `.specify/extensions.yml`. All three path tokens
must be identical literals resolving to the same safe workspace path; both
branches must be statically safe. Successful
matching lifecycle endpoints, source/cwd/scope and exact returned content or
empty absence output are required. Missing/altered pins, symlinks, dynamic shell
expressions, extra operations, noisy/partial output or failed commands cannot
gain this proof. Explicit null stdout and empty text are distinct recorded
representations of empty absence output. Missing stdout stays unverified; null
cannot prove a present-file read. Empty present files and lexical path aliases
are outside the new grammar.

Checker v9's reported backing adapter admits explicit null only for a unique
successful command with the new matching extension-absence certificate, exact
lifecycle/raw command, pinned inventory and empty-output hash. Only the derived
input to the inherited extension/separation helpers uses empty text; captured
observations and raw output are unchanged. Missing output, null reads, old or
malformed certificates, failed commands and duplicate records remain blocked.

Reference readiness also stays unverified when an unclassified operation starts
before the complete pinned reference finishes, overlaps it or lacks lifecycle
coordinates. Unknown operations after the checkpoint still fail workflow
classification without retroactively failing reference ordering.

Concurrent reads may be attributed only when each overlapping operational
envelope is independently proven read-only, complete and successful with exact
pinned output and consistent lifecycle metadata. Only full-read envelopes can
overlap; absence checks and discovery do not qualify as peer reads. Unknown, mutating, failed,
unfinished or wrong-scope overlaps remain failures. Prior state must be accounted
for; concurrency with setup, hooks or writes does not become safe merely because
one command is a read. A consuming write still requires every required read to
finish before it starts.

Newly proven conditional/read facts may satisfy downstream discovery-prefix and
prewrite dependency checks. Only precisely correlated artificial failures may
be replaced, with their old facts/issues retained in proof metadata. Actual
failures, incomplete operations, unrelated issues and isolation defects remain.
Captured commands are never executed or rewritten, and frozen normalizers are
not modified. This remains bounded static attribution, not shell emulation,
executable attestation or OS access tracing.

## Unchanged gates and separate dimensions

All three command-boundary gates remain: extension checks isolated from other
operations, every observed read isolated from discovery/mutation, and discovery
isolated from other operations. Multiple proven reads may share a read-only
envelope or overlap separate read-only envelopes; neither permits bundling reads
with discovery or writing. Discovery is optional. A gate with no recognized
discovery fact cannot alone establish live certificate coverage.

| Dimension | Passing requirement |
| --- | --- |
| Content correctness | Three distinct traceable requirements-quality questions covering measurable expiration, expired/reused outcomes and retention; no invented policy; separate semantic review. |
| Formatting | Unchecked CHK008–010, valid question/bracket syntax, preserved template and complete accurate final path/count/append/focus/depth/reviewer report. |
| Reference behavior | Complete pinned generation reference finishes before every project action; only relevant references loaded. |
| Workflow fidelity | All inherited hard gates, including certified extension state before separate setup, full context before writes, all command boundaries, exact prefix/checkbox states, separate complete postwrite readback and evidence-supported commentary/final/Git claims. |
| Efficiency | Descriptive input/cache/output/latency/read counts only. No matched baseline or replication: efficiency not evaluated. |

Preserve anonymous semantic-first review packets with separate lookup keys and
reviewer identity/prior-exposure disclosure. Then inspect all raw operations and
material narration. Bounded topic/narrative screens remain heuristics; no match
does not prove truthful narration. Keep original pending grades and review
sidecars separate. No pooling across models or instrument/router versions.

The [v9 proposal](../../docs/workflow-fidelity-pilot-v9.md) is exactly one fresh
GPT-6 Luna low append session, one turn, no retries, replacements, expansion or
extra judge. It is not authorized or launched. The unchanged prompt does not
force conditionals, concurrency or discovery; commands the model does not choose
remain unobserved live. No rerun may manufacture grammar coverage. One pass is
not reliability, hooks coverage, efficiency, compiler equivalence, promotion or
OPT-004 completion. Leave inline remains the compiler default.
