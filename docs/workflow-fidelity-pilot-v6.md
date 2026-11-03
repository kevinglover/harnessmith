# Workflow v6 offline append repairs

Status: **offline candidate; no live sessions authorized or launched**.
The [v5 results](workflow-fidelity-v5-results.md) remain unchanged: hooks passes,
append fails, both pass semantic content review. The append failure combines
unsupported read-only Python syntax with real missing verification and
unsupported final narration. These are separate problems; recognizing more
reads cannot supply a postwrite action that never happened.

## Targeted candidate

The authored [router v6](../evaluations/variants/speckit-checklist-router-v6/SKILL.md)
and its [review](../evaluations/variants/speckit-checklist-router-v6.review.json)
make the reference/pre-setup checkpoint and append verification sequence
explicit. The model must establish extension presence or absence before setup,
retain the original bytes, make the edit, then actually read and verify the
complete resulting artifact before reporting. A Git comparison is unnecessary
for this prefix proof; an unobserved attempt or error must not be reported.
Hook semantics, original discovery metadata and verbatim example references
remain preserved.

Normalizer v5 adds bounded static recognition of literal Python existence/text
reads and byte-representation/full-text reads, including supported compound
read commands. A bounded standalone full-file `cat` also carries explicit hash
and coverage proof. It never executes captured code. Exact returned output, pinned
state, lifecycle and path checks distinguish supported reads from unknown
operations. Cache-warning handling requires corroboration and cannot hide
real failures. Successful absence evidence is separate from a file-content read.

Checker v6 retains the final-readback gate and adds explicit pre-setup evidence,
setup separation and lifecycle-backed reference ordering. A complete reference
read must finish before any project action starts; derived event ordering within
one command cannot supply that checkpoint. New bounded narrative screens require
earlier matching evidence for recognized verification and Git claims. Passing a
screen or recognizing no claim is not a substitute for full raw review.

The new separate-final-readback gate enforces router v6's explicit action
checkpoint after the last write. An inherited bounded internal append/readback
still supplies valid read evidence and can support truthful narration, but does
not satisfy that new separate-action requirement by itself.

Git support is deliberately narrow: a root-working-directory `git diff` against
`HEAD`, a bounded ancestor or a commit hash, followed by `--` and the exact target.
The returned outcome must support the recognized claim, including any
same-sentence “no differences” conclusion. A failed comparison claim currently
requires the recorded nonzero “not a git repository” result. Other commands,
error paraphrases and general narration remain unverified by this bounded screen
and require raw review. No Git command is added to the pilot.

Collector v6 retains the established opt-in and all-result retention behavior,
with **one fixed append slot** and no model/count/retry override. Observations
use schema v5, checker/collector reports v6, and
[rubric v7](../evaluations/variants/router-quality-rubric-v7.md) versions the new
rules. Historical scores and instruments are not changed or replayed.

## Offline validation matrix

| Area | Positive controls | Negative controls |
| --- | --- | --- |
| Python reads | Literal existing/absent checks, exact byte and text output, supported read chains | Dynamic paths, side effects, shadowed names, symlinks/outside paths, partial/mismatched output and invalid lifecycle |
| Cache attribution | Exact known diagnostics with fully corroborated reads | Genuine failures mixed with cache noise, nonzero envelopes and unsupported operations |
| Setup checkpoint | Timely configuration read or pinned absence, separate successful setup | Missing/late evidence, unpinned absence, setup combined with reads |
| Verification | Complete matching final artifact read after the last write, exact original prefix | No read, prewrite/partial/stale/wrong-target/later read, modified prefix or checkbox state |
| Narration | Completed claims backed by earlier matching records | Unrecorded Git attempt/error, printed/filename command mentions, wrong command/outcome, unsupported final-read claims; quoted/planned/negated text used as proof |
| Collector | One retained synthetic result with pinned new/inherited versions | Fidelity and instrumentation failures retained without retry/replacement; disabled launch rejected |

All controls use newly constructed synthetic fixtures. No live session,
credential-backed process or real project hook is part of validation. The
original skill and every historical report, package, observation and score stay
frozen. Offline checks establish instrument/package behavior; model compliance
and future-host sandbox behavior remain unproven.

## Validation and preservation

Validation on 2026-10-25: **513 repository tests passed, 84% coverage**, including
**74 new regressions**: 30 parser, 23 checker, eight fake-server collector and
13 package tests. Ruff, mypy (49 source files), repository schema and
documentation checks pass. No model benchmark was rerun.

Cross-review tightened reference lifecycle ordering, Git working-directory and
target checks, same-sentence Git result claims, and the separate-final-read
checkpoint. The first full run had two integration failures because a complete
standalone `cat` lacked the new reference hash/coverage fields. Exact-output
attribution and four parser regressions repaired that gap; the final full run
passes. Both full-run logs and both offline preparations are retained, with the
initial preparation labeled superseded. Historical traces were never replayed
or regraded.

The final offline preparation at `/tmp/opt004-workflow-v6-review-final/` contains
one proposed case and **zero live sessions or attempts**. Source, package,
fixtures, unchanged prompt, workspace permissions and new/inherited instrument
hashes match. The private, gitignored
`evaluations/local-evidence/2026-10-25-workflow-v6-offline/` bundle retains
preparations, source snapshots, validation logs and preservation audits.
All **1,714 protected files and two symlinks** match their starting bytes/modes
or link targets. The separately excluded Finder metadata file is also unchanged.
Only three existing current-status documents are updated; implementation,
tests, package, rubric and proposal are new files.

The two verbatim example references retain their original terminal blank lines;
whitespace checks record those preservation exceptions and no others. The
skill-creator quick validator could not start because PyYAML is absent; no
dependency was installed. Package regressions cover discovery metadata,
provenance, reference routing, retained source spans, unchanged hooks and tamper
rejection. These checks establish offline readiness, not model compliance or
broader promotion.

## Smallest follow-up proposal, not authorized

After validation, propose exactly **one fresh GPT-6 Luna low session**:

| Session | Task | Expected checks |
| --- | --- | --- |
| `append-router-v6` | Append three questions to the existing synthetic security checklist using the unchanged original prompt | Required reference; extension absence before separate setup; constitution/spec/existing-byte reads; exact prefix and checkbox preservation; CHK008–010; complete postwrite readback before final report; accurate content/format and supported narration |

The [original prompt](../evaluations/workflow-fidelity/prompts/append.md) and
fixtures are reused without steering. This isolates the remaining append gap.
V5's hooks pass does not certify router v6 hooks; broader workflow validation
remains open. No baseline, repeated sample, hooks rerun, extra judge, retry,
replacement or expansion is included.

Planning estimate: **100–200k input and 1–2k output tokens**, up to 180 seconds.
The last append sample used 126,909 input and 1,130 output tokens. This is a
heuristic estimate, not a price or token cap. Caching and changed instructions
can change usage. Efficiency remains descriptive only.

Use the established network-disabled workspace-write configuration, excluded
temporary-directory writes, approval `never`, unrelated skills disabled and
returned-setting validation. Legacy host reads are not fully OS-isolated.
Retain every result and raw trace. Prepare the anonymous semantic packet before
opening grades/usage, disclose reviewer involvement and retain separate raw
review. One passing sample cannot establish reliability, efficiency, promotion
or OPT-004 completion. Earlier live approvals are consumed; this proposal has
no live authorization or queued launch.
