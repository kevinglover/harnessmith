# Safety model

Harnessmith is conservative at semantic and filesystem boundaries. A smaller
package is never sufficient reason to weaken instructions.

## What Harnessmith will not do automatically

- Silently discard behavior-bearing frontmatter or instructions.
- Weaken user or model invocation restrictions to satisfy a target.
- Summarize or rewrite semantic prose based on a heuristic.
- Extract an ambiguous heading or guess how to rewrite local fragment links.
- Apply a source-pinned recipe after the source hash changes.
- Write through a symlink or overwrite a populated directory it does not own.
- Treat a static size estimate as proof of runtime savings or behavior.

## Trust boundaries

Canonical skill content and recipes are reviewed inputs, not trusted executable
policy. Generated scripts are only produced by named transforms. A manifest is
evidence of compiler ownership and integrity, not a signature or sandbox.
Consumers must still review skills and execute bundled scripts under the target
harness's normal security controls.

## Fail-closed target adaptation

Adapters preserve known compatible fields, record safe presentation-field
filtering, and reject unsupported behavior-bearing fields. Invocation policy is
resolved before rendering; if the chosen target cannot represent it,
compilation stops. See [Target capabilities](targets.md).

## Lossless extraction

Selected sections are copied exactly into generated references and replaced by
a mandatory read instruction. The compiler records source spans and hashes and
checks that normative lines remain present across generated Markdown. This is a
strong regression guard, but it is not a semantic proof; reviewers remain
responsible for deciding whether moving the section preserves usable routing
context.

## Output ownership

Harnessmith writes to an empty directory or one containing a valid
Harnessmith-owned `.harnessmith.json`. On regeneration it removes only paths
listed in the earlier manifest. It refuses regeneration when an owned file no
longer matches its recorded hash, which prevents silently replacing manual
edits or trusting a stale ownership record.

Writes are staged beside the destination and published with a directory swap.
If publication fails, Harnessmith restores the previous directory. Use
`--dry-run` or `--diff` when the destination is uncertain, and run the
independent verifier before distributing generated output.

Bundled `references/`, `scripts/`, and `assets/` must contain regular files and
directories only. Symlinks and collisions with compiler-generated paths are
rejected. File contents are preserved byte-for-byte, including binary assets;
executable script metadata is recorded and verified separately.
