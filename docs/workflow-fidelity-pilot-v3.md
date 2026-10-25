# Workflow v3 repairs and proposed diagnostic pilot

Status: **offline candidate work only; no live sessions authorized or launched**.
The completed [six-session pilot](workflow-fidelity-results.md) and
[two-session v2 follow-up](workflow-fidelity-v2-results.md) retain their original
0/6 and 0/2 frozen outcomes. The original skill, prior router packages, traces,
artifacts, instruments, rubrics and reviews remain unchanged. OPT-004 remains
incomplete; no router is promoted or installed.

## Repair scope

The new [router v3](../evaluations/variants/speckit-checklist-router-v3/SKILL.md)
and [review record](../evaluations/variants/speckit-checklist-router-v3.review.json)
address behaviors observed in the last two sessions:

- Render automatic-hook announcements and optional-hook offers as actual
  user-visible blocks at the relevant pre/post phase. Include normalized command
  IDs and the configured offer details. A plan to display them, a final claim
  that they were offered, or a copied block after execution does not suffice.
- Prefer the available native file-editing tool for creation and append.
  Avoid heredocs and here-strings when temporary-directory writes are denied;
  do not broaden permissions or probe a known denied write path. Read the
  completed artifact to verify it and preserve every existing append byte.
- Report only actions and errors supported by actual tool results. The prior
  unrecorded Python-setup-error claim is not a valid recovery narrative.

Discovery metadata and unrelated example references remain unchanged. These
are authored instruction changes, not a content-preserving compiler extraction
or measured model-compliance improvement. The compiler's leave-inline default
does not change.

New checker, normalizer and collector modules use `workflow_fidelity_v3.py`,
`workflow_trace_v3.py` and `workflow_runtime_v3.py`, with
[rubric v4](../evaluations/variants/router-quality-rubric-v4.md). Frozen modules
are reused only as pinned dependencies or copied into separately versioned
implementations; they are not edited.

The parser addresses two bounded command shapes. A no-else existence check can
be a verified no-op only with pinned fixture-absence evidence and no preceding
or overlapping action that could invalidate it. The exact reviewed synthetic
setup and marker hooks may preserve this proof when their pinned code hashes
and successful returned JSON match; an arbitrary or modified hook cannot.
An allowlisted literal
`python3 -c` pathlib write can be attributed through static syntax inspection,
successful control flow, matching returned content and final artifact bytes.
Captured code is never executed by the parser. Arbitrary Python, output
spoofing, unproven paths or writes, masked errors and unsupported shell control
flow still fail closed. A real denied heredoc remains a failed operation even
if a later write succeeds.

Completed assistant messages retain lifecycle positions so the checker can
distinguish timely hook blocks from late or merely claimed offers, quoted
examples, indented code or contradictory fields. A final report must start
after the automatic hooks finish. Full artifact verification is corroborated
by exact returned bytes from a standalone literal `cat` or the supported
literal-write-plus-`cat` sequence, after all writes and before the report and
post-hook blocks. Other read forms are not automatically credited as verified
final bytes. Content,
formatting, reference behavior, workflow and efficiency remain separate.
Offline screens cannot prove truthful narration or semantic equivalence;
raw-trace and semantic review remain required.

## Smallest proposed live scope

Exactly **two fresh GPT-6 Luna sessions**, low reasoning, one turn and one
repetition per case, router v3 only. Append first, hooks second. No retries,
replacement sessions, baseline runs or additional model judges are proposed.

| Session | Unchanged task and initial state | Required observations |
| --- | --- | --- |
| `append-router-v3` | [Append prompt](../evaluations/workflow-fidelity/prompts/append.md); existing security checklist with reviewer note and mixed checkbox states | Full generation reference before project work; actual setup, constitution, spec and existing-file reads; sound handling of absent optional plan/tasks files if checked; exactly three distinct unchecked CHK008–010 questions with Gap markers; every existing byte preserved; successful workspace edit and final-artifact verification; accurate final report. |
| `hooks-router-v3` | [Hooks prompt](../evaluations/workflow-fidelity/prompts/hooks.md); absent target and harmless synthetic hook configuration | Full generation guidance and hook configuration; actual pre announcements/offers before the pre phase; automatic pre before setup; required context; four distinct unchecked CHK001–004 questions with Gap markers; successful creation and verification without denied temporary writes; actual post announcements/offers and automatic post with matching final hash; no optional, disabled or conditional hook execution or condition evaluation. |

