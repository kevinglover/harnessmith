# Changelog

All notable changes to Harnessmith are documented here. The project follows
[Semantic Versioning](https://semver.org/) and keeps an
[Unreleased](https://keepachangelog.com/en/1.1.0/) section for changes not yet
published.

## Unreleased

### Added

- Backward-compatible version-2 evaluation scenarios with independent canonical
  and compiled turn contracts across all targets, including invocation channels,
  approval, abort, hook failure, reference reloads, continuation, and compaction.
- Opt-in repeated runtime evidence collection with package/source/configuration
  hashes, environment versions, raw traces and usage, explicit mock labeling,
  and published scenario/evidence schemas. No built-in live provider is enabled.

- Target-aware metadata diagnostics and compile validation, with advisory
  installation-directory checks and preserved frontmatter text.
- Advisory host-specific body syntax and tool-permission diagnostics in audit
  and compilation output; embedded commands are never evaluated.
- Capability schema version 2 separating tool metadata preservation from
  unverified runtime grants and restrictions; version 1 schema retained.

- Versioned contracts, adapter capability declarations, and an offline fixture
  corpus.
- Explicit transform pipeline and Markdown parsing regression coverage.
- Reproducible packaging, repository quality checks, and release validation.
- Byte-exact preservation of bundled references, scripts, and binary assets,
  including executable metadata and fail-closed collision checks.
- Strict manifest validation and transactional package publication with
  modified-output protection and rollback.
- Environment-independent extension-hook parsing with fail-closed duplicate-key
  handling and exact fallback behavior for unsupported YAML.

## 0.1.0 - 2026-10-08

### Added

- Initial Harnessmith compiler, audit command, recipes, and deterministic
  compiled example.

[Unreleased]: https://github.com/kevinglover/harnessmith/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kevinglover/harnessmith/releases/tag/v0.1.0
