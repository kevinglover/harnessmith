# Workflow v9 offline conditional and read-overlap repairs

Status: **offline candidate; no live sessions authorized or launched**.
The [v8 result](workflow-fidelity-v8-results.md) remains frozen at **0/1** full
automated and complete reviewed gates. Its positive semantic content, formatting,
reference, append-preservation and separate final-readback findings remain
separate from the failed workflow gate. No historical trace is replayed or
regraded. The original skill and router v7 are unchanged.

## Evidence motivating the change

The frozen v8 raw trace contains successful standalone same-path conditionals:
records 103–104 check the absent extension configuration with
`if [ -f PATH ]; then cat PATH; else test ! -e PATH; fi`; records 215–216 use the
same form to return the full pinned constitution. The extension completion
explicitly records `aggregatedOutput: null`. Records 295–297 and 296–298 are
overlapping independent full reads of the existing checklist and specification;
both finish before the native append. The old normalizer leaves these forms
unverified, which also blocks downstream context and standalone discovery proof.

These are measured findings from one Luna sample. They do not establish general
model compliance or justify waiving the frozen checks. This repair uses fresh
synthetic counterparts and local fake-server cases; no old observations are
reprocessed. The v8 collector, raw records, artifacts, scores and review sidecars
remain intact, including the separate post-retention timing correction.

## New versions and bounded contracts

[Normalizer v8](../harnessmith/workflow_trace_v8.py) wraps the frozen normalizer
v7 and emits observation schema 8. It recognizes the standalone literal
conditional above only with identical path tokens in all three positions, safe
workspace resolution, both branches statically safe, matching successful
lifecycle/source/cwd/scope and a verified inventory pin. A present file must
return its complete, nonempty pinned bytes. Absence is restricted to pinned
`.specify/extensions.yml` with explicit null or empty text output and no noise.
Missing output, lexical path aliases, empty present files, dynamic shell syntax,
extra operations, symlinks and partial or failed commands receive no new proof.

Independent full reads may overlap only when each complete envelope is proven
read-only with exact pinned output. The proof inspects the whole connected
overlap group, including a peer that outlives the initial read. Unknown, failed,
unfinished, mutating or foreign-scope operations prevent credit. Absence checks,
discovery, setup and hooks cannot overlap reads under the new proof. Every
required read must still finish before a consuming action. A prior pinned
synthetic setup stub is allowed only through its inherited absence-preserving
proof; this does not generalize to project hooks.

New proofs can remove only exactly correlated artificial attribution and
prewrite-dependency failures; superseded facts and issues remain in certificate
metadata. They may restore downstream terminal-discovery proof after a newly
recognized safe prefix. Actual failures, unrelated issues and isolation defects
remain. A relevant foreign operation scope also adds explicit unverified evidence
even if an inherited read was credited. Later unrelated operations and passive
messages do not cause blanket rejection. Captured commands are never executed or
rewritten. This is bounded static attribution, not shell emulation, executable
attestation or OS access tracing.

[Checker v9](../harnessmith/workflow_fidelity_v9.py) prepares and checks only new
v9 bundles under [rubric v10](../evaluations/variants/router-quality-rubric-v10.md).
All inherited hard gates and all three command-boundary checks remain. During
fresh collector integration, explicit null absence output exposed an additional
backing gap: the frozen helper requires string output. A reported adapter now
admits only a unique successful record with the matching new pinned-absence
certificate, raw command/lifecycle, inventory and empty-output hash. It substitutes
empty text only in a derived helper input. Captured observations stay unchanged;
missing output, null reads and malformed or unsupported proofs remain blocked.

The first full-suite run exposed a separate dimension-reporting gap: an
unclassified early extension command disappeared from the inherited reference
action set, so reference readiness passed while workflow classification failed.
Checker v9 now requires unknown operations to have lifecycle coordinates and
start after the complete pinned reference. Earlier, overlapping or unordered
unknowns leave reference readiness unverified. Unknowns after the checkpoint
still fail workflow classification without retroactively failing reference
ordering. The original failing test run and its preparation remain retained.

[Collector v9](../harnessmith/workflow_runtime_v9.py) changes version wiring and
pins only. The fixed one-slot design, disabled-by-default gate, workspace-write
and network-disabled settings, 180-second maximum, durable attempt guard and
failure retention remain. No retry, sample-count or model override is added.
Router v7 and its [review](../evaluations/variants/speckit-checklist-router-v7.review.json)
remain byte-for-byte unchanged. No compiler transformation changes; leave inline
remains the default.

## Offline controls

| Area | Positive controls | Negative controls |
| --- | --- | --- |
| Conditional proof | Exact pinned present bytes; pinned extension absence with explicit null or empty text | Missing/noisy output, wrong or aliased paths, empty present file, unsafe branches, stale inventory, symlinks, failed or inconsistent lifecycle |
| Read overlap | Independently complete exact reads, sequential reads, timely consuming action | Unknown/mutating/failed/open/truncated peers, foreign scope, discovery or absence overlap, connected later mutation, reads finishing after consumption |
| Derived repairs | Precisely correlated inherited failures; newly proven timely required read | Unrelated issues, late or wrong-path reads, duplicate lifecycle IDs, stale postwrite pins |
| Checker backing | Unique matching explicit-null absence certificate; observation unchanged | Missing output, null present read, malformed/old/duplicate/failed/unbacked certificate |
| Reference checkpoint | Complete reference before known actions and any unknown operations | Unknown operations before/overlapping the read or without lifecycle coordinates; known project-read overlap |
| Collector | Fresh synthetic append and sequential case through local fake stdio server | Failed probes and overlap retained; mixed read/discovery still fails separation; missing final read and unsupported Git claims still fail; normalization exception retained |

