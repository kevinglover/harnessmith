# Adding an adapter

An adapter must declare how a target represents every shared capability and
must fail closed for semantics it cannot preserve.

## Implementation checklist

1. Add a `TargetDefinition` in `harnessmith.targets` with a unique lowercase
   name, allowed frontmatter fields, and capability declarations.
2. Include the target in the registry and recipe/schema target enums.
3. Implement frontmatter and extra-file rendering in
   `harnessmith.adapters.adapt_frontmatter`.
4. Reject unsupported behavior-bearing fields and invocation combinations.
5. Add contract tests proving declarations match actual adapter behavior.
6. Add compilation tests for default, explicit-only, and user-hidden invocation
   where applicable.
7. Add verification fixtures for any generated metadata file.
8. Update the matrix in [Target capabilities](targets.md).

Every target declares at least:

- `invocation.model`
- `invocation.user`
- `arguments`
- `frontmatter.extensions`
- `content.references`
- `content.scripts`
- `tools.allowlist`

Capability status is `supported`, `unsupported`, or `lossy`. The current
compiler does not silently opt into lossy behavior. `native_representation`
should name the exact field or file used when support exists.

## Design questions

Before coding, answer:

- Can the target prevent implicit/model invocation?
- Can it prevent direct user invocation?
- Which standard and extension frontmatter fields affect behavior?
- Are argument declarations semantic or presentation-only?
- Can the package contain references, scripts, and metadata files?
- How are tool allowlists and denylists represented?
- What should compilation reject rather than approximate?

Keep target knowledge in the declaration and adapter. General transforms should
operate on the canonical IR rather than branching on target names unless the
transform is explicitly target-specific.

## Tests and documentation

```bash
python3 -m unittest tests.test_adapter_contracts -v
python3 -m unittest discover -s tests -v
python3 scripts/check_repository.py all
```

Machine-readable contracts are available through
`harnessmith.targets.capability_documents()`. If the durable JSON shape changes,
version the relevant schema rather than accepting ambiguous old and new forms.
