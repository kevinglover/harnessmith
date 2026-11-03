# Workflow v11 offline parser and final-checkpoint repair

Status: **offline candidate; no live session authorized or launched**.
The [v10 result](workflow-fidelity-v10-results.md) remains frozen at **0/1**
automated and complete reviewed gates. Its positive content, formatting,
reference, append-preservation and readback findings stay separate. All original
skill bytes, previous packages, instruments, scores and historical evidence are
preserved. No historical trace is replayed or regraded.

## Evidence and changes

The v10 sample used `if test -f PATH; then cat PATH; else printf …; fi` for the
early extension check and constitution read. Both commands exited zero with
exact expected output; the frozen parser rejected their syntax, blocking
seven criteria and downstream discovery attribution. This was a measured parser
coverage gap in one sample, not evidence that arbitrary shell conditionals are
safe or that the failed workflow gate should be waived.

Raw review also found a genuine workflow omission: no extension check after
generation, although the reference called for one. Initial/final absence and a
target-only append establish fixture state, not performance of that checkpoint.
The frozen append checker had no dedicated requirement for this later check.
The two repairs therefore address different problems.

[Normalizer v10](../harnessmith/workflow_trace_v10.py) wraps frozen v9 and emits
observation schema 10. The new bounded grammar is
`if test -f PATH; then cat PATH; else printf 'ABSENT\n'; fi`, including safely
quoted non-login shell wrappers. The same safe literal path must be tested and
read. Both branches must be supported. Present output must match every pinned
byte; extension absence requires the exact marker and pinned absent state.
Missing/null/noisy output, unsupported branches, unsafe quoting, extra commands,
failed/incomplete lifecycles, stale pins and unsafe overlap cannot earn proof.

The prior prefix rules remain: before setup only accounted-for read-only and
synthetic setup actions are allowed. A later absence proof can account for one
completed native target-only append with the exact original prefix, unchanged
other files/modes and a separate complete final readback. Precisely superseded
attribution failures remain in certificate metadata; dependency and discovery
recovery cannot erase independent failures. Commands are neither rewritten nor
executed by normalization. This is bounded attribution, not shell emulation.

[Checker v11](../harnessmith/workflow_fidelity_v11.py) adds a mandatory append
checkpoint after the final write and separate complete readback, before the
final report starts. It requires a distinct successful backed extension-state
action, isolated from other operations. Earlier checks, snapshots, markers,
narrative claims or late/overlapping actions cannot substitute. Every inherited
hard gate remains binding, including truthful verification and Git claims.
This bounded fixture gate requires one fact per captured readback/check command
and exact final bytes in the returned readback text, in addition to its
normalized hash. It does not generalize to multiple edits or mixed readbacks.

[Router v8](../evaluations/variants/speckit-checklist-router-v8/SKILL.md) makes
that fresh action explicit in the generation route and step 8, even when the
pre-generation check found no configuration. Its
[review record](../evaluations/variants/speckit-checklist-router-v8.review.json)
pins the predecessor and source. Exactly two focused edits clarify this
checkpoint; discovery metadata, shared rules, both example references and all
other generation instructions remain unchanged. This authored semantic revision
is not a proven content-preserving compiler transformation. It prescribes no
shell spelling or fixture-specific workaround.

[Collector v11](../harnessmith/workflow_runtime_v11.py),
[pilot config](../evaluations/workflow-fidelity-v11/pilot.json) and
[rubric v12](../evaluations/variants/router-quality-rubric-v12.md) pin fresh
dependencies and retain the disabled-by-default, one-attempt boundary. The
original append prompt, synthetic fixtures, permissions and deadline stay the
same. Old manifests cannot be regraded with the new instruments. No compiler
selection rule changes; leave inline remains the default.

## Offline validation

Fresh synthetic traces and local fake-server tests cover present and absent
branches, safe shell wrappers, exact output, unsafe variants, downstream
discovery, final readback and the new checkpoint. A successful append with no
postcheck must fail; a separately completed certified postcheck before reporting
must pass when every other requirement is satisfied. Missing, early, late,
overlapping and unbacked checks remain failures. No real hook, model provider or
historical replay is part of these controls.

Validation on 2026-10-28: **785 repository tests passed, 85% coverage**, including
**42 new test methods**: 19 parser, 12 checker and 11 fake-server collector tests.
The final full suite verifies identical instrument/rubric hashes before and
after execution. Ruff passes; mypy passes all 64 source files. Independent code
review passes 56 fresh adversarial probes. These are offline instrument checks,
not a model-output judge or live benchmark.

