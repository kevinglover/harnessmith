# Skill optimization opportunity ledger

All entries were first identified and last reviewed on **2026-10-22**.
OPT-001 through OPT-003 are **validated offline** in the implementation follow-up;
OPT-004 through OPT-006 remain **proposed**. The original weekly review made no
implementation changes. See the [P1 follow-up](2026-10-22-p1.md).
Baseline evidence: [report](2026-10-22.md) and
[measurements and probes](2026-10-22-evidence.json).

## OPT-001 — Validate metadata against the selected target

- Priority: P1. Targets: all, especially generic. Effort: small–medium.
- Files: `harnessmith/parser.py`, `harnessmith/diagnostics/rules.py`,
  `harnessmith/targets.py`, parser/audit/adapter tests.
- Evidence: invalid name and overlength description probes are accepted for
  every target. Portable tool-list syntax also lacks validation.
- Benefit: report malformed packages before installation.
- Plan: make constraints explicit per target and distinguish portable validity
  from extensions. Preserve raw bytes while validating interpreted fields.
- Risk: blindly applying the strictest host's rules would reject valid extensions;
  directory-name checks must account for compiler output locations.
- Acceptance: boundary fixtures for lengths, names, types, and directory policy;
  invalid generic cases fail with stable diagnostics; valid host-specific cases
  remain supported; all current fixtures receive explicit expected outcomes.
- Implementation: explicit target metadata policies, HS102 field errors and HS103
  directory advice; compile rejection for invalid metadata; comments, quotes, and
  CRLF source bytes retained. Boundary/type tests cover every existing fixture.
- Status: validated (offline). First/last review: 2026-10-22.
  Runtime evidence remains explicitly unverified under OPT-004.

## OPT-002 — Clarify tool capability semantics

- Priority: P1. Targets: all. Effort: medium.
- Files: `harnessmith/targets.py`, `harnessmith/adapters.py`, `docs/targets.md`,
  `tests/test_adapter_contracts.py`.
- Evidence: `_COMMON_PACKAGE_CAPABILITIES` assigns `tools.allowlist` support to
  every target based on field representation alone. Current primary-source
  guidance and the tool-list probe are documented in the baseline report.
- Benefit: capability consumers can distinguish preservation from enforcement.
- Plan: distinguish representable metadata, permission grants, restrictive tool
  policy, unknown runtime support, and relevant version constraints. Keep
  conversions conservative where semantics cannot be demonstrated.
- Risk: public capability names may require a contract/schema migration; absence
  from a guide is not proof of unsupported runtime behavior.
- Acceptance: fixtures cover supported representations and unsupported semantic
  conversions; documentation uses precise terminology; enforcement claims have
  versioned runtime evidence or remain explicitly unverified.
- Implementation: capability schema v2 adds unknown runtime status and separates
  field preservation from grants/restrictions. Version 1 schema is retained.
  HS306 warns about unverified runtime semantics; unsupported conversions fail.
- Status: validated (offline). First/last review: 2026-10-22.
  Runtime evidence remains explicitly unverified under OPT-004.

## OPT-003 — Detect host-specific behavior in skill bodies

- Priority: P1. Targets: generic, cursor, codex; Claude as source/control.
  Effort: medium.
- Files: `harnessmith/audit.py`, `harnessmith/diagnostics/rules.py`,
  `harnessmith/compiler.py`, fixture corpus and audit tests.
- Evidence: the dynamic-body probe passes every adapter with no warnings.
- Benefit: byte-identical copying will no longer imply behavior portability.
- Plan: add targeted diagnostics for dynamic commands and substitution tokens;
  define reviewed target policies before attempting any transformation.
- Risk: documentation examples, escaped tokens, and code fences can produce false
  positives. Never execute probe content to classify it.
- Acceptance: active syntax, literal examples, escapes, and negative controls are
  distinguished; unsupported behavior receives an actionable diagnostic; any
  compilation rejection policy is explicit and tested without semantic rewriting.
- Implementation: HS307/HS308 diagnose known Claude body syntax and lexical
  example contexts; audit and compile expose findings without rewriting or
  executing content. Compilation policy is explicitly advisory.
- Status: validated (offline). First/last review: 2026-10-22.
  Runtime evidence remains explicitly unverified under OPT-004.

## OPT-004 — Expand fidelity coverage and capture real runtime evidence

- Priority: P2. Targets: all for offline contracts; Cursor, Claude, Codex for
  optional live runs. Effort: large, staged.
- Files: `harnessmith/evaluation.py`, `evaluations/scenarios/`,
  `tests/test_evaluation.py`, `docs/evaluation.md`.
- Evidence: three pinned scenarios pass 23 checks, but runtime metrics are null
  and the scenario set has no generic entry. A live-evaluator extension point
  exists without a built-in provider.
- Benefit: separate package correctness from measured behavioral fidelity and
  efficiency; enable valid longitudinal comparisons.
- Plan: add positive/negative trigger, explicit-only, abort, approval, hook,
  reference-load, repeated-turn, and compaction cases; begin with offline
  contracts, then opt-in trace adapters and paired canonical/compiled runs.
- Risk: model drift, nondeterminism, cache state, permission differences, and
  instrumentation changes confound measurements. Live runs require opt-in.
- Acceptance: source/recipe hashes, harness/model/mode versions, repeated samples,
  actions, outputs, reference reads, and measured usage accompany every runtime
  claim. Keep mock results labeled and preserve the disabled-by-default gate.
- Status: proposed. First/last review: 2026-10-22.

## OPT-005 — Review oversized canonical skills for explicit recipes

- Priority: P2. Targets: supported targets where each reviewed recipe applies.
  Effort: medium.
- Files: `skills/speckit-checklist/SKILL.md`, `skills/speckit-clarify/SKILL.md`,
  `recipes/`, scenarios and verification tests.
- Evidence: roots estimate 5,674 and 5,040 tokens. The existing analyze recipe
  demonstrates a 21% static normal-path reduction, while the model-card fixture
  demonstrates that extraction can increase the normal path.
- Benefit: potential context reduction; magnitude and runtime effect unknown.
- Plan: review optional branches and exact reference candidates, retain global
  constraints, and pin every recipe to its source hash. Compare normal path,
  fallback path, and total package, not only root size.
- Risk: mandatory extraction adds overhead; relocating branching or safety
  instructions can change behavior. Heuristic audit candidates are not approval.
- Acceptance: exact-content verification, unchanged workflow contracts, budget
  checks, and paired scenario results. Claim runtime gains only under OPT-004.
- Status: proposed. First/last review: 2026-10-22.

## OPT-006 — Audit discovery cost and trigger clarity across a catalog

- Priority: P3. Targets: Codex and Claude initially; Cursor when measured rules
  are available. Effort: medium.
- Files: `harnessmith/audit.py`, diagnostics, CLI, evaluation scenarios.
- Evidence: current audits are per skill. The local descriptions total 1,447
  characters; names, paths, formatting, and other installed skills are excluded.
  The baseline cites distinct host listing budgets.
- Benefit: identify skills whose triggers may become unavailable in large
  catalogs even when individual roots are small.
- Plan: add catalog-level size reporting with configurable, versioned host
  assumptions; test concise positive/negative trigger descriptions under crowded
  catalogs. Keep guidance advisory rather than rewriting descriptions.
- Risk: approximate counts cannot predict every host's truncation or selection;
  model and configuration changes invalidate hardcoded thresholds.
- Acceptance: report measured components and assumptions separately, add
  overflow/duplicate-name fixtures, and use optional runtime trigger trials before
  claiming improved selection accuracy.
- Status: proposed. First/last review: 2026-10-22.
