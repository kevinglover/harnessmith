# OPT-004 evidence and remaining acceptance work

Status reviewed 2026-10-25: **partially satisfied; not complete**. Codex now has
repeated, recipe-backed runtime measurements for explicit, read-only
consultations, a six-session Luna workflow cohort and separate two-session
router-v2, router-v3 and router-v4 follow-ups. Frozen automated passes are 0/6,
0/2, 1/2 and 0/2 respectively. V4 semantic content passes both cases, but the
targeted gate still fails on parser limits and genuine hooks workflow gaps;
narrower artifact/context behaviors pass. The wider fidelity matrix and
full workflow behavior remain open. Cohorts are not pooled.
The router remains a reviewed semantic redesign, not a verified
content-preserving compiler transformation.

The original task is `docs/weekly-reviews/opportunities.md`, under
“OPT-004 — Expand fidelity coverage and capture real runtime evidence” (lines
79–105 in the local ledger). That historical, gitignored entry predates the live
runs and still says no provider calls were made. This dated status document
supersedes its current-status statements without changing the historical ledger.

## Acceptance mapping

The original acceptance criterion is: “source/recipe hashes, harness/model/mode
versions, repeated samples, actions, outputs, reference reads, and measured usage
accompany every runtime claim. Keep mock results labeled and preserve the
disabled-by-default gate.” Its plan also calls for positive/negative trigger,
explicit-only, abort, approval, hook, reference-load, repeated-turn, and
compaction cases, starting offline and then using opt-in paired runs.

| Requirement | Current evidence | Status and limit |
| --- | --- | --- |
| Source, recipe, and package identity | Conditional and Luna comparison reports pin source, recipe, scenario, and every package file; router reports also pin the redesign review. Workflow manifests additionally pin fixtures, prompts and frozen instruments. | Satisfied for these recorded runs. Earlier direct-extraction reports intentionally have `recipe_sha256: null`; workflow original/authored packages also explicitly have no recipe. They are not recipe-backed evidence. |
| Harness, model, mode, and instrumentation versions | Reports record Codex CLI version, requested model, app-server mode, instrumentation version, permissions, cache policy, and configuration ID. | Partial reproducibility: the backend model snapshot is explicitly unreported. Requested model identity must not be presented as an immutable model snapshot. |
| Repeated comparable observations | Astra three-way: three observations per strategy/scenario; Luna four-way: four, with rotated order. All completed observations, including failures, are retained. Workflow: one observation per variant/case; all six initial, two v2, two v3 and two v4 attempts retained without replacements. | Satisfied for the frozen consultations; small descriptive samples, not a statistical guarantee. Not satisfied for workflow replication. Interrupted batches and differently instrumented cohorts remain separate. |
| Actions, outputs, reference reads, measured usage | Consultations contain answers, scored actions, ordered reference loads, usage/cache fields, latency and raw JSONL. Workflow adds before/after artifacts, raw stdout/stderr, lifecycle events and separate manual review. V3 proves pinned absent-file checks in its append sample. V4 preserves append bytes using an internal Python write/readback outside the frozen grammar; raw review separates that limit from hooks failures. | Satisfied for supported explicit consultations. Workflow command parsing remains bounded; the supported literal-Python grammar is validated offline, while the different live v4 append form remains unclassified. Neither parser is OS file-access tracing; unknown/failed commands remain failures. |
| Mock evidence distinguished from live evidence | Offline turn contracts use `mock-contract`; fake-provider tests use mock evidence; live reports use `runtime`. | Satisfied by the existing formats; mocked lifecycle events are not live workflow evidence. See [evaluation layers](evaluation.md). |
| Live collection opt-in | Runtime collectors reject disabled calls; comparison CLI only prepares packages unless enabled. | Satisfied by current collector boundaries. Approval is still required before any new live pilot. |
| Positive/negative triggers and explicit-only policy | Offline scenarios cover target invocation policy; live sessions explicitly supplied the chosen skill. | Open live: no implicit selection, non-trigger, crowded-catalog, or unauthorized model-invocation observations. Explicit input acceptance proves neither discovery nor automatic selection. |
| Approval, abort, hook, continuation, compaction | Version-2 synthetic turn contracts cover the events offline. Automatic markers ran in initial, v2, v3 and v4 hook cases. V4 verifies final bytes and renders both configured post blocks before post execution. | Partial live: v4 announces invented pre-hook IDs before reading configuration, omits the configured automatic pre block and offers the correct optional pre hook late. Approval, abort, optional-hook continuation, hook failure and compaction remain open. The consultation adapter remains read-only. |
| Checklist creation and state-preserving append | Earlier results remain frozen. V4 preserves every append byte, returns both final artifacts and has no denied checklist write; semantic content passes both. | Partial live: v4 automated passes are 0/2, complete reviewed gate passes 0/2. Append exposes a parser limit; hooks skips constitution after a masked failure, has pre-message gaps and unsupported commentary. No replication or causal improvement claim. See [initial](workflow-fidelity-results.md), [v2](workflow-fidelity-v2-results.md), [v3](workflow-fidelity-v3-results.md) and [v4 results](workflow-fidelity-v4-results.md). |
| Other target runtimes | Offline contracts include generic, Cursor, Claude, and Codex. | Open live for Cursor and Claude; results from Codex must not imply portability. |
| General fidelity and efficiency | Scoped measurements and content reviews exist; detailed limitations are preserved in the reports below. | Open: there is no general efficiency win or full workflow-equivalence claim, and several frozen formatting/reference checks failed. |

