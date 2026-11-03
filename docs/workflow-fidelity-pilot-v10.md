# Workflow v10 offline guarded-marker repair

Status: **offline candidate; no live sessions authorized or launched**.
The [v9 result](workflow-fidelity-v9-results.md) remains frozen at **0/1** full
automated and complete reviewed gates. Its positive content, formatting,
reference, append-preservation and final-readback findings remain separate from
its failed workflow gate. No historical trace is replayed or regraded. The
original skill, router v7, prompt and fixtures are unchanged.

## Measured gap and bounded change

The v9 raw trace records standalone same-path conditionals with
`else test ! -e PATH && echo ABSENT`: extension probes at complete raw records
88–89 and 446–447, and constitution read at 204–205. Both extension probes return
`ABSENT` plus newline, exit zero. The constitution returns exact pinned contents
from its present branch. The frozen parser rejects the operator in the else
branch, even when unused. These three unknown operations block seven criteria
and leave the standalone discovery command uncertified. All shell commands exit
zero. These are findings from one Luna sample, not evidence of reliability or a
reason to waive the frozen criteria.

[Normalizer v9](../harnessmith/workflow_trace_v9.py) wraps frozen v8 and emits
observation schema 9. It recognizes only the bounded standalone form
`if [ -f PATH ]; then cat PATH; else test ! -e PATH && echo ABSENT; fi` with the
same literal path in all three positions, safe path resolution, both branches
supported and a complete successful matching lifecycle. A present file must
return its complete nonempty pinned contents. Absence requires the pinned absent
extension path and the exact guarded marker output. Missing/null/noisy output,
wrong paths or markers, unsafe unused branches, extra commands, failed commands,
symlinks and stale pins cannot earn this proof.

The second extension check in v9 occurs after the native append. New proof may
account for one completed native update to the pinned checklist only when all
original bytes remain its prefix, other workspace files and modes stay unchanged,
and a separate complete final readback finishes before the probe. It cannot
declare arbitrary writes, shell operations, hooks or unknowns safe. Absence
probes still cannot overlap other operations. This is a narrow synthetic append
contract, not a general file-system mutation model.

Only exactly correlated attribution failures may be superseded, with old facts
and issues retained in certificate metadata. Newly certified context can repair
its precise dependency shadow, and a fully accounted-for prewrite prefix can
restore terminal-discovery proof. All workflow boundaries remain: extension
checks separate from other operations, setup separate from reads, reads separate
from discovery/mutation, and a distinct complete final readback before reporting.
No captured shell command is rewritten or executed during normalization.

The first fresh fake-server integration run exposed a transitive case: earlier
unknown guarded probes also blocked inherited complete-read overlap attribution.
The wrapper now reconsiders those precisely matched failures under v8's unchanged
intrinsic-read and connected-overlap proof rules after the earlier probes are
certified. This adds no concurrency grammar and does not excuse unknown,
mutating, incomplete or wrong-scope peers. The failed run is retained separately.

[Checker v10](../harnessmith/workflow_fidelity_v10.py),
[collector v10](../harnessmith/workflow_runtime_v10.py),
[pilot config](../evaluations/workflow-fidelity-v10/pilot.json) and
[rubric v11](../evaluations/variants/router-quality-rubric-v11.md) pin the new
instrument alongside inherited dependencies. Older bundles cannot be checked as
v10. The inherited explicit-null adapter remains tied to its matching v8 empty
absence proof; the new guarded-marker proof requires text. Raw observations and
historical scores remain unchanged. No compiler transformation changes; leave
inline remains the default.

## Offline controls and validation

| Area | Positive controls | Negative controls |
| --- | --- | --- |
| Conditional | Exact pinned present content and exact guarded marker for absent extension | Wrong/aliased paths, marker-only claims, different/noisy/missing output, failed commands, extra operations, unsafe unused branches, symlinks and stale inventory |
| Prefix | Complete reference, separate precheck/setup, complete context, downstream standalone discovery | Unknown/failed/open/foreign-scope operations, mutation, absence overlap and mixed command envelopes |
| Post-append | One completed target-only native append, exact original prefix, unchanged other files/modes and separate complete readback before probe | Other or ambiguous mutations, altered existing bytes, missing/partial/late readback and overlap |
| Checker | Fresh version-pinned bundle; old null proof preserved; all hard gates remain | Old manifests/schema, changed dependencies, unsupported verification/Git claims and command-boundary violations |
| Collector | One synthetic fake-server slot with precheck, context, discovery, append, readback and postcheck | Failed/unsupported proofs retained, no retry or expanded batch, disabled-by-default real launch |

