# Workflow v11 Luna append follow-up — 2026-11-02

Exactly **one approved GPT-6 Luna low session** completed, one turn, with no
retry, replacement, expansion, baseline, hooks rerun or extra model judge.
The frozen automated and complete reviewed case gates are **0/1**. Content,
formatting, reference behavior, exact prefix preservation and separate final
readback pass. A fresh post-generation extension check is recorded this time,
but its null output earns no qualifying proof under the frozen v11 gate.

Three Python verification commands and a `tail | od` inspection fall outside
the frozen parser's supported forms. Denied macOS cache-file diagnostics remain
failures in the unsupported Python envelopes. All 14 shell commands nevertheless
exit zero. These raw findings do not waive the three failed workflow criteria.

## Scope and provenance

The user explicitly approved the [v11 proposal](workflow-fidelity-pilot-v11.md)
in the new follow-up chat after its readiness review. The exact slot was
`append-router-v8-instrument-v11`: authored router v8, normalizer v10,
checker/collector v11 and [rubric v12](../evaluations/variants/router-quality-rubric-v12.md).
The original append prompt and synthetic fixture were unchanged. The proposal,
rubric, prior results and instruments remain frozen; their pending-approval
language records their prelaunch state. This report records the later execution.

| Identity | Recorded value |
| --- | --- |
| Model / effort | `gpt-6-luna` / `low`, validated from returned configuration |
| Harness / mode | `codex-cli 0.164.0-alpha.11.1`, app-server stdio |
| Backend model snapshot | Unreported; the model name is not an immutable snapshot |
| Collector / normalizer | `codex-workflow-stdio-v11` / `codex-workflow-trace-v10` |
| Launch Git HEAD | `9cb10831497103fc9b7b9dd1e0987204f660cd0d` |
| Original skill SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router-v8 review SHA-256 | `975fd65a76a6e82b43fa8d9123858ec04754941f6cc0fec0fe6510c310d18624` |
| Prepared/live manifest SHA-256 | `17257317d0f77ee6cf377d9d9ff2cb9aec395941c736b97da8fae0a64a9db5f2` |
| Collector configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |

The previous temporary preparation directory no longer existed. A fresh offline
preparation matched the archived manifest byte for byte: nine workspace files
and 23 pinned instruments, with zero attempts before launch. The live collector
then prepared its own new directory with the same manifest and additionally
pinned 23 runtime code dependencies. The preserved offline bundle was untouched.

The installed CLI had changed from `0.163` to `0.164` since v10. This was disclosed
before launch. Its generated protocol schema retained the required legacy
fields. A credential-free, non-model sandbox check confirmed workspace writes
and denied outside-workspace writes, `/tmp` writes and socket access. Its actual
logs, including macOS cache diagnostics, are retained. No protocol, instrument,
fixture or model substitution was made to accommodate the CLI update.

Collection kept workspace-only writes, network disabled, unrelated skills and
multi-agent tools disabled, non-login shell settings, approval `never` and the
180-second deadline. Legacy sandbox host reads remain OS-permitted; recorded
actions are not OS file-access tracing or executable attestation. No real hook
or original-skill edit occurred. User-facing dates use America/New_York.

The exact merged snapshot had already passed 785 tests with 85% coverage,
Ruff, mypy across 64 source files, repository checks, builds and wheel smoke
checks. All eight CI jobs passed on the launch commit after the Python 3.9 runner
fix. Those completed checks were not rerun for this pilot. Only the new CLI
compatibility/sandbox concern, preparation pins and preservation were checked.

## Separate dimensions

| Dimension | Frozen automation | Separate review |
| --- | --- | --- |
| Content correctness | Pass | Three distinct requirements-quality questions cover quantified expiration/reference clock, expired/reused outcomes and retention/deletion; no policy values invented. |
| Formatting | Pass | Unchecked CHK008–010, bracketed quality/Gap/spec markers, preserved structure and accurate path/count/append/focus/depth/reviewer report. |
| Reference behavior | Pass | Complete pinned generation reference precedes every project action; unrelated examples are not loaded. |
| Workflow fidelity | Fail | Exact prefix, context, native append, separate readback and a fresh isolated extension action are corroborated; classification and the new proof gate still fail. |
| Efficiency | Not evaluated | One-session usage only, above the input planning range; no baseline, replication or savings conclusion. |

The primary assistant saved judgments from an anonymous prompt/spec/constitution/
before/after/final-report packet before opening its key, grades, usage or raw
trace. The assistant was an involved coordinator who knew the case and candidate;
this was neither independent nor fully blinded. A separate mechanical auditor
checked integrity, not output quality. No extra model judge ran. Original
pending-review fields remain unchanged; reviews are separate sidecars.

## Frozen failures and separate raw findings

Coordinates below are **one-based lines in complete `raw/events.jsonl`**,
including sent and received records, not normalized notification indices.

1. **`classified-events`:** Python target inspections at 93–94 and 97–98,
   the final-newline pipeline at 101–102, and Python prefix verification at
   116–117 are unsupported by the frozen grammar. Raw inspection shows target
   reads, byte/hash/suffix calculations and printed results; no captured command
   was replayed. The final extension conditional at 121–122 is also unclassified.
2. **`successful-events`:** the three unsupported Python commands contain real
   denied `/tmp/xcrun_db-*` cache-file creation diagnostics. Unlike the recognized
   setup stub, these unknown envelopes do not qualify for the bounded cache-warning
   exemption. The frozen normalizer retains three failed constituent facts even
   though all shell exit codes are zero. There was no denied checklist write,
   permission expansion or failed shell exit.
