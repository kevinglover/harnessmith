# OPT-004 completion plan — 2026-11-02

Status: **S1 offline preparation in progress; live collection remains pending**.
The user chose to **keep the full scope and stage the work**, including live
Codex, Claude and Cursor evidence. This plan authorizes **zero live sessions**.
The completed v11 authorization is consumed. The original S0 planning task
changed no collector, instrument, scenario, router, source skill or historical
evidence. The later S1 implementation checkpoint below records additive offline
work; it grants no live authorization and leaves historical instruments frozen.

This is the prospective completion checklist. The dated entries in
[OPT-004 status](opt-004-status.md) remain historical evidence. The latest
[v11 result](workflow-fidelity-v11-results.md) is a completed diagnostic sample
with a frozen 0/1 full gate, including a performed but uncertified final extension
check. It is not an unlaunched pilot and will not be regraded.

## Completion boundary

OPT-004 delivers defensible coverage and measured evidence. Finish it when the
retained scope below has an audited disposition, the required comparable samples
have been collected and reviewed, and every runtime claim has its provenance.
Observed behavioral failures are valid results; unobserved or unmeasurable
required cases remain open. Completion must state the limits of the findings.

Track three distinct outcomes for every host/case:

| Field | Allowed outcomes | Meaning |
| --- | --- | --- |
| Evidence | Complete; missing; collector unsupported; host capability unverified; interrupted/incomplete | Whether the declared question was actually measured with the required records and repetitions. |
| Behavior | Pass; fail; mixed; unobserved; verified not applicable | What the recorded actions and reviewed output establish. A complete evidence cell may contain failures. |
| Promotion | Pending/ineligible; separately assessed | Whether a separate frozen use or efficiency policy passes. It does not control evidence completion. |

An adapter rejecting an event means **collector unsupported**, not that the host
lacks the feature. A demonstrated host limitation needs a versioned capability
record, primary documentation or a native rejection, and an explicit final
disposition. It is not a behavior pass or a waiver of required positive coverage.
Only the user can approve removing or deferring a required live cell through an
explicit scope change; an auditor's signoff cannot do so. Missing access, missing
instrumentation or an unavailable model does not become not applicable. The
user's current choice retains every required live cell. Generic remains an
offline contract target, not a fourth live host.

Router promotion, general savings, production reliability and compiler semantic
equivalence remain separate claims. The
[promotion rubric](../evaluations/variants/router-quality-rubric-v2.md) requires
three passing observations per variant/case for reviewed workflow use and adds
workload thresholds for an efficiency recommendation. Those are not the original
evidence task's success criteria. An all-failing but adequately measured batch
can finish a diagnostic question while leaving the candidate ineligible for use.
Leave inline remains the compiler default; router v8 is an authored redesign.

## Existing evidence to retain and reuse

Baseline for this plan: repository head `235268dfb4b22459dccca2baa977a8f0893eb531`.
The [evaluation guide](evaluation.md) describes 20 offline scenarios: three legacy
and 17 version-2 scenarios. The latter comprise four lifecycle, four non-trigger,
three explicit-channel, one Codex runtime probe and five checklist consultations.
Prior validation reports 516 scenario checks and 785 repository tests; this
planning task does not rerun them.

The [Astra comparison](conditional-loading-results.md) contains 27 observations;
the [Luna comparison](router-luna-results.md) contains 48. They already provide
repeated explicit consultation/reference evidence with preserved failures,
provenance and usage. Retain the complete cohorts, including every variant and
failure. Do not select a favorable subset, merge models/versions, or insert old
observations into new matched pairs. Existing Codex reference cells below remain
limited to their historical configurations; no current-version claim follows.

Workflow cohorts provide useful diagnostic observations, including one complete
v5 hook case and v11's artifact/reference successes. They do not supply repeated
canonical-versus-compiler-generated workflow evidence. V11's 0/1 gate remains
unchanged; its 305,997 input tokens are neither a forecast nor a per-session cap.

## Finite acceptance matrix

This matrix contains twelve requirements. Case IDs refer to the bounded catalog
below. New discoveries become separately proposed work; they do not silently
expand this matrix or consume additional sessions.

