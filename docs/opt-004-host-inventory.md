# OPT-004 prospective host inventory — 2026-11-02

Status: **offline discovery; no host qualified for new collection by this
inventory**. This is O1 input to the
[completion plan](opt-004-completion-plan.md), not live evidence or a stage
authorization. All retained host/case cells remain required. Documentation
describes candidate capabilities; only version-pinned qualification and later
authorized collection can establish this experiment's runtime claims.

## Evidence rules and local discovery

Each surface below separates local availability, documented operations,
observable records, accounting, and remaining work. `Collector unsupported`
means this repository lacks the required capture path. `Host capability
unverified` means the selected installed version has not demonstrated the
feature. Neither is `verified not applicable`. No model, account entitlement,
effective permission configuration or backend version is inferred from a product
name or from the current documentation.

On 2026-11-02, read-only filesystem/PATH inspection found:

| Surface | Local version result | Search boundary |
| --- | --- | --- |
| Claude Code CLI | Unavailable in inspected locations; version unverified | No `claude` or `claude-code` on PATH; no matching app in `/Applications` or `~/Applications`; no Claude executable in the inspected standard bin directories. |
| Claude Agent SDK | Unavailable in inspected environments; version unverified | No `claude-agent-sdk` in active Python package metadata; no `@anthropic-ai/claude-agent-sdk` or `@anthropic-ai/claude-code` package in repository `node_modules` or active Node's global package directory. |
| Cursor editor | Unavailable in inspected locations; version unverified | No Cursor app in `/Applications` or `~/Applications`; no `cursor` on PATH. |
| Cursor Agent CLI | Unavailable in inspected locations; version unverified | No `cursor-agent` or `agent` on PATH or matching executable in the inspected standard bin directories. |
| Cursor SDK | Unavailable in inspected environments; version unverified | No `cursor-sdk` in active Python package metadata; no `@cursor/sdk` in repository `node_modules` or active Node's global package directory. |

The inspected standard bin directories were `/opt/homebrew/bin`,
`/usr/local/bin`, and `~/.local/bin` (the last did not exist). The active Node
global package directory was
`~/.nvm/versions/node/v24.14.0/lib/node_modules`. Discovery used
`shutil.which`, directory entry names, package-file existence and
`importlib.metadata`; it did not load SDKs, inspect credentials, install software,
change settings, start an app/server or submit a provider request. This bounded
search does not prove absence from every directory or another machine. Account
access and exact model/effort availability remain unverified.

## Codex

The [Codex capability record](opt-004-codex-capability.md) records the installed
CLI, pinned local schema excerpts, documented candidate operations and remaining
qualification work. It distinguishes the current `0.164.0-alpha.11.1` binary
from the historical `0.163` configuration. Schema support is not runtime
qualification; usage reset/inheritance and compaction accounting remain
unresolved. Its [machine-readable pins](../evaluations/opt-004/capabilities/codex-0.164.0-alpha.11.1.json)
belong to prospective work and do not replace historical source snapshots.

## Claude Code and Agent SDK

These are related but separately pinned surfaces. The future stage must name
whether it drives interactive Claude Code or an SDK-controlled Code process,
and record both SDK and Code versions where relevant. There is no Claude live
collector in the repository. Generic mock adapters do not qualify either
surface.

