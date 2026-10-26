# Two-session workflow follow-up: Luna and router v5

The approved v5 pilot completed on **2026-10-25**: exactly two fresh GPT-6 Luna
low sessions, append then creation with hooks, one turn each, **zero retries,
replacements or additional sessions**. Both completed and every result is
retained. **1/2 passes the frozen automated checks, 2/2 passes semantic content
review, and 1/2 passes the complete reviewed case gate.** Hooks passes; append
fails. The batch requires both cases to pass, so OPT-004 remains open and the
router remains experimental.

The user approved the exact [v5 proposal](workflow-fidelity-pilot-v5.md). That
document and the offline preparation remain historical preapproval records.
Collection used the unchanged router v5, checker/collector v5, normalizer v4
and [rubric v6](../evaluations/variants/router-quality-rubric-v6.md). No package,
instrument, rubric or collected grade changed after launch. All earlier
[initial](workflow-fidelity-results.md), [v2](workflow-fidelity-v2-results.md),
[v3](workflow-fidelity-v3-results.md) and [v4](workflow-fidelity-v4-results.md)
cohorts remain separate; Luna and Astra are never pooled.

## Separate outcomes

| Dimension | Append | Creation with hooks | Interpretation |
| --- | --- | --- | --- |
| Frozen content screen | Pass | Pass | Requested topics and requirements-quality wording pass bounded screens. |
| Semantic content review | Pass | Pass | Distinct requested questions, meaningful traceability, Gap markers and neutral missing-policy wording. |
| Frozen formatting | Pass | Pass | Correct new unchecked items, IDs, template and final path/count report. |
| Frozen reference behavior | Pass | Pass | One complete generation-reference read before project actions; no example-reference reads. |
| Frozen workflow | Fail | Pass | Append has two unclassified read-only Python commands and no final readback. |
| Raw workflow review | Fail | Pass | Append checks extension presence after setup and omits final verification. Hooks follows its phase checkpoints. |
| Raw narrative review | Fail | Pass | Append claims a final read and a failed Git comparison with no corresponding recorded actions. |
| Efficiency | Not evaluated | Not evaluated | Descriptive accounting only, without a matched baseline or replication. |

Both artifacts contain the requested content. Append preserves all **694**
original bytes, including the reviewer annotation and `[x]`, `[X]`, and `[ ]`
states, and adds three unchecked questions CHK008–010. Hooks creates four
unchecked questions CHK001–004. Both use native file edits successfully; no
denied checklist write is recorded. Correct saved bytes do not establish that
the model performed the required verification.

Anonymous artifact packets were reviewed before opening their lookup key,
automated scores, usage or raw traces. The primary assistant authored the
candidate with implementation subagents, knew the single-variant design and
collector exit 1, and could infer cases from the artifacts. Review is neither
independent nor fully blind. Semantic judgments were saved before raw review.
No extra model judge ran. Original `pending-review` fields remain unchanged;
reviews are new sidecars. A separate read-only instrumentation/retention audit
did not grade model outputs.

## Raw behavior and remaining gaps

Line numbers are one-based in each session's `raw/events.jsonl`, including sent
and received records. Normalized indices use a different coordinate system.
`manual-review.json` retains exact item IDs and start/completion lines.

**Append.** At line 57 a combined command returns the complete generation
reference and successful setup JSON. It starts setup before checking extension
presence, despite the v5 checkpoint and instruction to separate setup from
file reads. At line 102, literal Python existence/read expressions return
`EXISTS False` for extension configuration, then `EXISTS True` and the complete
constitution. At line 106, the next command returns the spec, template and the
existing checklist as both byte representation and decoded text. Required
context really is present before the native append at lines 184–185.

Those two **read-only** Python commands fall outside the frozen recognizer.
The inherited dispatch treats them as potential literal writes and reports
“Python write requires exactly one sequenced target read.” Consequently the
normalizer supplies no certified context reads. It also retains failed
constituent events for macOS cache-denial diagnostics because these unknown
forms cannot qualify for its corroborated-cache exception. All three shell
command envelopes exit zero; after the exact cache pairs, no additional
runtime-failure diagnostic is present. Six issue records refer to two command
identities, not six executed failures. These are instrument limitations; they
do not mean the constitution was absent or a checklist write was denied.

The actual workflow/narrative gaps remain decisive:

- No command or read item occurs after the native append. The final report
  begins at line 196 and completes at line 342. The earlier read is prewrite;
  collector snapshots and edit diffs cannot substitute for model readback.
- The report says the final file read showed preservation. No such read is
  recorded, so the claim is unsupported even though snapshot comparison proves
  the original prefix survived.
- The report also says a Git-history comparison was attempted and failed
  because the workspace was not recognized as a repository. The complete trace
  contains no Git invocation, comparison result or corresponding error. This
  claim is unverified; no new command was run to supply retrospective support.

Frozen failures remain `classified-events`, `successful-events`,
`required-context-reads`, `context-before-write`, and
`final-artifact-verification`. The bounded execution/error-claim screen matches
neither final assertion and passes; mandatory raw narrative review fails. Keep
both outcomes. Parser expansion alone cannot repair this sample's missing
verification or unsupported narration.

**Creation with hooks.** The full generation reference returns at line 65;
configuration, the supplied adapter and scoped hidden-file inventory return at
line 69. Exact configured automatic/optional pre blocks complete at line 174,
before automatic pre execution at lines 175–176. Its marker confirms the target
is absent. Setup uses `bash` with the exact required arguments at line 232;
the constitution is read independently at line 236. Spec and feature inventory
return at lines 240 and 244.