| ID | Required coverage | Existing evidence | Remaining deliverable and exit condition |
| --- | --- | --- | --- |
| A01 | Identity, opt-in, retention and usage | Recorded cohorts pin sources/packages/configurations, preserve raw evidence and distinguish mocks. | Audit every reused/new claim for source and recipe or explicit no-recipe identity, harness/model/mode/instrument versions, actions, outputs, reads and usage. Keep backend snapshots explicitly unreported when unavailable. Verify opt-in and durable failure retention. |
| A02 | Offline contracts on generic, Codex, Claude and Cursor | The 20 scenarios cover the original concepts; lifecycle events are mocked. | Add only missing catalog cases and typed native-event controls under new versions. Every supported positive control and adversarial negative control has its expected outcome. Mocks remain labeled and do not close live cells. |
| A03 | Explicit consultation and reference selection | Repeated Codex skip/one/both-reference cohorts exist. | Reuse those Codex findings; collect R0–R2 on Claude and Cursor. Distinguish package reference loads from project context reads and retain unnecessary/missing loads as failures. |
| A04 | Implicit selection, non-trigger and explicit-only policy | Offline contracts; current live input forces the selected skill. | D1–D3 on each host: actual discovery/selection or abstention, a fixed crowded catalog and explicit refusal/acceptance. Never force a skill while claiming automatic selection. |
| A05 | Permission and approval boundaries | Offline constraints, returned live permission settings and non-model sandbox probes. | P1 on each host: correlated native approval decisions, allowed action after grant, no action after denial, and harmless denial probes. Verify effective permissions after lifecycle transitions too. Settings alone are insufficient. |
| A06 | Creation and state-preserving append | Separate diagnostic workflow cohorts; v11 preserves all 694 original bytes. | W1–W2 on each host using canonical/actual compiled packages, repeated under one frozen configuration. Complete context, target changes, checkbox states, full readback and report claims are measurable. Behavior may fail. |
| A07 | Automatic/optional/disabled/conditional hooks and failure | Offline events and isolated live hook evidence. | W3 and H1–H4 on each host: actual harmless fixture hooks, before/after order, acceptance/decline, disabled/conditional skip and nonzero exits. Record platform dispatch; a narration or marker alone is insufficient. |
| A08 | Continuation, resume, abort, fork and compaction | Mock lifecycle sequences; existing live collectors do not implement these operations. | L1–L4 on each host and L5 on Claude: actual native boundaries, causal IDs, parent/child lineage, restored constraints, reads and permissions. A prompt saying context was compacted is insufficient. |
| A09 | Cross-runtime coverage and surface identity | Offline target projections; live Codex only. | Separate capability records, qualified adapters and retained live results for Codex, Claude and Cursor. Assess Cursor SDK separately; its events cannot silently stand in for editor behavior. |
| A10 | Repetition and comparable measurements | Existing repeated consultations; workflow versions are distinct single-case diagnostics. | For each new cell, three predeclared canonical/compiled pairs with the same model/effort/host/version/permissions/instruments within that cell. Report every sample, cache/output/latency/read counts and incomplete attempts. No cross-host aggregate. |
| A11 | Output review and attribution | Historical involved-reviewer and blinding limits are disclosed. | New outputs receive semantic-first review before strategy key, scores and usage; retain per-criterion reasons. An independent reviewer audits the final claim-to-evidence mapping and unresolved interpretation disagreements. Disclose identity, exposure and blinding limits; no model judge is automatically authorized. |
| A12 | Final closure and unresolved behavior | Dated reports and status map exist. | One final audit covers A01–A12 and every retained host/case cell. Required evidence is complete; missing/unsupported/interrupted cells prevent closure unless the user explicitly approves a scope change removing or deferring them. A documented host limitation is a finding, not an auditor-granted waiver. Record behavior failures and separate promotion work without changing historical grades. |

Malformed-hook configuration and missing-template fallback are additional
promotion-policy cases. They remain visibly open in that policy but are not
silently added to this evidence plan. Strong reliability claims, further models,
additional extraction strategies and broader compiler transformation proofs also
require their own scoped work. This boundary does not declare those claims true.

## Bounded case catalog

Each ID is one predetermined trajectory per variant/repetition, potentially
containing several turns. All use synthetic fixtures and harmless local hooks.
Before implementation or collection, write exact prompts, operations, event
order, permissions and assertions for that ID. Do not split it into additional
cases after seeing output. If a host cannot exercise it within these limits,
record the blocker and revise the plan explicitly before any new approval.

