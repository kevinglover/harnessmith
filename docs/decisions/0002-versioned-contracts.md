# ADR 0002: Version durable contracts independently from package releases

- Status: accepted
- Date: 2026-10-08

## Decision

Every durable JSON document has a required integer `schema_version`. Version 1
schemas live in `schemas/`; Python shared vocabulary lives in
`harnessmith.contracts`. Package versions and schema versions do not imply one
another.

Unknown fields fail validation for recipes and top-level durable manifests.
Compatibility is fail-closed: adapters classify behavior as `supported`,
`unsupported`, or `lossy`, and lossy behavior may not silently compile.

## Consequences

Additive schema changes that affect consumers require a deliberate schema
decision. Downstream work should import the shared enums and records rather
than inventing parallel severity or capability labels.
