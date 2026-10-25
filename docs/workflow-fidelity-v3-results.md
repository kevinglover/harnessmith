# Two-session workflow follow-up: Luna and router v3

The approved v3 pilot completed on **2026-10-25 local time**: exactly two fresh
GPT-6 Luna sessions, append then creation with hooks, one turn each, **zero
retries and no added sessions**. Both completed; every result is retained.
**1/2 passes all frozen automated checks; 0/2 passes the complete reviewed
diagnostic.** The targeted gate fails, OPT-004 remains incomplete, and the
router remains experimental.

This is the execution record for the unchanged
[v3 proposal](workflow-fidelity-pilot-v3.md), using router v3,
checker/normalizer/collector v3 and
[rubric v4](../evaluations/variants/router-quality-rubric-v4.md). The proposal
remains a historical preapproval document. The earlier
[six-session cohort](workflow-fidelity-results.md) and
[v2 follow-up](workflow-fidelity-v2-results.md) retain their original results.
No code, package, rubric or frozen grade was changed after collection. These
cohorts and the Astra/Luna consultation results are not pooled. The router is
an authored semantic redesign, not a proven content-preserving compiler transform.

## Separate outcomes

| Dimension | Append | Creation with hooks | Interpretation |
| --- | --- | --- | --- |
| Frozen content screen | Pass | Fail | The hooks topic-allocation keyword screen misses a paraphrase of reuse; preserve the failure. |
| Semantic content review | Pass | Fail | Topic allocation passes both; hooks CHK001 presupposes a cross-workspace prevention policy absent from the fixture. |
| Formatting | Pass | Pass | Exact IDs/counts, unchecked states, template structure, questions, traceability, Gap markers and final-report fields pass. |
| Reference behavior | Pass | Pass | Full project-generation reference loaded once before project actions; neither loads example references. |
| Frozen workflow | Pass | Fail | Hooks omits post-phase blocks and runs one unsuccessful directory listing. |
| Raw narrative review | Fail | Fail | Append makes an unverified Git-comparison availability claim; hooks falsely claims the optional post offer was displayed. |
| Efficiency | Not evaluated | Not evaluated | Usage is descriptive; no matched baseline or replication. |

Both sessions use a successful native file edit and return the complete final
artifact in a subsequent standalone read. Both read constitution, spec and
template before writing. Append preserves every original byte, including the
reviewer annotation and `[x]`, `[X]`, and `[ ]` states, and adds CHK008–010.
Creation produces four unchecked items, CHK001–004. No denied checklist write
or heredoc attempt appears in either trace. These are observations in two
samples, not reliability or causal improvement estimates.

Anonymous artifact packets were reviewed before opening their lookup key,
scores, usage or raw traces. The primary assistant authored the candidate with
subagents, knew the single-variant design and nonzero collector exit, and could
infer cases from their artifacts. The review is neither independent nor fully
blind. No extra model judge session ran. Subsequent raw review is stored
separately. Original `pending-review` fields remain untouched; review outcomes
live in sidecars, not rewritten collector results.

## Raw behavior and remaining gaps

Line numbers below are one-based in each session's `raw/events.jsonl`, including
send and receive records. Normalized indices use a different coordinate system.
`manual-review.json` retains exact item IDs and start/completion lines.

**Append.** Generation guidance completes at line 53. The compound context
command at line 107 returns prerequisite JSON, constitution, template, spec
and the existing checklist. Its no-else checks of the pinned absent `plan.md`
and `tasks.md` are now supported by the v3 absence proof. No unknown or failed
workflow event is recorded. The native update completes at line 194; the exact
final artifact read completes at line 200. All frozen checks pass.

The final answer at line 368 nevertheless asserts that comparing against Git
was unavailable because the workspace is not a Git repository. The collector
returned `gitInfo: null`, but the trace contains no Git comparison command or
Git error. This is an unverified environmental inference, not a demonstrated
command failure or a proven-false assertion. Under rubric v4's requirement that
unsupported narration fails reviewed workflow, the narrative criterion fails.
Do not add a fictitious failed Git command to the action count. The append
preservation and reported setup cache diagnostics are corroborated.

**Creation with hooks.** Guidance and configuration are returned at line 74.
Actual automatic-pre and optional-pre blocks finish at line 195, with the
configured IDs, descriptions and optional prompt. The automatic pre marker
completes at line 197 before setup at line 241. Constitution, spec and template
finish at line 245. The native creation completes at line 299 and full artifact
read at line 305. The automatic post marker at line 360 records the exact final
artifact hash, before the final answer at line 504. Only the two permitted
synthetic automatic hooks run; no optional, disabled or conditional invocation
or condition evaluation is observed.

The remaining failures are distinct:

- Line 355 promises to render post-hook blocks, but no actual automatic-post
  announcement or optional-post offer appears before invocation. The final
  claim that both optional hooks were offered is incorrect. Pre-phase compliance
  does not substitute for post-phase compliance.
- `ls -la specs/001-invitations/checklists` at line 295 returns exit 1 because
  the directory does not yet exist. This is one real discovery failure, not a
  sandbox write denial or parser false positive. Two normalized unknown events
  and four issue records refer to this same command. Frozen `classified-events`
  and `successful-events` fail; do not count these as multiple failed commands.
