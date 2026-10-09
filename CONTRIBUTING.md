# Contributing to Harnessmith

Thank you for helping improve Harnessmith. By participating, you agree to
follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Harnessmith supports CPython 3.9 through 3.13. Create an isolated environment
and install the project with its development tools:

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Run the same core checks used by CI:

```console
python -m unittest discover -s tests -v
python -m coverage run -m unittest discover -s tests
python -m coverage report
python -m ruff check .
python -m mypy
python scripts/check_repository.py all
python -m build
python -m twine check dist/*
```

The repository check validates both the published JSON Schemas and the
checked-in recipes, fixture manifest, and compiled package manifests against
those schemas.

The fixture corpus is offline and pinned. Validate it with the fixture tests;
do not silently replace fixture sources or their provenance hashes.

## Change guidelines

- Add focused tests for behavioral changes and regressions.
- Preserve fail-closed behavior when a target cannot represent source
  semantics.
- Update `CHANGELOG.md` for user-visible changes.
- Do not hand-edit generated examples. Regenerate them using their checked-in
  recipes, then review the diff.
- Keep pull requests narrow and explain compatibility or schema implications.

CI on pull requests uses read-only repository permissions and requires no
contributor secrets. Maintainers perform releases through the separately
gated release workflow after reviewing the built artifacts.

## Releasing (maintainers)

1. Ensure CI passes on every supported Python version.
2. Move relevant Unreleased entries under the new semantic version and update
   `harnessmith.__version__`.
3. Run the Release validation workflow with that exact version.
4. Download and inspect the wheel and source distribution.
5. Create a signed `vX.Y.Z` tag and GitHub release only after review.

The workflow deliberately does not publish to PyPI or create a release.
