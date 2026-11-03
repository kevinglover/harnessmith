# Offline workflow fidelity instrument v1

The [pilot plan](../../docs/workflow-fidelity-pilot.md) specifies the exact proposed
six-session scope. This directory contains new synthetic CC0-1.0 project fixtures
and prompts, separate from historical scenario evidence. The original skill and
reviewed router are copied without edits during preparation; their existing
licenses and provenance remain applicable.

```bash
python3 -m harnessmith.workflow_fidelity prepare --output /tmp/opt004-workflow-review
python3 -m harnessmith.workflow_fidelity check \
  /tmp/opt004-workflow-review/create-router/manifest.json \
  /tmp/create-router-observation.json --output /tmp/create-router-checks.json
```

The second command requires an observation file supplied by an evaluator; it does
not launch a model, execute hooks or generate a checklist. Both output locations
must be new. `prepare` emits six workspace manifests and a `preparation.json`
index with manifest hashes. It snapshots the checker, rubric and pilot config in
`instrument/`. Every manifest pins package, fixture and prompt bytes. Check rejects
manifest, prompt or instrument drift, and refuses to silently use a different
checker version. Prepare a new bundle after changing the instrument.

## Normalized observation format

This is a version-1 pilot-specific interchange format, not the existing runtime
comparison report schema. It is evaluator input, not independent proof. Required
fields are `schema_version: 1`, `evidence_kind`, `completed`, `model`, `events` and
`output`. Use `offline-simulation` for authored controls or
`externally-captured-observation` for a future collector's normalized events.
The model must be `gpt-6-luna`. `output` includes the captured announcements and
final answer in order; `events` is an ordered list of completed operations:

| Type | Additional fields | Meaning |
| --- | --- | --- |
| `read` | `path`, `status`, `exit_code` | Workspace-relative file path; a successful read requires `completed` and exit code 0. |
| `setup` | `command`, `status`, `exit_code` | Exact synthetic setup command, completed with exit code 0. |
| `hook` | `command`, `status`, `exit_code` | Normalized hook ID, completed with exit code 0; collector must retain the actual local Python invocation in its raw trace. |
| `write` | `path`, `status`, optional `exit_code` | Workspace-relative checklist path; completed write, exit code 0 if present. Marker writes are consequences of hook commands, not separate allowed direct writes. |

Any failed/incomplete or unclassified operation fails workflow checks. The
collector must not drop such events while normalizing. Order means completion
order, with separate raw start/completion evidence sufficient to verify awaiting
hooks before subsequent actions. Directory creation can be associated with the
artifact write only after reviewing the actual command and its affected paths.
The setup stub returns template content; a separate template-read event is not
required. Constitution/spec reads, and an existing append-target read, must
precede artifact writes. Router guidance must precede all project operations.

Optional `raw_trace` identifies the retained raw events; optional `usage` stores
observed measurements for review. The current checker does not authenticate raw
traces or validate measurement completeness and always reports efficiency as
not evaluated. A live collector must provide harness/model/mode versions,
permissions, cache policy, actual usage and trace-to-event mappings before any
runtime claim. Do not fill those fields with estimates or expected events.

The resulting report separates automated checks for content screening,
formatting, reference behavior and workflow. It always sets model fidelity to
pending and promotion eligibility to false. Human semantic and raw-trace reviews
are mandatory next steps, even when all automated controls pass. Unit tests
exercise positive and corrupted artifacts/events in temporary directories; their
local script executions are fixture validation, never live skill observations.
