# Frozen review rubric for the router pilot

Apply this rubric to every strategy, without using strategy identity or usage to
judge quality. Keep output text and raw trace identifiers. Automated checks are
necessary but insufficient; record each criterion as pass/fail with supporting
answer text and explanation. Missing review is pending, never a pass.

## Security consultation

- Four unchecked, sequential checklist questions with traceability markers.
- Authorization covers both roles/permissions and workspace/tenant boundaries.
- Expiry asks for measurable definition rather than inventing a duration.
- Expired/reused invitation outcomes are addressed as requirement gaps.
- Invitation-record retention requirements are addressed without invented policy.
- Questions evaluate documented requirements, not running the implementation.

## API examples

- Both requested questions match the source exactly.
- The chosen questions address dependency outages and API evolution.
- Explanation distinguishes requirements coverage from testing implementation.
- No invented quotations or unsupported project claims.

## Examples and correction

- All three requested quotations match their source exactly.
- Explanation connects documented layout requirements with the distinction
  between reviewing a specification and exercising an export button.
- Final rewrite asks whether export behavior is documented; it must not assert
  invented product requirements or instruct an implementation test.
- Answer stays under 250 words (automated count conservatively includes commentary).

## Process and interpretation

Use the same frozen reference-read expectations for all extracted variants.
Retain unknown-command classification failures separately from answer failures.
Do not hide failures, rerun selectively, or change grading after seeing results.
Compare total/cached/uncached input, output, latency, read commands and answer
quality per task. Report structural pass, semantic review, and process pass
separately. This consultation pilot does not establish generation/hook fidelity
or implicit discovery quality. Full project-workflow evaluation is required before
promoting the redesigned package into the compiler or replacing the original skill.
