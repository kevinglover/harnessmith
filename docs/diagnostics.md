# Diagnostic rules

Harnessmith diagnostics use stable `HS` identifiers. The numeric namespace
communicates the affected area:

- `HS1xx` — source validity and ambiguity
- `HS2xx` — context efficiency
- `HS3xx` — target compatibility
- `HS4xx` — provenance and recipes (reserved)
- `HS5xx` — generated-package verification (reserved)

Diagnostics have `error`, `warning`, or `note` severity. An error means the
requested target cannot preserve the source behavior. A warning identifies a
condition likely to require action. A note is an optimization opportunity and
does not imply invalid input.

## Rule reference

### HS101 — Duplicate heading

Two or more sections have the same heading. Heading-only recipes cannot select
one occurrence unambiguously, so rename the sections before selecting either
one for transformation.

### HS201 — Recommended root budget exceeded

The always-loaded source exceeds the 5,000-token portable estimate. Review
`HS214` candidates before setting or enforcing the recommended recipe budget.
The estimate is deterministic and uses Harnessmith's documented
four-characters-per-token proxy; it is not measured runtime usage.

### HS214 — Reference-extraction candidate

A section is large, conditional, or clearly supporting material. Harnessmith
provides an exact-heading recipe fragment, but marks it as review-required
because a person must confirm load gates and the placement of behavior-bearing
instructions before extraction.

### HS305 — Target semantics unsupported

The selected adapter cannot represent a behavior-bearing source capability.
Compilation must remain fail-closed. Choose a compatible target or explicitly
revise the source semantics; Harnessmith does not offer an automatic fix.

## Library rendering and CI thresholds

`harnessmith.diagnostics` exposes deterministic text, JSON, and SARIF renderers.
`diagnostics_fail_threshold(findings, "warning")` returns true for warning and
error findings; a threshold of `note` includes every diagnostic. CLI policy is
kept separate from these library APIs.