- The frozen topic heuristic rejects CHK003's “invitations accepted again after
  use” wording because it lacks its expected reuse keyword. Semantic review
  finds the requested reuse topic present. This instrument limitation remains
  recorded without changing the frozen content-screen failure.
- Independently, semantic review fails CHK001: “boundaries preventing invitations
  across workspaces” presupposes prevention, while FR-1 leaves cross-workspace
  handling unspecified. The Gap marker does not remove that presupposition.
  This is a disclosed primary-review judgment under the inherited no-invented-
  policy/exclusivity criterion, not the keyword failure's rationale.

Thus the three frozen workflow failures are `classified-events`,
`successful-events`, and `hook-announcements`. Context/order, markers, final
artifact verification and final-report-after-hooks checks pass. All frozen
failures remain in the report.

Exact known macOS cache-write errors/warnings accompany successful JSON results
from the pinned synthetic adapters. They remain retained diagnostics; the claim
of no denied **checklist** write does not imply that no cache write was denied.
The bounded literal-Python-write parser was validated offline but was not
exercised by these native-edit sessions.

## Measured scope

| Session | Total input | Cached input | Uncached input | Output | Collector latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `append-router-v3` | 85,029 | 65,024 | 20,005 | 1,167 | 18.087 s |
| `hooks-router-v3` | 179,042 | 157,824 | 21,218 | 1,315 | 22.049 s |
| Batch accounting | **264,071** | **222,848** | **41,223** | **2,482** | **40.136 s** |

Usage uses the last cumulative event per session, not the sum of repeated
cumulative events. Uncached input is total minus cached input; latency is the
collector's per-session field. Shell command counts are three and seven, with
one native file edit each. Each has six normalized read events, including its
single generation-reference read. All completed calls and the one unsuccessful
directory listing are retained.

The batch falls within the proposal's 200–400k input and 2–6k output scope
estimate. Caches were uncontrolled. These figures do not measure billing,
efficiency, equivalence or an improvement over the previous cohorts. Root size
does not prove runtime savings.

## Provenance and retention

The private, gitignored bundle is
`evaluations/local-evidence/2026-10-25-workflow-v3-luna/`, absent from a fresh
checkout. Its README indexes:

- `report.json`, `environment.json`, `preparation.json`, `batch-events.jsonl`
  and `launch.log`: both attempts, settings and collection outcome.
- `append-router-v3/` and `hooks-router-v3/`: prompts, manifests, attempts,
  observations, frozen checks/results, raw JSONL/stdout/stderr, inventories and
  complete before/after/workspace snapshots, including hidden files.
- `instrument/`: frozen collector, inherited dependencies, parser/checker,
  pilot and rubric. Manifests pin original source, authored package/review,
  synthetic fixtures and prompt hashes; recipe identity is explicitly null.
- `review-input.json`, `review-key.json`, `semantic-review.json`,
  `manual-review.json` and `analysis.json`: anonymous packet, separate reviews
  and accounting; no historical rescore.
- `collection-copy-integrity.json` and `integrity-review.json`: all **105**
  original collection files copied byte-for-byte and all **953** prelaunch
  protected content files unchanged, including historical evidence, original
  skill and frozen v3 sources. New review/report files are additions.

The source collection remains at
`/private/tmp/opt004-workflow-v3-luna-live-20261025/`. Absolute trace paths still
refer there; they are not rewritten for the retained copy. Relocated workspaces
were not regraded. No result, failure, or raw trace was discarded.

| Identity | Recorded value |
| --- | --- |
| Model and reasoning | `gpt-6-luna`, low; backend snapshot unreported |
| Harness and mode | `codex-cli 0.163.0-alpha.11.1`, `app-server-stdio` |
| Instrumentation | `codex-workflow-stdio-v3` |
| Configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |
| Original source SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router v3 review SHA-256 | `6a56ac384ee1389c65895e51b056f864cf49a346a2237d054448c01d6a3807e2` |
| Rubric v4 SHA-256 | `03dde814ac6b5dce2263f1f19887a99555fc4d9c95ccfe081281ff5b1ff5f3c8` |

Before each turn, the collector validated workspace writes, disabled network,
approval `never`, excluded temporary-directory writes and disabled unrelated
skills. No real project hook was used. The legacy sandbox permits host reads;
recorded read-scope checks and inventories pass, but this is not OS-level read
isolation or a complete file-access audit.

Prelaunch validation was **342 tests passed, 84% coverage**, with ruff, mypy,
schema and documentation checks passing. Protected source hashes matched before
launch and after collection. Documentation/schema checks and retention audits
were repeated for this report; unchanged unit tests and completed benchmarks
were not rerun. The collector exited 1 for the retained failed checks, with
neither collector nor integrity errors.

## Decision

The targeted diagnostic fails. Keep OPT-004 open, leave inline as the compiler
default and retain the router as experimental. Post-hook rendering, grounded
narration and policy-neutral wording remain behavior gaps; the reuse keyword
screen remains an instrument limit. Any repairs need new versions and offline
controls before another separately approved pilot. Broader lifecycle/target
coverage, baseline fidelity, replication and independent review remain open.

The exact two-session authorization is consumed. No retry, expansion or further
live batch is queued.