## What the completed consultations show

Keep each model and instrumentation cohort separate. The following counts are
aggregations of existing check outcomes, not a new rubric or a rescore. The
original [frozen rubric](../evaluations/variants/router-quality-rubric.md) and
historical reports are unchanged.

For Astra's 27-session conditional pilot, all three strategies passed 9/9 output
substring contracts. Reference-read passes were canonical 9/9, mandatory 6/9,
and conditional 9/9. Other process checks passed 8/9, 9/9, and 9/9 respectively;
one canonical command-classification failure remains included. Enhanced exact
formatting/quotation checks were not present, so their status is **not assessed**.
Manual review of the nine conditional answers is useful but does not establish
comprehensive content equivalence. See [conditional results](conditional-loading-results.md).

Luna's 48-session four-way batch separates the dimensions as follows:

| Dimension, passes / observations | Canonical | Mandatory | Conditional | Router |
| --- | ---: | ---: | ---: | ---: |
| Human-style content review by primary assistant | 12/12 | 11/12 | 12/12 | 12/12 |
| Output substring contract | 12/12 | 12/12 | 12/12 | 12/12 |
| Frozen format/quotation checks (`quality-*`, all applicable checks per answer) | 8/12 | 8/12 | 6/12 | 8/12 |
| Reference-read checks | 12/12 | 9/12 | 11/12 | 12/12 |
| Other process checks (turn count, invocation, actions) | 12/12 | 11/12 | 11/12 | 12/12 |
| Historical combined automated result | 8/12 | 7/12 | 6/12 | 8/12 |
| Creation, append, and hook workflow | Not assessed | Not assessed | Not assessed | Not assessed |

Content review was neither independent nor fully blinded. The format/quotation
row includes exact traceability and full quoted-item requirements; content passes
do not cancel those failures. The process rows concern consultation traces, not
project workflow. See [Luna results](router-luna-results.md) for the original
per-scenario scores, input/cache/output measurements, latency, and limitations.

Efficiency is workload-dependent. Astra conditional loading saved 2.3% mean
total input on the skip case but used 75.2% and 76.5% more on the loaded cases.
On Luna, the router used 34.4% less on the skip case and 31.8% and 31.4% more on
the loaded cases. These are within-batch scenario comparisons only. A smaller
root does not establish lower runtime input. Uncontrolled cache variation is
not an intrinsic compiler saving, and usage is not observed billing. Neither
batch measures the production frequency of skip/load paths.

