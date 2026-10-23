# Verification and evaluation

Harnessmith distinguishes compiler correctness, static context measurement, and
behavioral evidence. Passing one category does not prove the others.

## What is verified today

Compilation checks exact extracted content, transform provenance, normative
statement retention, root heading order, and configured budgets. The
independent verifier additionally checks:

- manifest schema and Harnessmith ownership;
- safe relative paths and absence of symlink traversal;
- missing, unexpected, or hash-mismatched generated files;
- executable-mode drift and preserved-resource provenance;
- source and recipe drift when recorded paths are available;
- recomputed metrics and compiler invariants; and
- deterministic regeneration when source and recipe are resolvable.

Run it with:

```bash
harnessmith verify path/to/compiled-skill
harnessmith verify path/to/compiled-skill --json
```

Exit code `0` means valid and `1` means verification findings. Compile and audit
errors return `2`. A skipped check is not a pass; JSON consumers should inspect
both `valid` and the per-check status.

## Static metrics

Current “token” metrics are `ceil(characters / 4)`. They are reproducible and
dependency-free, but they are not output from a target tokenizer. Root,
normal-path, and packaged estimates describe possible instruction-loading paths,
not observed model behavior.

Harnessmith does not currently claim measured runtime tokens, latency, or model
quality. The offline evaluator checks pinned scenario contracts against a
deterministic mock transcript; that is behavioral regression evidence, not a
claim about an actual model or harness run.

## Evaluation layers

Use three separate gates:

1. **Compiler correctness:** unit tests and independent package verification.
2. **Static context:** compare the same source and generated package with the
   documented estimator.
3. **Behavioral fidelity:** run canonical and compiled skills against the same
   scenarios, checking invocation, required constraints, forbidden actions,
   reference loads, outputs, and failure behavior.

The offline fixture corpus exercises parser, audit, and target edge cases. The
versioned scenarios under `evaluations/scenarios/` additionally compare
invocation representation, required verbatim constraints, forbidden mock
actions, expected reference loads, and output assertions for canonical and
compiled variants. Results keep fidelity counts and static estimates separate;
`runtime_metrics` remains empty for offline runs. See
[the fixture README](../fixtures/README.md) and the broader
[cross-repository corpus notes](evaluation-corpus.md).

`harnessmith.evaluation.run_live_evaluation` is an extension point that requires
an explicit `enabled=True`. It has no built-in provider and is never used by
normal CI; callers are responsible for recording model and harness versions and
keeping nondeterministic observations separate.

## Reproducing repository checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_repository.py all
```

Networked or live-model evaluation should remain opt-in, report its model and
harness versions, and keep nondeterministic results separate from normal CI.

## Turn contracts (scenario version 2)

Version 1 remains readable. Version 2 keeps the fixture, target, compilation,
invocation policy, required constraints, and forbidden actions, and replaces
`mock_transcript`, `expected_reference_loads`, and `semantic_assertions` with
`turns`. The top-level prompt must equal the first turn's prompt. Both versions
have published schemas and are checked by the repository schema check.

Each turn supplies:

- an event (`prompt`, `approval`, `abort`, `hook`, `continuation`, or `compaction`),
  prompt text, and invocation channel (`user`, `model`, or `none`);
- an explicit expected invocation, independently of whether policy permits it;
- exact ordered actions, including repetitions;
- separate canonical and compiled reference reads, checked against package files;
- required and forbidden output substrings; and
- independent canonical and compiled mock traces.

A non-trigger can therefore expect no invocation even when model invocation is
permitted. An explicit-only skill cannot pass a model invocation check by merely
setting its expected result to true. Action order, unexpected actions, and
activity after an abort are checked per turn. A missing or extra runtime turn
fails the turn-count check.

The corpus now has 14 scenarios: three legacy scenarios, four lifecycle
scenarios, four non-trigger scenarios, and three explicit-channel scenarios.
The lifecycle and non-trigger cases cover every target; explicit-only cases
cover the three targets that represent that policy. The new synthetic lifecycle
fixture models approval, continuation, compaction, hook failure, reference
reloads, and abort without changing existing pinned sources.

These are **mock contract checks**, not observations of harness behavior.
`evidence_kind: "mock-contract"` makes that explicit in offline results.
Events describe inputs an adapter must arrange; the offline evaluator does not
compact a real context or execute hooks. Substring assertions are deterministic
acceptance checks, not a model-quality judge. Canonical/compiled mock agreement
does not establish live fidelity or reduced runtime cost.

## Repeated runtime evidence

`harnessmith.runtime_evidence.run_runtime_evidence` adds a structured collector
alongside the legacy `run_live_evaluation` callback. The legacy callback remains
compatible but its bare observations are not a complete evidence report.

The new collector requires a version-2 scenario, a passing offline contract,
an explicit `enabled=True`, and at least two paired samples (default three).
An `EvidenceEvaluator` adapter implements `evaluate(request) -> RuntimeSample`.
No provider ships with Harnessmith, and normal CI never contacts one.

```python
from pathlib import Path
from harnessmith.evaluation import load_scenario
from harnessmith.runtime_evidence import RuntimeEnvironment, run_runtime_evidence

scenario = load_scenario(Path("evaluations/scenarios/lifecycle-generic.json"))
# adapter is your implementation of EvidenceEvaluator, configured independently.
# Fill each identifier from the actual run environment, not this example.
environment = RuntimeEnvironment(
    harness="your-harness", harness_version="recorded-build",
    model="your-model", model_version="recorded-snapshot",
    mode="your-mode", mode_version="recorded-mode-version",
    instrumentation_version="your-trace-adapter-version",
    permission_policy="recorded-permissions",
    cache_policy="recorded-cache-policy",
    configuration_id="identifier-for-recorded-settings-and-seeds",
)
report = run_runtime_evidence(
    scenario, adapter, repository_root=Path.cwd(), environment=environment,
    samples=3, enabled=True,
)
```

Each request contains exact package bytes, executable paths, a unique fresh
session ID, the sample and variant, environment identifiers, and ordered input
turns. Expected answers and mock transcripts are excluded from provider requests.
The adapter must install those bytes in an isolated session, apply the declared
configuration, arrange lifecycle events, and capture actual actions, outputs,
reference reads, input/output tokens, and latency for the whole session. Return
one `TurnTrace` per turn in a `RuntimeSample`. Missing, negative, boolean, or
noninteger usage is rejected instead of being presented as measured usage.
Unsupported instrumentation must fail rather than fabricate events or counts.
The collector cannot independently verify an adapter's honesty or isolation.

Pairs alternate canonical/compiled execution order to reduce order effects.
The report retains every raw sample and its fidelity checks, without declaring
an aggregate efficiency win. A failed trace remains in the report with failed
checks. Provider exceptions or malformed measurements abort collection; they do
not produce a completed evidence report. Callers can retain provider logs for
interrupted runs.

`schemas/runtime-evidence.schema.json` describes completed reports. Provenance
includes source SHA-256, a normalized scenario hash (including expectations),
compiler version, the environment, exact file hashes and executable paths for
both packages, and a normalized compilation-configuration hash. These scenarios
use direct extraction configuration, so `recipe_sha256` is explicitly null;
recipe-backed runs are not yet supported. Static token estimates remain separate
from measured usage. Test adapters must set `evidence_kind="mock"`; only actual
instrumented harness runs should use `"runtime"`.

Real runs are still needed before making fidelity, token, latency, or cost
claims. Compare like environment/configuration identifiers, inspect individual
failures and cache conditions, and retain repeated samples rather than treating
one successful pair as proof.
