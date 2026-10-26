# Workflow v7 offline absence-certificate repair

Status: **offline candidate; no live sessions authorized or launched**.
The [v6 result](workflow-fidelity-v6-results.md) remains frozen at **0/1**
automated and complete reviewed gates. Semantic content and raw append behavior
passed separately. Its sole failed criterion was `extension-config-before-setup`:
the frozen parser recognized the successful conditional but did not certify its
literal `else printf` branch. This proposal repairs instrumentation only.

## Targeted change and provenance

The original skill, [router v6](../evaluations/variants/speckit-checklist-router-v6/SKILL.md),
its [review](../evaluations/variants/speckit-checklist-router-v6.review.json), the
[append prompt](../evaluations/workflow-fidelity/prompts/append.md), and all
fixtures remain byte-identical. There is no router-v7 package or new compiler
transformation. Leave inline remains the compiler default.

[Normalizer v6](../harnessmith/workflow_trace_v6.py) wraps frozen v5 and upgrades
only an independently corroborated absence diagnostic for a standalone literal
conditional testing `.specify/extensions.yml`. Both branches must be safe: the
present branch reads that same path with `cat`; the absent branch uses supported
literal `printf` output. Exact nonempty stdout, an explicitly pinned absent path,
verified baseline inventory, safe path components and a matching successful
start/completion pair are required. The new certificate retains proof metadata,
including the inventory and returned-output hashes. It never executes captured
code, converts absence into a content read, strips output noise or clears an
inherited failure.

The prefix before this checkpoint must contain only accounted-for successful
reads/diagnostics. Earlier setup, hooks, writes, unknown/unverified operations,
foreign operational scopes and overlapping or still-open operations prevent the
new certificate. This is deliberately bounded attribution, not shell emulation
or OS file-access tracing. Unsupported commands still require explicit diagnosis
and raw review; a printed label alone never establishes absence.
The new certificate rejects explicit login/interactive shell wrappers, including
in prior commands, and requires source agreement at each lifecycle endpoint.
Only explicitly recognized read-only diagnostic reasons are allowed in its
prefix; an artifact-directory creation diagnostic cannot qualify. Non-login
shell startup and executable behavior remain outside independent parser attestation.

[Checker v7](../harnessmith/workflow_fidelity_v7.py) accepts only newly prepared
v7 bundles and schema-v6 observations, pins all inherited/new dependencies and
retains every v6 hard gate unchanged. Completed reference loading must precede
the absence probe; absence must precede separate setup; full context, exact append
preservation, a separate final readback and supported narration remain required.
Bounded lexical and narrative screens keep their existing versions and limits.

[Collector v7](../harnessmith/workflow_runtime_v7.py) wires the new instruments
into one fixed slot with the existing network-disabled workspace-write settings,
180-second maximum, one durable attempt guard, all-result retention and no model,
count or retry override. Its default is disabled. New [rubric v8](../evaluations/variants/router-quality-rubric-v8.md)
records the certificate rule; earlier rubric versions, scores and traces stay
frozen. No historical trace is replayed or regraded.

## Offline validation matrix

| Area | Positive controls | Rejections and unchanged boundaries |
| --- | --- | --- |
| Literal branch | Relative/quoted/absolute same-file paths; supported literal formatting; exact returned output | Label alone, wrong path, dynamic values, unsupported formats, extra commands or side effects in either branch |
| Pinned state | Explicit absence and matching inventory hash | Present file/directory, missing pin, tampered inventory, symlink components and workspace escapes |
| Lifecycle | Matching successful endpoints, prior completed reference read | Missing/duplicate/mismatched endpoints, nonzero exit, wrong scope, prior setup/write/unknown command, overlapping or open operations |
| Evidence | Certificate carries exact output and inventory hashes | Empty, partial, altered or noisy output; final filesystem alone; no retroactive credit from later actions |
| Checker | Fresh synthetic trace satisfies the unchanged append gates | Wrong schema/dependency pins; late absence; missing separate final read; unsupported Git claims |
| Collector | One fake-server result, pinned sources, unchanged router/prompt and permissions | Disabled launch, invalid timeout, instrumentation exception and fidelity failures retained without retry or replacement |

