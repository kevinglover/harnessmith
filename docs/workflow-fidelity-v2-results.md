# Two-session workflow follow-up: Luna and router v2

The approved follow-up completed on **2026-10-24 local time** (2026-10-25 UTC):
exactly two fresh GPT-6 Luna sessions, append then creation with hooks, one turn
each, **zero retries and no added sessions**. Both attempts and all results are
retained. The frozen full-workflow result is **0/2 passes**. OPT-004 remains
incomplete and the router is not promoted.

This is the execution record for the unchanged
[two-session proposal](workflow-fidelity-pilot-v2.md), using router v2,
checker/normalizer v2 and [rubric v3](../evaluations/variants/router-quality-rubric-v3.md).
That proposal remains a historical preapproval document. The earlier
[six-session cohort](workflow-fidelity-results.md), its grades, original skill
and older instruments are unchanged. No result is pooled with that cohort or
with the Astra or Luna consultation benchmarks. Router v2 is an authored
semantic redesign, not a proven content-preserving compiler transformation.

## Separate outcomes

| Dimension | Append | Creation with hooks | Interpretation |
| --- | --- | --- | --- |
| Content screen | Pass | Pass | Three and four distinct requested topics respectively; these automated screens remain heuristics. |
| Semantic content review | Pass | Pass | Questions assess requirements quality, cite the matching requirement, flag missing policy, and invent no policy values. Review is not independent or fully blind. |
| Formatting | Pass | Pass | Exact new IDs/counts, unchecked states, question/quality/traceability syntax, template structure, Gap markers and final-report fields pass. This does not certify all narrative claims. |
| Reference behavior | Pass | Pass | Full project-generation reference loaded once before project actions; no example references loaded. |
| Frozen workflow | Fail | Fail | Append has two unverified absence checks; hooks has genuine behavior failures plus an unclassified recovery write. Details below. |
| Efficiency | Not evaluated | Not evaluated | Usage is recorded; one sample per case and no matched baseline cannot establish savings. |

Both runs read the full constitution and feature spec before writing. The append
preserved every original byte, including the reviewer note and `[x]`, `[X]`,
and `[ ]` states, and added only CHK008–010. Creation produced CHK001–004, one
question for each requested topic. Every new item carries a Gap marker. These
are positive observations of previously missing behaviors, not reliability or
causal improvement estimates.

Anonymous artifact packets were reviewed before opening the lookup key, usage,
frozen scores or raw traces. The primary assistant knew the single-variant
design, had authored the candidate, and knew the collector returned nonzero;
the case is inferable from its prompt and artifact. The retained review is
therefore neither independent nor fully blind. No extra model judge sessions
were launched. Raw-trace review was performed afterward and retained separately.
The collector's original `pending-review` fields remain unchanged; completed
review lives in the sidecars, not a rewritten collection report.

## Raw behavior and instrument limits

Line numbers below are one-based in each session's `raw/events.jsonl`, including
send and receive records. Normalized event indices use a different coordinate
system. `manual-review.json` records item IDs and both start/completion lines.

**Append.** The full generation reference completes at line 65; setup,
constitution, template, spec and existing checklist are returned at line 78.
The file-change event completes at line 154 and the complete final-file read at
line 160. The frozen setup/context/order and preservation checks all pass.

Only `classified-events` and `successful-events` fail. Two no-else existence
checks for the fixture's absent `plan.md` and `tasks.md` produce no output.
The bounded normalizer cannot prove those individual statements succeeded, even
though the enclosing command exits zero. Raw review finds absence checks,
not an observed required-context omission or failed append. These are remaining
instrument limits; **the failed grades are not changed**.

**Creation with hooks.** The generation reference and hook configuration are
read at line 72. The automatic pre marker completes at line 76, before the
successful shell setup at line 181. Constitution, spec and template finish at
line 185. The final write is corroborated by returned artifact text at line 252;
the automatic post marker at line 293 records the exact final artifact hash.
Only the two allowed automatic markers run; no optional, disabled or conditional
hook execution or condition evaluation is observed.

Three actual behavior gaps remain:

- Required automatic `EXECUTE_COMMAND` blocks and usable optional `To execute:`
  offers are absent from completed assistant messages. Naming the optional IDs
  in the final answer and claiming that offers were shown does not supply them.
- A heredoc at line 248 fails because the sandbox denies temporary-file
  creation. Its aggregate shell exit is zero, but captured output explicitly
  records the failure. A subsequent Python write recovers within the same turn;
  this is not an additional session or a batch retry.
- Commentary at line 179 claims a Python setup invocation caused a syntax error.
  The raw commands contain no such invocation or error result. The recorded
  shell setup succeeds. This is unsupported narration, not evidence of another
  executed failure.

