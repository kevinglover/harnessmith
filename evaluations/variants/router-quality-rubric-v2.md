# Fidelity and promotion rubric v2 — 2026-10-24

Status: prospective criteria, frozen before the proposed workflow pilot runs.
This is a new rubric, not a correction to the
[historical consultation rubric](router-quality-rubric.md). Do not regrade or
replace historical scores. A later rule change requires a new rubric version,
new report identity, and an explicit comparison with the old rules.

## Evidence contract

Record each criterion as `pass`, `fail`, `pending`, or `not-applicable`, with an
artifact/trace location and rationale. Missing evidence is pending; an output
claim is not an observed action. Keep automated checks and human review separate.
Never collapse the five dimensions below into one compensating score.

Freeze source, recipe (or explicitly no recipe), package, router review, prompt,
fixture, checker and rubric hashes before collection. Record requested model,
available backend version (or unreported), harness/mode/instrumentation versions,
permissions, cache policy, order and unique session IDs. Keep all attempts,
including failures, interruptions and classifier errors. No selective retries.
Each new batch gets a new output directory; historical bundles are read-only.
Mocks and manually authored traces must be labeled offline simulations.

Compare only like model, harness, permission and instrumentation configurations.
Never pool Luna with Astra. Unknown backend versions and uncontrolled caches
limit conclusions even when requested model IDs match.

## Five independent dimensions

| Dimension | Required checks | Passing criterion |
| --- | --- | --- |
| Content correctness | Every new item reviews requirements quality; covers the case's specified concerns; distinguishes missing requirements from product facts; no invented policy, quotation or exclusivity. | All case criteria pass semantic review with cited item text. Keyword screens alone cannot pass this dimension. |
| Formatting | Requested file/template structure, exact unchecked `- [ ] CHK###` new items, globally sequential IDs, question form, traceability, accurate final path/count/create-or-append report; exact quotations where requested. | Every frozen assertion passes. Bold IDs, missing prefixes and malformed markers remain failures even if readable. |
| Reference behavior | Actual successful reads of required references before their guidance is used; no prohibited/unnecessary optional reads under frozen expectations; preserve read order when specified. | All positive and negative read assertions pass. Distinguish classifier/collector failures from model failures; neither is a pass. |
| Workflow fidelity | Setup and required context read; correct destination; create/append semantics; existing bytes and all checkbox states preserved; mandatory pre/post hook invocation and completion in order; optional offered and invoked only after explicit authorization (no authorization in this pilot); disabled hooks and hooks with nonempty conditions skipped without evaluating those conditions. | All applicable artifact and observed event checks pass. Transcript announcements and marker files alone cannot prove execution. |
| Efficiency | Total/cached/uncached input, output, latency, command/read counts, repeated reads, per-case and per-configuration distributions. | Use the efficiency gate below; a smaller root or lower uncached mean alone never passes. |

For semantic review, present outputs without strategy or usage labels, using a
separate lookup key. Record reviewer identity and any prior exposure. Review all
outputs, cite rationale for every failure, and resolve disagreements explicitly.
One reviewer is a limitation, not an independent validation claim. Historical
review was not fully blinded and must continue to be described that way.

## Promotion levels

1. **Offline pilot ready:** deterministic fixture preparation, provenance,
   checker positive controls and adversarial negative controls pass. This
   validates the evaluation instrument only. Model content/reference/workflow
   fidelity and efficiency remain pending.
2. **Narrow workflow pilot passed:** all six proposed sessions complete and all
   applicable content, formatting, reference and workflow checks pass for both
   variants, including semantic review. Any baseline failure also blocks this
   gate until understood. One observation per cell is diagnostic coverage only;
   report individual failures, never an equivalence or efficiency claim.
3. **Eligible for reviewed workflow use:** after separate approval, at least
   three fresh observations per variant per required case in a frozen matrix
   pass every hard fidelity criterion. The matrix must also cover malformed
   hook configuration, missing template fallback, hook failure, optional-hook
   continuation/decline, abort, and any supported invocation/lifecycle behavior.
   Publish all attempts and uncertainty. This is a policy floor for coverage,
   not statistical proof of equivalence or closure of OPT-004 across all targets.
4. **Eligible for an efficiency recommendation:** levels 1–3 pass and the
   efficiency gate passes for the stated workload. Recommendation remains
   scoped to the measured model/configuration and declared workload.

Even level 4 does not make the router a content-preserving compiler transform.
The [review record](speckit-checklist-router.review.json) documents intentional
semantic changes. Incorporating it as a transformation would require a separately
reviewed contract and proof of the claimed preservation properties, beyond
behavioral samples. Until then it is an authored experimental alternative;
do not replace the source skill or silently select it during compilation.

## Efficiency gate and decision rules

These thresholds are prospective **review policy**, not findings inferred from
the old samples. Do not tune them after seeing the next results.

- Predeclare task frequencies (weights summing to one), measured baseline,
  supported model/configuration and acceptable latency. Unknown weights mean
  no general workload recommendation; publish per-task results only.
- Require at least three observations per variant/task and retain per-sample
  totals, means and ranges. Compare contemporaneous baselines under the same
  collection settings. Do not reuse the six-session pilot to claim a replicated
  saving, or rerun completed benchmarks without a separately approved question.
- Require at least 10% lower workload-weighted mean **total input** and no more
  than 10% increase in weighted mean session latency. Disclose every per-task
  regression; a task with over 10% more total input is ineligible for automatic
  selection and can only be a separately reviewed, explicit tradeoff.
- The 10% margins are practical thresholds chosen before collection. Report
  sample variability and limitations; passing them at small sample counts is
  not a statistical guarantee. Stronger reliability claims need an additional
  predeclared uncertainty/power plan and approval.
- Report cached input and uncached input separately; cache state is uncontrolled
  unless demonstrated otherwise. Dollar/credit estimates, if ever requested,
  need dated rates and must remain distinct from observed billing and usage.

**Default decision: leave inline.** Extraction can be explicitly reviewed for
packaging, readability or a static context budget without claiming runtime
savings. Mandatory extraction preserves section bytes but adds read gates;
conditional extraction additionally needs pinned optionality and a justified
load condition. Size/heading cues are review heuristics, not predictions.

A workload break-even calculation may illustrate a hypothesis using measured
means, but does not authorize extraction or generalize across models. The prior
Astra skip-rate illustration and Luna routing differences remain separate,
descriptive evidence. See [OPT-004 status](../../docs/opt-004-status.md) and the
[minimal next pilot](../../docs/workflow-fidelity-pilot.md).
