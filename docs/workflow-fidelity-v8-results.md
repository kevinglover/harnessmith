# Workflow v8 Luna append follow-up — 2026-10-26

Exactly **one approved GPT-6 Luna low session** completed, one turn, with no
retry, replacement, expansion or extra model judge. The frozen automated and
complete reviewed case gates remain **0/1**. Separate semantic content,
formatting, reference behavior, append preservation and final readback pass.

The raw trace corroborates successful isolated extension/setup/discovery actions
and all required reads before writing. Seven automated failures arise from
unsupported `else test ! -e` conditionals and conservative overlapping-read rules,
with a downstream rejection of the terminal-discovery certificate. Every shell
command returned exit zero. Preserve these raw findings separately from the
failed grades; this report does not waive or recompute a criterion.

## Approved scope and frozen provenance

The user approved the exact [v8 proposal](workflow-fidelity-pilot-v8.md):
`append-router-v7-instrument-v8`, using the original append prompt and synthetic
fixture, authored router v7, normalizer v7, checker/collector v8 and
[rubric v9](../evaluations/variants/router-quality-rubric-v9.md).
No package, instrument, fixture, original skill or historical evidence changed.
The router is a reviewed semantic redesign, not a proven content-preserving
compiler transformation. No compiler change is made by this run.

| Identity | Recorded value |
| --- | --- |
| Model / effort | `gpt-6-luna` / `low`, validated from returned configuration |
| Harness / mode | `codex-cli 0.163.0-alpha.11.1`, app-server stdio |
| Backend model snapshot | Unreported; requested model name is not an immutable snapshot |
| Collector / normalizer | `codex-workflow-stdio-v8` / `codex-workflow-trace-v7` |
| Original skill SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router-v7 review SHA-256 | `89fc65b25a4b888ab350d88a6988da149b92777aa4a86d18168272eff1539c84` |
| Rubric-v9 SHA-256 | `389ef7c6e367e2606a90e252266e12e4832e69ee23eff4a166c4213e80b31158` |
| Prepared/live manifest SHA-256 | `f1b132c8d0314c1465533645d0f5b15660548cd5b9ddd39073acd2d0fa0e9929` |
| Collector configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |

The manifest pins nine workspace files, source, package, fixtures, prompt and 17
prepared instruments. The environment additionally pins all 17 runtime code
dependencies. The existing 634-test offline validation remains intact; unchanged
tests and completed benchmarks were not rerun. Read-only prelaunch review
verified the fixed slot, one-attempt guards, deadline, pins and retention behavior.

Collection used workspace-write with network disabled, temporary-directory writes
excluded, non-login shell settings, unrelated skills disabled and a 180-second
deadline. No external project, credential or real hook action is recorded. The
legacy sandbox still permits host reads; recorded-path checks are not OS-level
read isolation. No inference is made about invisible provider-internal behavior.

## Separate results

| Dimension | Frozen automation | Separate review |
| --- | --- | --- |
| Content correctness | Pass | Three distinct requirements-quality questions cover measurable expiration/reference point, expired/reused outcomes and retention/deletion. No policy value invented. |
| Formatting | Pass | Unchecked CHK008–010, bracketed quality/Gap/spec markers, preserved structure and complete final path/count/append/focus/depth/reviewer report. |
| Reference behavior | Pass | Complete pinned generation reference finishes before project actions; no unrelated example loads. |
| Workflow fidelity | Fail | Raw evidence corroborates the requested append checkpoints, including isolated checks/discovery, full context, exact prefix and separate readback. Parser/certificate failures remain binding. |
| Efficiency | Not evaluated | One descriptive sample, no paired baseline or replication. |

Semantic review was saved from an anonymous prompt/spec/constitution/before/after/
final-report packet before opening grades, usage, the lookup key or raw trace.
The reviewer was the involved primary assistant and knew the single-case design;
review was neither independent nor fully blinded. The independent prelaunch
auditor did not judge the model output. No additional model judge ran.
Original pending-review fields remain unchanged; semantic and raw judgments are
separate sidecars.

## Failed criteria and raw evidence

All coordinates below are **one-based lines in complete `raw/events.jsonl`**,
including sent and received records, not normalized notification indices.

1. **`classified-events` and `successful-events`:** extension check 103–104 and
   constitution read 215–216 use `if [ -f PATH ]; then cat PATH; else test ! -e
   PATH; fi`. Both exit zero. The extension path is pinned absent, with no stdout;
   the constitution action returns its complete pinned contents. The parser
   rejects the unsupported else-test branch as `unsupported literal output
   command`, including when that branch was not selected. No `else printf` is used.
2. **`required-context-reads` and `context-before-write`:** the constitution read
   above is unclassified. Existing-checklist read 295–297 overlaps spec read
   296–298. Both independent read-only commands return exact pinned bytes and
   complete before the write at 382. The parser marks the first read unknown
   because another operation is still open, then records a missing prewrite
   dependency. This is not evidence that the file was skipped or read after writing.