The recovery `python3 -c` write is outside the normalizer's bounded grammar and
creates no recognized write event. Consequently `setup-and-write-order`,
`context-before-write` and `automatic-hook-order` fail despite the corroborated
raw order. `classified-events`, `successful-events` and `hook-announcements`
also fail. The raw interpretation does not erase the real heredoc failure or
missing offers, and it does not override any frozen check.

Exact known macOS cache warnings from the pinned setup/marker adapters were
retained as diagnostics alongside their successful JSON results. The denied
heredoc remains a failure. Aggregate exit zero is never used to dismiss it.

## Measured scope

| Session | Total input | Cached input | Uncached input | Output | Collector latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `append-router-v2` | 81,582 | 62,848 | 18,734 | 893 | 11.918 s |
| `hooks-router-v2` | 158,384 | 128,384 | 30,000 | 1,648 | 20.483 s |
| Batch accounting | **239,966** | **191,232** | **48,734** | **2,541** | **32.401 s** |

Each input/output figure is the last cumulative token-usage event for that
session, not a sum of repeated cumulative events. Uncached input is total minus
cached input; latency is the collector's per-session field. The batch falls
within the proposal's heuristic input/output allowance. Provider caching was
uncontrolled. These are neither billing measurements nor an efficiency
comparison, and root size is not evidence of runtime savings.

## Provenance and retention

The private, gitignored bundle is
`evaluations/local-evidence/2026-10-24-workflow-v2-luna/`; it is absent from a
fresh checkout. Its README indexes the following retained files:

- `report.json`, `environment.json`, `preparation.json`, `batch-events.jsonl`
  and `launch.log`: complete two-attempt collection and exit status context.
- `append-router-v2/` and `hooks-router-v2/`: `attempt.json`,
  `attempt-events.jsonl`, `manifest.json`, `prompt.md`, `observation.json`,
  `checks.json`, `result.json`, `raw/events.jsonl`, `raw/events.stdout`,
  `raw/events.stderr`, before/after inventories and complete workspace snapshots
  (including hidden package, constitution and hook files).
- `instrument/`: exact collector, inherited dependencies, checker/normalizer,
  config and rubric snapshots. Each session manifest also pins the original
  source, authored package/review, prompt and synthetic fixture hashes.
- `review-input.json`, `review-key.json`, `semantic-review.json`,
  `manual-review.json` and `analysis.json`: anonymous packet, lookup key and
  separate postcollection reviews/accounting. No historical score was replaced.
- `collection-copy-integrity.json` and `integrity-review.json`: all **103**
  collected files copied byte-for-byte and all **734** prelaunch protected
  content files unchanged, including historical evidence and original skill.

The source collection remains at
`/private/tmp/opt004-workflow-v2-luna-live-20261024/`. Absolute paths in traces
refer to that original location and are intentionally not rewritten in the
retained copy. Rechecking a relocated workspace is not the recorded evaluation.

| Identity | Recorded value |
| --- | --- |
| Model and reasoning | `gpt-6-luna`, low; backend snapshot unreported |
| Harness and mode | `codex-cli 0.163.0-alpha.11.1`, `app-server-stdio` |
| Instrumentation | `codex-workflow-stdio-v2` |
| Configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |
| Original source SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router v2 review SHA-256 | `8d45dba4f67ea54d90248a5d1729edb21594e3c0f2654e8b1877138bb2abfb54` |
| Rubric v3 SHA-256 | `93242e95a6259892acc3b6c5b3e35d7d0f889751578f1c8b8656b4f904e09e8b` |

Recipe identity is explicitly null because this is an authored redesign.
Permissions were validated before each turn: workspace writes, network off,
approval `never`, temporary-directory writes excluded and unrelated skills
disabled. Only synthetic fixture hooks were available; no real project hook
was invoked. The legacy sandbox permits host reads at the OS level. Recorded
read scope and artifact inventories pass, but this is not an OS read-isolated
container or complete file-access audit.

Prelaunch validation remained **260 tests passed, 84% coverage**, with ruff,
mypy, schema and documentation checks passing. Frozen source hashes matched
before launch and after collection. No collector, checker, router or rubric
change was made after observing these results. Documentation/schema checks and
the protected-file audit were repeated for this results update; benchmarks and
the unchanged unit suite were not rerun.

## Decision

The targeted gate fails. Keep router v2 experimental and OPT-004 open. Any next
repair should first isolate the absent-file conditional parser case, the
unsupported recovery-write shape, and actual hook-offer rendering in offline
regressions. Those would require new instrument/candidate versions; they must
not alter this cohort's grades. The broader trigger/lifecycle/target coverage,
replication, baseline comparison and independent review remain open.

The exact two-session authorization is consumed. No retry, expansion or further
live batch is queued. A new live proposal would need separate approval.
