# Workflow repair pilot v4

Offline preparation only; no live sessions are authorized by these files.
`pilot.json` fixes exactly two router-v4 cases, append then creation with hooks,
one fresh single-turn GPT-6 Luna low session each. No retries or replacement
slots. The original synthetic project fixtures and task prompts are unchanged.

See the [proposal](../../docs/workflow-fidelity-pilot-v4.md),
[prospective rubric v5](../variants/router-quality-rubric-v5.md), and
[reviewed package identity](../variants/speckit-checklist-router-v4.review.json).

Checker/collector v4 reuse the pinned trace normalizer v3 and its schema-3
observations. No shell grammar, failed-command tolerance or sandbox boundary
changes. Preparation pins new and inherited instruments. The bounded topic
screen retains matched reuse cues; the final-hook-claim screen retains phase
and supporting event/message IDs. Neither passes semantic correctness or general
narrative accuracy. Review remains mandatory even when no claim is recognized.

The collector is disabled by default. Tests use synthetic observations and a
local fake stdio server, never a provider or real project hooks. Every attempted
result must be retained. Instrumentation/isolation defects stop the remaining
slot; ordinary fidelity failures do not authorize replacement. Earlier evidence
is not regraded. A passing diagnostic would not establish runtime savings,
equivalence, reliability, promotion or OPT-004 completion.

Prepare into a fresh directory without credentials or provider access:

```bash
python3 -m harnessmith.workflow_fidelity_v4 prepare \
  --output /tmp/opt004-workflow-v4-review
```
