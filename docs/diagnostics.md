# Diagnostic rules

Harnessmith diagnostics use stable `HS` identifiers. The numeric namespace
communicates the affected area:

- `HS1xx` — source validity and ambiguity
- `HS2xx` — context efficiency
- `HS3xx` — target compatibility
- `HS4xx` — provenance and recipes (reserved)
- `HS5xx` — generated-package verification

Diagnostics have `error`, `warning`, or `note` severity. An error means the
requested target cannot preserve the source behavior. A warning identifies a
condition likely to require action. A note supplies review context and does not imply invalid input.

## Rule reference

### HS101 — Duplicate heading

Two or more sections have the same heading. Heading-only recipes cannot select
one occurrence unambiguously, so rename the sections before selecting either
one for transformation.

### HS102 — Invalid target metadata

A required field, string type, length, name, map, or tool-list representation
violates the selected target policy. Each field has its own source span. These
errors block compilation without changing the source. Structurally unreadable
frontmatter still raises a parser error before field-level diagnostics.

### HS103 — Installation directory mismatch

The source folder differs from the portable skill name. This is an advisory
installation warning: compiler staging paths and corpus IDs may differ. Claude
permits name overrides. See [Metadata validation](targets.md#metadata-validation).

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

### HS306 — Tool runtime semantics unverified

The compiler preserves an accepted tool field, but has no versioned runtime
evidence for grants or enforcement. Preservation is not an exclusive allowlist.

### HS307 — Host-specific body syntax

A known Claude dynamic command or substitution occurs in ordinary body text for
a non-Claude target. Review portability; compilation preserves it with a warning.

### HS308 — Possible literal host syntax

Known syntax occurs in a code context, quote, comment, or escaped text. This note
separates likely examples from ordinary prose without asserting that host
preprocessing ignores them. Use a note threshold to require review of both.

## Library rendering and CI thresholds

`harnessmith.diagnostics` exposes deterministic text, JSON, and SARIF renderers.
`diagnostics_fail_threshold(findings, "warning")` returns true for warning and
error findings; a threshold of `note` includes every diagnostic. CLI policy is
kept separate from these library APIs.

## Catalog findings

The read-only `catalog` command emits advisory warnings in the HS4xx namespace:
`HS401` for duplicate skill names, `HS402` for exceeding an operator-supplied
listing budget, and `HS403` for identical descriptions after case/whitespace
normalization. These findings do not establish host truncation or model trigger
accuracy. See [Catalog discovery audit](catalog-audit.md) for measurements and
versioned assumptions. Existing per-skill audit output is unchanged.