| Case | Required observation | Maximum task model turns per trajectory | Physical threads per trajectory |
| --- | --- | ---: | ---: |
| R0 | Explicit consultation where optional references must be skipped. | 1 | 1 |
| R1 | Explicit consultation requiring one designated reference. | 1 | 1 |
| R2 | Explicit consultation requiring both designated references in order. | 1 | 1 |
| D1 | Implicit positive selection in a fixed 16-skill catalog: one target, seven near-topic distractors and eight unrelated skills, with no explicit skill input. | 1 | 1 |
| D2 | Non-trigger prompt in that same fixed 16-skill catalog; observe abstention. | 1 | 1 |
| D3 | Explicit-only policy: implicit request refused, then explicit user invocation accepted. | 2 | 1 |
| W1 | Create the checklist with required context, reference behavior, complete readback and truthful report. | 1 | 1 |
| W2 | Append while preserving every original byte, ID, note and mixed checkbox state; verify separate readback and final extension action. | 1 | 1 |
| W3 | Automatic pre/post hooks in order; optional offered; disabled and nonempty-condition hooks skipped. | 1 | 1 |
| H1 | Optional hook offered, then explicitly accepted and executed once. | 2 | 1 |
| H2 | Optional hook offered, then declined without execution. | 2 | 1 |
| H3 | Actual synthetic pre-hook nonzero failure and the frozen expected failure handling. | 1 | 1 |
| H4 | Actual synthetic post-hook nonzero failure and truthful reporting. | 1 | 1 |
| P1 | Native approval denied, then a fresh request granted; correlate each decision with its action. Include non-model boundary probes before/after. | 4 | 1 |
| L1 | Initial work, ordinary continuation, then disconnect/restart and native resume of the same thread with constraints retained. | 3 | 1 |
| L2 | Interrupt a running synthetic action; observe cancellation and no subsequent forbidden action within a predeclared quiet window. | 1 | 1 |
| L3 | Initial work, actual explicit compaction boundary, then continuation with constraints/reference behavior checked. | 2 | 1 |
| L4 | Initial parent work, native fork and one child continuation with lineage, constraints and effective permissions checked. | 2 | 2 |
| L5 | Claude-only native idle compaction followed by continuation, if the selected version exposes that event; capability must be established first. | 2 | 1 |

R0–R2 reuse existing Codex cohorts; they are new cells for Claude and Cursor.
The 16-skill catalog is a bounded interference condition with both plausible
competitors and irrelevant choices, not a claim about arbitrary catalog sizes.
Freeze names, descriptions, bytes, placement and ordering identically for the
paired variants; only the target package treatment differs. Record the target's
position and reject accidental explicit hints. No extra catalog sizes are included.

There are 18 common cases, plus L5 for Claude: **55 host/case cells** across the
three live hosts. Three Codex reference cells already have historical evidence;
**52 cells need new qualified collection** under this plan. Their finer behavior
results remain separate from evidence completeness. Catalog IDs are prospective,
not claims that executable scenarios or suitable host APIs already exist.

The paired treatments are the unedited canonical package and **one actual
compiler-generated package**, pinned by source, recipe/configuration and package
hashes. Choose and review one relevant recipe per fixture/target before freezing;
do not hand-author the compiled arm, substitute router v8, or assume existing
Codex recipes are portable. Any necessary fixture/recipe work is prospective and
does not change the original checklist skill. Historical router evidence remains
a separately labeled authored treatment.

## Stages, dependencies and collection ceilings

Three repetitions are a proposed diagnostic design choice, not three required
successes. One host/model/effort/version configuration is selected per host;
cross-host results remain separate. More models or surfaces require a new plan.
Every live stage needs its own later approval of exact pinned inputs and counts.

