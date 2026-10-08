# Architecture

Harnessmith compiles a canonical `SKILL.md` into a deterministic package for a
target agent harness. It separates source meaning, reviewed optimization
policy, target representation, and generated output.

## Pipeline

1. The parser builds a lossless intermediate representation with source spans.
2. A recipe optionally pins the source hash and selects reviewed transforms.
3. Target adaptation preserves supported behavior and fails closed otherwise.
4. Deterministic transforms move exact source material or apply named,
   narrowly reviewed optimizations.
5. Verification checks normative retention and transform provenance.
6. The writer replaces only files owned by an earlier Harnessmith manifest.

The compiler currently supports `generic`, `cursor`, `claude`, and `codex`.
Target behavior remains implemented in `harnessmith.adapters`; capability
contracts introduced by the roadmap will make those decisions declarative.

## Stable boundaries

- `harnessmith.model` contains the current parser and compiler IR.
- `harnessmith.contracts` defines shared, target-neutral vocabulary for new
  diagnostics, adapter declarations, and fixture metadata.
- `schemas/` defines version 1 durable JSON formats.
- Recipes record intent; manifests record what happened.
- Audits are advisory and read-only. Compilation is deterministic and
  fail-closed when behavior cannot be represented.

## Safety invariants

- Never silently discard behavior-bearing instructions.
- Never weaken invocation policy to satisfy a target.
- Never rewrite semantic prose without an explicit reviewed transform.
- Never overwrite files not owned by a valid Harnessmith manifest.
- Never apply a source-pinned recipe after the source hash changes.

## Versioning

Schema versions are independent of the Python package version. Consumers must
reject an unsupported schema version rather than guessing. See ADR 0002.
