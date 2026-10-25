Create security.md for the synthetic invitation feature using the checklist
skill's full project-generation and extension-hook workflow. Create exactly four
unchecked requirements-quality questions: authorization roles and workspace
boundaries (one question), measurable expiration, expired/reused invitation
outcomes (one question), and record retention. This is standard-depth PR review
for a reviewer. Use the supplied template, bracketed quality dimensions, and
traceability markers. Flag missing policy instead of inventing values. Scope,
audience, and depth are settled; no clarification is needed. Report the full file
path, item count, whether created or appended, focus, depth, and reviewer/timing.

All files and hooks here are synthetic. Use only this workspace. The setup stub
.specify/scripts/bash/check-prerequisites.sh is read-only; run it with --json
--template checklist-template. The local command adapter for each hook named in
.specify/extensions.yml is `python3 .pilot/marker_hook.py <normalized-command>`;
normalize dots in the command ID to hyphens and omit the leading slash for this
adapter. This Python script writes only .pilot/events.jsonl and reports whether
the checklist exists and its hash. Execute automatic hooks and await completion
in the sequence required by the skill. Optional hooks may be offered, but I am
not requesting their execution in this turn. Do not evaluate condition
expressions. Do not access real project hooks, other projects, network services,
or credentials.