## Evidence index and provenance

The following exact paths are relative to the repository root. They are private,
gitignored local evidence, absent from a fresh checkout. Public report links are
provided above; local paths are written as paths so documentation validation does
not depend on private evidence being installed. Do not regenerate the historical
`analysis.json` files or replace completed reports during follow-up work.

| Cohort | Exact local bundle path | Contents and scope |
| --- | --- | --- |
| Astra explicit probe, instrumentation v1 | `evaluations/local-evidence/2026-10-23-codex-probe/` | `report.json`, raw traces and adapter snapshot; four completed sessions, all fidelity failures from the recorded PATH/classification issue. |
| Astra probe, instrumentation v2 | `evaluations/local-evidence/2026-10-23-codex-path-rerun/` | `report.json`, raw traces and adapter snapshot; four sessions, 24/24 current checks. Separate instrumentation cohort. [Probe interpretation](codex-runtime-evidence.md). |
| Astra initial checklist batch | `evaluations/local-evidence/2026-10-23-checklist-live-v1/` | `none/report.json` covers four sessions; one further pair completed in the interrupted one-reference case, one session failed mid-turn, five were never started. No complete repeated report for that partial case. [Initial interpretation](checklist-runtime-benchmark.md). |
| Astra extraction follow-up | `evaluations/local-evidence/2026-10-23-checklist-savings-v2/` | `security/report.json`, `append-policy/report.json`, `some/report.json`, `most/report.json`; sixteen completed sessions, 12/16 combined checks passed. Includes source/package snapshots, raw logs and `analysis.json`. [Follow-up interpretation](checklist-savings-followup.md). |
| Astra conditional comparison | `evaluations/local-evidence/2026-10-23-conditional-three-way/` | Twenty-seven sessions, three strategies × three repetitions × three scenarios. `analysis.json` preserves summary calculations. |
| Stopped Astra router attempt | `evaluations/local-evidence/2026-10-24-router-live/` | `STOPPED.json`, preparation snapshots, and two raw logs: one completed session and one interrupted session. No completed comparison report; excluded from Luna. |
| Luna four-way comparison | `evaluations/local-evidence/2026-10-24-router-luna/` | Forty-eight sessions, four strategies × four repetitions × three scenarios. `analysis.json`, `review-input.json`, `review-key.json`, `semantic-review.json`, and `usage-summary.json` preserve the reviews and calculations. |
| Luna write-capable workflow pilot | `evaluations/local-evidence/2026-10-24-workflow-luna/` | Six approved sessions, original/router × create/append/hooks, no replacements. Frozen `report.json`/`checks.json`, complete raw traces, artifact snapshots, manifests, instrument copies, separate `analysis.json` and `manual-review.json`. [Results and exact provenance layout](workflow-fidelity-results.md). |
| Luna router-v2 workflow follow-up | `evaluations/local-evidence/2026-10-24-workflow-v2-luna/` | Exactly two approved sessions, append then hooks, no retries or additions. Frozen v2 instruments/rubric v3, all raw logs/artifacts/grades, anonymous semantic packet and separate raw review. All 103 collection files retained; 734 prelaunch protected files unchanged. [Results and provenance](workflow-fidelity-v2-results.md). |
| Luna router-v3 workflow follow-up | `evaluations/local-evidence/2026-10-25-workflow-v3-luna/` | Exactly two approved sessions, append then hooks, no retries or additions. Frozen v3 instruments/rubric v4; 1/2 automated passes, targeted reviewed gate fails. All 105 collection files retained; 953 prelaunch protected files unchanged. [Results and provenance](workflow-fidelity-v3-results.md). |
| Luna router-v4 workflow follow-up | `evaluations/local-evidence/2026-10-25-workflow-v4-luna/` | Exactly two approved sessions, append then hooks, no retries or additions. Frozen checker/collector v4, normalizer v3, rubric v5; 0/2 automated passes, 2/2 semantic content passes, targeted gate fails. All 107 collection files retained; 1,394 prelaunch protected files unchanged. [Results and provenance](workflow-fidelity-v4-results.md). |

