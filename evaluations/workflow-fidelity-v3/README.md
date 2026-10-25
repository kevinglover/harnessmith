# Workflow repair pilot v3

Offline preparation only. No live sessions are authorized by these files.
`pilot.json` selects exactly two new router-v3 cases: append, then creation with
hooks, one fresh single-turn GPT-6 Luna low session each, with no retries or
replacement slots. It reuses the original synthetic fixtures and exact prompts.

See the [scope and estimate](../../docs/workflow-fidelity-pilot-v3.md),
[prospective rubric v4](../variants/router-quality-rubric-v4.md), and
[router-v3 provenance review](../variants/speckit-checklist-router-v3.review.json).

Checker, trace normalizer and collector v3 preserve every older instrument and
score. The prepared manifest pins the complete baseline inventory and the known
absent optional plan/tasks paths. Only those bounded absence checks gain support;
unknown control flow or possible earlier mutation still fails. Complete agent
messages retain lifecycle indices separately from operation events. Hook blocks
must be shown at the correct phase, and final artifact reads must prove complete
final bytes after writes. This proof currently supports standalone literal `cat`
with exact returned final bytes, or the bounded literal write-plus-`cat` form;
other compound reads and partial excerpts do not qualify. Descriptions and optional prompts are fixture-specific
screens, not a general YAML or semantic judge.

The collector remains disabled by default. Its offline tests use a local fake
stdio server and synthetic hooks, with no provider access. Native file-change
creation and exact-byte append are the preferred write path; temporary-directory
permissions remain restricted. A denied heredoc remains a failed action even if
an eventual write recovers. Every attempt and partial result must be retained.

Prepare into a fresh directory. Keep future reports separate by model, package,
instrument and rubric. Offline controls do not certify model behavior; a passing
two-case diagnostic would neither promote the router nor prove runtime savings.