The hook case also exercises creation. A standalone create session adds no
identified repair target. One unchanged session cannot exercise both the
existing-file append contract and the absent-file creation contract. Combining
them would change the task, initial state and interpretation, so these two
unchanged cases are the smallest comparable diagnostic scope.

Every applicable hard check plus raw and semantic review must pass to clear
this targeted gate. The reviewer must verify one-to-one topic allocation,
missing-policy meaning, actual offer rendering, evidence-grounded narration
and write behavior. Prepare anonymous artifact packets before exposing scores,
usage or the lookup key; record reviewer identity and prior exposure. A review
by the candidate's author is not independent or fully blind. An artifact pass
does not cancel a workflow or instrumentation failure.

Planning allowance: **200,000–400,000 total input tokens and 2,000–6,000 output
tokens**, with at most 180 seconds per session (six minutes of collector time).
The previous two sessions used 239,966 input and 2,541 output tokens. This is a
heuristic allowance, not a token, price or spending cap; changed instructions
and provider caching can move usage outside it. Report total/cached/uncached
input, output and latency separately. No efficiency comparison is proposed.

The collector remains disabled by default, fixed to these two slots and
single-attempt. Preparation copies only synthetic fixtures into fresh isolated
workspaces. Any later approved run must validate returned model/permissions,
use workspace writes with network and temporary-directory writes disabled,
disable unrelated skills, retain every attempt and stop remaining slots on
instrumentation/isolation defects. Ordinary fidelity failures are retained;
they do not authorize replacement sessions. Host reads remain possible under
the legacy CLI sandbox; trace scope checks are not an OS read-isolated container.
The original skill directory and real project hooks are out of scope.

No live command is part of this work. This proposal requires new approval;
previous two- and six-session authorizations are consumed. Even two passing
samples would not demonstrate replication, baseline equivalence, broader
trigger/lifecycle/target coverage, efficiency, promotion or OPT-004 completion.

## Offline validation

The versioned config is
[`evaluations/workflow-fidelity-v3/pilot.json`](../evaluations/workflow-fidelity-v3/pilot.json).
The preparation entry point requires no credentials and starts zero sessions:

```bash
python3 -m harnessmith.workflow_fidelity_v3 prepare \
  --output /tmp/opt004-workflow-v3-review
```

Use a fresh output path. Tests use synthetic events and a local fake server,
never a provider or real project hooks. Positive controls cover both proposed
workflows. Negative controls exercise invalid absence claims, unsafe/dynamic
writes, masked failures, late or fabricated hook offers, missing verification
and state corruption. Historical observations are not passed through a new
checker or assigned revised grades.

Validation on 2026-10-24: **342 repository tests passed; 84% coverage**. The 82
v3 regression tests comprise 42 trace cases, 27 checker cases, six fake-server
collector cases and seven package-integrity cases. Ruff, mypy (41 source files),
repository schemas/documentation and `git diff --check` passed. Review added
controls for quoted/future/negated offers, Markdown code indentation and a final
report that precedes hook completion. The final complete suite includes those
repairs; the earlier 341-test validation log is also retained.

Positive controls cover native file-change creation and byte-preserving append,
complete readback, actual timed pre/post blocks, and successful known marker
hooks. A denied heredoc followed by a successful write still fails. Parser
controls include absent no-else branches after the exact pinned setup/marker,
changed adapter bytes, mutation/overlap, literal non-ASCII Python payloads with
actual UTF-8 byte proof, spoofed output, dynamic code, path escape and partial
reads. Fake collection verifies one turn per slot, no retry, disabled execution,
model/permission checks, all-result retention and stopping on instrument errors.
These validate authored fixtures and instrumentation, not model behavior or an
OS sandbox execution guarantee.

The fresh prepared bundle is `/tmp/opt004-workflow-v3-review/`. A retained copy,
both suite logs, coverage report, source snapshots and hash audit are in the
private, gitignored
`evaluations/local-evidence/2026-10-24-workflow-v3-offline/` directory. Preparation
records exactly two proposed cases, **zero live sessions and zero attempts**.
Its manifest, package, fixture and instrument hashes were checked. A before/after
audit matches all **856 protected content files**, including the original skill,
prior versions and all retained historical evidence. No historical observation
was rescored.

Repository package checks validate the exact original discovery metadata and
reviewed file identities. The skill-creator quick validator remains unavailable
because PyYAML is absent; no dependency was installed. Package tests and static
code review do not substitute for the proposed live fidelity observations.