For **each** conditional and Luna comparison bundle, the three scenario
subdirectories are exactly:

- `checklist-core-security-codex/`
- `checklist-optional-some-codex/`
- `checklist-optional-most-codex/`

Within each is `report.json` (scored observations and provenance),
`preparation.json` (pre-run package provenance), `raw/<trace-id>.jsonl`, and
`raw/<trace-id>.stderr`. `trace-id` is the first 24 hexadecimal characters of
SHA-256 of the report observation's `session_id`. Exact packages are under
`canonical/`, `mandatory/`, `conditional/`, and, for Luna, `router/`.

Read-only verification on 2026-10-24 found all 75 observation JSONL files and
matched every recorded package file hash: 27 file checks across the three
conditional reports and 39 across the three Luna reports. No evidence was
rewritten. The historical result documents record successful schema validation
of all six reports against their respective comparison schema versions; the
read-only review also revalidated all six with the published schemas.

Shared input identities in those six reports:

| Input | SHA-256 |
| --- | --- |
| [Original source](../skills/speckit-checklist/SKILL.md) | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| [Conditional recipe](../recipes/speckit-checklist.conditional.codex.json) | `25f22085ebf5aee5a868f5256b53193bd7b3c6f854e56e977af8a78e5326d96e` |
| [Router review and exact file hashes](../evaluations/variants/speckit-checklist-router.review.json) | `db709963d00c0f2ab50c1615328a0080f708953f99f6a7a67b61ed1d11ceaf6a` |
| Historical frozen rubric | `f8f86cce8e52d6b364146b28302fa0bb697e676a9883f22d99853170194a5f16` |

The shared environment is `codex-cli 0.163.0-alpha.11.1`, `app-server-stdio`,
instrumentation `codex-app-server-explicit-v3`, low reasoning, read-only sandbox,
and approval `never`. Models are `gpt-6-astra` for the conditional batch and
`gpt-6-luna` for the completed router batch. Their underlying snapshots are
unreported. The original package remains unchanged; matching hashes establish
identity, not semantic equivalence.

## Workflow pilot decision and remaining work

The frozen [promotion rubric v2](../evaluations/variants/router-quality-rubric-v2.md)
and [workflow pilot proposal](workflow-fidelity-pilot.md) were retained unchanged.
After explicit approval, the [write-capable collector](workflow-runtime-collector.md)
completed exactly six Luna sessions. Its prelaunch validation passed 207 tests
with 84% coverage. The [results](workflow-fidelity-results.md) separate content,
formatting, reference behavior, workflow and usage. No session was replaced or
added. Final reports preserve all frozen failures; later manual findings are
separate evidence, not rescoring.

The narrow workflow promotion gate fails. Genuine gaps include constitution
loading, usable optional-hook offers, required hook announcements, topic
allocation and missing gap markers; conservative command/count parsing adds
instrument limitations. The semantic review was not blinded as v2 requested,
so that review procedure also remains unsatisfied. The six cases consumed
752,771 total input and 7,854 output tokens; one repetition and uncontrolled
caches cannot establish efficiency or equivalence.

After separate approval, the [versioned follow-up](workflow-fidelity-pilot-v2.md)
completed exactly two Luna sessions using router v2, checker/normalizer v2 and
rubric v3. The [results](workflow-fidelity-v2-results.md) retain **0/2 full frozen
passes**, with content, formatting and reference checks passing in both. Both
read constitution; append preserves every original byte; requested topics and
Gap markers are present. Required hook announcements/offers and sandbox-compatible
writing still fail. Absent-file conditionals and a recovery Python write expose
remaining parser limits; raw review distinguishes them without changing grades.

Usage was 239,966 input and 2,541 output tokens, with no baseline efficiency
comparison. Semantic review used anonymous packets before scores/usage, but the
primary reviewer authored the candidate and knew the design; it is not independent
or fully blind. The two sessions are a diagnostic cohort, not a replacement for
the failed paired pilot or evidence of promotion. All historical packages,
instruments and grades remain frozen. No retries or additional sessions ran.

