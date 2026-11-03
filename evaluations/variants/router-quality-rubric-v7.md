# Fidelity rubric v7 — append reads and supported verification

Prospective only: router v6, checker/collector v6 and normalizer v5. Observations
use schema v5; checker/collector reports use v6. The
[v5 results](../../docs/workflow-fidelity-v5-results.md) remain frozen at 1/2
automated and complete reviewed case passes, with 2/2 semantic content passes.
No historical observation is regraded. All unchanged criteria from
[rubric v6](router-quality-rubric-v6.md) and broader promotion requirements from
[rubric v2](router-quality-rubric-v2.md) remain in force.

## New bounded rules

| Area | Required evidence and rejection boundary |
| --- | --- |
| Read-only Python | Recognize only explicitly supported literal-path AST forms for existence/conditional text reads and byte-representation/full-text reads. Never execute captured code. Exact returned output, pinned bytes, matching lifecycle, allowed paths and valid order must corroborate reads; dynamic paths, hidden side effects, symlinks, partial output and unsupported syntax cannot pass. |
| Absence before setup | Extension absence must be pinned at preparation and established by a successful bounded check before setup. Existing configuration must actually be read before setup. Late discovery, a missing inventory entry or unsupported claim does not satisfy the checkpoint. |
| Separate setup | Setup must complete as a separate action from file reads. A combined guidance/setup command cannot certify that the model read and applied the pre-execution checkpoint before starting setup. |
| Reference checkpoint | A successful full baseline-hash generation-reference read must complete before every project action starts, including extension absence checks. Reference and project reads sharing one command cannot establish this checkpoint. |
| Cache diagnostics | Only exact known cache-warning pairs may be separated from independently corroborated read output. Retain the raw diagnostics. A real runtime failure mixed with cache noise, a failed envelope, or incomplete evidence remains a failure. Successful context attribution never waives a failed action. |
| Final verification | After the last write, require a completed full target read in a separate tool action whose returned bytes/hash match the final artifact, before the final report. For append, preserve the exact original prefix, IDs, notes and checkbox states. Prewrite reads, patches, collector snapshots, partial/stale output and later reads cannot substitute. A bounded internal append/readback retains valid attribution and may ground narration, but alone fails the new separate-action checkpoint. |
| Verification narration | Recognized completed assertions about final reads or verification require earlier corroborated postwrite read evidence for the correct target. An assertion cannot supply its own evidence. Preserve unmatched/general wording for mandatory raw review. |
| Git narration | Recognized assertions about an attempted Git comparison or its error require an earlier actual matching invocation and returned outcome. The bounded grammar accepts only root-cwd `git diff` against `HEAD`, a bounded ancestor or commit hash, then `--` and the exact target; same-sentence result claims must also match output. Failed-comparison support currently requires a nonzero “not a git repository” result. Mentions in filenames or printed text, unrelated Git commands, future actions and inferred repository absence cannot support the claim. No Git command is required to verify the preserved prefix, and this pilot adds no Git probe. |

The new screens cover completed commentary and final messages, with explicit
negative controls for quoted, fenced, hypothetical, planned and negated text.
They remain bounded screens, not a truthfulness classifier. Missing support is
unverified; supported narration about a failed command does not clear that
command's failure. Unknown operations still fail automated workflow checks.

## Separate dimensions and diagnostic gate

| Dimension | Passing requirement for the proposed append case |
| --- | --- |
| Content correctness | Three distinct requirements-quality questions: measurable expiration, expired/reused outcomes, retention. Meaningful traceability and Gap markers; no invented policy. All semantic criteria must pass separate review. |
| Formatting | Exactly CHK008–010, unchecked, correct question/bracket syntax and preserved template; accurate final full path, new count, append status, focus, depth and reviewer/timing. |
| Reference behavior | One required generation reference read before project actions; no unrelated example reference loads. |
| Workflow fidelity | All existing invariants plus the new setup/absence checks, actual final readback, exact prefix/state preservation and supported factual narration. Every applicable automated assertion and raw review must pass. |
| Efficiency | Descriptive input/cache/output/latency/read accounting only; no baseline or replication, so efficiency is not evaluated. |

The smallest new diagnostic is **one append-only session**. A passing result
would validate that one sample under v7, not the full workflow matrix or router
v6 hooks. V5's passing hooks case remains a separate historical result and is
not imported as a v6 pass. All broader replication, baseline, independent
review, lifecycle/trigger, other-runtime and efficiency requirements remain
open. OPT-004 cannot be completed or the router promoted by this diagnostic.

## Review and approval boundary

Use the inherited semantic-first protocol: anonymous prompt/spec/constitution,
before/final artifact and final-report packet; separate lookup key; record
reviewer identity and prior exposure. Preserve semantic judgments before
opening raw traces, automatic grades or usage. Then review all material claims
against complete raw records and artifacts. Keep screen/review differences and
original pending-review fields; add review sidecars, never rewrite grades.

The [v6 proposal](../../docs/workflow-fidelity-pilot-v6.md) specifies one fresh
GPT-6 Luna low session, one turn, zero retries/replacements/expansion and no extra
model judge. New tests use synthetic traces and a local fake server only.
This rubric, offline preparation and earlier approvals do not authorize launch.
