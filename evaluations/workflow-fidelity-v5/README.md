# Workflow repair pilot v5

Offline candidate only. No live sessions are authorized or launched by this work.
The fixed design has two router-v5 cases, append then creation with harmless
synthetic hooks. The original prompts and fixtures remain unchanged.

See the [repair plan](../../docs/workflow-fidelity-pilot-v5.md),
[rubric v6](../variants/router-quality-rubric-v6.md), and
[package review](../variants/speckit-checklist-router-v5.review.json).
Checker/collector v5 consume schema-4 observations from normalizer v4. New and
inherited dependencies, package, source, fixtures and prompts are hash-pinned.

Prepare two isolated workspaces without credentials, provider calls or attempts:

```bash
python3 -m harnessmith.workflow_fidelity_v5 prepare \
  --output /tmp/opt004-workflow-v5-review
```

Tests use synthetic observations and a local fake server. They distinguish
internal append verification and proven reads from failed command envelopes,
masked failures, invented hooks and unsupported commentary. They validate
instrument behavior and package contracts, not live model compliance.

Prior evidence, scores, instruments and the original skill are frozen. The
collector stays disabled by default; no previous live authorization carries
forward. Any future approval must cover the exact two fresh Luna low sessions,
one turn each, no retries or replacements. Retain every result; stop remaining
slots on instrumentation/isolation defects. Semantic/raw review is mandatory;
efficiency and broader promotion remain unproven.
