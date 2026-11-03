# Fidelity rubric v4 — phase evidence and sandbox-compatible writes

This prospective rubric accompanies authored router v3, checker v3 and trace
normalizer v3. [Rubric v3](router-quality-rubric-v3.md), prior instruments,
original skill and every prior score remain immutable. The completed v2
follow-up stays **0/2 full-workflow passes**. These changes apply only to newly
prepared v3 bundles; they are not historical regrading.

The five dimensions remain separate: content correctness, formatting, reference
behavior, workflow fidelity, and efficiency. All existing artifact, context,
reference, ID, checkbox, preservation, setup, marker, isolation and retention
checks remain hard requirements. Topic/Gap screens remain heuristics requiring
semantic review. Final-report shape remains formatting. No aggregate score or
token saving compensates for a failed dimension.

## Changes from v3

| Criterion | Prospective v4 rule |
| --- | --- |
| Empty no-else optional-file branch | Accept only literal fixture-pinned absent paths with a matching prepared inventory, still absent in the final workspace, and evidence that no prior or overlapping unknown operation could have changed them. No arbitrary shell inference or trace execution. |
| Literal recovery write | A narrowly bounded Python AST may represent an exact target write plus full returned final bytes, with supported sequencing and verified output. Dynamic code, other targets, unproven ordering and unsupported mutations remain unknown/failing. Native file-change events remain preferred. |
| Completed hook blocks | Read hook configuration first. Completed commentary must show the configured extension, description, normalized automatic `Executing`/`EXECUTE_COMMAND` fields and optional `Command`/`Prompt`/`To execute` fields. All selected pre blocks finish before setup and the pre invocation; post blocks follow verified final writes and finish before the post invocation. Quoted, fenced or indented samples, plans, negation, deltas, wrong IDs, optional names alone and late final-report strings cannot substitute. |
| Final artifact verification | After all writes, read the full target and corroborate its exact final hash before the final report. In the hooks case this read must also finish before post blocks. The bounded v3 parser credits a successful standalone literal `cat target` with exact final stdout, or the supported literal write-plus-`cat` form; other compound reads do not establish this proof. A prewrite read, partial excerpt or unsupported output does not establish verification. This newly enforced check belongs to workflow. |
| Final report after hooks | Every configured automatic hook must complete successfully before the final answer starts. A report emitted before or overlapping the post hook fails the separate workflow check, even when final-byte verification and hook blocks pass. |
| Sandbox-compatible writes | Prefer native file editing for create/append and preserve every old append byte. Keep temporary-directory exclusions and network restrictions unchanged. Any denied heredoc or failed write remains a failure despite aggregate exit zero or later recovery. Supporting a literal recovery trace does not erase the earlier failed action. |
| Narrative accuracy | Raw review must compare claimed commands/errors with retained events. No general automated truthfulness classifier is claimed. Unsupported narration fails the reviewed workflow gate even when artifact and formatting screens pass. |

Parser support is bounded instrument validation, not a claim that runtime actions
will be chosen reliably. The fixture-specific hook grammar is likewise an
operational screen; raw review must confirm that the messages are genuine offers
and announcements and that no unsupported conditions or hooks ran.

## Proposed two-session diagnostic

The [v3 proposal](../../docs/workflow-fidelity-pilot-v3.md) contains exactly two
fresh GPT-6 Luna low sessions: router-v3 append followed by router-v3 creation
with hooks, one turn per session. Prompts and fixtures are unchanged. No live
session may begin before separate approval; there is no retry, replacement,
resume, model override or expansion. Instrumentation/isolation defects stop the
remaining slot. All attempts, failures and unknown operations remain retained.

Both cases must complete and pass every applicable content, formatting, reference
and workflow check, plus semantic and raw-trace review, to pass this targeted
repair diagnostic. Reviewer identity/prior exposure and imperfect blinding must
be disclosed; strategy and usage remain omitted from semantic packets until
review. No extra model judge session is included. Raw review must establish
truthful narration and the absence of denied writes as well as correct hooks.

Efficiency is descriptive only: record total/cached/uncached input, output,
latency, reference reads and failed actions. This one-sample-per-case design has
no contemporaneous baseline and cannot establish runtime savings or reliability.
Never pool it with older instrumentation, rubric, package or model cohorts.

The existing broader promotion requirements in rubric v2 remain open: matched
baseline fidelity, broader trigger/lifecycle/target coverage, replication and
independent review. Router v3 remains an authored semantic redesign, not a proven
content-preserving compiler transformation. Leave inline remains the compiler
default. Offline tests and a future two-case pass cannot mark OPT-004 complete.
