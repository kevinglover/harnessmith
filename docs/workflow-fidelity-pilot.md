# OPT-004 minimal workflow fidelity pilot

Status: offline preparation and instrument checks only. No live sessions are
authorized or launched by this work. The proposed model is **GPT-6 Luna**, low
reasoning. Historical benchmarks, source skill and router package are unchanged.

## Exact proposed batch

[The versioned pilot definition](../evaluations/workflow-fidelity/pilot.json)
selects the original package and the reviewed router. Each case runs once per
variant in a fresh workspace: **3 cases × 2 variants × 1 repetition = 6 sessions**.
These six sessions diagnose workflow gaps; they cannot establish repeatability,
equivalence, workload savings, or completion of OPT-004. Mandatory and conditional
extraction are omitted from this first workflow probe to keep scope small.

| Case and exact prompt | Expected artifact and behavior | Primary failure controls |
| --- | --- | --- |
| [Create](../evaluations/workflow-fidelity/prompts/create.md) | Create `specs/001-invitations/checklists/security.md` using the supplied template; exactly four unchecked questions, CHK001–CHK004. Cover roles/workspace boundaries, measurable expiration, expired/reused invitations, and retention. | Missing setup/context/template reads, wrong path, malformed/checked items, invented policy, implementation-testing questions, inaccurate final report. |
| [Append](../evaluations/workflow-fidelity/prompts/append.md) | Preserve the complete original file prefix, notes and mixed `[x]`/`[X]`/`[ ]` states; append exactly three unchecked questions, CHK008–CHK010, about expiration, expired/reused outcomes and retention. | Overwriting/reformatting old content, normalizing existing markers, renumbering, duplicate IDs, checked new items, failure to inspect the existing file. |
| [Hooks](../evaluations/workflow-fidelity/prompts/hooks.md) | Create the four-item checklist; actually run and await mandatory pre-hook before setup/generation and post-hook after generation. Offer the optional hook without executing it; skip disabled hooks and hooks with nonempty conditions without evaluating expressions. | Announcing execution without invocation, wrong ordering, missing completion, forbidden hook execution, tampered scripts, incorrect artifact/marker hashes. |

For all router sessions, a successful read of
`references/project-generation.md` must precede project actions. The original
package has this guidance inline. Neither variant needs the optional example or
anti-example references for these frozen tasks. Project context reads and package
reference reads are recorded separately. Exact reference expectations belong to
the case and must not be relaxed after collection.

The prompts intentionally settle scope, depth, audience and destination and map
synthetic hook IDs to a local adapter. This tests explicit invocation and the
specified workflow under those conditions; it does not test automatic discovery,
clarification quality or real extension command dispatch.

## Isolation and preparation

The fixtures contain a small synthetic invitation specification, constitution,
checklist template, append seed, read-only prerequisite stub, and a local Python
marker hook. The stub emits only local feature/template JSON. The marker hook
writes only `.pilot/events.jsonl`, recording whether the target exists and its
hash. No real `.specify` scripts or extensions run. Package copies and manifests
are outside the original skill directory; each prepared session has its own
workspace and before-state hashes.

Prepare the review bundle without credentials or provider access:

```bash
python3 -m harnessmith.workflow_fidelity prepare \
  --output /tmp/opt004-workflow-review
```

The destination must be new. Preparation pins the source, router review and
package files, fixture files, exact prompt, checker and rubric. A router hash
or retained-source mismatch fails preparation. There is no live-launch switch.
The `check` subcommand validates a prepared session against an externally supplied
normalized observation and its resulting workspace. It never executes commands
from observations. Use `python3 -m harnessmith.workflow_fidelity check --help`
for its exact file arguments.

The existing `CodexEvaluator` is read-only and supports a single explicit turn.
It must not be used to claim collection of writes or hook actions. A future
write-capable collector must be reviewed and tested before an approved launch:
restrict writes to the fresh workspace, disable network and unrelated skills,
retain raw commands/results and artifact snapshots, verify actual permissions,
and derive normalized facts from successful events. It must reject unsupported
events instead of inventing observations. That collector is not implemented here.

## Offline checks and interpretation

Run the focused instrument checks:

```bash
python3 -m unittest tests.test_workflow_fidelity -v
```

Validation on 2026-10-24: all 181 repository tests passed, including 18 workflow
instrument tests; total measured code coverage was 84%. Ruff, mypy, schema and
documentation checks, and `git diff --check` passed. Preparation produced the six
fresh workspaces with `live_sessions_started: 0`. A before/after hash comparison
confirmed all 417 protected historical evidence, variant, report and original
source files were unchanged. The
[observation contract](../evaluations/workflow-fidelity/README.md) documents how
to supply normalized facts and why they remain subject to raw-trace review.

Positive controls use authored artifacts and **offline-simulation** traces.
Negative controls corrupt artifacts or events to demonstrate that the checker
rejects them. Executing the synthetic setup and marker scripts in temporary
directories validates only those local fixtures. It does not run the skill or
establish model fidelity.

The checker reports content screening, formatting, reference behavior, workflow
checks and efficiency separately, following the
[v2 rubric](../evaluations/variants/router-quality-rubric-v2.md). Content keyword
screens cannot establish semantic correctness. Normalized events can be forged;
marker files alone cannot prove hook execution. Semantic review and raw-trace
review therefore stay pending even when automated checks pass. A full live verdict
requires both reviews, every applicable hard check, and retained raw evidence.
Efficiency stays unassessed without actual usage; the six single observations
will be descriptive even if later collected.

Malformed extension YAML, missing-template fallback, hook failures, optional-hook
acceptance/decline across turns, abort/approval handling, compaction, repeated
turns, and other harnesses remain outside this small pilot. They remain open in
[the OPT-004 acceptance map](opt-004-status.md).

## Approval scope and estimate

The next live request is exactly the six sessions above, with no retries,
automatic expansion, or reruns of completed consultation benchmarks. Rotate the
two variants' order across cases: create canonical/router, append router/canonical,
hooks canonical/router. Retain failures and stop on an isolation or
instrumentation defect. A stopped batch remains incomplete, with unused sessions
unspent. Fixing the instrument requires a new reviewed batch identity before any
replacement sessions.

Planning allowance: **40,000–100,000 total input tokens and 1,000–3,000 output
tokens per session**, or **240,000–600,000 input and 6,000–18,000 output** for six.
These are deliberately broad heuristics: earlier Luna consultation means were
roughly 17,000–42,000 input, and workflow reads/writes may add substantial context.
They are not measured forecasts or billing estimates. Propose a 180-second
timeout per session, up to 18 minutes of collector time plus preparation and
review. A timeout is not a hard token or spending limit.

Approval is required because the user explicitly requested review of the exact
cases, count, checks and scope before any paid/live session. This document and the
prepared bundle make that request reviewable. Approval of six sessions would not
authorize a larger token benchmark or promotion of the router.
