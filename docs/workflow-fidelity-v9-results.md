# Workflow v9 Luna append follow-up — 2026-10-26

Exactly **one approved GPT-6 Luna low session** completed, one turn, with no
retry, replacement, expansion or extra model judge. The frozen automated and
complete reviewed case gates remain **0/1**. Separate semantic content,
formatting, reference behavior, append preservation and final readback pass.

Raw review corroborates the requested append checkpoints. The model used a
same-path conditional with `else test ! -e PATH && echo ABSENT`, outside the
frozen parser's new grammar. Three unclassified conditionals and a downstream
discovery-certificate rejection cause seven failed criteria. All nine shell
commands exit zero. These positive raw findings do not waive the failed gates.

## Scope and provenance

The user authorized the pending [v9 proposal](workflow-fidelity-pilot-v9.md):
`append-router-v7-instrument-v9`, using the unchanged original append prompt,
synthetic fixture and router v7, normalizer v8, checker/collector v9 and
[rubric v10](../evaluations/variants/router-quality-rubric-v10.md).
The proposal and rubric remain frozen prelaunch records; this report records
their subsequently approved execution. Earlier authorizations remain consumed.
No original skill, router, instrument, fixture or historical evidence changed.
The router remains a reviewed semantic redesign, not a proven content-preserving
compiler transformation. No compiler change is made by this run.

| Identity | Recorded value |
| --- | --- |
| Model / effort | `gpt-6-luna` / `low`, validated from returned configuration |
| Harness / mode | `codex-cli 0.163.0-alpha.11.1`, app-server stdio |
| Backend model snapshot | Unreported; model name is not an immutable snapshot |
| Collector / normalizer | `codex-workflow-stdio-v9` / `codex-workflow-trace-v8` |
| Launch Git HEAD | `78da46ace778b2b6abd61cc53be3c699a00852a3` |
| Original skill SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router-v7 review SHA-256 | `89fc65b25a4b888ab350d88a6988da149b92777aa4a86d18168272eff1539c84` |
| Rubric-v10 SHA-256 | `010f37c67918796b9cdca96d0b5d2f642dece883b7994c37cf4b18c9f031ef3c` |
| Prepared/live manifest SHA-256 | `f99670185dc952703e741b5e484d8c60790d6db2a064d63ceab7ebc7e50e6aeb` |
| Collector configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |

The manifest pins nine workspace files and 19 prepared instruments; environment
provenance also pins 19 runtime code dependencies. The committed 692-test,
85%-coverage validation includes the approved documentation-checker portability
fix; the v9 offline candidate's earlier 684-test record stays unchanged. Completed
tests and benchmarks were not rerun for this launch. Read-only preflight verified
the fixed slot, pins, one-attempt guards, deadline and failure retention.

Collection used workspace-write, network disabled, temporary-directory writes
excluded, non-login shell settings, unrelated skills disabled and a 180-second
deadline. No external project, credential or real hook action is recorded. The
legacy sandbox still permits host reads; recorded-path review is not OS-level
read isolation. Dates use America/New_York; the UTC completion timestamp falls
on October 27.

## Separate dimensions

| Dimension | Frozen automation | Separate review |
| --- | --- | --- |
| Content correctness | Pass | Three distinct requirements-quality questions cover measurable expiration/reference clock, expired/reused outcomes and retention/deletion. No policy values invented. |
| Formatting | Pass | Unchecked CHK008–010, bracketed quality/Gap/spec markers, preserved structure and accurate path/count/append/focus/depth/reviewer report. |
| Reference behavior | Pass | Complete pinned generation reference finishes before project actions; unrelated examples are not loaded. |
| Workflow fidelity | Fail | Raw checks, reads, ordering, command separation, prefix and separate readback are corroborated; frozen parser/certificate failures remain binding. |
| Efficiency | Not evaluated | Descriptive one-session usage only; no paired baseline or replication. |

The primary assistant saved semantic judgments from an anonymous prompt/spec/
constitution/before/after/final-report packet before opening its key, grades,
usage or raw trace. The reviewer was an involved author/coordinator who knew the
single-case design; this was neither independent nor fully blinded. Separate
read-only preflight and integrity auditors did not judge the output. No extra
model judge ran. Original pending-review fields remain unchanged; review findings
are retained in separate sidecars.

## Failed criteria and grammar coverage

Coordinates below are **one-based lines in complete `raw/events.jsonl`**,
including sent and received records, not normalized notification indices.

1. **`classified-events` and `successful-events`:** extension checks 88–89 and
   446–447, and constitution read 204–205, use
   `if [ -f PATH ]; then cat PATH; else test ! -e PATH && echo ABSENT; fi`.
   The three path tokens match within each command. Both extension probes return
   `ABSENT` after the successful absence test; the constitution returns all pinned
   contents from its present branch. All exit zero, but the extra guarded echo
   yields `unsupported operator in simple command`, including for the unused
   constitution else branch. No frozen certificate is granted.
2. **`required-context-reads` and `context-before-write`:** the unclassified
   constitution prevents a pass. Its raw contents complete before writing;
   the specification and original checklist also return complete pinned bytes.
   There are no overlapping operations or late reads in this sample.