These controls use new synthetic events and harmless local fake servers. They
do not call a model provider, run real hooks or replay historical live evidence.
Validation on 2026-10-26: **743 repository tests passed, 85% coverage**, including
**51 new regressions**: 21 parser, 21 checker and nine fake-server collector tests.
The final 51-test targeted run and retained passing fake-server capture also
pass after two type-only annotations were added. Ruff passes; mypy passes all
61 source files. The earlier type-check failure, first integration failures,
failed synthetic capture and earlier preparation remain retained separately.

Independent offline review passes 59 fresh adversarial probes, including exact
native `move_path: null` metadata, file modes, safe read-overlap recovery and
connected unsafe peers. The review caught the native-envelope compatibility
issue before final validation. An initial overlap probe incorrectly demanded a
new certificate for an already credited read; that failed oracle result and the
corrected probe remain separate. Final probes were rerun after the type-only
annotations and pass against the final source. This is code/instrument review,
not a model-output judge or a live benchmark.

All **3,249 protected files and two symlinks** retain starting bytes/modes or
link targets. The three current-status documents contain additions only relative
to the starting working tree. The v9 public result, uncommitted starting work,
all private evidence, original skill and router v7 are preserved.

Final offline preparation at `/tmp/opt004-workflow-v10-review-final-typed/`
contains one case, nine workspace files, 21 pinned instruments and **zero
attempts**. Prepared manifest SHA-256:
`1c8827b901f03c2ad348421d8f7aac4019f5a1deda995e5a018885a1fdf01956`.
Original skill SHA-256 remains
`1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45`;
router-v7 review SHA-256 remains
`89fc65b25a4b888ab350d88a6988da149b92777aa4a86d18168272eff1539c84`.
The collector pins 21 runtime code dependencies. Original prompt, fixtures,
package bytes and modes match their pins.

The private, gitignored
[offline bundle](../evaluations/local-evidence/2026-10-26-workflow-v10-offline/README.md)
retains final and earlier preparations, failed and passing fake captures,
sources, dependencies, probes, logs and preservation audits. Its
[validation record](../evaluations/local-evidence/2026-10-26-workflow-v10-offline/validation.json)
and [inventory](../evaluations/local-evidence/2026-10-26-workflow-v10-offline/manifest.json)
identify the final evidence. Existing results are never overwritten by final
success. Repository/schema/documentation and whitespace outcomes are recorded
in that validation record.

## Smallest follow-up proposal — approval required

Exactly **one fresh GPT-6 Luna low session**, one turn and repetition:

| Session | Task | Expected checks |
| --- | --- | --- |
| `append-router-v7-instrument-v10` | Use unchanged router v7, original append prompt and synthetic fixture to append three questions to `specs/001-invitations/checklists/security.md` | Complete generation reference before project actions; certified isolated extension check before separate setup; full required context; isolated discovery if used; all 694 original bytes and checkbox states preserved; unchecked CHK008–010; separate complete final readback; any postcheck supported; accurate content, formatting and narration |

No baseline, hooks rerun, replication, retry, replacement, expansion or extra
judge session. The prompt does not force a conditional, marker or post-append
probe. If the model chooses another supported form, retain that result and mark
unused grammar unobserved live. Do not rerun to manufacture coverage.

Planning scope: **100–225k input and 1–2k output tokens**, at most **180 seconds**.
The v9 sample used 201,255 input, 1,298 output and 22.383 seconds. This widened
planning range is a heuristic, not a cap, price, billing estimate or savings
comparison. No live session or attempt is started by preparation.

If separately approved, verify returned model/effort/permissions and disabled
unrelated skills, retain every result, save the anonymous semantic-first review
before opening grades/traces/usage, and disclose authorship/prior exposure and
blinding limits. Then review every raw operation and material commentary/final
claim. Preserve pending grades and separate sidecars. Report content, formatting,
references, workflow and descriptive efficiency independently; empty bounded
match arrays never prove truthful narration.

One pass would establish only that reviewed sample. It would not establish
reliability, router-v7 hooks fidelity, efficiency, compiler equivalence, promotion
or OPT-004 completion. Luna and Astra remain separate, and the legacy sandbox
does not fully isolate host reads. Prior authorizations are consumed. This
proposal authorizes **zero live sessions**, and no launch is queued.
