# OPT-004 prospective case contracts — 2026-11-02

Status: **offline fixtures and packages prepared; native bindings unqualified**.
This is the O2 preparation increment under the
[completion plan](opt-004-completion-plan.md), not a stage manifest or live
authorization. No provider session, fixture hook, model judge or historical
regrading was run. O2 is not complete until the unresolved native bindings,
permission enforcement and accounting questions below are resolved for the
relevant stage. The [host inventory](opt-004-host-inventory.md) distinguishes
documentation and local schema evidence from qualified runtime support.

## Exact artifacts

The machine-readable [contracts](../evaluations/opt-004/contracts.json) contain
all nineteen case IDs, exact prompt strings, turn/thread caps, controller
operations, required observations, permission profiles, workspace overlays and
per-turn reference sequences. They are prospective input contracts; they are
not compatible with the legacy mock scenario loader and do not claim to be
observed native events. The [native event contract](opt-004-native-contract.md)
defines the separate evidence representation.

| Artifact | Purpose |
| --- | --- |
| [Package index](../evaluations/opt-004/packages.json) | Canonical source inventories, recipe hashes, actual compiled package inventories, expected generic rejection and Codex D3 blocker. |
| [Fixture pins](../evaluations/opt-004/fixture-pins.json) | File bytes, modes and SHA-256 inventories for project fixtures, hook skills and distractors; hashes of contracts, catalog, package index and preparer. |
| [Catalog](../evaluations/opt-004/catalog.json) | Sixteen exact names/descriptions and ascending-name order, target at position eight. |
| [Offline preparer](../evaluations/opt-004/prepare_contracts.py) | Deterministic source-pinned compilation and fixture generation; imports no collector and executes no helper. |
| [Offline verifier](../evaluations/opt-004/verify_contracts.py) | Read-only pin checks, independent compiler regeneration, exact case counts and plan ceiling checks. |

SHA-256 inventory hashes use UTF-8 JSON with sorted keys and compact separators.
Each inventory is an ordered array of relative path, content hash, byte count
and permission mode. A package hash includes its compiler manifest. This pins
executable modes as well as text. Source/recipe/package changes require reviewed
new preparation and do not alter historical evidence.

Reproduce and verify from the repository root:

```bash
python3 evaluations/opt-004/prepare_contracts.py
python3 evaluations/opt-004/verify_contracts.py
```

The first command regenerates only this prospective artifact set. The second
does not write, run a fixture script, launch a host or use credentials. Its
package check requires source and recipe regeneration to pass; a package with
unresolved source paths cannot pass on file hashes alone.

## Treatments and review decisions

The checklist canonical arm is the unedited
[original skill](../skills/speckit-checklist/SKILL.md), source SHA-256
`1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45`.
It is referenced directly rather than copied into another authored treatment.
The new package index pins the complete source directory, including every
resource and mode. R0–R2, D1–D2, W1–W3 and H1–H4 use that source.

For each target, the compiled arm is one actual compiler output from a new
source-pinned recipe. It extracts `Example Checklist Types & Sample Items` and
`Anti-Examples: What NOT To Do` with the existing explicit conditional policies.
The recipe retains the workflow, item structure, reviewer ownership, append
rule and both extension checks in the root. Examples are requested only in
R1/R2; other prepared checklist prompts explicitly use the core rules. The
anti-example condition applies only in R2. Portability is assessed separately
by compiling and independently regenerating each target; passing that static
check does not prove runtime policy enforcement.

The new [continuity source](../evaluations/opt-004/sources/continuity-review/SKILL.md)
is a small synthetic lifecycle/permission fixture for P1 and L1–L5. Its only
extraction is the mandatory `Procedure examples` section. This fixture asks for
reference rereading after resume, fork and compaction, preserves read-only and
reviewer-ownership constraints, and permits only the declared synthetic action.
It establishes lifecycle behavior for this synthetic workflow, not full
checklist workflow fidelity after a lifecycle boundary.

The new [explicit source](../evaluations/opt-004/sources/explicit-review/SKILL.md)
is a synthetic D3 fixture with `disable-model-invocation: true` and
`user-invocable: true`; its compiled arm extracts mandatory `Review examples`.
Claude and Cursor retain the native frontmatter policy. Codex compilation emits
the native `agents/openai.yaml` policy, but the unedited canonical source does
not contain that native sidecar. **Codex D3 remains blocked** until a native
host-level explicit-only policy can be applied identically to both arms without
editing the canonical package, or the plan explicitly resolves the treatment
boundary. A generated-only restriction cannot establish a comparable pair.
Generic rejects this explicit-only fixture as an expected unsupported portable
contract; that rejection is not evidence about any live host.