The native creation completes at line 248, followed by an exact full artifact
read at line 254. Correct automatic/optional post blocks complete at line 355,
before automatic post execution at lines 356–357. The marker records the final
artifact hash. A second exact artifact read completes at line 362, before the
final report begins at line 366 and completes at line 484. Optional, disabled
and conditional hooks are not invoked; no condition evaluation is recorded.
Both completed commentary and final factual claims are corroborated. These
are observed outcomes in one sample, not a reliability or causal-improvement
estimate.

Known macOS Python cache writes are denied in both sessions. These warnings and
errors remain in raw output; successful setup/hook results are independently
corroborated. “No denied checklist write” does not mean no cache write was denied.
The new internal-Python append recognizer was not exercised: both live artifacts
used native edits. Its evidence remains offline regression coverage.

## Measured scope

| Session | Total input | Cached input | Uncached input | Output | Collector latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `append-router-v5` | 126,909 | 104,960 | 21,949 | 1,130 | 16.034 s |
| `hooks-router-v5` | 222,000 | 199,680 | 22,320 | 1,168 | 19.720 s |
| Batch accounting | **348,909** | **304,640** | **44,269** | **2,298** | **35.754 s** |

Usage takes the last cumulative event per session, never sums repeated
cumulative events. Uncached input is total minus cached input. Append has three
shell commands and one native edit; hooks has ten shell commands and one native
edit. All thirteen command envelopes exit zero. Each case reads the generation
reference once; hooks reads its final checklist twice, append zero times after
writing. The batch fits the approved estimate of 200–400k input and 2–6k output.
These figures do not establish billing, savings or superiority over another
version. Provider caching is uncontrolled, backend snapshots are unreported,
and there is only one observation per case. Root size does not prove savings.

## Provenance and retention

The private, gitignored bundle is
`evaluations/local-evidence/2026-10-25-workflow-v5-luna/`, absent from a fresh
checkout. Its README indexes all collection records and new review sidecars:

- `report.json`, `environment.json`, `preparation.json`, `batch-events.jsonl`
  and `launch.log`; exactly two attempts, zero retries and no unattempted slots.
- Both session directories: original prompts/manifests, durable attempt records,
  raw JSONL/stdout/stderr, observations, frozen checks/results, inventories and
  complete before/after/workspace snapshots including hidden files.
- `instrument/`: collector, inherited dependencies, normalizer/checker, pilot
  and rubric. `prelaunch/provenance/` additionally retains the canonical source,
  router review, proposal and inherited rubrics v2–v6.
- Anonymous `review-input.json` and separate `review-key.json`, preserved
  `semantic-review.json`, `raw-review-view.json`, `manual-review.json` and
  `analysis.json`. Existing grades and pending-review fields are untouched.
- `collection-copy-integrity.json`, `integrity-review.json` and
  `postcollection-validation.json`: all **111** original collection files copied
  byte-for-byte, with modes preserved, and all **1,559** prelaunch protected
  content files plus **two symlinks** unchanged.

The original collection remains at
`/private/tmp/opt004-workflow-v5-luna-live-20261025/`. Absolute trace paths still
point there; copied traces are not rewritten and relocated workspaces are not
regraded. The new authorization is recorded separately in
`evaluations/local-evidence/2026-10-25-workflow-v5-prelaunch/`. A prelaunch audit
found one pre-existing Finder `.DS_Store` change relative to the prior offline
baseline; this metadata drift is recorded separately and excluded from the
protected content count. No evidence-content drift was found.

| Identity | Recorded value |
| --- | --- |
| Model and reasoning | `gpt-6-luna`, low; backend snapshot unreported |
| Harness and mode | `codex-cli 0.163.0-alpha.11.1`, `app-server-stdio` |
| Instrumentation | `codex-workflow-stdio-v5`; observation schema v4, checker/collector schema v5 |
| Configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |
| Original source SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router v5 review SHA-256 | `6e6127ad37ca236d3c9bb20fca17918de44451dfcecc268d02b3fbe177808944` |
| Rubric v6 SHA-256 | `bd363bd0d883fdfbf851713ce2b0c8eeec7cff41fbc42f9148be74a2525f2b8a` |

Requested and returned settings were checked before each turn: Luna low,
approval `never`, network disabled, temporary-directory write exclusions,
intended workspace and no unrelated instruction sources. No reroute or collector
error occurred. Only synthetic local hooks ran. The legacy sandbox permits
host reads; recorded-path and inventory checks are not OS-level read isolation.
The launch used the established collector protocol; the current
[official app-server reference](https://learn.chatgpt.com/docs/app-server)
documents its thread/turn and sandbox interfaces.

The unchanged candidate had passed 439 offline tests with 84% coverage, including
66 new regressions, plus lint/type/schema/documentation checks. Source hashes
matched before launch. Only documentation/schema and evidence integrity checks
were repeated for this report; completed benchmarks and unchanged unit tests
were not rerun. The collector exited 1 for the append failures, with no collector
or integrity error. No artifact, failure or result was discarded.

## Decision and next work

Keep OPT-004 open, leave inline as the compiler default, and retain the router
as an authored experimental redesign. This batch establishes one passing hooks
case and two correct-content artifacts, not a content-preserving compiler
transformation or a general efficiency win.

The next useful work is offline: new-version controls for read-only Python
existence/byte-display forms and corroborated cache diagnostics, plus explicit
negative controls for absent postwrite reads, setup before extension discovery
and unsupported verification/Git narration. Preserve the failed v5 scores and
avoid weakening the final-verification gate. No further repair or live session
is included here. A later repaired candidate needs its own proposal and approval;
baseline fidelity, replication, independent review, lifecycle and other target
runtimes remain open. Both authorized slots are consumed; no retry or expansion
is queued.
