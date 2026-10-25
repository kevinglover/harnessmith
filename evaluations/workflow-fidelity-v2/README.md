# Workflow repair pilot v2

Offline preparation only unless a new live batch is explicitly approved.
`pilot.json` selects exactly two router-v2 cases: append, then creation with hooks.
It reuses the original synthetic fixtures and exact prompts; none are overwritten.

See the [scope and estimate](../../docs/workflow-fidelity-pilot-v2.md),
[prospective rubric v3](../variants/router-quality-rubric-v3.md), and
[router-v2 provenance review](../variants/speckit-checklist-router-v2.review.json).

The v2 checker/trace modules preserve all v1 modules and historical scores.
Tests are offline simulations, including adversarial traces and artifacts. They
validate the instrument, not model behavior. Historical results are not regraded.
The new runtime adapter uses the two-slot design and is disabled by default;
ordinary tests run a fake server without provider access.

Use a new output directory for each preparation. Reports remain versioned and
separate by model, instrument and package. A passing two-case diagnostic cannot
promote the router, demonstrate savings, or replace the failed six-case gate.
