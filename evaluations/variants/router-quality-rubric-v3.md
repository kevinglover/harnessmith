# Fidelity rubric v3 — targeted workflow repair

This prospective version accompanies router v2, checker v2 and trace normalizer
v2. It does not overwrite [rubric v2](router-quality-rubric-v2.md) or any scores
from the completed six-session pilot. Original skill and router v1 remain frozen.

The five independent dimensions, evidence-retention rules, model separation,
reviewer disclosure requirements and efficiency gates from v2 still apply.
All attempts, failed commands, unknown operations and partial outcomes must be
retained. Changed assertions below apply only to a new report with this version
and pinned instruments. No compensating aggregate score is permitted.

## Changes from v2

| Criterion | Frozen v2 behavior | Prospective v3 behavior |
| --- | --- | --- |
| Compound command evidence | Unknown compound reads fail classification even when their returned bytes establish a read. | A bounded grammar accepts literal operations only with supported control flow and evidence of execution/success. Newline/masked exits require stronger output corroboration; a final zero is insufficient. Raw item IDs, ordering and failed operations remain visible. Unsupported syntax is still a failure. |
| Required read completeness and ordering | Path-level reads and normalized event order can conceal partial excerpts or overlapping operations. | A required guidance/context excerpt must cover its pinned file; a read must finish before the consuming action starts. A path match or earlier completion-list position alone is insufficient. |
| Final count and report | Regex requires a narrow numeric phrase and considers combined assistant output. | Evaluate completed final-answer text separately from commentary. Accept equivalent Markdown, small spelled numbers, item labels and bounded descriptive words; reject wrong/contradictory counts, future intent and missing required report fields. Artifact IDs/checkbox syntax remain exact. |
| Topic allocation | Aggregate keyword screen can accept combined topics plus a redundant fourth question. | Check one-to-one item/topic allocation for the synthetic prompt with a bounded screen, then require semantic review. All four topics in one item cannot pass because other items repeat them. |
| Missing policy markers | Traceability can pass using only a spec reference. | Synthetic missing-policy items also require a `Gap` marker. A spec reference does not substitute for identifying the missing policy. |
| Constitution, hook offers, preservation | Required reads, usable offers, actual hook actions/order and byte preservation are hard requirements. | Unchanged. Mere claims of reading, offering or executing never replace evidence. |

V3 places the final-report and Gap-marker checks in the formatting dimension;
v2's final-report check remains under workflow in its historical scores. Topic
allocation remains a content screen. These organizational changes are explicit
and do not alter the frozen results or allow one dimension to offset another.

Offline comparisons use synthetic positive and adversarial controls representing
the recorded failure shapes. They compare rule behavior without rewriting or
replacing historical observations or calling a provider. Supporting more command
forms is not permission to infer arbitrary shell behavior or execute trace text.

## Two-session diagnostic gate

The [new pilot](../../docs/workflow-fidelity-pilot-v2.md) proposes exactly two
fresh GPT-6 Luna sessions, router v2 only: append, then creation with hooks.
These cover all identified repair targets with no redundant standalone create
case. Both sessions must complete and pass every applicable content, formatting,
reference and workflow check, with raw-trace review and blinded semantic review,
to pass this **targeted diagnostic gate**. Unknown evidence is pending/failing,
not a pass. Instrumentation/isolation defects stop the batch; no replacements.

This new gate does not replace v2's failed six-session paired gate, demonstrate
baseline equivalence, or promote the router. Replication, contemporaneous baseline
coverage, wider lifecycle/target coverage and the existing v2 promotion levels
remain unmet. Efficiency stays descriptive with one sample per case. No new
workload weights or savings threshold are inferred from the earlier usage.

Semantic review packets must omit strategy and usage, use anonymous stable IDs,
and retain a separate lookup key. Review final checklist plus prompt, source spec
and relevant instructions. Record reviewer identity and prior exposure. Blinding
can be imperfect in a single-variant pilot; disclose this and do not call such a
review independent if the reviewer authored the revision or saw keyed results.
Scores remain pending until review evidence exists; offline authored examples
cannot pass model fidelity.

The router is an authored redesign. Versioning its workflow repairs establishes
provenance, not content-preserving transformation or live reliability. Leave
inline remains the compiler default. Approval of a future two-session pilot
would authorize only those observations, not installation or promotion.
