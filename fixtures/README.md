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

The ten fixtures cover six named ecosystems: Anthropic Skills, GitHub Awesome
Copilot, Hugging Face Skills, Microsoft Skills, Vercel Agent Skills, and GitHub
Spec Kit. Cases include a minimal skill, explicit-only invocation, unsupported
behavior-bearing frontmatter, duplicate headings, example-heavy content,
heading-like text inside a fence, Setext headings, cross-links, an HTML block,
and a root above the recommended 5,000-token budget.

## Validate offline

From the repository root:

```bash
python3 -m unittest tests.test_fixture_corpus -v
```

Validation rejects unknown fields, duplicate IDs, unsafe paths, missing files,
unknown targets, malformed diagnostic IDs, and hash drift. Updating fixture
content therefore requires an intentional manifest hash update.
