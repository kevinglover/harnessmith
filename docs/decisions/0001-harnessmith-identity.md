# ADR 0001: Harnessmith is the sole public identity

- Status: accepted
- Date: 2026-10-08

## Decision

Use `harnessmith` for the distribution, Python package, CLI command, generated
manifest owner, and documentation. `Skill Compiler` describes the former
workspace and project phase; it is not an alias or compatibility surface.

## Consequences

New code must not introduce a `skill_compiler` import or command. Historical
references may remain where they explain provenance. A future rename requires
a separate migration decision because recipes and manifests are durable data.