3. **`extension-config-before-setup` and
   `extension-check-isolated-from-other-operations`:** both raw extension probes
   are separate successful actions, and the first finishes before setup.
   Pinned absence and the guarded marker corroborate absence on raw review,
   but cannot substitute for the frozen normalized certificate.
4. **`context-reads-isolated-from-discovery-and-mutation`:** missing classified
   constitution evidence blocks this gate. Raw context reads are separate from
   setup, discovery and editing.

The fourth normalized issue rejects the standalone discovery action 283–284:
earlier unclassified conditionals leave its prefix uncertain. The command
`rg --files specs/001-invitations` returns the exact two-file inventory from a
known-existing directory, without a fallback, redirection or companion read.
The discovery-isolation check passes because this rejected listing is unknown,
not a recognized discovery fact. That pass alone is not proof of attribution.

The newly supported exact `else test ! -e PATH` grammar, explicit-null absence
adapter and concurrent-read rules are **unobserved live** in this sample. The
guarded echo form is different; all operations are sequential and both absence
results are text. No successful terminal-discovery certificate is established.
The result does not disprove the offline controls or establish their live
coverage. No trace is replayed, command executed by the reviewer or score changed.

## Successful observations and narration

- Reference 60–61 returns all **26,045 pinned bytes** before any project action.
- Setup 130–136 uses the exact requested arguments and returns the expected
  feature/spec/template JSON, exit zero. Its two macOS temporary-directory/cache
  warning/error pairs are retained and accurately reported. No checklist write
  is denied; the model does not retry or broaden permissions.
- Constitution 204–205, specification 208–209 and original checklist 287–288
  return exact complete pinned bytes. Template content is returned in the setup
  JSON and matches its pin; no separate template read is claimed.
- Native edit 349–350 appends exactly three questions. All **694 original bytes**,
  reviewer annotation, whitespace, IDs and `[x]` / `[ ]` / `[X]` states remain an
  exact prefix of the **1,140-byte** final file. Final SHA-256:
  `87670e97b41cef6817b253b17f5ab1d6fb5c5c40c28c76ee5eeb495c2527d93a`.
- Separate readback 392–393 returns every final byte before report 451–657;
  no later artifact write occurs. A second isolated extension probe follows.
- All eight completed commentary messages and the final report were reviewed.
  Material absence, setup/cache, spec-gap, append and readback claims have prior
  raw support. No Git comparison, invented execution failure, unavailable tool
  or hook execution is claimed. All bounded narrative-match arrays are empty;
  these conclusions come from raw review, not empty matcher results.

Only the target checklist changes. No extension configuration or hook execution
is present, so this does not establish router-v7 hooks fidelity.

## Usage and retained evidence

| Measure | Value |
| --- | ---: |
| Input tokens | 201,255 |
| Cached input | 179,584 |
| Uncached input | 21,671 |
| Output tokens | 1,298 |
| Collector latency | 22.383 seconds |
| Shell commands / native edits | 9 / 1 |
| Generation-reference reads / separate postwrite reads | 1 / 1 |

Usage is the last cumulative update at raw line 658, not the sum of 11 updates.
Input is slightly above the heuristic 100–200k planning range, which was not a
hard cap. These figures establish no savings, causal improvement, billing or
reliability claim. Luna/Astra and instrument/router versions remain separate.

Original collection: `/private/tmp/opt004-workflow-v9-luna-live-20261026/`.
Private, gitignored [retained bundle](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/README.md):

- [Frozen report](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/report.json),
  [checks](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/append-router-v7-instrument-v9/checks.json)
  and [raw trace](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/append-router-v7-instrument-v9/raw/events.jsonl).
- [Semantic review](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/semantic-review.json),
  [raw review](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/manual-review.json)
  and [analysis](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/analysis.json).
- [Manifest/provenance](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/append-router-v7-instrument-v9/manifest.json),
  [environment](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/environment.json),
  [mechanical integrity review](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/integrity-review.json)
  and [validation](../evaluations/local-evidence/2026-10-26-workflow-v9-luna/validation.json).

All **81 original collection files** retain bytes/modes. Raw paths are unchanged
and relocated observations are not regraded. All **3,099 prelaunch protected
files and two symlinks** remain unchanged. The 662 raw rows comprise five sends
and 657 receives; received records match raw stdout. There is one thread start,
one turn start and one completed turn, no recorded error/reroute event, retry or
replacement. Collector exit 1 records the failed automated gate, with null
collector/integrity errors. No auth file is retained.

## Remaining work

The approved one-session batch is complete; its authorization is consumed.
If separately requested, the smallest useful next work is an offline bounded
certificate for the same-path conditional's `test ! -e` plus literal marker,
covering both branches and downstream discovery. Controls should reject a
mismatched path, unguarded marker, failed test, wrong/noisy output, extra operation,
mutation or unsafe overlap. Preserve all historical failures and use fresh
synthetic fixtures. No repair or additional live run is authorized by this batch.

Leave inline remains the compiler default. Baselines, replication, independent
output review, hooks/lifecycle and other-runtime coverage remain open. This
sample establishes neither router promotion nor compiler equivalence, and
**OPT-004 remains incomplete**.