| Concern / cases | Offline evidence and candidate operation | Qualification still required |
| --- | --- | --- |
| Discovery and explicit use: R0–R2, D1–D3 | Claude documents automatic skill selection, explicit `/skill-name` invocation and `disable-model-invocation`. The explicit-only field also changes catalog visibility; skill content persists across turns, while `allowed-tools` grants expire on the next user message. [Skill semantics](https://code.claude.com/docs/en/skills) | Pin isolated catalog discovery and exact explicit invocation bytes. Capture actual invocation and successful resource reads independently of expected text; distinguish missing discovery from abstention. Recheck effective permissions on each continuation. |
| Continuation, restart/resume and fork: L1, L4 | CLI has continue/resume flags. SDK `resume` targets a saved session; `forkSession` branches its conversation into a new session. Session history persistence does not snapshot filesystem changes. [CLI](https://code.claude.com/docs/en/cli-reference), [sessions](https://code.claude.com/docs/en/agent-sdk/sessions) | Record source session, child session and fork point from native records; correlate process restart to resumed identity and restored permissions. Do not treat a subagent or copied prompt as a fork. |
| Native interrupt: L2 | SDK supports interruption. Recent Code versions advertise interrupt-receipt capabilities; an ordinary interrupt receipt can still list queued messages that may run afterward. [SDK reference](https://code.claude.com/docs/en/agent-sdk/typescript) | Pin the installed control protocol; capture request/receipt, action termination and quiet-window observations. An interrupt acknowledgement alone does not prove cancellation or absence of subsequent actions. |
| Explicit compaction: L3 | `/compact`, `PreCompact`, `PostCompact` and SDK `compact_boundary` are documented. Boundary metadata distinguishes `manual` and `auto`, but that distinction alone does not identify idle compaction. [Hooks](https://code.claude.com/docs/en/hooks), [SDK reference](https://code.claude.com/docs/en/agent-sdk/typescript) | Establish that the chosen control surface invokes a native compact operation, and retain its completion, session identity, post-boundary behavior and attributable usage. A user prompt describing compaction is insufficient. |
| Native hook dispatch: W3, H1–H4 | Hooks expose tool and session events including `PreToolUse`, `PostToolUse`, `PostToolUseFailure` and permission events. Nonzero exit handling depends on event and exit code. [Hooks](https://code.claude.com/docs/en/hooks) | Bind fixture phases to actual platform dispatch, preserve command input/output/exit records, and freeze failure semantics. A skill's own marker writes are not independent hook-dispatch evidence. |
| Approval and permissions: P1; lifecycle cases | SDK permission evaluation includes hooks, rules, modes and `canUseTool`; earlier decisions can bypass the callback. `dontAsk` denies rather than asking at the callback step. [SDK permissions](https://code.claude.com/docs/en/agent-sdk/permissions) | Pin a configuration that actually exercises deny then grant, correlate each native request with its decision/action, and qualify harmless non-model boundary probes. Record effective rules and sandbox state before/after transitions; setting names alone prove neither isolation nor approval handling. |

### Claude idle compaction is a concrete prelaunch blocker

Current documentation limits idle compaction to interactive terminal, VS Code
chat, or local/SSH desktop Code sessions, with auto-compaction enabled, one-hour
prompt caching, available feature flags, sufficient context, and about an hour
since the last request. The default context threshold is 200,000 tokens; its
documented override has a 100,000-token floor. The `idleCompaction` setting
requires Code 2.1.290 or later. These are documentation findings, not observations
of an installed version. [Idle compaction settings](https://code.claude.com/docs/en/settings-reference#idlecompaction)

**Disposition for L5:** the documented wait cannot fit the plan's 180-second
whole-trajectory bound. A headless SDK choice also does not establish the
documented interactive surface. Keep the cell required and unobserved. Before
any L5 preparation that depends on different timing or surface, obtain an
explicit plan revision or version-specific evidence of a qualifying operation.
Do not replace L5 with threshold-triggered auto-compaction, manual compaction,
an old pre-aged session or a synthetic idle event. No longer deadline or extra
surface is authorized by this inventory.

### Claude usage boundary

The usage guide distinguishes per-message tokens and cumulative result totals.
It specifically says Code 2.1.277 changed SDK/print resume accounting: normal
exit saves totals, and resume or fork restores earlier spend; older versions
started the resumed call's totals at zero. Summing restored cumulative results
double-counts prior work. The guide also distinguishes estimated cost from
authoritative billing. [Cost and usage](https://code.claude.com/docs/en/agent-sdk/cost-tracking)

For O2–O3, pin that behavior to the installed version and preserve raw
message/session IDs, every result, process-exit status and pre-transition
baselines. Qualify both reset and inherited counters. A fork's inherited parent
spend must be counted once across the trajectory; missing baseline or ambiguous
counter scope blocks aggregation. The opened documentation did not establish
whether every required native compaction's model work is exposed as separately
identifiable usage or included in each relevant total. That remains an explicit
L3/L5 accounting blocker, not a zero. Interrupted calls also need attributable
partial usage, not an assumed final result.

## Cursor editor: retained live target

The editor is the retained Cursor surface. CLI and SDK findings below are
separate capability records, not substitutes for editor evidence.

| Concern / cases | Offline evidence and candidate operation | Qualification still required |
| --- | --- | --- |
| Discovery / explicit-only: R0–R2, D1–D3 | Cursor documents automatic skill selection and explicit `/skill-name`; `disable-model-invocation: true` restricts the skill to explicit use. [Skills](https://cursor.com/docs/skills) | Installed-version catalog inspection, invocation attribution and read capture for the frozen 16-skill catalog. Catalog listing alone cannot prove selection. |
| Work and interrupt: W1–W2, L2 | Agent can edit files/run commands; the UI has Stop. [Agent mode](https://cursor.com/help/ai-features/agent) | An editor collector must capture native tool lifecycles, read outputs, cancellation and the whole quiet window. UI Stop is an operation, not proof of cancelled subprocesses. |
| Fork: L4 | Cursor distinguishes a full fork from a side chat; a fork copies parent conversation history according to its selected fork point. [Side chats and forks](https://cursor.com/help/ai-features/side-chats) | Native parent/child IDs, fork point, copied history boundaries, permissions and usage baselines. A side chat does not satisfy L4. |
| Hooks and approvals: W3, H1–H4, P1 | Hook documentation describes session/tool events and shell/MCP decisions `allow`, `deny`, `ask`. [Hooks](https://cursor.com/docs/hooks) | Correlated native approval decisions and actual dispatch/completion records; before/after effective permissions and harmless boundary probes. Hook permission output alone is not a recorded human/native approval decision. |
| Compaction: L3 | Editor hooks document observational `preCompact` with `auto`/`manual` trigger; context UI reports occupancy and summarization. [Hooks](https://cursor.com/docs/hooks), [context usage](https://cursor.com/docs/agent/prompting) | Pin an actual explicit control and completion event on the installed editor. A pre-event or declining context count cannot alone certify successful native compaction. |
| Continue and restart/resume: L1 | Conversation continuity is a required experiment operation, with no local editor installation available to inspect. | Identify restart/resume controls, stable IDs and a durable event source. Do not infer editor resume semantics from SDK `Agent.resume`. |
| Whole-trajectory usage: all cases | Context occupancy is not cumulative billed/token usage. No editor usage export was qualified here. | Attributable input, cache, output and latency records, interrupted usage and native compaction inclusion; determine whether resume/fork counters reset or inherit history. |

All 18 required Cursor cells remain **collector unsupported / host capability
unverified**, with behavior unobserved and promotion pending/ineligible. This is
an inventory disposition; the two blockers are separate dimensions and neither
waives a cell. Editor version, model/effort, access, automated controls, effective
permissions, raw event storage and usage attribution remain unresolved.

## Cursor Agent CLI: separate candidate surface

Official CLI parameters include `--resume`, `--continue`, explicit model
selection and JSON/stream-JSON output. The output reference describes session
IDs, tool events and a terminal result; failed streams may end without that
result. [CLI parameters](https://cursor.com/docs/cli/reference/parameters),
[output format](https://cursor.com/docs/cli/reference/output-format)

No CLI version or schema was available locally. Native approval correlation,
interrupt acknowledgements, explicit compaction, fork lineage, effective
permission transitions and complete token accounting are unqualified. A
future CLI implementation must retain stderr and truncated streams instead of
requiring a successful final JSON object. Choosing this surface to satisfy the
editor cells would require an explicit scope decision; this inventory makes
none. No CLI runs, sandbox commands or authentication checks were performed.

## Cursor SDK: separate candidate surface

The TypeScript SDK documents local and cloud runtimes, repeated `send`,
`Agent.resume`, `run.cancel`, tool-call IDs and summary start/completion events.
Local agents default to unrestricted tool execution; `autoReview` is a separate
option. Tool restrictions and `systemPrompt` are not persisted through resume
and must be supplied again. The opened reference did not expose a native fork
or explicit compact method; this is a documentation gap, not proof that no
version has either feature. [TypeScript SDK](https://cursor.com/docs/sdk/typescript)

The Python SDK documents per-turn usage events and per-run cumulative usage;
missing usage remains `None`. Its billed-usage query is distinct, and local
account access can be unavailable. These facilities do not establish editor
usage availability or complete compaction accounting. [Python SDK usage](https://cursor.com/docs/sdk/python)

**Disposition:** SDK installation/version, account access, permissions,
raw-schema compatibility and all experiments are unqualified. Pin local versus
cloud runtime separately; do not mix them in pairs. Before any prospective SDK
collection, qualify reset/inheritance baselines, interrupted partial usage and
whether summary work enters the totals. Treat absent usage as unavailable and
fail closed on resumed permission widening. A native user approval trajectory
must not be silently replaced by an SDK classifier decision. SDK adoption for
required Cursor editor cells needs an explicit scope change.

## O1 handoff and remaining gates

This record supplies documentation candidates and explicit local-access gaps;
it does not finish host qualification. Before a host's live-stage manifest can
be reviewed, the following remain necessary:

1. Select and inspect an installed surface/version; pin executable or package
   identity, model/effort, effective permissions, settings and API schema.
2. Implement the versioned collector and qualify native attribution, event order,
   durable partial retention and no-provider behavior while collection is off.
3. Resolve compaction usage and resume/fork baselines with version-specific
   evidence and synthetic accounting controls; preserve unavailable quantities.
4. Resolve the L5 timing/surface conflict explicitly without changing the other
   cells or spending additional attempts.
5. Freeze the relevant exact cases, prompts, paired packages, counts, resource
   policy and stop rules, then obtain the plan's separate live-stage approval.

Official sources above were opened on 2026-11-02. They are mutable documentation,
not installed-version snapshots. No historical report, score, collector or source
skill was changed to produce this inventory.
