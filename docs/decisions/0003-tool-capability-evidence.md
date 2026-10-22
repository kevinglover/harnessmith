# ADR 0003: Separate tool representation from runtime permission evidence

- Status: accepted
- Date: 2026-10-22

## Decision

Emit adapter capability schema version 2, retaining version 1 for historical
readers. Add an `unknown` status rather than using `supported` for untested host
behavior. Other durable contracts remain at version 1.

Separate tool metadata preservation, preapproval grants, and restrictions. Keep
legacy capability keys for discoverability, but correct their statuses and
explain their replacement semantics. A field that can be serialized does not
prove runtime enforcement. Document source dates and known version constraints;
all runtime claims remain unverified until measured under OPT-004.

The shared contract, adapter behavior, schemas, and consumer documentation change
together and are checked by capability, metadata, and schema tests. This is one
integrated contract change, not independent extensions by separate workstreams.

## Consequences

Consumers must explicitly accept capability version 2. A consumer expecting
version 1 must reject version 2 instead of interpreting unknown as supported.
Compilation can preserve tool metadata with an advisory diagnostic, while known
unsupported restrictive frontmatter continues to fail closed. No grant/restriction
conversion is inferred from spelling or field presence.
