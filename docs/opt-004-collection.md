# OPT-004 O3 transport and stage collection — November 3, 2026

Status: **shared collection infrastructure and bounded Codex observation
implemented offline; O3 remains incomplete across the retained scope**.
This increment extends the [capture foundation](opt-004-capture.md). It does not
qualify effective host permissions or enable native collection. No live host,
provider session, fixture hook or historical regrade was run.

## New implementation

| Component | Implemented behavior | Qualification boundary |
| --- | --- | --- |
| [Stdio capture v1](../harnessmith/native_transport.py) | Bidirectional literal argv subprocess transport; continuous stdout/stderr readers; exact raw chunks and complete frame bytes committed before JSON parsing; bounded frame/queue sizes; deadline and owned process-group cleanup. | Tested with local credential-free fake servers. This transport is not a sandbox and does not establish any host capability or OS permission policy. |
| [Stage runner v1](../harnessmith/native_stage.py) | Frozen manifest, exact file/mode/tree pins, exclusive stage directory, durable slot consumed before launch, result retention before advancing, per-stage attempt/thread/task-turn ceilings, stop on collection/integrity/usage failure. | `run_mock_stage` accepts only mock mode and requires explicit enablement. It is not a native approval mechanism or a prepared live stage. |
| [Codex observer v1](../harnessmith/codex_native_observer.py) | Bounded fresh-thread/turn, command proposal/execution/completion, request/decision/resolution and cumulative usage mapping. Explicit skill input plus exact successful full root read can establish the bounded explicit invocation observation. | Synthetic protocol tests only. It emits no effective permission snapshot. Implicit activation, abstention, file changes, other tool families, hooks and lifecycle controls remain unsupported. |
| [Capture journal v2](../harnessmith/native_capture.py) | Serializes concurrent stream writes; retains the v1 mock-attempt interface; recovery handles a crash before journal/blob-directory initialization completes. | Local filesystem durability and private controller-owned evidence assumptions remain. Historical collectors are unchanged. |

