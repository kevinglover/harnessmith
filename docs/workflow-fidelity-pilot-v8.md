# Workflow v8 offline discovery and command-boundary repairs

Status: **offline candidate; no live sessions authorized or launched**.
The [v7 result](workflow-fidelity-v7-results.md) remains frozen at **0/1** full
automated and complete reviewed gates, with positive semantic content,
formatting, reference and append-artifact findings reported separately.

## Evidence motivating the change

The frozen v7 trace contains two distinct problems. Raw records 91–92 combine
an extension conditional with discovery of `.specify` and absent `.pilot`,
suppress stderr and return exit 2. That is a real failure, not a valid absence
certificate. Records 158–159 return full pinned reads followed by a successful
terminal `rg --files specs/001-invitations`; the old parser leaves that last
statement unverified. The required reads also share an action with discovery.
Recognizing the successful listing must not waive that workflow violation.

These are measured findings from one Luna sample, not general model behavior.
The old collector, observations, grades, raw traces, review sidecars, package and
rubric remain unchanged. No historical trace is replayed or regraded. The original
skill is unchanged; leave inline remains the compiler default.

## New versions and limits

[Router v7](../evaluations/variants/speckit-checklist-router-v7/SKILL.md) and its
[review](../evaluations/variants/speckit-checklist-router-v7.review.json) revise
only command-boundary/discovery instructions in the root and generation guide.
Extension checks, setup and discovery use separate actions. Required context
reads may share only read-only actions. Discovery searches known-existing roots,
skips absent optional integration directories and retains stderr/exit status.
No adapter search is needed without config or supplied integration instructions.
Actual discovery failures must be reported. Frontmatter, shared rules, examples,
hook selection/rendering, setup arguments, content guidance, append preservation,
postwrite verification and supported-narration requirements are retained.
This is a reviewed semantic redesign, not a content-preserving compiler pass.

[Normalizer v7](../harnessmith/workflow_trace_v7.py) wraps frozen v6. It can
certify one terminal literal `rg --files DIRECTORY`, standalone or following only
literal full `cat` reads, with newline, semicolon or `&&` separators. Proof
requires successful matching lifecycle/source/cwd/scope, verified baseline
inventory, safe existing visible root, exact ordered read prefix and the complete
unique visible listing. Listing order may vary. Proof metadata retains output
and inventory hashes, prior attribution and any specifically superseded issues.

The same narrow standalone/`&&` grammar loses inherited discovery credit if
the new proof fails. Only an exactly proven terminal unknown and its two matching
artificial issues may be replaced; real failures and unrelated issues survive.
Captured commands are never executed. Flags, multi-root discovery, pipelines,
redirects and compound absence probes receive no new certificate; unsupported
grammar retains its frozen parser behavior and limitations. Symlinks, missing
roots, ambiguous output, prior mutation/uncertainty and overlapping lifecycles
prevent new proof. The pinned synthetic prerequisite stub is allowed only with
its inherited absence-preserving evidence. This is bounded attribution, not
shell emulation or OS access tracing. Ignore rules, executable behavior and shell
startup are not independently attested. Raw review remains mandatory.

[Checker v8](../harnessmith/workflow_fidelity_v8.py) genuinely prepares and grades
new v8 bundles with schema-7 observations; all dependencies are pinned. Three new
gates separately enforce extension-check isolation, read isolation and discovery
isolation. All observed reads, including template/optional/package reads, are
covered; required-path presence remains mandatory. Discovery is optional but
cannot share an action with reads, setup, hooks, writes or unknowns. Unique
successful matching command records must back evidence.
Only narrow passive label/cache diagnostics can accompany context reads;
only corroborated read-only cache noise can accompany the extension proof.
Missing or unknown evidence cannot pass by default. All inherited reference,
absence ordering, setup, artifact, final readback, hook and narration gates remain.
Bounded topic/narrative screens retain their existing versions and limits.

[Collector v8](../harnessmith/workflow_runtime_v8.py) wires the instruments into
one fixed slot, retains the existing workspace-write/network-disabled settings,
180-second maximum and durable one-attempt guard. It is disabled by default.
It retains raw events, snapshots and results on failure; there are no retry,
sample-count or model overrides. [Rubric v9](../evaluations/variants/router-quality-rubric-v9.md)
states the prospective rules, separate dimensions and promotion limits.

## Offline validation scope

| Area | Positive control | Negative controls |
| --- | --- | --- |
| Terminal discovery | Exact pinned listing after complete ordered reads; standalone listing; newline/semicolon/`&&` | Missing/duplicate/extra output, wrong order or read bytes, invalid inventory, missing root, symlink, unsafe syntax, failed/mismatched/open/overlapping lifecycle, prior mutation |
| Command boundaries | Extension proof alone; context reads together; discovery separately | Fully attributed mixed read/discovery; extension plus discovery/setup/unrelated reads; unknowns, missing evidence or duplicate records |
| Collector integration | One synthetic local fake-server append with new pins and unchanged permissions | Mixed discovery fails separation; failed compound probe retains exit/failures; missing final read, unsupported Git claim and instrumentation errors retained without replacement |
| Package integrity | Frozen original/predecessor identity and unchanged substantive spans | Unreviewed source/package changes, altered source mappings, executable files and symlinks |