The trigger/lifecycle/target matrix, replication and promotion criteria remain
open; a small workflow pilot cannot close all of OPT-004. Further live collection
needs separate approval of the exact cases and scope; no further batch is queued.

## V3 repairs and completed follow-up

The [v3 repair and pilot proposal](workflow-fidelity-pilot-v3.md) versions the
remaining fixes without changing either completed workflow cohort. Router v3
moves actual announcement/offer blocks to action checkpoints, prefers native
workspace file edits under restricted temporary-directory permissions, and
grounds reports in returned tool results. Parser/checker v3 address pinned
absence checks, bounded literal Python writes, message timing and final-artifact
verification. Rubric v4 records these prospective changes separately.

Synthetic regressions and fake-server collection validated the instruments and
package contracts before launch: 342 tests passed with 84% coverage. After
separate approval, exactly two fresh Luna sessions completed using the unchanged
tasks and fixtures. The [v3 results](workflow-fidelity-v3-results.md) preserve
**1/2 full automated passes and 0/2 complete reviewed passes**. Both native edits
and final readbacks succeed; append exercises the repaired absence proof and
preserves its existing bytes. No denied checklist write is observed.

Post-hook blocks remain absent, a discovery `ls` fails, and both final reports
contain unsupported narration. The hooks topic keyword screen misses a reuse
paraphrase; semantic review separately flags a presupposed prevention policy.
Frozen failures and separate review judgments are retained without rescoring.
Usage is 264,071 input and 2,482 output tokens; it is not a baseline comparison
or reliability estimate. Review is neither independent nor fully blind.

The original skill, all previous packages, instruments, grades and evidence
remain frozen; leave-inline stays the compiler default and the router remains
experimental. Both authorized slots are consumed, with no retry or expansion.
No further live batch is queued; new live work requires separate approval.

## V4 repairs and completed follow-up

The [v4 proposal](workflow-fidelity-pilot-v4.md) addresses the remaining observed
behavior gaps with an isolated authored router revision: post-hook templates at
the execution checkpoint, grounded reporting, neutral missing-policy questions
and discovery through the existing feature directory. Checker v4 adds bounded
reuse paraphrases with inspectable cues and a limited final-hook-claim evidence
screen. It retains the v3 parser and all prior hard requirements. General
narrative accuracy and policy meaning still require review; no screen can
automatically certify them.

Offline validation passes 373 tests with 84% coverage, plus lint/type/schema/doc
checks. The fresh preparation contains two cases and zero attempts. All 1,321
protected existing files match their starting hashes; historical observations
are not rescored. These checks establish instrument/package readiness only.

After explicit approval, the [v4 results](workflow-fidelity-v4-results.md) record
exactly two completed Luna low sessions, append then creation with synthetic
hooks, with no retries or additions. [Rubric v5](../evaluations/variants/router-quality-rubric-v5.md)
remains frozen. Automated results are **0/2**; separate semantic content passes
**2/2**, but the complete reviewed gate remains **0/2**.

The append's internal Python write/readback preserves bytes and supports its
report, but is outside the frozen parser grammar. Hooks correctly renders post
blocks and executes both automatic markers. It still invents pre-hook blocks,
offers the correct optional pre hook late, skips constitution after a masked
setup failure, and narrates an unrecorded failed invocation. Full reference and
configuration bytes are visible in nonzero compound commands; the normalizer
cannot certify those reads. A singular count modifier also exposes a formatting
screen limit. All original scores remain unchanged.

The batch used 247,946 input and 2,644 output tokens, with no matched baseline
or savings claim. All 107 original files were retained and 1,394 prelaunch
protected files remain unchanged. The next work is new-version offline
regressions and repairs, followed by a separately proposed pilot. Both approved
slots are consumed; no further live batch is queued. Broader replication,
baseline, lifecycle/target and independent-review requirements remain open.