3. **`fresh-post-generation-extension-checkpoint`:** the separate final probe
   at 121–122 uses `if [ -f PATH ]; then cat PATH; else test ! -e PATH; fi`,
   exits zero and returns explicitly null output. It has no qualifying
   post-append absence certificate. The frozen v11 gate requires `ABSENT` plus
   newline and a supported proof accounting for the append and full readback;
   null output and earlier unknown operations cannot supply that proof.

There are 11 retained normalized issues across these operations. No failure
is removed and no new certificate is manufactured during review. Passing
isolation checks do not certify unclassified operations that those checks do
not recognize.

Unlike the missing action in v10, the v11 post-generation action **was performed**
after the final write, complete readback and additional prefix comparison, and
before the report began. Pinned absence in both snapshots and the target-only
append corroborate fixture state. This is positive raw evidence of that action,
separate from failure to satisfy the frozen instrument's proof contract. It
does not establish configured-hook fidelity or justify changing either grade.

## Successful observations and coverage limits

- Reference 56–57 returns all pinned generation-reference bytes before project
  activity. Early extension check 60–61 completes before separate setup 64–70.
- The early null-output absence probe earns the inherited trace-v8
  `literal-else-test` certificate. The explicit-null backing adapter admits
  exactly that command without altering the captured observation.
- Constitution 73–74 earns the inherited present-file conditional certificate;
  specification 77–78, original checklist 85–86 and template 89–90 return
  complete pinned bytes before writing. The setup JSON also contains the exact
  template and expected feature path/document list.
- Standalone discovery 81–82 returns the expected two-file inventory and earns
  an inherited terminal-discovery certificate.
- Native append 105–106 preserves all **694 original bytes**, reviewer notes,
  whitespace, IDs and `[x]` / `[ ]` / `[X]` states as an exact prefix of the
  **1,170-byte** final file. Final SHA-256:
  `d49a583a0d6763520e5b97ec9df07270a1eb273a4b8824fbd383cf7d05531ae7`.
- Separate readback 111–112 returns every final byte. Additional comparison
  116–117 embeds the exact original byte literal and reports a matching prefix,
  the correct new IDs and unchecked states. Raw inspection supports the final
  preservation claim despite the parser's inability to attribute that Python form.
- All 15 operations are sequential: 14 shell commands and one native edit.
  The opening commentary is future intent; the final report's artifact claims
  have prior support. No Git comparison, hook execution, clean-error assertion
  or completed extension-check claim is made. Both completed messages were
  reviewed; empty bounded narrative-match arrays alone prove nothing.

The new `if test -f` / `printf` grammar was **not chosen**, so its live coverage
remains unobserved. No qualifying post-append absence certificate is emitted.
The inherited early null-output adapter, conditional constitution read and
terminal-discovery proof are observed in this sample. Concurrent-read recovery
is unobserved. These findings are kept separate by model, router, instrument
version and CLI version; no rerun manufactures missing coverage.

## Usage and retained evidence

| Measure | Value |
| --- | ---: |
| Input tokens | 305,997 |
| Cached input | 277,120 |
| Uncached input | 28,877 |
| Output tokens | 1,506 |
| Collector latency | 36.142 seconds |
| Shell commands / native edits | 14 / 1 |
| Generation-reference reads / separate full postwrite reads | 1 / 1 |

Usage is the last cumulative update at raw line 254, not the sum of 16 updates.
Input exceeds the 100–225k planning heuristic; output is within the 1–2k range.
Those ranges were neither caps nor prices. Additional inspection commands are
observed, but this one sample establishes no causal token-cost explanation,
billing amount, savings or reliability estimate.

Original collection: `/private/tmp/opt004-workflow-v11-luna-live-20261102/`.
The private, gitignored
[retained bundle](../evaluations/local-evidence/2026-11-02-workflow-v11-luna/README.md)
contains all original collection files, raw events/stdout/stderr, snapshots,
manifest and instrument pins, separate semantic/raw reviews, the mechanical
audit and preparation/authorization records. Original paths are preserved and
relocated observations are not regraded. No authentication file is retained.

The mechanical audit passes all 14 checks. All **89 original collection files**
retain their hashes and modes; all **4,226 prelaunch protected files and two
symlinks** remain unchanged. Raw stdout matches the 253 received messages;
with five sends there are 258 raw rows. Exactly one thread and one turn start,
one turn completes, and no RPC/server error or model reroute is recorded.
Raw stderr is empty. The three current-status documents contain additions only.

Collector exit 1 records the failed automated gate; the session completed with
null collector and integrity errors. Every outcome is retained. The
[preservation audit](../evaluations/local-evidence/2026-11-02-workflow-v11-luna/preservation-audit.json)
and [validation record](../evaluations/local-evidence/2026-11-02-workflow-v11-luna/validation.json)
record the final byte/mode/link and documentation checks.

## Remaining work

The approved one-session slot is complete and its authorization is consumed.
No retry, replacement, repair or further live session is authorized by this
batch. If separately requested, next work should use fresh offline controls
for bounded read-only verification and post-append null-output absence proof,
with new versions and all negative controls preserved. Do not broaden general
shell attribution or reinterpret historical evidence to obtain a pass.

The router remains an authored semantic redesign. Leave inline remains the
compiler default. Baselines, replication, independent review, configured hooks,
other runtimes and the wider matrix remain open: **OPT-004 is incomplete**.
