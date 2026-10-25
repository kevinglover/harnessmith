# Six-session Luna workflow fidelity results

On 2026-10-24 all **six approved GPT-6 Luna sessions completed**, with exactly
one model turn per session, no replacement sessions, and no batch expansion.
The frozen automated result is **0/6 full passes**. The narrow pilot promotion
gate did not pass, and OPT-004 remains incomplete. The original skill, router,
prompts, fixtures, rubric and checker were not changed during collection or review.

This implements the [approved pilot](workflow-fidelity-pilot.md) with the
[write-capable collector](workflow-runtime-collector.md). The proposal remains
an unchanged pre-approval record; this report records its execution. The batch
used the original and authored router, not mandatory/conditional extraction.
It is a separate Luna workflow/instrumentation cohort, not pooled with the prior
Luna consultations or any Astra results.

## Separate fidelity dimensions

Counts below retain the frozen check outcomes. Manual review supplements them;
it does not replace failed checks or change `checks.json` or `report.json`.

| Dimension or bounded check | Canonical | Router | Interpretation |
| --- | ---: | ---: | --- |
| Content keyword screens | 3/3 | 3/3 | Screening only; cannot establish meaning. |
| Primary assistant semantic review: requested topic allocation and no invented policy | 3/3 | 2/3 | Router hooks combines expiration/outcomes and duplicates topics in its fourth item. Review limitations below. |
| Frozen artifact formatting checks | 3/3 | 3/3 | Counts, IDs, unchecked new items, question form, traceability and template structure pass. Not a full formatting verdict. |
| Frozen final-report check (stored under workflow) | 0/3 | 0/3 | Numeral/count pattern rejects otherwise readable reporting; failures retained. |
| Frozen reference checks | 3/3 | 0/3 | Original has no extracted references. Router compound reads are unclassified; raw review finds the required generation read in all three. |
| Frozen workflow checks, all applicable checks | 0/3 | 0/3 | Mix of observed omissions, failed operations and conservative classification. |
| Append byte-prefix and checkbox preservation | 1/1 | 1/1 | Existing notes, IDs and mixed `[x]`, `[X]`, `[ ]` states preserved exactly. |
| Mandatory hook execution/completion order and marker artifacts | 1/1 | 1/1 | Pre-hook before setup; post-hook after final write; final hashes match. |
| Required hook announcement/optional-offer blocks | 0/1 | 0/1 | Both omit the usable optional offers and required command blocks. |
| General efficiency | Not established | Not established | One observation per case/variant, uncontrolled caches. |

All six preserve fixture/package inputs, executable modes and allowed file
inventory. No observed command accesses another project or real hooks. These
are artifact/trace checks, not a complete OS file-access audit.

The primary assistant reviewed every final item against the fixture and prompt;
it had already seen strategy and usage labels. This deviates from the v2 rubric's
blinded presentation procedure and limits the semantic findings. A separate
agent independently audited both creation traces/artifacts, also with labels
visible; it did not independently review the other four cases. Neither review
is a blinded validation of the complete pilot. Details and exact item text are
retained in the separate `manual-review.json` sidecar.

## Observed gaps and instrument limitations

The following are model/workflow findings, not merely classification failures:

- **Router append omits the constitution read.** Its complete raw command list
  reads the generation reference, spec, template and existing checklist, but
  never the fixture constitution. Appended bytes nevertheless meet the prompt.
- **Neither hook run provides the optional-hook offers.** Required automatic
  announcements with normalized command IDs are also absent. Canonical says
  optional hooks were offered, but no usable offer appears. Both execute only
  the two eligible automatic markers; optional, disabled and conditional hooks
  are not executed, and no condition evaluation is observed.
- **Router hooks violates the requested one-question-per-topic allocation.**
  CHK002 combines measurable expiration and expired/reused outcomes; CHK004
  repeats roles/expiration/outcome clarity. All topics are mentioned, so the
  keyword screen misses this. No concrete policy values are invented.
- **Creation markup is incomplete.** Canonical CHK001 and router CHK001/CHK003
  omit the `Gap` marker for missing requirements despite the supplied guidance.
  This supplemental formatting finding is outside the frozen artifact assertions;
  their passing scores remain unchanged.
- **Failed operations are retained.** Router create and append each first try a
  heredoc that cannot create a shell temporary file under the no-`/tmp` sandbox.
  They recover within the same turn using file changes or `python3 -c`.
  Canonical hooks also issues an `ls` against the not-yet-created checklist
  directory and receives exit code 1. These are not clean workflow passes.

The trace normalizer rejects compound reads and dynamic write commands when it
cannot safely attribute success to each operation. A shell's final exit code
can mask earlier failures, as both heredoc attempts demonstrate. Raw successful
outputs establish the setup JSON in all six, spec/template context in all six,
and constitution content in five. All three router sessions successfully read
`references/project-generation.md` before project actions; no optional example
or anti-example reference read is observed. Their frozen reference checks still
fail. Full normalized read counts are therefore incomplete, not zero.