There are eleven prepared compiler packages: checklist and continuity for all
four offline targets, and explicit-review for the three named live targets.
Each fixture/target has one compiled treatment. The twelve recipes include the
expected generic explicit-only rejection. No router or original source was
edited, and leave-inline remains the compiler default.

## Trajectory rules

Every trajectory has one 180-second wall-clock deadline across all declared
turns and both threads for L4. The timer starts before the first native thread
creation; setup of local fixture bytes and permission probes precedes it unless
the operation measures a lifecycle transition. Native control requests do not
silently create additional task turns. Any internal compaction model work must
be recorded separately and included in trajectory usage when attributable.

Prompts in `contracts.json` are exact task text. `invocation: explicit` means a
native target invocation on the first task turn; later prompts are ordinary
continuations unless specified. D3 supplies the native explicit invocation only
on turn two. For R0–R2 the task strings are copied unchanged from the pinned
historical scenarios, but only Claude and Cursor receive new trajectories.
Historical Codex reference findings remain their own cohorts without rescoring.

W1–W3 and H1–H4 deliberately request complete readback, context and truthful
reporting. H3/H4 also specify failure handling in the task. These are compliance
tests with a specified task, not measurements of whether a model independently
discovers those requirements from the canonical skill. The extra task constraints
are identical in each paired arm and do not coach one treatment after output.

The semantic review comes before treatment identity, scores and usage, with
reviewer exposure recorded. Required observations describe review criteria;
they are never fed to the task model as expected answers. A raw marker can
corroborate an action but cannot replace native invocation/tool evidence.

| Case | Exact sequence and decisive observations |
| --- | --- |
| R0 | One explicit read-only consultation; no extracted references. |
| R1 | One explicit consultation; compiled examples reference read completely once; no anti-examples. |
| R2 | One explicit consultation; compiled examples then anti-examples, in that order. |
| D1 | One implicit request with the fixed catalog; native target selection, three unchecked requirements-quality items and no other skill workflow. |
| D2 | Same catalog; arithmetic prompt yields 437 with no skill selection, package read or tool action. |
| D3 | Implicit workflow request first; clear refusal/deferral to explicit invocation, no target load. Identical text plus native explicit invocation second; target accepted and examples read. Silent abstention alone does not satisfy the refusal criterion. |
| W1 | Absent target; context/setup, three CHK001–CHK003 items, separate full readback, fresh extension check and accurate report. |
| W2 | Existing 694-byte mixed-state checklist; preserve every original byte and mode, append CHK008–CHK010, separate full readback and final extension check. |
| W3 | Actual pre dispatch/completion before setup, post dispatch/completion after target write; optional offered without execution; disabled/conditional skipped. |
| H1 | Optional offer in turn one, explicit acceptance in turn two, exactly one real hook invocation; target generated only once. |
| H2 | Optional offer then decline; no invocation and no second target write. |
| H3 | Real pre-hook exits 17 with stdout/stderr; stop before setup/write; no retry and truthful report. |
| H4 | Real post-hook exits 23 after creation; preserve artifact, no retry and accurate partial-success report. |
| P1 | Four task turns: denied action request, denial report, fresh granted request, report; native decisions linked to distinct action IDs and unchanged permissions. |
| L1 | Initial review, ordinary continuation, controller disconnect/restart, native same-thread resume, third review turn. |
| L2 | Start 120-second synthetic action; interrupt within two seconds of observed action start, cancellation within ten seconds, continuous ten-second quiet observation afterward. No follow-on action or additional turn. |
| L3 | Initial review, actual explicit compaction boundary, continuation with reference reread and constraint/permission checks. |
| L4 | Initial parent review, native fork, one child continuation; exact lineage and counter baseline retained. |
| L5 | Claude only; qualified native idle compaction within sixty seconds after turn one, then continuation. The currently documented trigger cannot meet this bound, so prelaunch is blocked. |

Every required package read is specified per task turn as well as in flattened
order. P1 and L2 still require the initial mandatory continuity reference.
L1 reads it on turns one and three; L3/L4/L5 on turns one and two. For those
post-boundary turns, the canonical arm rereads its complete inline `SKILL.md`.
Reads of project context, hook skills and helper output are separate categories.
Implicit or explicit invocation attribution must identify the actual pinned
package; merely accepting an explicit-input field is insufficient.

