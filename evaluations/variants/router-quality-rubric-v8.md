# Fidelity rubric v8 — literal else-output absence certificates

Prospective instrument revision only: unchanged router v6, checker/collector v7
and normalizer v6. Observations use schema v6; checker/collector reports use v7.
The [v6 result](../../docs/workflow-fidelity-v6-results.md) stays frozen at **0/1**
automated and complete reviewed gates, with positive semantic and raw behavioral
findings reported separately. No historical trace is replayed or regraded.
All hard gates in [rubric v7](router-quality-rubric-v7.md), and broader promotion
requirements in [rubric v2](router-quality-rubric-v2.md), remain in force.

## New bounded certificate

The parser may certify a standalone literal `if [ -f PATH ]; then cat PATH;
else printf LITERAL; fi` absence probe only when both branches are statically
safe, the paths agree and remain in the workspace, the manifest explicitly pins
absence with a verified inventory, and the returned nonempty output exactly
matches the supported literal printf rendering. Paths with symlink components,
existing files/directories, dynamic expressions, side effects in either branch,
compound commands or unsupported printf syntax cannot gain this certificate.
Captured commands are never executed to interpret them.

A matching successful start/completion pair must corroborate the entire command.
Prior mutation, setup, hook execution, failed/unknown/unverified operations and
overlapping or still-open operational lifecycles prevent certification. The new
certificate permits only bare commands or recognized non-login `-c` wrappers;
explicit login/interactive wrappers are rejected in the probe and its prefix.
Prior directory creation and other mutating/unreviewed diagnostic types are
excluded, and earlier command sources must agree across lifecycle endpoints.
The new shell certificate does not strip cache warnings or other output. A printed
absence label alone, missing inventory entry, commentary claim or final snapshot
cannot prove the checkpoint. Certification adds explicit proof metadata to the
derived absence diagnostic; it does not turn absence into a content read or
erase inherited failures. Static attribution is still not OS file-access tracing.
Shell startup and executable behavior are not independently attested by this
parser; the controlled collector environment and raw review remain necessary.

## Separate dimensions and unchanged gates

| Dimension | Passing requirement for this diagnostic |
| --- | --- |
| Content correctness | Three distinct, traceable requirements-quality questions covering measurable expiration, expired/reused outcomes and retention, without invented policy; separate semantic review required. |
| Formatting | Exactly unchecked CHK008–010, correct question/bracket syntax, preserved template and accurate final path, count, append status, focus, depth and reviewer/timing. |
| Reference behavior | Complete baseline-matching generation-reference read finishes before every project action, including the absence check; no unrelated example loads. |
| Workflow fidelity | Every existing gate: pinned absence before separate setup, required context, exact original prefix and checkbox states, separate complete matching postwrite read before final report, and corroborated factual narration. New absence grammar may supply evidence but does not waive ordering or any other gate. |
| Efficiency | Descriptive input/cache/output/latency/read accounting only. No matched baseline or replication; efficiency is not evaluated. |

The smallest future diagnostic is one append session with the unchanged router,
fixtures and prompt. A pass would apply to that one instrument-v7 sample only.
Earlier hooks and append cohorts stay separate. No pooling across versions or
models, reliability claim, router promotion or OPT-004 completion follows.
Broader baseline, replication, independent review, trigger/lifecycle and
other-runtime coverage remains open. Leave inline stays the compiler default.

## Review and approval boundary

Preserve the semantic-first review protocol: anonymous prompt/spec/constitution,
before/final artifact and final-report packet with a separate lookup key; record
reviewer identity and prior exposure before viewing grades, raw traces or usage.
Then review complete raw actions and every material claim. Empty bounded-screen
matches do not prove truthful narration. Retain original pending-review fields
and grades, adding review sidecars rather than rewriting evidence.

The [v7 proposal](../../docs/workflow-fidelity-pilot-v7.md) specifies one fresh
GPT-6 Luna low append session, one turn, zero retries/replacements/expansion and
no extra model judge. Offline tests use synthetic traces and a local fake server.
No live session is authorized or launched by this rubric or preparation.
