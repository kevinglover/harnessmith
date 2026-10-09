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