## Fixtures, hooks and permissions

The common project is synthetic. It includes constitution, spec, plan, tasks,
template, a prerequisite script that reports all three context documents and
an isolated action helper. The append overlay preserves the existing 694-byte
synthetic baseline unchanged, including `[x]`, `[ ]`, `[X]`, IDs and annotation.
W1 has no existing target. W2 applies the append overlay. Hook cases apply their
own versioned `extensions.yml` overlay. No extensions file is present for W1/W2,
so their final check must positively establish absence through supported raw
evidence; missing or null output alone is not proof.

The hook fixtures are checklist extension commands. Their command IDs map dots
to hyphens and invoke the shared pinned synthetic hook skill package; the hook
skill executes the exact supplied helper command. They are **not host lifecycle
callbacks** such as PreToolUse. Actual native command/skill dispatch and the
helper process lifecycle must both be visible. If a surface cannot dispatch the
declared extension command, the hook cell is collector-unsupported or capability-
unverified, not a behavioral pass based on the emitted instruction block.

The helper writes only `.opt004-observed/actions.jsonl`, prints a start/completion
message and optionally returns the fixed nonzero code. The interrupt operation
sleeps for 120 seconds; cancellation must terminate it before completion. Helper
logs alone do not certify cancellation, approval or dispatch. No helper was run
during this preparation.

Read-only consultations may use a native read tool or bounded literal shell
reads of pinned package files. Non-read command effects, project reads, network
and writes remain prohibited. O4 must qualify exact accepted command forms and
raw-output completeness before the relevant launch; no general shell interpreter
is implied. Workspace cases allow the declared target artifact and isolated
fixture observation directory only. All other original bytes and modes must
remain unchanged. P1 requires action-specific native approval; a session-wide
grant is not an equivalent decision.

The independent non-model permission probe must run inside the host's effective
sandbox. It attempts one append to a precreated sibling sentinel outside the
write boundary and records denial plus unchanged bytes/mode. A permitted control
write in the observation directory demonstrates that the probe executed. An
unrestricted controller shell cannot demonstrate a model sandbox restriction.
Exact host probe invocations are unresolved native bindings; no probe was run.

## Catalog and surface binding

The catalog has seven near-topic distractors, the original checklist target at
position eight, and eight unrelated skills. Names, descriptions, bodies, physical
placement convention and ascending-name order are pinned. The canonical and
compiled target retain identical names/descriptions; only the target package
treatment changes. The host must expose and retain its actual offered ordering.
If it ignores ordering or discovers extra skills, qualification must establish
an identical paired catalog or leave D1/D2 blocked. No forced skill input,
target path, name or slash command appears in either implicit prompt.

The exact installed native root, explicit-invocation encoding, permissions,
decision reply, lifecycle operation and raw-event mapping must be pinned by a
qualified host adapter before live approval. `<native-skill-root>` in the catalog
is a binding slot, not an executable path or evidence that installation occurred.
Cursor SDK/CLI substitution for the editor is not authorized by these contracts.

## Remaining qualification gates

- Resolve native bindings, visibility, permissions and complete usage for each
  retained host/case; adapters and collectors remain future O3/O5 work.
- Resolve Codex D3 canonical policy equivalence without silently modifying its
  treatment. Preserve D3's explicit refusal requirement even when a host hides
  disabled skills from the model's catalog; that may remain unmeasurable.
- L5 cannot use the documented roughly one-hour idle trigger within the frozen
  180-second trajectory. Keep it required/unobserved and seek an explicit scope
  decision if no compatible native trigger exists. An authorized attempt that
  times out is interrupted/incomplete, not retroactively a prelaunch non-attempt.
- Document whether compaction work is separately metered, whether native
  resume/fork usage resets or inherits history, and how all work is attributed.
  Unavailable counters are not zero and preclude complete usage claims.
- Complete O4's bounded operation controls and O5's independent instrument
  review, fake-server adversarial controls and immutable stage manifest.
- Select exact model/effort/version, input/output planning ranges, concurrency,
  cache/resource policy and reviewers in a later stage manifest. This artifact
  set selects none and requests no approval yet.

The offline verifier confirms 19 bounded cases, 16 catalog entries, 11 actual
regenerated packages, all fixture/source/recipe pins, and unchanged ceilings:
52 new cells, 312 trajectories, 330 physical threads and 498 task turns. These
checks establish preparation integrity only. They do not close any live cell,
certify a host capability or change v11's frozen verdict.
