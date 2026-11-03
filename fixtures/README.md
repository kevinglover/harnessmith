# Offline fixture corpus

This directory contains original, compact test skills used to exercise
Harnessmith without network access. The files are synthetic equivalents: they
model structural traits observed in the named ecosystems, but do not copy
upstream skill text. Corpus content is dedicated under CC0-1.0.

`manifest.json` follows `schemas/fixture-manifest.schema.json`. Every record
pins its local source bytes with SHA-256 and records:

- the upstream ecosystem that motivated the case;
- the synthetic corpus revision (`synthetic-equivalent-v1`);
- the local source path and license;
- targets expected to preserve the fixture's declared semantics; and
- stable diagnostic IDs expected by future evaluation runners.

The revision is deliberately a corpus-artifact revision, not an upstream Git
commit: no upstream bytes are redistributed. When a future fixture vendors an
upstream file under a compatible license, its record must instead use the full
upstream commit SHA and retain the upstream license and attribution.

## Coverage

The original ten fixtures cover six named ecosystems: Anthropic Skills, GitHub Awesome
Copilot, Hugging Face Skills, Microsoft Skills, Vercel Agent Skills, and GitHub
Spec Kit. Cases include a minimal skill, explicit-only invocation, unsupported
behavior-bearing frontmatter, duplicate headings, example-heavy content,
heading-like text inside a fence, Setext headings, cross-links, an HTML block,
and a root above the recommended 5,000-token budget.

An additional original Harnessmith lifecycle fixture covers read-only approval,
abort, hook failure, continuation, and compaction contracts. It is pinned at
`synthetic-lifecycle-v1` and dedicated under the same CC0-1.0 terms. Its events
are synthetic evaluation inputs, not recorded behavior of those ecosystems.

## Validate offline

From the repository root:

```bash
python3 -m unittest tests.test_fixture_corpus -v
```

Validation rejects unknown fields, duplicate IDs, unsafe paths, missing files,
unknown targets, malformed diagnostic IDs, and hash drift. Updating fixture
content therefore requires an intentional manifest hash update.

## Existing repository skill

`local-speckit-checklist` pins the existing `skills/speckit-checklist/SKILL.md`
without copying or modifying it. Unlike the synthetic fixtures, this entry uses
its local Git source revision and the repository's AGPL-3.0-only license; the
skill retains its spec-kit attribution. It supports the larger-skill Codex
benchmark's three optional-reference workloads. Diagnostic IDs are unique even
when a rule occurs at multiple source spans.
