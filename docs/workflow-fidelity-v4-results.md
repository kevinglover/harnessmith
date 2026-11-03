# Two-session workflow follow-up: Luna and router v4

The approved v4 pilot completed on **2026-10-25**: exactly two fresh GPT-6 Luna
sessions, append then creation with hooks, one turn each, **zero retries and no
added sessions**. Both completed and every result is retained. **0/2 passes all
frozen automated checks; 2/2 passes the separate semantic content review.** The
complete reviewed gate remains **0/2** because it also requires automated and
workflow compliance. OPT-004 stays open and the router remains experimental.

This records execution of the unchanged [v4 proposal](workflow-fidelity-pilot-v4.md)
with router v4, checker/collector v4, the frozen v3 normalizer, and
[rubric v5](../evaluations/variants/router-quality-rubric-v5.md). The proposal
remains a historical preapproval document. No code, package, rubric, or collected
grade was changed after launch. Earlier [initial](workflow-fidelity-results.md),
[v2](workflow-fidelity-v2-results.md), and [v3](workflow-fidelity-v3-results.md)
cohorts remain separate, as do Astra and Luna results. An authored router
redesign is not a proven content-preserving compiler transformation.

## Separate outcomes

| Dimension | Append | Creation with hooks | Interpretation |
| --- | --- | --- | --- |
| Frozen content screen | Pass | Pass | Requested topics and requirements-quality wording pass bounded lexical screens. |
| Semantic content review | Pass | Pass | Distinct questions, meaningful traceability, Gap markers and policy-neutral wording. |
| Frozen formatting | Pass | Fail | Hooks says “four item checklist”; the bounded count grammar expects plural items/questions or a labeled count. Artifact formatting passes. |
| Frozen reference behavior | Pass | Fail | Hooks returns the full guidance, but a later no-match discovery exits 1 in the same command; normalization does not certify the earlier read. |
| Frozen workflow | Fail | Fail | Append uses an unsupported Python write/readback form; hooks has actual context, timing and failed-action gaps as well as conservative parsing. |
| Raw narrative review | Pass | Fail | Hooks commentary claims an unrecorded failed invocation; its final Python setup failure/recovery claim is corroborated. |
| Efficiency | Not evaluated | Not evaluated | Descriptive usage only; no matched baseline or replication. |

Append preserves every original byte, including the reviewer annotation and
`[x]`, `[X]`, and `[ ]` states, and adds three unchecked items, CHK008–010.
Creation produces four unchecked questions, CHK001–004. Both final artifacts
are returned in full, and no denied checklist write appears. These are observed
outcomes in two samples, not reliability estimates or proof of improvement.

Anonymous artifact packets were reviewed before opening their lookup key,
scores, usage or raw traces. The primary assistant authored the candidate with
subagents, knew the single-variant design and collector exit 1, and could infer
cases from artifacts. Review is neither independent nor fully blind. No extra
model judge session ran. Semantic review was preserved before raw review;
original `pending-review` fields remain unchanged. Reviews are new sidecars.

## Raw behavior and remaining gaps

Line numbers below are one-based in each session's `raw/events.jsonl`, including
send and receive records. Normalized indices use a different coordinate system.
`manual-review.json` records exact item IDs and start/completion lines.

**Append.** Full generation guidance returns at line 67. The command at line 80
returns valid setup JSON, constitution, template, existing checklist and spec,
and confirms no extension configuration. At line 166, a successful `python3 -c`
command reads the old bytes, opens the target in append mode, writes literal
items, rereads the file, asserts `new == old + add`, and prints its complete
content. Snapshot comparison independently confirms prefix preservation. This
is an internal Python readback, not a separate shell read. The final report at
line 371 accurately describes count, preservation, policy gaps and setup cache
diagnostics. No Git-availability claim is added.