The Codex mapping uses the pinned [0.164 schema inventory](opt-004-codex-capability.md)
and the [official app-server documentation](https://learn.chatgpt.com/docs/app-server)
retrieved November 3. In particular, a pending command item is not execution.
The observer waits for nonempty output or a completed command with an exit code.
A silent command's execution is therefore observed at completion; this does not
establish its actual start time for interrupt/deadline behavior checks.

Approval RPC IDs are typed separately from client request IDs. The original
request preserves any host `approvalId` alongside its RPC ID. Only single-action
accept/decline is recognized; session grants and uncorrelated resolutions fail.
The typed decision requires the server's resolution notification. Full raw
requests/replies remain available for the later native binding review.

The invocation rule accepts only an isolated literal `cat PATH` or `cat -- PATH`
with the canonical shell-quoted pinned root path, zero exit and byte-exact output.
Package identity uses O2's file-byte/mode inventory encoding. Null, partial,
noisy, wrong-path and failed output cannot certify a load. An answer claiming to
use a skill, explicit input alone, and a root read without explicit input do not
produce invocation observations. This is a narrow root-read control, not O4's
workflow verifier or proof of implicit selection.

## Retention and stage semantics

`StdioCapture` writes receive/stderr chunks from independent reader threads, even
when the protocol consumer is idle. Receive frames have separate content-addressed
backing. Invalid UTF-8/JSON, partial trailing frames and stream/queue overflows
stop collection with the bytes received so far retained. It does not silently
truncate or substitute a parsed message for the raw stream.

The stage runner retains a complete manifest as a blob and records each consumed
slot before starting its attempt. Every attempt has its own journal and isolated
workspace. The manifest pins the executed transport, capture, stage, contract
and observer Python sources; executable; normalization policy; source, recipe,
package and fixture inventories. It also retains exact commands, environment,
protocol steps, requested model/effort, resource/cache/permission descriptions
and count/deadline ceilings. These descriptions do not prove effective policies.

Inputs are checked before launch and after each retained result. Already measured
workspace outputs are excluded from later fixture comparisons; immutable inputs
and future workspaces remain pinned. Overlapping/reused attempt workspaces are
rejected. A final-attempt immutable-input change still stops the stage.

Thread creation/resume/fork and task-turn requests are capped before sending.
Observed thread/turn overages are retained and then fail the attempt. Each stage
has a maximum 180-second per-attempt deadline including snapshot/startup and
normalization overhead. Cleanup kills the owned process group, drains/join readers
and retains cleanup errors. Cleanup has a separate bounded wait so that timeout
handling can reap processes; a timed-out attempt cannot become complete.

After the scripted terminal boundary and transport cleanup, every queued captured
frame is normalized before final usage selection. Whole-trajectory totals use
one final cumulative interval per fresh thread, not a sum of repeated totals or
`last` plus `total`. Every observed task turn needs usage backing. Absent cache
write data remains null; resets and inherited epochs are unsupported. Late usage
is retained when received, but native delivery/finality semantics still need
qualification. No live whole-trajectory accounting claim follows from fake data.

A failure stops the stage, with no retry/replacement. Exclusive directories also
prevent restarting the same stage after a controller crash. Read-only recovery
reports its consumed slots and missing terminal records. SIGKILL can prevent
cleanup and after snapshots; recovery invents neither. An external supervisor is
still needed to contain orphan processes after controller death before native
launch. Reader errors and failed process-group termination are explicit failures,
not permission-enforcement evidence.

The observer/transport APIs are trusted Python test infrastructure. A mock label
is not a security boundary for arbitrary callbacks or commands. The tests use
synthetic helpers, explicit child environments and no credentials. The runner
contains no default executable, model credentials or native launch path.

## Remaining O3 requirements by scope

| Requirement | Disposition after this increment |
| --- | --- |
| Durable raw/partial retention and attempt scheduling | Implemented and tested with fake processes, including controller death and input drift. Native supervisor/startup/cleanup qualification remains O5 work. |
| Codex W/D/P observation | Partial fresh-turn/command/approval/usage mapping. Effective permissions and permission probes are not mapped; file changes, hooks, discovery and implicit/negative invocation need bindings. The integrated fake Codex case intentionally remains incomplete because permission evidence is absent. |
| Codex L1–L4 | Resume/fork/interrupt/compaction bindings and complete accounting remain unqualified; explicit requests fail closed. No synthetic event substitutes for them. |
| Claude retained cases | No installed/version-pinned native collector qualified. Shared stdio infrastructure does not establish Claude control, invocation or usage semantics. |
| Cursor editor retained cases | No editor event/control/usage source qualified. Substituting CLI/SDK would change the retained surface and is not done. |
| Immutable live stage / approval | Not prepared. O2 permission/accounting bindings, O4 operation checks and O5 independent review remain prerequisites. |

These are completion blockers, not waived requirements. The PR can deliver this
offline infrastructure increment, but cannot honestly mark full O3 complete with
these retained native-host obligations unresolved.

## Validation

The final full suite passes **862 tests with 85% repository coverage**, including
**74 focused tests**. Ruff passes, mypy passes all **69 source files**,
and repository schema/documentation checks plus the 19-case/11-package verifier
pass. All validation uses synthetic records and local helper processes.

Focused suites cover raw-before-parse durability, concurrent stderr, malformed
and unbounded protocol, process startup failure, deadlines, descendant cleanup,
controller SIGKILL, consumed slots, source/policy/mode drift, over-limit events,
missing usage, native/disabled gates, exact root-read attribution, approval
correlation, cumulative accounting and the explicit missing-permission finding.

```bash
python3 -m unittest discover -s tests -p 'test_native*.py' -v
python3 -m unittest discover -s tests -p 'test_codex_native_observer.py' -v
python3 evaluations/opt-004/verify_contracts.py
python3 scripts/check_repository.py all
python3 -m ruff check .
python3 -m mypy
```

The initial full-suite run found the draft's stale 15-schema assertion after the
native schema added a sixteenth; the assertion is updated. Type annotations and
variable names were corrected in the additive native contract without changing
its validation rules. The two standalone preparation scripts need imports after
repository-path setup; Ruff now scopes E402 exceptions to those two files,
preserving their pinned bytes. No historical instrument was changed.