All controls use new synthetic inputs and a local fake stdio server. No provider
session, real authentication, model judge or real project hook is part of this
validation. The original skill and historical content are protected by starting
byte/mode inventories. Only the current changelog/evaluation/OPT-004 status
documents are updated; implementation, tests, rubric and proposal are new files.

## Validation and preservation

Validation on 2026-10-25: **558 repository tests passed, 85% coverage**, including
**45 new regressions**: 29 parser, 10 checker and six fake-server collector tests.
Ruff, mypy (52 source files), repository schema/documentation and whitespace
checks pass. The full suite ran once after targeted fixes; no model benchmark
was rerun. Independent code review identified prior directory creation,
explicit login wrappers and mismatched prefix sources as certificate gaps; the
new tests cover each, and the reviewed final targeted suite passes.

The preparation at `/tmp/opt004-workflow-v7-review/` contains one proposed case,
nine workspace files, 15 pinned instruments and **zero attempts**. Its manifest
SHA-256 is `216ee6c76192842311986a90e6df065bac16f8099f281dfc7496e2bf3c91be81`.
The rubric-v8 SHA-256 is
`cb85583e557a0e46ef8b4336afd6a3a92023a1f3d517f9339e1bd1ce805d9ebb`.
The unchanged router-v6 review SHA-256 is
`8f8f386a2f421dbc8eebc303db4d8bbc217c1c5409bffd9972917fe5b84a9315`;
all four package files, original prompt, fixtures, source and executable modes
match their pins. The collector snapshots 15 runtime code dependencies.

All **1,983 protected files and two symlinks** retain their starting bytes/modes
or link targets. The separately tracked Finder metadata also remains unchanged.
The three updated current-status documents contain additions only. The private,
gitignored `evaluations/local-evidence/2026-10-25-workflow-v7-offline/` bundle
retains preparation, source/dependency snapshots, original inputs, all saved
validation logs, coverage and
preservation/provenance audits. This is offline evidence only; the frozen v6
failure remains 0/1 and no new model-compliance result is claimed.

## Smallest follow-up proposal, not authorized

Exactly **one fresh GPT-6 Luna low session**, one turn and one repetition:

| Session | Task | Required evidence |
| --- | --- | --- |
| `append-router-v6-instrument-v7` | Use unchanged router v6 and the original prompt to append three questions to the existing synthetic security checklist | Full generation reference first; pinned extension absence before separate setup; constitution/spec/existing checklist reads; exact original prefix and checkbox states; unchecked CHK008–010; complete separate postwrite readback; correct content/format and supported commentary/final claims |

This isolates the remaining instrument gap without changing model instructions.
The model may choose a different valid probe; if it does not use `else printf`,
the sample cannot establish live coverage of that specific new grammar. Retain
that outcome; do not steer, retry or expand the batch. No baseline, hooks rerun,
replication, replacement or extra judge session is included. The historical v5
hooks pass is not a router-v6 hooks pass.

Planning estimate: **100–200k input and 1–2k output tokens**, at most 180 seconds.
The frozen v6 append used 178,288 input, 1,039 output and 20.260 seconds. The
range is a planning heuristic, not a token cap, price, billing estimate or
efficiency comparison. Provider caching and execution choices remain variable.

Any approved future run must validate returned model/effort/permissions, disable
unrelated skills, retain every result and raw record, and use the existing
semantic-first review packet followed by complete raw review. Disclose reviewer
involvement and preserve review sidecars separately from frozen grades. Legacy
host reads are not fully OS-isolated. Report content, formatting, reference
behavior, workflow and descriptive efficiency separately. One passing sample
cannot establish reliability, efficiency, promotion or OPT-004 completion.

The prior v6 authorization is consumed. This preparation has **zero live
sessions and zero attempts**; no new launch is queued. The next live action
requires explicit approval of this exact one-session scope.