3. **`extension-config-before-setup` and
   `extension-check-isolated-from-other-operations`:** the raw standalone extension
   conditional finishes successfully before setup 144–150, but its unsupported
   grammar supplies no normalized path/certificate. The gates correctly fail
   under their frozen evidence requirements; physical isolation alone is not a
   certified pass.
4. **`context-reads-isolated-from-discovery-and-mutation`:** missing normalized
   constitution/prewrite-read evidence prevents a pass. Raw commands separate
   required reads from setup, discovery and mutation. The overlapping reads do
   not share an action with mutation or discovery.

The five normalized fidelity issues comprise the two unsupported conditionals,
the read-overlap rejection, its prewrite dependency failure, and a terminal
discovery proof rejection. Instrumentation itself is valid; collector and
integrity errors are null.

The standalone `rg --files specs/001-invitations` at 289–290 returns the exact
two-file listing, exits zero and queries a known-existing directory. There is no
`.pilot` query, stderr redirection, fallback or mixed read/discovery command.
Normalizer v7 nevertheless rejects its certificate because the earlier unknown
conditionals make the prefix uncertain. Thus **no successful new terminal
discovery certificate is established live**. The separate discovery-isolation
gate passes because the rejected listing is represented as unknown, not as a
discovery diagnostic; this pass alone is not proof of attribution or grammar
coverage. A mixed `cat` plus terminal `rg` form is not exercised in this sample.

## Successful observations and narration

- Reference read 58–59 returns all 26,045 pinned bytes before any project command.
- Setup 144–150 uses the exact requested arguments and returns the expected JSON
  plus two known macOS cache-warning pairs, exit zero. Those denied cache writes
  are retained; no checklist write is denied.
- Constitution 215–216, template 293–294, original checklist 295–297 and spec
  296–298 each return exact complete pinned contents before the native edit.
- Native edit 382–383 appends exactly three questions. All **694 original bytes**,
  notes, whitespace, IDs and `[x]` / `[ ]` / `[X]` states are an exact prefix of the
  **1,137-byte** final file. The final SHA-256 is
  `7c1a02ec5682f674b082f3c6ff741c51e57a27e2070e197dfd1261beb36a619d`.
- Separate final read 436–437 returns all final bytes before report 441–607;
  no later artifact write occurs.
- All seven completed commentary messages and the final report were reviewed.
  Absence, setup/cache, principles, prior checklist and completed append/readback
  claims have preceding raw support. No Git comparison, unavailable tool or
  invented execution failure is claimed. All bounded narrative-match arrays are
  empty, so raw review—not absence of a match—supports these conclusions.

Only the target checklist changes. No extension configuration or hook execution
is present; this is not router-v7 hooks fidelity evidence.

## Usage and retained evidence

| Measure | Value |
| --- | ---: |
| Input tokens | 163,744 |
| Cached input | 122,240 |
| Uncached input | 41,504 |
| Output tokens | 1,320 |
| Collector latency | 22.096 seconds |
| Shell commands / native edits | 9 / 1 |
| Generation-reference reads / separate postwrite reads | 1 / 1 |

Usage is the last cumulative update at raw line 608, not a sum of the nine updates.
These figures are not a savings, causal-improvement, billing or reliability claim.
Luna and Astra cohorts and all instrument/router versions remain separate.

Original collection:
`/private/tmp/opt004-workflow-v8-luna-live-20261026/`.
Private, gitignored [retained bundle](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/README.md):

- [Frozen report](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/report.json),
  [checks](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/append-router-v7-instrument-v8/checks.json)
  and [raw trace](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/append-router-v7-instrument-v8/raw/events.jsonl).
- [Semantic review](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/semantic-review.json),
  [raw review](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/manual-review.json)
  and [analysis](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/analysis.json).
- [Manifest/provenance](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/append-router-v7-instrument-v8/manifest.json),
  [environment](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/environment.json)
  and [retention inventory](../evaluations/local-evidence/2026-10-26-workflow-v8-luna/manifest.json).

All **77 original collection files** retain their bytes/modes. Raw paths remain
unchanged and relocated observations are not regraded. All **2,468 prelaunch
protected files and two symlinks** remain unchanged. The 612 raw rows comprise
five sends and 607 receives, with received records exactly matching raw stdout.
There is one thread start, one turn start and one completed turn; no recorded
error/reroute event, collector retry or replacement. No auth file is retained.

## Remaining work

This closes the approved one-session batch. No repair or further live run is
authorized by it. If separately requested, the smallest useful next work is
offline: bounded same-path else-test conditional proofs for both branches,
safe attribution of overlapping independent reads, and transitive discovery
regressions. Continue rejecting unknown/mutating overlap and preserve every
historical grade. Do not steer or rerun the model to manufacture syntax coverage.

Leave inline remains the compiler default. The one sample does not establish
reliability, efficiency, compiler equivalence or router promotion. Baselines,
replication, independent output review, hooks/lifecycle and other-runtime coverage
remain open, so **OPT-004 is not complete**.
