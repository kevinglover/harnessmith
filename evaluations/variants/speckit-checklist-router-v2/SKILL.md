---
name: "speckit-checklist"
description: "Generate a custom checklist for the current feature based on user requirements."
argument-hint: "Domain or focus area for the checklist"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/checklist.md"
user-invocable: true
disable-model-invocation: false
---

# Requirements-quality checklists

Evaluate what the requirements document specifies: completeness, clarity,
consistency, measurability, and scenario coverage. Do not turn the task into
implementation testing. Respect the user's focus, audience, depth, and requested
output; do not invent requirement values or missing project facts.

## Shared rules

- Write questions about whether requirements are defined, quantified, consistent,
  or complete. Cover relevant primary, alternate, exception, recovery, and
  non-functional scenarios; flag missing requirements instead of inventing them.
- For checklist items, use `- [ ] CHK###` with incrementing IDs, a question, and a
  bracketed quality dimension. Reference existing requirements with `[Spec §ID]`;
  use `[Gap]`, `[Ambiguity]`, `[Conflict]`, or `[Assumption]` as appropriate.
  When a question identifies a missing policy or requirement, include `[Gap]`
  even when it also cites a related existing spec section.
  At least 80% of generated items must have a traceability reference or marker.
- Custom checklists are reviewer-owned. Generate unchecked items only. `[x]`
  means reviewer approval of requirements quality, not implementation completion.
  Evaluate existing items only when the reviewer asks. The built-in
  `checklists/requirements.md` maintained by specify/clarify is a separate case.
- When writing a checklist file, preserve every existing byte, including notes
  and checkbox states; append with IDs continuing after the last existing ID.
  Never replace or reformat prior content.
- Honor the user's requested count and allocation. When they ask for one question
  per topic, assign a distinct question to each topic; do not combine topics or
  fill the count with a question that repeats them. Consolidate duplicates only
  within that allocation. Without an explicit allocation, prioritize by risk if
  candidates exceed 40 and combine more than five low-impact edge cases.

## Choose the relevant guidance

For a consultation using supplied context, answer directly using the shared rules.
Do not initiate project generation just because this skill is selected. Clarify
only missing information that materially changes the requested result.

For creating or appending an actual project checklist, read
[project-generation.md](references/project-generation.md) before taking project
actions. It contains prerequisite/template discovery, constitution and feature
context loading, clarification defaults, file structure, reporting, and the full
before/after extension-hook procedure. Follow its sequence, including enabled
mandatory hooks and their completion, unless the user has explicitly limited scope.

For requests for domain sample questions, or when examples are needed to resolve
an item-writing ambiguity, read
[Example Checklist Types & Sample Items](references/example-checklist-types-sample-items.md).

For requests for wrong/right examples or for correcting implementation-test wording,
read [Anti-Examples: What NOT To Do](references/anti-examples-what-not-to-do.md).

Load only the guidance relevant to the task. A linked reference is not itself a
reason to read it. When quoting an example, read its source and preserve its wording.
