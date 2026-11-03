# Workflow v6 append follow-up results — 2026-10-25

Exactly **one approved GPT-6 Luna low session** completed, one turn, with no
retry, replacement or expansion. The frozen automated and complete reviewed
case gates remain **0/1**. Semantic content passes **1/1**, and separate raw
review corroborates the requested append behavior. The sole automated failure
is an absence-certificate limitation: the model checks extension absence before
setup, but the inherited parser does not certify its explicit `else printf`
branch. The failed grade is retained unchanged.

The [v6 proposal](workflow-fidelity-pilot-v6.md),
[rubric v7](../evaluations/variants/router-quality-rubric-v7.md), package,
instruments and all earlier evidence remain frozen. Correct observed behavior
does not waive a failed frozen assertion, establish reliability or close OPT-004.
The one authorized slot is consumed; no further live work is queued.

## Separate outcomes

| Dimension | Frozen automation | Separate review |
| --- | --- | --- |
| Content correctness | Pass | Pass: three distinct requirements-quality questions cover measurable expiration, expired/reused outcomes together, and record retention; no invented policy. |
| Formatting | Pass | Pass: unchecked CHK008–010, question syntax, Gap/quality/FR markers, retained structure and accurate final path/count/append/focus/depth/reviewer report. |
| Reference behavior | Pass | Pass: the full required generation reference finishes as a separate action before project work; no example reference is loaded. |
| Workflow fidelity | Fail | Raw behavior corroborated: timely extension check, separate setup, required context, native append preserving the original prefix, separate complete final read and supported narration. The frozen certificate requirement still fails. |
| Efficiency | Not evaluated | Descriptive usage only; no baseline or replication. |

The artifact preserves all **694 original bytes**, including notes, whitespace,
IDs and `[x]`, `[X]`, `[ ]` states, and ends at **1,123 bytes**. The appended
questions cite the corresponding FR-2, FR-3 and FR-4 gaps without supplying
missing policy values.

An anonymous prompt/spec/constitution/before/after/final-report packet was
reviewed before opening its lookup key, grades, usage or raw trace. The primary
assistant authored the candidate with implementation subagents, knew the
one-case design and collector exit code 1, and could infer the case. Review is
neither independent nor fully blind. Semantic judgments were saved first;
raw review and the read-only instrumentation audit are separate sidecars.
No extra model judge ran. Original `pending-review` fields are unchanged.

## Raw behavior and the remaining certificate gap

Line numbers below refer to the complete `raw/events.jsonl`, including sent and
received records; normalized event indices use a different coordinate system.

The required generation reference returns at lines **63–64**. Its complete
25,094 bytes match the pinned reference hash. A separate extension check at
**104–105** runs this bounded conditional in the prepared workspace:

```sh
if [ -f .specify/extensions.yml ]; then
  cat .specify/extensions.yml
else
  printf 'NO_EXTENSIONS_FILE\n'
fi
```

It returns exactly `NO_EXTENSIONS_FILE` plus a newline and exits zero. The path
is pinned absent; the only preceding project-relevant action is the reference
read, and before/after inventories contain no extension configuration. Setup
does not start until **108**, after the check completes, and returns the expected
JSON at **114** with the exact requested arguments.

The inherited [conditional classifier](../harnessmith/workflow_trace_v3.py)
sets `certified_absence` only for the no-`else` form. Its literal-output branch
is recognized as a successful `fixture absence` diagnostic but gets
`certified_absence: false`. Normalizer v5 retains that behavior; checker v6
requires the explicit certificate. Consequently `extension-config-before-setup`
fails even though raw evidence corroborates the checkpoint. There are no
unclassified events, failed command envelopes, collector errors or integrity
errors. No classifier was changed and no observation was regraded.

Constitution, spec and existing checklist reads complete at **190**, **194**
and **202**, before the native edit at **267–268**. Scoped feature discovery at
**197–198** is not used to infer hidden-file absence. The complete final file is
read in a distinct action at **322–323**, matching the retained artifact hash.
The final report starts at **327** and completes at **499**; no later write occurs.

All five completed commentary messages and the final report were reviewed.
The setup/cache report follows its result; existing-item facts follow their
reads; appended-item facts follow the edit; final verification claims follow
the complete readback. No Git invocation, Git comparison claim, invented failed
attempt or unsupported blocker is recorded. The new narrative screens match
no claims: the final “Verification: Read back…” wording is outside their bounded
matcher. Its support comes from raw review, not a vacuous screen pass. This
sample does not exercise live rejection of an unsupported Git assertion.