| Stage | Work and dependencies | Variant trajectories | Physical threads | Maximum task model turns |
| --- | --- | ---: | ---: | ---: |
| S0 | This plan, evidence index and user-confirmed full scope. | 0 | 0 | 0 |
| S1 | Offline capability records, fixture/recipe preparation, new event schema and adapters; qualify each host independently. | 0 | 0 | 0 |
| S2 | Codex W1–W3, after their S1 qualification. | 18 | 18 | 18 |
| S3 | Codex D1–D3, P1 and L1, after their S1 qualification and review of S2's measurement integrity. | 30 | 30 | 66 |
| S4 | Codex H1–H4 and L2–L4, after their S1 qualification and review of S3's measurement integrity. | 42 | 48 | 66 |
| S5 | Claude's 19 cases, after its independent S1 qualification; split approval by the same case groups plus references/idle compaction. | 114 | 120 | 180 |
| S6 | Cursor's 18 cases, after its independent S1 qualification; split approval by the same case groups plus references. | 108 | 114 | 168 |
| S7 | Final independent evidence audit and acceptance disposition. | 0 | 0 | 0 |
| **Maximum new collection** | **52 cells × 2 variants × 3 repetitions; no replacement allowance.** | **312** | **330** | **498** |

These are ceilings for the full staged plan, not authorization, a spending
estimate or a claim that every cell is currently executable. A trajectory is
one variant/repetition, not a canonical/compiled pair; there are 156 new pairs.
Only L4 adds a child thread. Restarting a process for L1 does not create a new
thread. Native control events are recorded separately from model turn starts.
Task model turns for a fork are bounded across parent and child together.
The 498 ceiling counts declared task turns, not necessarily all internal model
requests: native compaction may perform separately metered model work. O1–O2
must establish that accounting boundary before a stage can be approved.

Counts follow `2 × repetitions × cases`, with thread/turn multipliers from the
catalog. Rotate canonical/compiled order within each case, starting with
canonical on repetitions 1 and 3 and compiled on repetition 2. Do not interleave
variants inside one thread or count historical samples toward a new batch.
Use a proposed 180-second **whole-trajectory** deadline, shared across turns
and any fork; exact idle/abort observation windows must fit within it. A feature
that cannot be observed within that bound is a prelaunch blocker, not permission
to extend the run automatically. Deadlines do not enforce token or price caps.

Before approval of each stage, provide an input/output planning range grounded
in its prepared prompt/context and available comparable evidence, disclose its
uncertainty, and record concurrency/resource/cache policies. Do not extrapolate
v11's single-case tokens into a promised total. No price is assumed. Exact
models and installed host versions are verified then, not inferred from the
weekly ledger's version notes. A changed version creates a separate configuration.

## Offline implementation work packages

| Work | Dependency | Concrete output and acceptance |
| --- | --- | --- |
| O1 — Capability and evidence inventory | S0 | For each named surface, record installed version, primary documentation/local schema evidence, controllable operations, observable events, approval/permission model, usage availability and unresolved access. Distinguish host-unavailable from collector-unimplemented. Assess Cursor SDK as a separate surface; it cannot satisfy editor claims without an explicit scope decision. |
| O2 — Prospective contracts and paired packages | O1 | Exact case fixtures, expected event boundaries, turn caps, source/recipe/package pins and catalog inventory. Version the turn schema to represent native approvals, interrupts, resume/fork lineage, compaction and permission transitions. Missing host features remain explicit, never fabricated from prompt text. |
| O3 — Measurement and retention | O2 | New versioned collectors with invocation attribution independent of expected answers, typed causal records, per-attempt journals, raw capture, before/after state and attributable whole-trajectory usage. Persist every attempt before advancing; preserve partial results on exceptions. Current generic collection accumulates records in memory, so durable partial retention needs explicit work. |
| O4 — Bounded workflow verification | O2 | Decide which literal target-read/hash/prefix/newline forms and post-append null-output absence proof are supportable. Use fresh synthetic controls and raw event backing, reject wrong paths, unknown side effects, incomplete/failed lifecycles, stale pins and overlap. Distinguish genuine denied cache writes from verified target operations without erasing diagnostics. No broad shell emulation. Unsupported forms may remain unsupported and clearly reported. |
| O5 — Qualification and review | O3–O4 for the relevant stage | Fake-server positive and adversarial negative controls pass; disabled collection performs no provider call; permission isolation is checked without a model where possible; prepare an immutable stage manifest with exact counts and stop rules. Run only checks appropriate to new code. Independent instrument review precedes any live approval. |
| O6 — Stage reviews and final audit | Each approved stage; S7 after all retained cells | Retain semantic-first judgments, raw attribution and a per-cell evidence/behavior/promotion table. Audit all original files and modes, compare claims to raw locations, publish a sanitized report and keep raw traces private. |

