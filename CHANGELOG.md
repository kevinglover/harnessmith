# Changelog

All notable changes to Harnessmith are documented here. The project follows
[Semantic Versioning](https://semver.org/) and keeps an
[Unreleased](https://keepachangelog.com/en/1.1.0/) section for changes not yet
published.

## Unreleased

### Added

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
