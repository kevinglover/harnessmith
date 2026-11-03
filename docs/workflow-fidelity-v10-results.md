# Workflow v10 Luna append follow-up — 2026-10-27

Exactly **one approved GPT-6 Luna low session** completed, one turn, with no
retry, replacement, expansion or extra model judge. The frozen automated and
complete reviewed case gates remain **0/1**. Separate content, formatting,
reference behavior, append preservation and final readback pass.

Two unsupported `if test -f` conditionals and the resulting discovery-proof
rejection cause seven automated failures. Raw review also finds a separate
workflow omission: no fresh extension check is recorded after generation,
although the unchanged skill calls for one. All nine shell commands exit zero.
These positive artifact findings do not waive the failed workflow gate.

## Scope and provenance

The user authorized the [v10 proposal](workflow-fidelity-pilot-v10.md):
`append-router-v7-instrument-v10`, with the unchanged original append prompt,
synthetic fixture and router v7, normalizer v9, checker/collector v10 and
[rubric v11](../evaluations/variants/router-quality-rubric-v11.md).
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
| Collector / normalizer | `codex-workflow-stdio-v10` / `codex-workflow-trace-v9` |
| Launch Git HEAD | `78da46ace778b2b6abd61cc53be3c699a00852a3` |
| Original skill SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router-v7 review SHA-256 | `89fc65b25a4b888ab350d88a6988da149b92777aa4a86d18168272eff1539c84` |
| Rubric-v11 SHA-256 | `095a8445455cfce1bacde2f6f245261fb7364b8536a1f5a17b87c36116240466` |
| Prepared/live manifest SHA-256 | `1c8827b901f03c2ad348421d8f7aac4019f5a1deda995e5a018885a1fdf01956` |
| Collector configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |

The manifest pins nine workspace files and 21 prepared instruments; environment
provenance also pins 21 runtime code dependencies. Existing uncommitted v9
results and v10 offline changes are preserved. Prior offline validation records
743 passing tests and 85% coverage, followed by 51 targeted tests and 59 fresh
adversarial probes passing against the final source after type-only annotations.
Completed tests and benchmarks were not rerun for this launch. Read-only
preflight verified the fixed slot, pins, one-attempt guards, deadline and retention.

Collection used workspace-write, network disabled, temporary-directory writes
excluded, non-login shell settings, unrelated skills disabled and a 180-second
deadline. No real project hook was run. Legacy sandbox host reads are not fully
isolated; recorded-path review is not OS tracing or executable attestation.
Dates use America/New_York.

## Separate dimensions

| Dimension | Frozen automation | Separate review |
| --- | --- | --- |
| Content correctness | Pass | Three distinct requirements-quality questions cover measurable expiration/reference clock, expired/reused outcomes and retention/deletion. No policy values invented. |
| Formatting | Pass | Unchecked CHK008–010, bracketed quality/Gap/spec markers, preserved structure and accurate path/count/append/focus/depth/reviewer report. |
| Reference behavior | Pass | Complete pinned generation reference finishes before project actions; unrelated examples are not loaded. |
| Workflow fidelity | Fail | Exact prefix, complete reads, separate operations and final readback are corroborated. Frozen attribution failures remain binding; the post-generation extension checkpoint is separately unverified. |
| Efficiency | Not evaluated | Descriptive one-session usage only; no paired baseline or replication. |

The primary assistant saved semantic judgments from an anonymous prompt/spec/
constitution/before/after/final-report packet before opening its key, grades,
usage or raw trace. The reviewer was an involved author/coordinator who knew the
single-case design; this was neither independent nor fully blinded. A separate
read-only mechanical auditor did not judge the output. No extra model judge ran.
Original pending-review fields remain unchanged; reviews are separate sidecars.

## Frozen failures and unobserved grammar

Coordinates below are **one-based lines in complete `raw/events.jsonl`**,
including sent and received records, not normalized notification indices.

1. **`classified-events` and `successful-events`:** extension probe 100–101 and
   constitution read 219–220 use `if test -f PATH; then cat PATH; else printf …;
   fi`, inside a shell wrapper. This differs from the newly supported
   `if [ -f PATH ]; then cat PATH; else test ! -e PATH && echo ABSENT; fi`.
   The extension returns exactly `ABSENT` plus newline and the constitution
   returns complete pinned contents, both exit zero. The frozen instrument
   rejects both conditionals and grants neither a read nor an absence proof.
2. **`required-context-reads` and `context-before-write`:** the unclassified
   constitution prevents a pass. Its full raw contents finish before writing;
   the specification, template and original checklist also return pinned bytes.
3. **`extension-config-before-setup` and
   `extension-check-isolated-from-other-operations`:** the early extension probe
   is a separate successful command before setup. Pinned absence and its marker
   corroborate state in raw review, without substituting for a frozen certificate.
4. **`context-reads-isolated-from-discovery-and-mutation`:** missing classified
   constitution evidence blocks this gate. Raw reads are separate from setup,
   discovery and editing; all operations are sequential in this sample.

The third normalized issue rejects the standalone discovery action 296–297:
earlier unclassified conditionals leave its prefix uncertain. The command
`rg --files specs/001-invitations` returns the exact two-file inventory from a
known-existing directory, without fallback, redirection or a companion read.
Discovery isolation passes because this rejected listing is unknown, not a
recognized discovery fact. That pass alone is not proof of attribution.