The current [Codex adapter](codex-runtime-evidence.md) accepts only one explicit
`prompt/user` turn, disables other discovered skills and reports invocation from
explicit acceptance. The [turn contract](../harnessmith/evaluation_turns.py)
does not contain native approval IDs, resume/fork lineage or effective permission
transitions. The frozen v11 collector is one explicit append turn with approval
`never`. Extend none of them in place for these new experiments; preserve their
source snapshots, behavior and old report identities.

O1–O2 must document whether compaction has separately metered model work and
whether fork/resume counters include inherited history or reset. O3 must retain
thread/turn/compaction identities and counter baselines, then aggregate documented
totals or deltas without counting inherited cumulative usage twice. Include
compaction usage when it is part of the required trajectory total; unavailable
usage is not zero. If that total cannot be attributed, the cell remains
blocked/incomplete and cannot support a complete usage claim. Qualify these
accounting rules with synthetic reset, inheritance and compaction controls.

Qualification controls must include: wrong or missing invocation evidence;
early/denied unauthorized actions; duplicate, missing or reordered lifecycle
events; action after abort; nonzero hook exits and missing output; false resume,
wrong fork lineage, absent compaction; permission widening; source/package drift;
null/missing/noisy read output; malformed protocol; interrupted capture; and
unavailable usage. Matching expected text alone cannot make these controls pass.
No model judges or live capability probes are implicit in S1.

## Stopping rules

1. Freeze the stage's cases, treatments, models, versions, permissions, instruments,
   expected native events, counts, deadlines and review rules before collection.
   Approval applies only to that manifest; this plan starts or queues nothing.
2. Stop at the declared number of attempts regardless of behavior scores. Three
   failures remain three failures. No retry, replacement, extra baseline, extra
   judge or opportunistic new case is included in these ceilings.
3. Stop the stage immediately on provenance/integrity failure, unexpected
   permission widening or out-of-scope activity, model rerouting, malformed
   protocol, timeout, missing required usage or an unaccounted lifecycle. Retain
   all completed, interrupted and unattempted slots; do not automatically use
   unused slots after a repair. Expected fixture denials/nonzero hook exits are
   case observations, not infrastructure defects.
4. Completed behavioral failures with intact instrumentation remain in the fixed
   batch. Unknown command forms retain failed/unverified findings. Classifier
   limitations must not erase actual raw actions or be mislabeled model failures.
   If a limitation prevents the named question from being measured, mark that
   cell incomplete and apply rule 3 rather than spending more attempts.
5. No per-output parser patching, instrument changes, prompt coaching or router
   changes during a batch. New shell spelling alone does not create an automatic
   repair task. O4 gets one planned offline design/qualification cycle; if its
   essential question remains unmeasurable, report the blocker and request a
   revised scope before another cycle. Ordinary fixes needed to meet that
   cycle's frozen negative controls are not new live authorization.
6. A necessary later repair receives new versions and fresh synthetic tests.
   Never replay/regrade old traces to replace their verdicts. A new collection
   proposal states the unresolved cell, prior attempts and additional count;
   it is outside this plan's existing approval and ceilings until accepted.
7. Review and publish each stage's findings before proposing the next stage.
   Readiness to advance depends on measurement integrity, not a perfect behavior
   score. A serious behavior failure may justify stopping further spending and
   proposing corrective work; it does not silently close the unobserved cells.
8. New host releases and unrelated defects become explicitly tracked follow-up
   proposals. Do not automatically restart completed cells on every version
   update. Preserve the originally stated configuration limits.

## Final acceptance audit

For each of the 55 host/case cells, list the cohort/configuration, complete and
incomplete attempts, raw/provenance locations, instrument coverage, reviewer,
five separate dimensions and evidence/behavior/promotion outcomes. Reuse the
three historical Codex reference cells without new scoring; retain their known
review limitations. Record cache/input/output/latency distributions only within
comparable cohorts. No aggregate savings or equivalence assertion is required.

The independent audit must check A01–A12, supported negative conclusions,
provenance/retention, review order, all consumed authorizations, unattempted slots
and any demonstrated host limitations. Explicitly identify behavior defects and
promotion-policy work that remain. Do not label collector blind spots as proven
host limitations. If required live coverage is still missing, keep OPT-004 open
and state the exact cells; the full cross-runtime scope is not silently deferred.

