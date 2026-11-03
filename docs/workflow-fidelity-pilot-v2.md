# Targeted workflow repair: versions and proposed follow-up

Status: **offline implementation and validation only; no new live sessions
authorized or launched**. The completed [six-session results](workflow-fidelity-results.md)
and their failed grades remain unchanged. OPT-004 is still incomplete.

## Versioned repairs

The new [router v2](../evaluations/variants/speckit-checklist-router-v2/SKILL.md)
and [review record](../evaluations/variants/speckit-checklist-router-v2.review.json)
preserve the original skill and router v1. Discovery frontmatter and both example
references are unchanged. The root and project-generation procedure intentionally
change; the latter is no longer claimed to be a verbatim extraction.

- Read the constitution at its documented path before writes, even when
  `AVAILABLE_DOCS` does not list it. This applies to append as well as creation.
- Render the required automatic-hook announcements and usable optional offers
  with normalized command IDs. A claim that an offer was made does not replace
  it. Execute optional hooks only after explicit authorization.
- Let an explicit one-question-per-topic allocation override consolidation.
  Do not fill the requested count with duplicated or combined topic questions.
- Add `Gap` for missing policy even when a related requirement is cited; preserve
  the complete existing byte prefix and checkbox states when appending.
- Choose writes compatible with the actual sandbox, avoiding constructs that
  need unavailable temporary-file writes. This does not expand permissions.

These are candidate instruction repairs, not measured improvements in model
behavior or a content-preserving compiler transformation. Nothing installs the
candidate or selects it automatically in the compiler.

The new checker and normalizer use separate modules and identities:
`workflow_fidelity_v2.py`, `workflow_trace_v2.py`, and prospective
[rubric v3](../evaluations/variants/router-quality-rubric-v3.md). Old instruments
and scores are retained. The normalizer recognizes a bounded set of compound
reads using control flow and returned evidence; it retains unknown or failed
operations. It never executes trace text or treats aggregate exit zero as proof
that every embedded command succeeded. Final-answer text is separated from
commentary so a plan or an announcement cannot satisfy the final report.
Required reference/context reads must cover their pinned content and finish
before consuming actions start. A short excerpt or overlapping write cannot pass
solely because the path and completion order look correct. Exact known macOS
cache warnings remain diagnostics only when the pinned synthetic adapter returns
the matching successful JSON result; other permission failures still fail.
The parser remains deliberately bounded. A terminal `rg --files | sort` can
support attribution of an earlier successful `&&` read, but `sort` can hide the
producer's exit status, so the pipeline itself stays unverified and prevents a
clean workflow pass. Arbitrary pipelines, dynamic scripts and masked fallbacks
remain unsupported. The follow-up must retain such failures rather than loosen
the rules after observing model command choices.

The count checker accepts equivalent Markdown and small spelled numbers while
rejecting wrong counts and future-only claims. Exact artifact syntax and
preservation checks stay strict. Per-item topic and Gap screens catch the
synthetic failure shapes; semantic review is still required. Rule changes and
unchanged promotion requirements are listed explicitly in rubric v3.

## Smallest proposed live scope

Exactly **two fresh GPT-6 Luna, low-reasoning sessions**, one per row, router v2
only. Run append first, hooks second. One repetition; no replacements, retries,
expansion or other models. These are diagnostic repair checks, not a comparison
to the original or router v1. The earlier six sessions remain their own cohort.

| Session | Unchanged prompt and fixture | Required observations |
| --- | --- | --- |
| `append-router-v2` | [Append prompt](../evaluations/workflow-fidelity/prompts/append.md), existing checklist with mixed states and reviewer note | Generation reference before project actions; actual setup, constitution, spec and existing-file reads before writing; preserve every existing byte and `[x]`, `[X]`, `[ ]`; exactly three new unchecked CHK008–010 questions, one each for expiration, expired/reused outcomes and retention, with Gap markers; accurate final report. |
| `hooks-router-v2` | [Hooks prompt](../evaluations/workflow-fidelity/prompts/hooks.md), no existing checklist | Generation reference and hook config read; automatic pre completes before setup; constitution/spec/template context; four distinct unchecked CHK001–004 questions covering the four requested topics; automatic post completes after final write with matching hash; required command announcements and usable optional offers; no optional, disabled or conditional hook execution or condition evaluation. |