All six final reports communicate a full path, operation, item count, focus,
standard depth and reviewer/PR timing. The frozen count regex does not accept
spelled numbers, intervening Markdown, or phrases such as “4 unchecked
requirements-quality questions.” This is an evaluator limitation, not evidence
that these facts were absent. No post-run patch or regrade was applied.

The sandbox's legacy schema permits host reads. The prompt bounds scope and
the collector rejects recorded outside reads; this is weaker than OS-enforced
read confinement. OS preflight verified workspace writes succeed and outside,
`/tmp` and socket operations are denied. Python also prints macOS cache warnings
while returning valid setup/marker JSON. These environment effects and model
recoveries are preserved, not silently corrected or rerun.

## Usage and scope

Requested model `gpt-6-luna`, low reasoning; CLI `0.163.0-alpha.11.1`,
`app-server-stdio`, instrumentation `codex-workflow-stdio-v1`. Backend snapshot
is unreported. Each session has one cumulative token total, used once.

| Session, in execution order | Total input | Cached input | Uncached input | Output | Elapsed ms | Completed shell commands |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| create-canonical | 122,352 | 102,784 | 19,568 | 1,165 | 15,774 | 5 |
| create-router | 130,393 | 111,104 | 19,289 | 1,816 | 25,336 | 5 |
| append-router | 79,465 | 61,056 | 18,409 | 1,079 | 14,199 | 4 |
| append-canonical | 163,712 | 141,568 | 22,144 | 1,169 | 19,013 | 5 |
| hooks-canonical | 123,870 | 94,976 | 28,894 | 1,291 | 18,383 | 9 |
| hooks-router | 132,979 | 96,000 | 36,979 | 1,334 | 19,812 | 6 |
| Total | **752,771** | **607,488** | **145,283** | **7,854** | **112,517** | **34** |

Shell counts include failed operations and do not count file-change tools; six
completed file-change items are additionally retained. A command may contain
multiple reads. The generation reference appears once in each router trace.
No distribution, repeatability, workload weighting or saving can be inferred
from one observation per cell. The input total exceeds the pre-run heuristic
allowance of 240,000–600,000; that estimate was not a token cap. Output is within
the 6,000–18,000 allowance. These are usage measurements, not billing.

## Evidence, provenance and validation

The complete private, gitignored bundle is
`evaluations/local-evidence/2026-10-24-workflow-luna/`. It is absent from a fresh
checkout. The original collection directory is
`/private/tmp/opt004-workflow-luna-live-20261024/`; absolute paths in transcripts
refer there. All 229 original bundle files match the retained copy byte for
byte. Do not rerun checks against relocated paths or overwrite old reports.

- `environment.json`, `preparation.json`, `batch-events.jsonl`, `report.json`:
  configuration, approved/attempted slots, complete results and no unused slots.
  `preparation.json`'s zero live count records preparation time; the final report
  and six `turn/start` requests record actual execution.
- Each of `create-canonical`, `create-router`, `append-router`,
  `append-canonical`, `hooks-canonical`, `hooks-router` contains `manifest.json`,
  `prompt.md`, attempt records, `raw/events.jsonl`, exact stdout/stderr,
  before/after snapshots and inventories, `observation.json`, `checks.json`,
  and `result.json`. Raw JSONL line references in `manual-review.json` resolve
  to these unchanged traces.
- `instrument/` preserves collector modules, checker, rubric and pilot config.
  `analysis.json` records usage/frozen failures; `manual-review.json` records
  supplemental interpretation without replacing them. `integrity-review.json`
  records the read-only provenance checks.
- `sandbox-preflight/` retains the non-model OS permission probe.
  `offline-tests.log` retains the prelaunch **207 passing tests**, including
  18 fixture, 18 normalizer and 8 collector tests. Coverage was **84%**; Ruff,
  mypy, schema and documentation checks passed before launch.

Every manifest pins prompt, fixtures, source, package, router review, checker,
rubric and configuration. `recipe_sha256` is explicitly null because these
are original/authored packages. Source SHA-256 remains
`1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45`;
rubric v2 is `f4f471bc4eb9acb0e16ecc39fc06a48e052eb8795fa3bc30077031124952512a`;
checker is `bea13fc258aa01bb1554a0768baee17edc88fd9a8a70c062ba535e73557d496d`.
All 429 protected content files match the prelaunch inventory. The only changed
entry among 430 tracked hashes is the parent directory's Finder `.DS_Store`
metadata; it was not restored or treated as experiment evidence.

## Decision after the approved batch

The [v2 promotion gate](../evaluations/variants/router-quality-rubric-v2.md)
remains blocked. Append preservation and automatic-hook ordering now have narrow
live evidence; full workflow fidelity, blinded semantic review and replication
remain open. The router remains an authored semantic redesign. Compiler defaults
continue to leave content inline; root reduction is not proof of runtime savings.

The next useful work is offline: design a versioned normalizer/checker revision
with adversarial controls for compound success/failure and count formatting,
and review explicit constitution/optional-offer/topic-allocation requirements.
Any changed grader must retain and compare the old outcomes. No new instrument,
skill variant or live batch was substituted after these results. Further live
sessions require a new exact scope and approval; none are launched or queued.
