# CLI reference

Harnessmith accepts a path to `SKILL.md` or its containing directory. Use the
installed `harnessmith` command or substitute `python3 -m harnessmith`.

## Audit

```bash
harnessmith SOURCE --target TARGET --audit [--json]
harnessmith SOURCE --target TARGET --audit --format text|json|sarif
```

Audit is read-only. It reports static size, bundled-resource inventory, target
compatibility, section classifications, structured diagnostics, and a recipe
template with no transforms selected. The legacy `--json` flag emits the
complete audit report. `--format text|json|sarif` emits structured diagnostics
only, and `--fail-on note|warning|error` returns exit code `1` when a finding
meets the chosen threshold.

## Compile

```bash
harnessmith SOURCE --target TARGET --output DIRECTORY [OPTIONS]
harnessmith SOURCE --recipe RECIPE.json --output DIRECTORY [OPTIONS]
```

Key options:

| Option | Meaning |
| --- | --- |
| `--recipe PATH` | Load reviewed target, source hash, transforms, and budgets. |
| `--extract-section HEADING` | Move an exact section into a mandatory reference; repeatable. |
| `--optimize-extension-hooks` | Enable the narrow Spec Kit extension-hook transform. |
| `--invocation source\|explicit\|automatic` | Preserve or deliberately override invocation policy. |
| `--source-id ID` | Record a stable provenance path instead of the input argument. |
| `--max-root-tokens N` | Fail above the generated-root static estimate. |
| `--max-normal-path-tokens N` | Fail above root plus mandatory-reference estimate. |
| `--json` | Emit the compile report as JSON. |
| `--dry-run` | Compile and validate without writing. |
| `--diff` | Report added, modified, and removed paths without writing. |

`--dry-run` and `--diff` are mutually exclusive. Both require `--output`
because the preview compares against that destination. An explicit CLI value
overrides the equivalent recipe value; a CLI target that conflicts with the
recipe target is rejected.

## Verify

```bash
harnessmith verify PACKAGE [--json]
```

Verification reads an existing generated package and never rewrites it. See
[Verification and evaluation](evaluation.md) for the checks and evidence
boundaries.

## Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | Command completed; verification found no issue. |
| `1` | `verify` found an invalid package, or audit met `--fail-on`. |
| `2` | Invalid arguments, unreadable input, or a compiler/audit safety error. |

## Targets and selectors

Targets are `generic`, `cursor`, `claude`, and `codex`. See the
[capability matrix](targets.md) before overriding invocation policy.

Section selection uses exact heading text. When a heading repeats, select a
stable occurrence such as `Examples[2]`.

## Version

```bash
harnessmith --version
```
