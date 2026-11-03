# OPT-004 prospective native trajectory contract

Status, 2026-11-02: **offline structural contract; no qualified live adapter**.
This additive contract addresses part of O2 in the
[completion plan](opt-004-completion-plan.md). It does not change the old
[evaluation turns](../harnessmith/evaluation_turns.py), scenarios, collectors,
raw evidence or grades. It authorizes no live collection.

The [implementation](../harnessmith/native_contract.py) provides
`parse_trajectory`, `integrity_findings` and `usage_totals`. The
[published v1 schema](../schemas/native-trajectory-v1.schema.json) defines shape;
`trajectory_schema()` generates that same schema. Cross-record causal checks
run separately. Both are needed: JSON Schema validation alone does not establish
valid lineage, authorization, measurement integrity or a completed case.

## Records and boundaries

A trajectory identifies its target, exact surface and installed host version,
mode (`native` or `mock`), capture status and elapsed capture duration. The stage
manifest must additionally pin model/effort, instruments, source/recipe/package,
permissions, prompts, case requirements and approval. This trajectory document
is not a substitute for that manifest.

Every event has a unique ID, increasing sequence, nondecreasing elapsed
milliseconds from one monotonic trajectory clock, thread ID, nullable task turn
ID, nullable earlier causal event ID, origin and raw location. A restart or fork
must not reset that trajectory clock. The declared capture duration supports the
later case checker’s deadline and quiet-window checks; sequence alone cannot
measure them. `native` means backed by the host’s raw records, including a
qualified normalization of those records. `controller` is an orchestration
observation and cannot establish a native lifecycle acknowledgment. `mock`
remains explicitly synthetic and cannot qualify a live cell. Generic is only an
offline target.

| Record family | Required distinction |
| --- | --- |
| `thread.started`, `thread.disconnected`, `thread.resumed`, `thread.forked` | Resume retains thread ID, correlates the prior process disconnect and names a new process. Fork creates a new child ID and cites an earlier event on its actual parent. |
| `turn.started`, `turn.completed` | Task/control role, nullable prompt raw location, native turn identity and completed/failed/interrupted terminal status. Task turns require real prompt backing; internal control turns have no synthetic user prompt. Completions correlate their starts; overlapping turns on one thread are flagged. |
| `approval.requested`, `approval.decided` | Approval ID, proposed action ID, request/decision causal relation and grant/deny. The adapter must preserve the raw RPC request ID as well as any host approval ID in backing evidence. |
| `action.proposed`, `action.started`, `action.completed` | A queued item is not execution. Start requires execution evidence; completion retains succeeded/failed/cancelled, nullable exit code and output backing. Dispatch distinguishes tool, skill command, host hook and non-model boundary probe. |
| `interrupt.requested`, `interrupt.completed` | Request identity, cancellation acknowledgment and turn correlation. New action starts after the request are flagged; already-running cancellation and quiet-window behavior need the case checker. |
| `compaction.started`, `compaction.completed` | Native compaction identity and explicit/idle/automatic trigger. A prompt claiming compaction cannot generate these records. |
| `permission.snapshot` | Effective canonical read/write capability sets, network permission and approval policy. Resume/fork/compaction requires a new snapshot before subsequent work. Earlier snapshots remain comparison baselines. |
| `invocation.observed`, `discovery.snapshot` | Skill/package identity and independent raw invocation proof; catalog hash, discovery backing and capture completeness. Expected invocation does not generate an observation. |
| `read.observed`, `output.recorded` | Read category (package reference/project context/target/other), exact path, blob SHA-256, byte range and full-read flag, associated completed successful action and output raw locations. |

For Codex specifically, a command item can start before its approval request.
That host notification can only establish `action.proposed` until execution is
independently established. A declined pending command is retained as raw
proposal/approval evidence, not invented execution. `thread.forkedFromId` and
subagent `parentThreadId` must not be interchanged. See the
[host inventory](opt-004-host-inventory.md) for the pinned source evidence and
remaining binding work.

