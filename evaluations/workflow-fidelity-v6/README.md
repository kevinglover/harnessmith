# Append repair pilot v6

Offline candidate only. No live session is authorized or launched by this work.
The fixed design is one `append-router-v6` session using the original synthetic
append prompt and fixtures. Router v5's passing hooks case remains historical;
it is not a new-version hooks result.

See the [proposal](../../docs/workflow-fidelity-pilot-v6.md),
[rubric v7](../variants/router-quality-rubric-v7.md) and
[package review](../variants/speckit-checklist-router-v6.review.json).
Checker/collector v6 consume schema-5 observations from normalizer v5. All
new and inherited dependencies, source, package, fixtures and prompt are pinned.

Prepare the single isolated workspace without credentials, provider calls or
attempts:

```bash
python3 -m harnessmith.workflow_fidelity_v6 prepare \
  --output /tmp/opt004-workflow-v6-review-final
```

Synthetic regressions cover literal read-only Python, full standalone `cat`
hash/coverage proof, safe cache attribution,
configuration/absence before standalone setup, complete postwrite verification
and unsupported verification/Git claims. The local fake server checks retention,
version wiring and the one-attempt boundary; it does not run Codex or a provider.

Historical evidence, old instruments, previous scores and the original skill
are frozen. The collector is disabled by default. A later approval must cover
exactly one fresh GPT-6 Luna low session, one turn, no retries or replacements.
Retain every outcome and stop on instrumentation/isolation defects. Semantic
and raw review remain mandatory. No efficiency or general promotion claim is
part of this diagnostic.
