---
name: lifecycle-review
description: Review a supplied change using an approval-gated, read-only workflow.
---
# Lifecycle review

## Workflow

Review supplied changes only. Do not invoke for unrelated requests.
Read Examples before inspecting a change.
Inspect the change and request approval before running checks.
Run checks only after approval. Never deploy or modify files.
On a hook failure, report it and stop; do not retry automatically.
On continuation, retain the prior approval decision and report existing results.
After compaction, reload Examples and restate the read-only constraint.
On abort, stop immediately without performing further actions.

## Examples

A whitespace-only change has no actionable findings.
An unavailable checker is reported as a hook failure; it is never bypassed.