The frozen Python recognizer requires exactly one sequenced external target
read. This internal read/write/read/assert/print form is outside its bounded
grammar and becomes one completed unknown event. Consequently `classified-events`,
`setup-and-write-order`, `context-before-write`, and `final-artifact-verification`
fail. All four failures remain. Raw evidence corroborates the artifact and
ordering without turning an unsupported parser path into an automated pass or
replaying the write. All four shell commands returned exit 0.

**Creation with hooks.** Full generation guidance returns at line 66, followed
by a no-match `rg --files` discovery that exits 1; its patterns target hidden
directories without enabling hidden-file discovery. This is a retained nonzero
command outcome, not a denied write. The normalizer cannot certify the earlier
read independently. At line 225 the complete configuration is returned, then
`cat` receives setup arguments as filenames and exits 1. Configuration is visible
in raw output but has no certified normalized read event.

The behavior gaps are distinct:

- Before reading configuration, line 221 announces invented `specify-context`,
  `speckit-audit`, and `checklist-ready` hooks. None is configured or invoked.
  The correct automatic pre announcement never appears. The correct optional
  pre offer at line 409 arrives after pre execution and setup, so it is late.
- Line 300 claims an earlier adapter invocation returned “Unknown synthetic
  command” for an inferred ID. No such invocation or result exists in the trace.
  This unsupported factual narration fails raw review, independently of final
  report checks.
- At line 306, Python attempts to execute the shell prerequisite script and
  returns a `SyntaxError`. The `&&` chain skips constitution loading; `|| true`
  masks the failure, then template/spec/discovery run and the aggregate exit is
  0. Constitution is never returned in this session. A successful `sh` recovery
  at line 310 supplies setup JSON, but cannot erase the earlier failure or
  supply the missing constitution.

The two permitted automatic markers do run in order: pre at line 302 before
successful setup, and post at line 513 after the native file edit at line 411
and exact standalone artifact read at line 414. The post marker records the
final artifact hash. No optional, disabled, conditional or invented hook is
invoked, and no condition evaluation appears in the trace.

Both configured post blocks are actually rendered at line 511 before post
execution, with correct IDs, descriptions and optional prompt. The frozen
final-offer screen marks the combined offer claim unverified because it lacks
a certified configuration read and the pre timing fails. **This does not mean
post blocks were absent.** The final report at line 673 truthfully describes
the Python failure and `sh` recovery; both optional offers occurred, but only
the post offer was timely. The earlier unsupported error story still fails
the general narrative criterion.

Frozen hooks failures are `final-report`, `expected-reference-set`,
`reference-before-project-actions`, `classified-events`, `successful-events`,
`required-context-reads`, `context-before-write`, `hook-config-before-execution`,
`hook-announcements`, and `recognized-final-hook-claims-supported`. The singular
“four item checklist” count is understandable by meaning but outside the
inherited count grammar; its frozen failure is retained. Two command envelopes
exit nonzero, and one additional constituent failure is masked by a successful
envelope. Multiple issue records are not additional executed commands.

Known macOS cache-write errors/warnings accompany successful setup, marker and
append commands. They remain in raw output. No denied **checklist** write does
not imply that no cache write was denied. The live append exercises a Python
write outside the supported grammar; the hooks artifact uses a native edit.

## Measured scope

| Session | Total input | Cached input | Uncached input | Output | Collector latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `append-router-v4` | 85,092 | 65,408 | 19,684 | 1,003 | 14.205 s |
| `hooks-router-v4` | 162,854 | 122,880 | 39,974 | 1,641 | 23.599 s |
| Batch accounting | **247,946** | **188,288** | **59,658** | **2,644** | **37.804 s** |

Usage is the last cumulative event per session, never a sum of repeated
cumulative events. Uncached input is total minus cached input; latency is the
collector's per-session field. Append has four shell commands and no native
edit; hooks has seven shell commands and one native edit. Raw output contains
one full generation-reference read per session; the frozen normalized read
statuses differ as described above. No example reference is loaded.

The batch fits the approved estimate of 200–400k input and 2–6k output tokens.
Provider caches were uncontrolled, backend snapshots unreported, and only one
sample per case was collected. These figures do not establish billing, savings,
equivalence or an improvement over previous cohorts. Root size alone does not
prove runtime savings.

