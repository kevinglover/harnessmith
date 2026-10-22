# Weekly skill optimization reviews

Review schedule: Mondays at 9:00 a.m. America/New_York, starting October 26,
2026. Reports are produced by the weekly review automation attached to the
setup chat.

## Scope

Discover the supported targets from `harnessmith.targets` and `docs/targets.md`
each week. At setup these are generic Agent Skills, Cursor, Claude Code, and
Codex. Review current official specifications, documentation, release notes,
and relevant primary research against the implementation, recipes, fixtures,
and evaluation evidence in this repository.

## Reports

Save each review as `YYYY-MM-DD.md` using the review date in America/New_York.
Preserve earlier reports; use a time suffix for an additional run on the same
date. The first review establishes the baseline. Each report should include:

1. Review date, coverage window, repository revision and relevant working-tree
   changes, supported targets, and source access gaps.
2. A per-target summary of relevant upstream changes, linked primary sources,
   publication/update dates when available, and retrieval dates. Distinguish
   newly published changes from older information newly discovered.
3. Ranked improvement opportunities with stable IDs, affected files/targets,
   supporting evidence, expected benefit, effort, risks, and a concrete
   validation plan. Separate recommendations from implemented changes.
4. Comparable measurements and changes since the previous review: compiler
   verification and fidelity results, estimated root and normal-path context,
   and total packaged instructions. Identify source/recipe hashes and the
   metric method. Report runtime tokens, latency, cost, or quality only when
   actual versioned runtime evidence exists. Mock transcripts and character
   estimates must remain labeled as such.
5. Progress on previously identified opportunities, supported by file, commit,
   or test evidence. Use proposed, in progress, implemented, validated,
   deferred, or rejected status; implementation alone is not validation.
6. Recommended next actions and limitations. Explicitly record when there are
   no new actionable improvements or when comparisons are unavailable.

Update the index below and maintain `opportunities.md` as the cumulative
opportunity ledger once the first review identifies candidates. Reuse IDs
across reports. Do not overwrite historical measurements or infer improvement
from an incompatible baseline or a smaller root alone.

The recurring task researches, evaluates, and reports. Implementation changes
are separate follow-up work. Local checks may write disposable outputs to a
temporary directory. Live model evaluation follows the repository's opt-in
policy; unavailable runtime evidence is a report limitation, not a passing
result.

## Report index

Setup on October 22, 2026. An initial review established the baseline that day;
the regular Monday schedule starts October 26. Track follow-up work in the
[opportunity ledger](opportunities.md).

| Review date | Report | New opportunities | Validated improvements | Coverage gaps |
| --- | --- | --- | --- | --- |
| 2026-10-22 | [Baseline review](2026-10-22.md) | 6 proposed | 0 new; existing recipe reverified | No live runs; schema dependency unavailable |

Implementation follow-up: [October 22 P1 work](2026-10-22-p1.md) records offline
validation of OPT-001 through OPT-003. It is separate from the historical weekly
review and does not claim runtime improvements.
