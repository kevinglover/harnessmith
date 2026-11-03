---
name: explicit-review
description: Provide a brief requirements-quality review only when explicitly invoked by the user.
disable-model-invocation: true
user-invocable: true
---
# Explicit requirements review

Only operate after explicit user invocation. An implicit request must not load
this skill or run its workflow. When invoked, read Review examples completely,
then provide the requested requirements-quality assessment without editing files.

## Review examples

"Invitations expire quickly" lacks a measurable duration and reference clock.
This is a requirements-quality finding, not an implementation test result.
