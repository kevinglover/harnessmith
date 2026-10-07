# Cross-Repository Evaluation Corpus

Harnessmith should optimize Agent Skills as a format, not treat one generator
or ecosystem as the product boundary. This corpus adds breadth without
vendoring third-party content into the repository.

The machine-readable source of truth is
[`benchmarks/repositories.json`](../benchmarks/repositories.json). Every entry
pins an upstream commit so measurements can be reproduced even as a repository
changes.

## Candidate repositories

| Repository                 | Why it belongs in the corpus                                      | Useful stress cases                         |
| -------------------------- | ----------------------------------------------------------------- | ------------------------------------------- |
| `anthropics/skills`        | First-party examples with both concise and very large skills      | API references and skill-authoring guidance |
| `github/awesome-copilot`   | A broad, actively maintained collection across many domains       | Very large playbooks and modernization      |
| `microsoft/skills`         | A large collection with nested plugin and skill layouts           | Authoring guidance and SDK workflows        |
| `huggingface/skills`       | Domain-heavy workflows with commands, training, and deployment    | CLI and model-training procedures           |
| `vercel-labs/agent-skills` | A smaller product-focused collection with modern framework skills | Optimization and deployment workflows       |

Counts and candidate sizes in the manifest are discovery data, not quality
rankings. They identify inputs likely to exercise long roots, nested headings,
conditional detail, bundled resources, or target-specific metadata.

One pinned skill from each repository passes a Cursor-target audit:

| Skill               | Estimated source tokens | Review candidates |
| ------------------- | ----------------------: | ----------------: |
| `skill-creator`     |                   8,247 |                 4 |
| `doc-and-modernize` |                  12,386 |                 6 |
| `copilot-sdk`       |                   7,118 |                 1 |
| `hf-cli`            |                   8,403 |                 2 |
| `vercel-optimize`   |                   4,328 |                 2 |

These are parser and audit smoke tests, not claims of behavioral equivalence or
automatic optimization. Token counts use Harnessmith's deterministic
four-characters-per-token estimate.

## Running a local evaluation

Check out a pinned repository outside Harnessmith, then point the audit at any
skill directory or `SKILL.md`:

```bash
python3 -m harnessmith /path/to/repository/skills/example \
  --target cursor \
  --audit \
  --json
```

The audit is read-only. It reports:

- source and resource size;
- target-frontmatter compatibility;
- nested and duplicate heading risks;
- behavior-bearing lines that need preservation;
- large or conditional sections worth human review; and
- a safe recipe template with no transformations selected.

Review the findings, choose exact sections, and save a recipe beside the
Harnessmith source. Compilation then pins the audited source hash:

```bash
python3 -m harnessmith /path/to/repository/skills/example \
  --recipe recipes/example.cursor.json \
  --output /path/to/generated/example
```

If upstream changes the source, compilation stops and requires a new audit.
This keeps optimization policy and target compatibility in Harnessmith without
forking or permanently rewriting the upstream skill.

## Evaluation sequence

Start with one skill from each shape rather than the largest files only:

1. a short control that should receive no extraction;
2. a long single-file skill with reference candidates;
3. a skill that already bundles `references/`, `scripts/`, or `assets/`;
4. a skill with non-standard target metadata; and
5. a skill with global safety or approval rules that must remain in the root.

For each target, compare the canonical and compiled package on invocation
semantics, required reads, command ordering, approval boundaries, output
structure, failure behavior, and path-loaded tokens. A smaller root alone is
not a passing result.

## Licensing and updates

Do not vendor a candidate repository merely to run an audit. Clone it under its
own license and keep only measurements, recipes, and fixture content whose
license has been reviewed. `NOASSERTION` in the manifest means the GitHub API
did not identify a license; it does not mean the content is unlicensed or free
to redistribute.

Refresh a repository revision deliberately. Re-run discovery and behavioral
checks before replacing a pinned SHA or accepting a changed source hash.