When the retained evidence requirements are satisfied, add a current closure
entry to the status ledger and link the audit. Preserve the dated history,
including v11's 0/1. Completing this plan's evidence work would not promote the
authored router, alter the original skill or change the leave-inline default.

## S0 planning outcome (historical)

S0 is documented and the full-scope choice is recorded. S1–S7 are pending.
This task produces the plan and navigation links only. It runs no new benchmark,
preparation, provider session, hook, historical normalization or score calculation.
The next implementation deliverable is **O1–O2: a capability inventory and exact
prospective contracts**, followed by stage-specific offline qualification.

## S1 implementation checkpoint — 2026-11-02

The subsequent request to work on this plan begins its offline implementation.
The [host inventory](opt-004-host-inventory.md) records local availability,
official documentation, candidate controls, usage boundaries and unresolved
access. The [Codex record](opt-004-codex-capability.md) pins the installed binary
and selected generated protocol schemas. These are capability inputs, not live
observations or qualified adapters.

The [prospective case contracts](opt-004-case-contracts.md) now contain exact task
prompts and per-turn reference expectations for all 19 cases, synthetic project
and hook fixtures, the fixed 16-skill catalog and 11 actual compiler-generated
packages. Source, recipe, package and fixture bytes/modes are pinned. The
[additive native trajectory contract](opt-004-native-contract.md) represents
approval/action causality, lifecycle identity, effective permission snapshots,
task versus internal control turns, elapsed time and attributable usage. Old
turn contracts and collectors remain unchanged.

| Work | Current disposition | Remaining exit condition |
| --- | --- | --- |
| O1 | Offline inventory recorded; local Codex schema pinned; Claude/Cursor access and accounting gaps explicit. | Resolve version-specific surface, capability and usage questions needed by each stage. |
| O2 | Fixture/package/case preparation and native event contract implemented; partial. | Qualify exact host bindings, permission enforcement, Codex D3 equal canonical policy and lifecycle accounting; resolve L5 timing. |
| O3 | Partial: [November 3 retention foundation](opt-004-capture.md) tested with synthetic sources. | Native transports/normalizers, independent invocation attribution, permission/accounting bindings and durable stage scheduling remain open. |
| O4 | Pending. | One bounded operation-verification design/qualification cycle with fresh controls. |
| O5 | Structural synthetic tests and package-pin checks pass; full qualification pending. | Native fake-server controls, permission isolation, immutable stage manifest and independent instrument review. |
| O6 | Pending. | Approved-stage reviews and final independent evidence audit. |

The installed Codex CLI is `0.164.0-alpha.11.1`, a separate configuration from
the historical `0.163.0-alpha.11.1` cohorts. Claude and Cursor installations were
not found within the inventory's stated search boundaries; their versions and
account access remain unverified. Resume/fork counter baselines and compaction
usage attribution remain launch blockers wherever the inventory says unresolved.

Claude L5 has an additional timing/surface conflict: the documented native idle
compaction requires about an hour of inactivity on eligible interactive
surfaces. It cannot fit this plan's 180-second whole-trajectory limit. L5 stays
required and unobserved. Resolving it needs version-specific evidence that fits
the current contract or an explicit plan revision; this checkpoint changes
neither the deadline nor the retained scope. See the inventory's primary source.

The prepared Codex D3 compiled package represents explicit-only policy in native
metadata, while the unedited canonical fixture lacks that metadata. An equal
host-level policy or an explicit treatment decision is still needed; compilation
alone cannot close this comparability gap. Generic's explicit-only rejection is
an offline control, never a live-host limitation finding.

O1 documentation and O2 preparation do not close S1: new collectors, bounded
workflow verification, qualification controls and independent instrument review
are still required. S2–S7 remain pending. No new live attempts, fixture-hook
executions, model judges or historical regrades have occurred in this checkpoint.

Validation for this increment: 26 focused native-contract tests pass; the
offline verifier regenerates all 11 compiled packages and checks source/recipe/
fixture pins, the 16-entry catalog and unchanged 312/330/498 collection ceilings.
Fresh changed-content, executable-mode, missing-file and extra-file controls
are rejected. Repository schema/documentation checks and whitespace checks pass.
These are preparation checks, not full O5 fake-server qualification. Ruff and
mypy were unavailable in the inspected local environments and were not run.