Permission set comparison is deliberately literal and conservative: paths and
capabilities must already be canonicalized by a reviewed adapter. The contract
does not interpret wildcard grants, recursive paths or host-specific policy
precedence. A changed approval policy is a finding requiring review. Invocation,
discovery and read records preserve fields needed by later checks; constructing
those fields is not proof that a read classifier or discovery collector exists.

## Usage accounting

Each usage interval names a meter, counter epoch, thread, normalization-policy
reference, raw source, and disjoint work IDs. Work IDs reference `turn.started`
or `compaction.started` events. Every native turn (task or internal control) and compaction must be covered
exactly once; overlapping or missing coverage prevents totals. If a host total
already includes a compaction, that one interval must cover both identities.
Do not add a second separately counted compaction interval for the same work.
A host-internal compaction turn and its compaction start can share one inclusive
interval; this is not an additional task turn. Stage validators, not this event
contract, enforce the separate case task-turn and physical-thread caps.

The five normalized counters are:

- `input_tokens`: all input, including cache reads and cache writes.
- `cached_input_tokens`: the cache-read subset of normalized input.
- `cache_write_input_tokens`: the cache-creation/write subset of normalized input.
- `output_tokens`: all output, including reasoning output where reported.
- `reasoning_output_tokens`: the reasoning subset of normalized output.

A host’s raw `input_tokens` need not already have this meaning. In particular,
Claude cache categories must be reconciled by a versioned policy before these
normalized values are emitted. Retain raw categories and provider-specific
additional metrics in the backing evidence. `null` means unavailable, not zero.
A known unsupported category may be zero only when pinned source evidence and
qualification establish that interpretation. Missing counters produce a finding
and `usage_totals` returns `None`.

`basis=delta` requires a null baseline and `request_delta` reason. A cumulative
interval requires explicit baseline and final counters. Its reason distinguishes
fresh, inherited, reset and continuation. Fresh/reset baselines are zero;
inherited baselines are subtracted rather than counted as new work. Contiguous
intervals on one thread/meter/epoch must meet at the same counters. A reset needs
a new epoch. Values cannot decrease within an interval. This allows synthetic
reset/inheritance controls without assuming a real host follows those rules.

The installed host’s handling of resume/fork counters, compaction cost and
cache categories must still be established in O1–O3. A plausible subtraction
formula is not such evidence. Unknown accounting keeps the required cell
blocked/incomplete. Totals are unavailable for any trajectory integrity finding;
no input/output savings, billing or cross-host aggregate is computed here.

## Findings, retention and remaining qualification

Shape errors raise `ValueError`, including unknown fields/event kinds. Validly
shaped bad observations remain parseable: duplicate/reordered events,
uncorrelated approval, missing execution output, failed lineage, stale or widened
permissions, unfinished lifecycle, mock/native confusion and missing/overlapping
usage produce separate findings. A denied approval or nonzero fixture exit with
intact records is an observation, not automatically an infrastructure failure.

O3 must durably capture raw bytes before parsing and preserve partial attempts
on exceptions. This module does not implement a journal, provider call, raw
normalizer, executable scenario, shell classifier, launch gate or semantic judge.
Its checks do not establish full O5 qualification. In particular, source/package
drift, complete discovery for abstention, correct host dispatch, quiet windows,
required case-specific events and exact target-read/append proof remain adapter,
manifest and case-checker responsibilities. A well-formed empty or partial record
cannot claim measured zero usage.

The focused [synthetic tests](../tests/test_native_contract.py) exercise strict
shape, grants/denials, pending items, interrupt actions, failed hooks/reads,
resume/fork/compaction, permission refresh, usage inheritance/reset/overlap,
unknown cache data and interrupted capture. They do not invoke fixture hooks or
any provider and do not close a live evidence cell.
