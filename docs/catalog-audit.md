# Catalog discovery audit

`harnessmith catalog skills --target codex --json` recursively inventories
`SKILL.md` files in the supplied directory. Targets currently supported are
`codex` and `claude`. This is a read-only static inventory of that directory,
not an inventory of everything installed in a running host. Directory symlinks
are not traversed; symlinked `SKILL.md` files are rejected. Missing or malformed
required metadata fails the command rather than silently dropping entries.

## Measurements and assumptions

The version-1 synthetic listing is one compact JSON object per line, with keys
`name`, `description`, and `path`, in that order. Paths are relative to the
catalog root; entries are sorted by path. Non-ASCII characters are retained and
each line ends with a newline. Character counts use Unicode code points, not
UTF-8 bytes. The token estimate is the existing four-characters-per-token proxy,
rounded up over the whole listing.

The report separates the raw name, description, and path characters from
formatting overhead (keys, quotes, punctuation, newline, and JSON escaping).
These components sum to the exact synthetic listing length. Source hashes,
a listing hash, and a normalized profile hash support repeatable comparisons.
The report does not include root bodies, tools, system prompts, absolute install
paths, hidden host entries, or other context unless represented by an explicit
reserve. It does not predict which skills a host will omit or select.

Without a profile there is **no budget threshold**. Supply `--profile PATH`
with explicit versioned assumptions to enable overflow findings. For example,
this is a synthetic testing profile, **not a measured Codex limit**:

```json
{
  "schema_version": 1,
  "profile_id": "synthetic-crowded-catalog-v1",
  "target": "codex",
  "host_version": "unverified",
  "listing_format": "json-lines-name-description-path-v1",
  "budget_characters": 12000,
  "reserved_characters": 2000,
  "evidence": "Operator-selected test threshold; no host truncation measurement."
}
```

`budget_characters` is a positive integer or null. `reserved_characters` is a
nonnegative integer added to the measured listing for comparison. Overflow is
`max(0, listing + reserve - budget)`; equality does not overflow. Null budget
produces null overflow. Unknown fields, unsupported versions/formats, and a
target mismatch are rejected. Change `profile_id` when revising assumptions;
record measured host/model/mode versions and evidence in the profile before
using it to interpret a real installation.

## Findings and output

- `HS401`: identical skill names in multiple paths.
- `HS402`: synthetic listing plus reserve exceeds the supplied budget.
- `HS403`: descriptions match after case folding and whitespace normalization.

Findings are advisory warnings. Identical descriptions are a review signal,
not proof of an ambiguous trigger. Distinct descriptions can still overlap;
this command performs no semantic classification or rewriting. Positive and
negative trigger trials in a crowded catalog require opt-in runtime evaluation
before any selection-accuracy claim. Runtime metrics remain null.

`--json` prints the full report. `--format json` or `--format sarif` prints
only structured diagnostics; text is the default. `--fail-on warning` returns
1 for any of these findings. Invalid inputs return 2. Otherwise the command
returns 0. No output files are written.

Contracts: [profile schema](../schemas/catalog-profile.schema.json),
[report schema](../schemas/catalog-report.schema.json).