The hooks case also exercises new-file creation, so another standalone create
session would repeat that coverage. Combining append and creation in one session
would change the frozen tasks and would not exercise both initial file states.
Two is the smallest diagnostic scope covering both without rewriting prompts.

Every applicable hard check, raw-trace review and semantic review must pass for
the new targeted gate. Reviewers must inspect one-to-one topic allocation and
missing-policy meaning, not only keywords. Prepare anonymous final-artifact
review packets without strategy/usage, retain the lookup key, and disclose
reviewer exposure; a single-variant design cannot completely hide candidate
identity. Review remains pending until performed. There are no additional model
judge sessions in this proposal.

## Isolation, preparation and approval boundary

The [versioned config](../evaluations/workflow-fidelity-v2/pilot.json) reuses the
unchanged synthetic fixtures and harmless marker hook. It pins the new router
and review, original source, exact prompts, fixture hashes, grading dependencies
and rubric. Preparation creates only the two proposed workspaces and starts zero
model sessions:

```bash
python3 -m harnessmith.workflow_fidelity_v2 prepare \
  --output /tmp/opt004-workflow-v2-review
```

Use a new output path. Preparation and checks require no credentials. The
versioned `workflow_runtime_v2` collector is disabled by default and fixed to
these two slots. Its transport/permission lifecycle is inherited from the frozen
collector; fake-server integration tests exercise the new normalizer and checker
without contacting a provider. It retains every attempt, raw stdout/stderr,
before/after artifact, observation, check and cumulative usage measurement.

A future approved collection must use a fresh directory outside the repository,
workspace-only writes, no network, no `/tmp` or environment-temp write access,
and approval `never`. The legacy CLI still permits host reads at the OS level;
the prompt and recorded-scope checks constrain them, not a read-isolated
container. Real project hooks and the original source directory are out of scope.
Stop remaining slots on instrumentation/isolation failures; never replace a
failed or interrupted session. Ordinary fidelity failures remain recorded.

Planning allowance: **200,000–400,000 total input tokens and 2,000–6,000 output
tokens** across both sessions, with at most 180 seconds per session (six minutes
of collector time). This is a heuristic allowance, not a spending or token cap:
the prior router append/hooks observations used 212,444 input and 2,413 output,
and the prior full batch exceeded its estimate. Changed instructions, tools and
cache behavior can move usage outside this range. Report cached/uncached input
and latency separately; no cost or savings claim is proposed.

This document supplies the exact cases, count, checks and estimate for later
approval. **No live invocation is part of the current work.** Passing two samples
would not establish replication, baseline equivalence, promotion, or completion
of OPT-004. The broader invocation/lifecycle/target matrix remains open.

## Offline validation record

Validation on 2026-10-24: **260 repository tests passed; 84% coverage**. The 53
new tests comprise 27 trace regressions, 16 checker/preparation cases, five
router integrity/tamper tests and five fake-stdio collector integrations. Ruff,
mypy (38 source files), repository schema/documentation checks and
`git diff --check` passed. These are instrument/package tests, not observations
of model compliance.

Positive controls cover both prospective cases. Negative controls cover masked
write failures, partial/unpinned reads, read/action overlap, path escapes,
qualified executable spoofing, fabricated or missing setup/marker output,
missing final answers, incorrect counts, combined topics, missing Gap markers,
missing constitution, absent offers, unauthorized hooks and append corruption.
Fake integrations exercise two slots, one turn per slot, all-result retention,
model/permission validation, interrupted collection, no retry and disabled-by-default
execution. Real project hooks and provider processes are never invoked by tests.

The prepared review bundle is `/tmp/opt004-workflow-v2-review/`; a retained copy,
validation logs, source snapshots and integrity report are in the private,
gitignored `evaluations/local-evidence/2026-10-24-workflow-v2-offline/` directory.
Its preparation records exactly two cases and zero live sessions. A before/after
SHA-256 audit matches all **672 protected content files**, including original
skill, router v1, old checker/collector/rubrics, completed reports and raw traces.
No historical observation was rescored.

The repository's package loader validates source/package hashes and retained
discovery metadata. The bundled skill-creator quick validator could not run
because PyYAML is unavailable; its inspected allowlist also excludes four
deliberately retained source frontmatter fields. Those fields were preserved,
not removed to satisfy the narrower helper. This is a validation-tool limitation,
not a claim that the candidate has passed model testing.