Three complete fake-server captures are retained: a wrapped conditional with
the fresh postcheck passes every automated gate; an otherwise correct append
without the postcheck fails only the new checkpoint; a null-output postcheck
fails classification and the checkpoint. Each capture uses an empty mock
authentication file and synthetic events; no captured shell command or real
hook is executed. The pending prepared pilot still has **zero attempts**.

The first full suite had one error: the post-null fake case lacked `checks.json`
while the prospective rubric was being edited. Its temporary collector result
was removed by test cleanup, so the cause is unconfirmed. The failed log and
coverage remain separate from the retained fresh post-null diagnostic and the
complete passing rerun with stable pins. Earlier missing-tool/dependency logs
and a checker-test manifest-serialization oracle correction also remain retained.

The generic skill validator ran but rejects inherited extended frontmatter keys
outside its allowlist. Its failure is retained. Repository parsing, YAML syntax,
reference routing and package/source/predecessor pins pass; the unchanged
metadata was not removed to satisfy that validator. Validation dependencies
were installed only in temporary directories, with no project dependency change.

All **3,769 protected files and two symlinks** retain their starting bytes/modes
or link targets. The three current-status documents contain additions only.
Existing uncommitted v9/v10 work, every private evidence bundle, the original
skill and all previous router versions are preserved.

Final preparation at `/tmp/opt004-workflow-v11-review-final/` contains one case,
nine workspace files, 23 pinned instruments and zero attempts. The collector
also pins 23 runtime code dependencies. Prepared manifest SHA-256:
`17257317d0f77ee6cf377d9d9ff2cb9aec395941c736b97da8fae0a64a9db5f2`.
Original skill SHA-256 remains
`1498921d8bfef7bb158a5dce91fac71bb7b5f2cdc64972c7e2f8d289baa10a45`;
router-v8 review SHA-256 is
`975fd65a76a6e82b43fa8d9123858ec04754941f6cc0fec0fe6510c310d18624`.

The private, gitignored
[offline bundle](../evaluations/local-evidence/2026-10-28-workflow-v11-offline/README.md)
retains source snapshots, final preparation, complete positive/negative fake
captures, initial/final logs, independent probes, scripts and coverage data.
Its [preservation audit](../evaluations/local-evidence/2026-10-28-workflow-v11-offline/preservation-audit.json),
[validation record](../evaluations/local-evidence/2026-10-28-workflow-v11-offline/validation.json)
and [manifest](../evaluations/local-evidence/2026-10-28-workflow-v11-offline/manifest.json)
retain the actual checks and file identities. Raw paths are not rewritten and
relocated observations are not regraded.

## Smallest proposed live follow-up — approval required

| Field | Exact proposed scope |
| --- | --- |
| Session | `append-router-v8-instrument-v11` |
| Model / effort | GPT-6 Luna (`gpt-6-luna`), low |
| Count | **One session, one turn, one repetition** |
| Package / instruments | Router v8, normalizer v10, checker/collector v11, rubric v12 |
| Input | Unchanged original append prompt and synthetic fixture; existing mixed checkbox states and reviewer note |
| Requested output | Three unchecked CHK008–010 questions covering measurable expiration, expired/reused outcomes and retention; no invented policy |
| Workflow checks | Reference before project actions; isolated precheck/setup; complete context before write; separated discovery/reads; original bytes/states preserved; separate complete final readback; fresh isolated extension check before report; supported narration |
| Permissions | Prepared workspace writes only, network disabled, unrelated skills disabled, no real hooks or external project access; legacy host-read limitation disclosed |
| Limits | 180-second deadline; no retry, replacement, expansion, matched baseline, hooks rerun or extra model judge |
| Planning estimate | Roughly 100–225k cumulative input and 1–2k output tokens, commonly tens of seconds; heuristics from nearby Luna append samples, not caps, prices or savings predictions |

This single case can observe both repairs while preserving a useful artifact
check. The model chooses its own command spelling. If it does not choose the new
grammar, report that coverage as unobserved; do not rerun to manufacture coverage.
The post-generation action itself is required regardless of spelling.

If approved later, retain every result, including failures, interrupted attempts,
raw events, workspace snapshots, usage and provenance. Save anonymous semantic
judgments before opening grades/key/usage/raw; disclose reviewer involvement and
blinding limits. Then review every operation and material claim against evidence.
Leave pending grades intact and retain separate review sidecars. Report content,
formatting, references, workflow and efficiency independently. Empty bounded
matcher arrays do not establish truthful narration.

One pass would establish only that reviewed sample. Reliability, configured-hook
fidelity, independent output review, replication, paired efficiency evidence,
other runtimes and the wider OPT-004 matrix remain open. Luna and Astra and
different instrument/router versions stay separate. All earlier authorizations
are consumed; **this proposal authorizes zero live sessions**.