All fake-server authentication is empty and local. No provider session, model
judge or real project hook runs. Historical tests may run as ordinary regressions;
historical live traces and benchmarks are not replayed. New implementation,
tests, rubric, pilot and this proposal are versioned; only the three current-status
documents receive additions in place.

## Validation and preservation

Validation on 2026-10-26: **684 repository tests passed, 85% coverage**, including
**50 new regressions**: 25 parser, 17 checker and eight fake-server collector tests.
The first full suite exposed the reference-ordering gap described above; after
the new checker repair, the second full suite passed. Both runs remain retained.
Ruff and mypy (58 source files) pass. Final repository/schema/documentation and
whitespace outcomes are recorded in the retained validation receipt.

Independent review used seven initial adversarial probes and nine further
overlap/null-output probes, all passing. Final read-only review found no remaining
actionable mismatch in the reference-boundary repair. This was code review of
synthetic controls, not a model-output judge or a live benchmark.

All **2,620 protected files and two symlinks** retain their starting bytes/modes
or link targets. The three current-status documents contain additions only
relative to the starting working tree. The original skill, router v7 and all
historical evidence remain frozen, including v8's 0/1 full gate.

The final offline preparation at `/tmp/opt004-workflow-v9-review-final/` contains
one case, nine workspace files, 19 pinned instruments and **zero attempts**.
Its manifest SHA-256 is
`f99670185dc952703e741b5e484d8c60790d6db2a064d63ceab7ebc7e50e6aeb`;
rubric-v10 SHA-256 is
`010f37c67918796b9cdca96d0b5d2f642dece883b7994c37cf4b18c9f031ef3c`.
The collector pins 19 runtime code dependencies. Router-v7 review SHA-256 remains
`89fc65b25a4b888ab350d88a6988da149b92777aa4a86d18168272eff1539c84`;
original skill SHA-256 remains
`1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45`.
Original prompt, fixtures, permissions and package bytes/modes match their pins.

The private, gitignored
[offline bundle](../evaluations/local-evidence/2026-10-26-workflow-v9-offline/README.md)
retains preparation, new sources, inherited dependencies, unchanged inputs,
independent probes, logs, coverage and preservation audits. Its
[validation record](../evaluations/local-evidence/2026-10-26-workflow-v9-offline/validation.json)
and [inventory](../evaluations/local-evidence/2026-10-26-workflow-v9-offline/manifest.json)
identify the evidence. Earlier failed checks, the original explicit-null failing
mock, the first full-suite failure, its earlier preparation and source snapshot
remain separate from a fresh passing final mock. None is regraded in place.

## Smallest follow-up proposal — approval required

Exactly **one fresh GPT-6 Luna low session**, one turn and one repetition:

| Session | Task | Expected checks |
| --- | --- | --- |
| `append-router-v7-instrument-v9` | Use unchanged router v7, the original append prompt and synthetic fixture to add three questions to `specs/001-invitations/checklists/security.md` | Complete generation reference first; isolated certified extension state before separate setup; complete context before write; reads and discovery isolated; all 694 original bytes and checkbox states preserved; unchecked CHK008–010; separate complete final readback; correct content/format and evidence-supported narration |

This is one end-to-end append diagnostic, with **no baseline, hooks rerun,
replication, retry, replacement, batch expansion or extra judge session**.
The prompt does not prescribe conditionals, concurrent reads or discovery. If
the model uses another valid form or omits unneeded discovery, retain the result
and report the unused grammar as unobserved live. Do not steer or rerun to
manufacture coverage.

Planning scope: **100–200k input and 1–2k output tokens**, at most **180 seconds**.
The frozen v8 sample used 163,744 input, 1,320 output and 22.096 seconds. This range
is a heuristic, not a token cap, price, billing estimate or efficiency comparison.

If separately approved, verify returned model/effort/permissions and disabled
unrelated skills, then retain every result. Save an anonymous semantic-first
review packet and separate lookup key; disclose reviewer identity and prior
exposure before grades/traces/usage. Inspect every raw operation and material
commentary/final claim afterward. Keep review sidecars separate from pending
grades. Report content, formatting, references, workflow and descriptive
efficiency separately; empty bounded-match arrays do not prove truthful narration.

One pass would establish only that single reviewed sample. It would not establish
reliability, router-v7 hooks fidelity, efficiency, compiler equivalence, promotion
or OPT-004 completion. Luna and Astra remain separate; legacy host reads are not
fully OS-isolated. The v8 authorization is consumed. This preparation starts
**zero live sessions and zero attempts**, and no launch is queued.