No new certificate is emitted. The guarded-echo grammar, post-append absence
certificate, safe concurrent-read recovery and explicit-null absence adapter
remain **unobserved live**. No successful terminal-discovery certificate is
established. This sample neither disproves their offline controls nor establishes
their live coverage. No command was replayed or historical score recomputed.

## Separate post-generation checkpoint finding

The unchanged router-v7 generation reference, step 8 (lines 324–327), calls for
checking extension configuration after checklist generation. The sole extension
probe is 100–101, before setup. Native append 380–381 and final readback 427–428
are followed by the final report; no fresh extension check is recorded.

The configuration is pinned absent in both snapshots and only the checklist
changes, so no configured hook was missed in this fixture. Those snapshots and
earlier knowledge do not demonstrate performance of the later checkpoint. The
model does not claim to have performed it. The frozen checker has no dedicated
append-case requirement for a fresh post-generation absence check: this is a
separate raw-review finding, not an added criterion or a changed historical grade.

## Successful observations and narration

- Reference 59–60 returns all **26,045 pinned bytes** before project actions.
- Setup 148–154 uses the requested arguments and returns expected feature/spec/
  template JSON, exit zero. Two macOS temporary-directory/cache warning/error
  pairs are retained and accurately reported. No checklist write is denied,
  and no permissions are broadened or failed command retried.
- Constitution 219–220, specification 223–224, template 227–228 and original
  checklist 300–301 return complete pinned bytes before writing. Template
  content also matches the setup JSON.
- Native edit 380–381 appends exactly three questions. All **694 original bytes**,
  reviewer annotation, whitespace, IDs and `[x]` / `[ ]` / `[X]` states remain an
  exact prefix of the **1,156-byte** final file. Final SHA-256:
  `661862287ef34f455221b158ebfb7797b73f33633ecf82ab15a646d224a7c1ed`.
- Separate readback 427–428 returns every final byte before report 432–579;
  no later artifact write occurs.
- All seven completed commentary messages and the final report were reviewed.
  Material early-absence, setup/cache, spec-gap, append and readback claims have
  preceding raw support. No Git comparison, unavailable tool, invented failure,
  hook execution or post-generation check is claimed. Bounded narrative-match
  arrays are empty; these findings come from raw review, not empty matchers.

Only the target checklist changes. This absent-configuration fixture does not
establish router-v7 configured-hook fidelity.

## Usage and retained evidence

| Measure | Value |
| --- | ---: |
| Input tokens | 202,594 |
| Cached input | 180,480 |
| Uncached input | 22,114 |
| Output tokens | 1,480 |
| Collector latency | 26.810 seconds |
| Shell commands / native edits | 9 / 1 |
| Generation-reference reads / separate postwrite reads | 1 / 1 |

Usage is the last cumulative update at raw line 580, not the sum of 11 updates.
It falls within the heuristic planning range; that range was not a hard token
cap. These figures establish no savings, causal improvement, billing or
reliability claim. Luna/Astra and instrument/router versions remain separate.

Original collection: `/private/tmp/opt004-workflow-v10-luna-live-20261027/`.
Private, gitignored [retained bundle](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/README.md):

- [Frozen report](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/report.json),
  [checks](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/append-router-v7-instrument-v10/checks.json)
  and [raw trace](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/append-router-v7-instrument-v10/raw/events.jsonl).
- [Semantic review](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/semantic-review.json),
  [raw review](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/manual-review.json)
  and [analysis](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/analysis.json).
- [Manifest/provenance](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/append-router-v7-instrument-v10/manifest.json),
  [environment](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/environment.json),
  [mechanical integrity review](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/integrity-review.json)
  and [validation](../evaluations/local-evidence/2026-10-27-workflow-v10-luna/validation.json).

All **85 original collection files** retain bytes/modes. Raw paths are unchanged
and relocated observations are not regraded. All **3,607 prelaunch protected
files and two symlinks** remain unchanged. The 584 raw rows comprise five sends
and 579 receives; received records match raw stdout. There is one thread start,
one turn start and one completed turn, no recorded protocol error/reroute, retry
or replacement. Collector exit 1 records the failed automated gate, with null
collector/integrity errors. No auth file is retained.

The mechanical auditor's first version-string comparison omitted the known
`codex-cli ` prefix distinction between CLI output and returned thread metadata.
That initial audit is preserved separately; its corrected comparison passes
all 15 checks. No model result, trace or score changed as a result.

## Remaining work

The approved one-session batch is complete and its authorization is consumed.
If separately requested, next work should begin offline with bounded
`if test -f` / `printf` branch and wrapper-quoting controls, plus an explicit
prospective post-generation checkpoint gate and workflow guidance. Supporting
another parser spelling alone would not close the newly observed workflow gap.
Preserve all historical results and use new versions and synthetic fixtures.
No repair or further live run is authorized by this batch.

Leave inline remains the compiler default. Baselines, replication, independent
output review, hooks/lifecycle and other-runtime coverage remain open. This
sample establishes neither router promotion nor compiler equivalence, and
**OPT-004 remains incomplete**.
