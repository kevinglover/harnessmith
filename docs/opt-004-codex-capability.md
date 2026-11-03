# OPT-004 Codex capability record — 2026-11-02

Status: **offline inventory, not a qualified live adapter**. This record belongs
to O1 of the [completion plan](opt-004-completion-plan.md). No app-server was
initialized, thread started, model queried, fixture hook executed or permission
setting changed to produce it. Model availability and backend snapshot are
unreported. This record does not consume or grant live collection authorization.

## Installed identity and reproducible evidence

The installed executable reports `codex-cli 0.164.0-alpha.11.1`. The enclosing
desktop app's plist reports bundle `com.openai.codex`, version `26.1021.31345`,
build `21828`. The candidate measured surface remains **app-server over stdio**;
the enclosing app identity does not turn its events into desktop UI evidence.
The earlier `0.163.0-alpha.11.1` cohorts remain distinct configurations.

The [offline schema inventory](../evaluations/opt-004/capabilities/codex-0.164.0-alpha.11.1.json)
contains the executable path/hash, repository revision, commands, selected JSON
schema excerpts and hashes of their original generated files. Excerpts label
filtered method unions and retain their JSON pointers. They are inspection
evidence, not a new provider protocol implementation. Reproduce on the same
binary using `codex --version` and
`codex app-server generate-json-schema --experimental --out <temporary-directory>`.
These are local tooling operations, not a running app-server. The commands
exited successfully with a PATH-alias permission warning; it was not suppressed
or repaired by widening permissions.

## Operations exposed by this binary

Every entry below is **schema-supported, runtime-unverified**. The referenced
schema names and excerpts are retained in the inventory. Expected answers in a
fixture cannot establish that any operation occurred.

| Required cases | Local protocol evidence | Remaining adapter obligation |
| --- | --- | --- |
| R0–R2, W1–W2 | `TurnStartParams.UserInput` supports explicit `skill` input; native item lifecycles carry command actions/output. | Bind accepted input separately from actual invocation; attribute reads and target writes from raw native operations. Historical Codex reference cells are reused, not rerun. |
| D1–D3 | `skills/list`, `skills/config/write`, `skills/extraRoots/set`; `SkillMetadata` reports path, name, description, scope and enabled state. | Freeze the complete 16-skill discovery input and ordering, omit explicit skill input for D1/D2, independently establish invocation/abstention, and verify an explicit-only policy representation. Listing a skill is not invocation. |
| P1 | `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `serverRequest/resolved`. Command requests carry thread/turn/item IDs and optional `approvalId`. | Retain JSON-RPC request IDs as well; correlate deny and one-action grant with native action execution. A pending command item is not proof that execution began. Do not grant session-wide or persistent amendments. |
| L1 | `thread/resume`; its response includes thread identity, model, provider, sandbox and approval settings. | Actually disconnect/restart and resume the same thread; verify retained constraints and effective permissions, including non-model probes. A second prompt in one process is insufficient. |
| L2 | `turn/interrupt` requires both `threadId` and `turnId`; terminal turn/item records are available. | Establish cancellation of the running fixture process and the complete quiet window; an interrupt acknowledgement alone does not prove cancellation. |
| L3 | `thread/compact/start` accepts a thread ID; native compaction notifications/items are exposed. | Retain the real boundary and its model work, not a textual claim of compaction; account for internal turns separately from task turns. |
| L4 | `thread/fork` and `Thread.forkedFromId`. `parentThreadId` instead denotes a subagent; `sessionId` can be shared. | Verify a distinct child with the correct fork source, before/after permissions and usage baselines. Do not substitute subagent creation or use shared session ID as unique thread identity. |
| W3, H1–H4 | Native command item lifecycles; separate `hook/started` and `hook/completed` records have hook run IDs, event names, execution mode and status. | Checklist extension dispatch must retain its actual tool/process exit/output and order. Host lifecycle callbacks are a separate mechanism. `HookRunSummary` has no numeric exit-code field; a hook summary or marker cannot replace exit evidence. |

The official app-server guide documents lifecycle requests, correlated approval
flows, and compaction item lifecycles. It also states that asynchronous hooks
lack the synchronous hook notifications. Its `thread/shellCommand` operation
runs outside the thread sandbox, so it cannot establish the requested sandbox
denial probes. These are documented constraints, not tests of this installation.
[Official app-server documentation](https://learn.chatgpt.com/docs/app-server)

Native lifecycle hooks require their own configuration and trust setup; all
matching active layers may contribute hooks. O2/O5 must freeze those layers and
trust identity before launch. Do not assume that a checklist extension manifest
installs native callbacks.
[Official hook documentation](https://learn.chatgpt.com/docs/hooks)

Official skill documentation describes both explicit and description-based
implicit activation. It does not establish that the prospective fixed catalog
will be selected correctly, or supply an observation for D1–D3.
[Official skill documentation](https://learn.chatgpt.com/docs/build-skills)

## Usage and permission accounting blockers

The local `ThreadTokenUsageUpdatedNotification` requires thread and turn IDs and
contains `last` and `total` counters. Its breakdown includes input, cached input,
output, reasoning output and total tokens, plus optional cache-write input.
Keep an absent cache-write measurement explicitly unavailable; the schema's
default is not proof of observed zero cache writes.

Neither those schemas nor the inspected documentation establish whether
fork/resume totals inherit or reset, or whether compaction model work is fully
included in the thread totals. **Whole-trajectory accounting for L1/L3/L4 is
unresolved.** O3 must retain counter baselines and work identities and O5 must
qualify reset/inheritance/compaction controls. Do not sum parent and child totals
without an established baseline, add `last` to an already inclusive `total`, or
substitute the Responses compaction API's usage for Codex app-server usage.

Start/resume/fork responses and `ThreadSettingsUpdatedNotification` expose
configuration. They do not prove OS enforcement or the absence of other config
layers. Required boundary probes, isolated roots, denied outside writes and
permission comparisons remain O3/O5 work. No new case is launch-ready merely
because the schema contains a matching method. The old one-turn collectors
remain unchanged and unqualified for these new trajectories.