All inputs are fresh synthetic traces or local temporary fixtures. Fake-server
auth is empty and no provider session, model judge or real project hook runs.
Only the three current-status documents are updated in place; implementation,
tests, router, rubric, pilot and this proposal are new versions.

## Validation and preservation

Validation on 2026-10-25: **634 repository tests passed, 84% coverage**, including
**76 new regressions**: 30 parser, 25 checker, eight fake-server collector and
13 package-contract tests. The full suite ran once after targeted repairs.
Ruff, mypy (55 source files), repository schema/documentation and whitespace
checks pass. The two verbatim example references retain their original terminal
blank lines. The skill quick-validator could not run because PyYAML is absent;
its failure log is retained, and the package-contract checks passed.

Independent code review found that the initial context gate omitted template and
optional reads. The final gate covers all observed non-extension reads, and the
new discovery-isolation gate also rejects setup/discovery combinations. The
fresh before/after reproduction now fails both appropriate separation gates.
No further actionable findings remained in this review. Earlier failed offline
checks are retained, including the first collector mock whose setup-output
fixture needed correction; they are not rewritten as successful results.

The offline preparation at `/tmp/opt004-workflow-v8-review/` contains one case,
nine workspace files, 17 pinned instruments and **zero attempts**. Its manifest
SHA-256 is `f1b132c8d0314c1465533645d0f5b15660548cd5b9ddd39073acd2d0fa0e9929`.
The router-v7 review SHA-256 is
`89fc65b25a4b888ab350d88a6988da149b92777aa4a86d18168272eff1539c84`;
rubric-v9 SHA-256 is
`389ef7c6e367e2606a90e252266e12e4832e69ee23eff4a166c4213e80b31158`.
The collector pins 17 runtime code dependencies. Original prompt, fixtures,
original skill and all predecessor package bytes/modes match their identities.

All **2,237 protected files and two symlinks** retain their starting bytes/modes
or link targets. The three current-status documents contain additions only
relative to the starting working tree. The private, gitignored
[offline bundle](../evaluations/local-evidence/2026-10-25-workflow-v8-offline/README.md)
retains preparation, new sources, inherited dependencies, inputs, logs, coverage,
independent reproductions and provenance/preservation audits. Its
[validation record](../evaluations/local-evidence/2026-10-25-workflow-v8-offline/validation.json)
and [inventory](../evaluations/local-evidence/2026-10-25-workflow-v8-offline/manifest.json)
identify that evidence. These are offline results only; the frozen v7 gate
remains 0/1 and no new model-compliance result is claimed.

## Smallest follow-up proposal — approval required

Exactly **one fresh GPT-6 Luna low session**, one turn and one repetition:

| Session | Task | Expected checks |
| --- | --- | --- |
| `append-router-v7-instrument-v8` | Use router v7 with the unchanged original prompt and append fixture to add three questions to `specs/001-invitations/checklists/security.md` | Full generation reference first; standalone pinned extension absence before separate setup; complete required context reads isolated from discovery; skip absent optional roots; exact original prefix/checkbox states; unchecked CHK008–010; separate complete final read; correct content/format and supported commentary/final claims |

This is the smallest end-to-end diagnostic of the remaining append workflow.
No baseline, hooks rerun, replication, replacement, retry, batch expansion or
extra judge session is included. The unchanged prompt does not force discovery
or a specific parser grammar. If the model chooses another valid form or omits
unneeded discovery, retain that result and record new-grammar live coverage as
unobserved. Do not steer or rerun to manufacture coverage.

Planning scope: **100–200k input and 1–2k output tokens**, at most **180 seconds**.
The frozen v7 sample used 161,451 input, 1,134 output and 18.294 seconds. The range
is a heuristic, not a token cap, price, billing estimate or efficiency claim.

Any approved run must validate returned model/effort/permissions, disable unrelated
skills and retain every result. Use the anonymous semantic-first packet with a
separate lookup key; disclose reviewer identity and prior exposure before seeing
grades/traces/usage. Then review complete raw actions and material narration.
Keep review sidecars separate from frozen pending grades. Report content,
formatting, references, workflow and descriptive efficiency separately. Legacy
host reads are not fully OS-isolated. One pass proves neither reliability nor
router-v7 hooks fidelity, efficiency, compiler equivalence, promotion or OPT-004
completion. Luna and Astra results remain separate.

The v7 authorization was consumed. This v8 preparation starts **zero live
sessions and zero attempts**. No launch is queued; approval must name this new
one-session scope before any live action.
