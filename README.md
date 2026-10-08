# Harnessmith

Harnessmith audits and compiles canonical Agent Skills into deterministic,
target-aware packages for `generic`, `cursor`, `claude`, and `codex` harnesses.

> **Alpha:** the CLI, package manifest, and optimization passes may change before
> a stable release.

Harnessmith keeps optimization reviewable. It moves exact source sections only
when you select them, records every transform in `.harnessmith.json`, and fails
when a target cannot preserve behavior-bearing semantics. It does not silently
rewrite instructions to make a skill fit.

## Install

From a checkout, use Python 3.9 or newer:

```bash
python3 -m pip install -e .
harnessmith --version
```

You can also run every example below as `python3 -m harnessmith ...` without
installing the console script.

## Five-minute workflow

Audit a skill without writing files:

```bash
harnessmith skills/speckit-analyze \
  --target cursor \
  --audit \
  --json
```

Preview the checked-in, source-pinned recipe:

```bash
harnessmith skills/speckit-analyze \
  --recipe recipes/speckit-analyze.cursor.json \
  --output /tmp/harnessmith-preview \
  --diff
```

Compile and independently verify the package:

```bash
harnessmith skills/speckit-analyze \
  --recipe recipes/speckit-analyze.cursor.json \
  --output /tmp/harnessmith-preview

harnessmith verify /tmp/harnessmith-preview
```

The recipe pins the source SHA-256. If the source changes, compilation stops
until the recipe is reviewed. `--dry-run` and `--diff` compile and validate in
memory without writing the output directory.

## What compilation changes

An exact section extraction replaces the selected root section with a mandatory
read instruction and moves its original bytes into `references/`:

```text
SKILL.md                         compiled package/
├─ Workflow                     ├─ SKILL.md (workflow + required read gate)
└─ Detailed examples     ->     ├─ references/detailed-examples.md
                                └─ .harnessmith.json
```

The generated manifest records source and recipe hashes, output hashes,
transform provenance, and static size estimates. See the
[optimization walkthrough](docs/optimization-model.md#walkthrough-large-skill-to-progressive-disclosure)
for an exact example.

## Documentation

- [CLI reference](docs/cli.md)
- [Architecture](docs/architecture.md)
- [Optimization model](docs/optimization-model.md)
- [Target capability matrix](docs/targets.md)
- [Recipes](docs/recipes.md)
- [Diagnostics](docs/diagnostics.md)
- [Verification and evaluation](docs/evaluation.md)
- [Safety model](docs/safety-model.md)
- [Adding an adapter](docs/adding-an-adapter.md)
- [Roadmap](docs/roadmap.md)

The earlier [investigation and design report](docs/harness-aware-skill-compilation.md)
is retained as historical research. The task-focused guides above describe the
current implementation.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_repository.py docs
```

The repository also contains Spec Kit-derived skills used as real compiler
inputs. Their maintenance and integration layout are documented in the
[legacy research report](docs/harness-aware-skill-compilation.md) and are not
the product boundary.

Harnessmith is licensed under the [GNU Affero General Public License v3.0](LICENSE).