The setup command emits two exact macOS Python cache-warning/error pairs.
Their denied cache writes remain in the trace; the setup result is independently
corroborated. The native checklist write succeeds. No real project hook runs;
this fixture has no hook configuration and cannot establish v6 hooks fidelity.

## Measured scope

| Session | Input | Cached input | Uncached input | Output | Collector latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `append-router-v6` | 178,288 | 157,312 | 20,976 | 1,039 | 20.260 s |

Usage is the last of ten cumulative updates, raw line 500, never their sum.
There are eight shell commands, one native edit, one generation-reference read
and one postwrite target read. These figures fit the proposal's heuristic
100–200k input / 1–2k output estimate. They establish neither billing nor
efficiency gains. Caching is uncontrolled and the backend model revision is
unreported; this is one sample without a contemporaneous baseline. Do not pool
it with Astra or differently instrumented Luna cohorts.

## Provenance and retention

The private, gitignored bundle is
`evaluations/local-evidence/2026-10-25-workflow-v6-luna/`, absent from a fresh
checkout. All **69 original collection files** are retained byte-for-byte with
modes preserved. The original collection remains at
`/private/tmp/opt004-workflow-v6-luna-live-20261025/`; raw absolute paths are not
rewritten and relocated artifacts are not regraded.

The bundle contains the frozen report/environment/preparation, durable attempt
and batch records, complete raw JSONL/stdout/stderr, observations and grades,
prompts/manifests, before/after/workspace inventories and hidden files, and all
instrument snapshots. Separate files retain the anonymous review packet/key,
semantic review, full raw review view, manual review, analysis and integrity
audit. `prelaunch/` records this authorization and source/proposal/rubric hashes.

All **1,860 prelaunch protected content files and two symlinks** remain unchanged.
The original skill, previous packages, proposals, instruments and scores are
preserved. The read-only audit verifies one thread/start, one turn/start, one
attempt, and all **499 received messages** against raw stdout. There are no
recorded reroutes, provider errors, RPC errors or retries. Unobservable
provider-internal behavior is not a claim of this audit.

| Identity | Recorded value |
| --- | --- |
| Model / reasoning | `gpt-6-luna`, low; backend revision unreported |
| Harness / mode | `codex-cli 0.163.0-alpha.11.1`, `app-server-stdio` |
| Instrumentation | `codex-workflow-stdio-v6`; normalizer/observation v5, checker/collector v6 |
| Configuration SHA-256 | `30f6f817e2a8b6f97e254d43a7e48a1a4233790e0f7b13a011fcc50d8c41ebc2` |
| Original source SHA-256 | `1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45` |
| Router v6 review SHA-256 | `8f8f386a2f421dbc8eebc303db4d8bbc217c1c5409bffd9972917fe5b84a9315` |
| Rubric v7 SHA-256 | `bf54858323e30e097cb6da78748abcb97cf8e94ec254e62e0ce2de010cc547fe` |
| Manifest SHA-256 | `be97656bedb569c8c94e2d805efc00a7a824a8f71642a8f02a39da6c6e63e949` |

Requested and returned Luna low, approval `never`, network-disabled
workspace-write sandbox, temporary-directory exclusions, intended workspace
and empty unrelated instruction sources match. Five unrelated skills were
disabled. Legacy host reads are not fully OS-isolated. The established
thread/turn and sandbox protocol is documented in the current
[official app-server reference](https://learn.chatgpt.com/docs/app-server).

The unchanged candidate had passed 513 offline tests with 84% coverage and
lint/type/schema/documentation checks. Frozen sources matched before launch.
Only evidence integrity and documentation/schema checks were repeated for this
report; completed benchmarks and unchanged unit tests were not rerun.

## Decision and next work

Keep the frozen **0/1** full gate and the separate positive artifact/raw findings.
Leave inline remains the compiler default, the router remains an authored
experimental redesign, and OPT-004 stays open.

The smallest next repair is offline and limited to a new-version absence
certificate for bounded literal `else` output, with pinned inventory, safe
branches/paths, mutation-free ordering and exact returned-output proof. Tests
must reject fabricated labels, unpinned absence, side effects, late/overlapping
checks and mismatched output. This report implements no repair and authorizes
no further live run. Broader baseline, replication, independent review, hooks,
lifecycle and target-runtime requirements remain open.
