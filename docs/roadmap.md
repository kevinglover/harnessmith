# Roadmap

This roadmap converts the next improvement cycle into parallel workstreams.
All branches start from the Phase 0 contracts and keep the safety invariants in
[`architecture.md`](architecture.md).

## Phase 0: foundation

- [x] Reconcile the public identity as Harnessmith.
- [x] Record architecture and versioning decisions.
- [x] Define shared diagnostic, adapter capability, and fixture vocabulary.
- [x] Publish version 1 schemas for diagnostics, capabilities, fixtures,
  recipes, and package manifests.
- [x] Preserve existing target behavior and establish a green baseline.

Baseline recorded on 2026-10-08: `python3 -m unittest discover -s tests -v`
passes all 31 tests on Python 3.9-compatible source. The foundation phase adds
contract tests only; it does not alter compilation or adapter behavior.

## Parallel workstreams

| Workstream | Primary ownership | Depends on |
| --- | --- | --- |
| Fixture corpus | `fixtures/`, corpus validation | Phase 0 fixture schema |
| Diagnostics | audit rules, text/JSON/SARIF | diagnostic contract |
| Adapter contracts | target declarations and contract tests | capability contract |
| Verification CLI | `verify`, `--dry-run`, `--diff` | manifest schema |
| Transform pipeline | parser spans and verified passes | architecture invariants |
| Documentation | README and task-focused guides | merged CLI behavior |
| Packaging and CI | build, test, schema and docs gates | published schemas |

Behavioral evaluation follows the fixture corpus and adapter declarations. An
integration pass then checks schema drift, generated artifacts, CLI consistency,
documentation examples, and clean-wheel installation.

## Shared ownership rules

Changes to `harnessmith/contracts.py`, `schemas/`, or schema semantics require
cross-workstream review. Workstreams may consume these contracts but should not
extend them independently. `harnessmith.adapters` remains authoritative until
the adapter-contract workstream deliberately migrates it.

## Acceptance gate

- Existing compilation behavior remains compatible.
- All durable JSON formats have explicit schemas and versions.
- Corpus and behavioral tests run offline by default.
- Unsupported semantics fail closed.
- Static estimates and live runtime measurements are reported separately.
- Built artifacts install and run in a clean environment.
- Publishing remains a separate, explicitly authorized action.