## Provenance and retention

The private, gitignored bundle is
`evaluations/local-evidence/2026-10-25-workflow-v4-luna/`, absent from a fresh
checkout. Its README indexes:

- `report.json`, `environment.json`, `preparation.json`, `batch-events.jsonl`
  and `launch.log`: exactly two attempts and their configuration/outcome.
- `append-router-v4/` and `hooks-router-v4/`: prompts, manifests, attempts,
  observations, frozen checks/results, raw JSONL/stdout/stderr, inventories,
  complete before/after/workspace snapshots and hidden files.
- `instrument/`: frozen collector, inherited dependencies, parser/checker,
  pilot and rubric. Manifests pin original source, authored package/review,
  fixture and prompt hashes; recipe identity is explicitly null.
- `review-input.json`, `review-key.json`, `semantic-review.json`,
  `manual-review.json` and `analysis.json`: separate semantic/raw reviews and
  calculations, without historical rescoring.
- `collection-copy-integrity.json`, `integrity-review.json` and
  `postcollection-validation.json`: all **107** original collection files
  copied byte-for-byte and all **1,394** prelaunch protected files unchanged.
  A separate read-only structural audit confirmed retention and session bounds.

The original collection remains at
`/private/tmp/opt004-workflow-v4-luna-live-20261025/`. Absolute trace paths still
refer there; they are not rewritten. Relocated workspaces were not regraded.
The initial automatic-approval rejection started no process or session and is
retained separately in `evaluations/local-evidence/2026-10-25-workflow-v4-prelaunch/`.
The user's subsequent explicit approval authorized the sole two-session launch.

| Identity | Recorded value |
| --- | --- |
| Model and reasoning | `gpt-6-luna`, low; backend snapshot unreported |
| Harness and mode | `codex-cli 0.163.0-alpha.11.1`, `app-server-stdio` |
| Instrumentation | `codex-workflow-stdio-v4`; observation schema v3, checker/collector schema v4 |
| Configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |
| Original source SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router v4 review SHA-256 | `20831886b935794d97ab90435b8e4d7552c85fa85bfbeec18d26c973cda49e52` |
| Rubric v5 SHA-256 | `68071994a151512e43dde025a529cb54d3d8842ae8146089ca5302ba50d5bc80` |

The collector validated Luna low, workspace writes, network disabled, approval
`never`, temporary-directory write exclusions, intended cwd and no unrelated
instruction sources before each turn. No model reroute occurred. Only synthetic
local hooks ran. The legacy sandbox permits host reads; trace/inventory checks
are not OS-level read isolation or a complete file-access audit.

Prelaunch validation passed **373 tests, 84% coverage**, plus ruff, mypy, schemas
and documentation checks. Documentation/schema and retention checks were repeated
for this report; unchanged unit tests and completed benchmarks were not rerun.
The collector exited 1 for frozen failures, with no collector or integrity error.
No result, artifact, failure or raw trace was discarded.

Publication preserves terminal blank lines in eight frozen router example
references and the frozen v4 checker test file. Git's staged whitespace check
reports these existing bytes as new-file EOF warnings; they are documented
exceptions, not source edits. Other whitespace findings are not waived.

## Decision and next work

Keep OPT-004 open, leave inline as the compiler default, and retain the router
as experimental. The next useful work is offline: add new-version regressions
for internal append/readback, constituent read evidence in nonzero chains,
singular count modifiers, hidden discovery, masked context failures, invented
pre-hook blocks and unsupported commentary claims. Preserve conservative failure
handling; successful recovery must not erase an earlier failed action.

Any candidate repair must use new versions and retain these scores. Only after
offline validation should a new exact pilot be proposed for separate approval.
Baseline fidelity, replication, lifecycle/target coverage and independent review
remain open. The two-session authorization is consumed; no retry, expansion or
additional live batch is queued.
