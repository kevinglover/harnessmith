## Pre-Execution Checks

**Before setup: render, execute, then proceed.** Read and select the pre-hooks
below. Emit every selected automatic announcement and optional offer as actual,
completed user-visible commentary before invoking any pre-hook. Multiple blocks
may share one message. Then invoke automatic hooks in configuration order and
wait for their returned results. Only after this checkpoint may setup begin.
A promise to show offers, a list of IDs, or a later report is not the checkpoint.
For both phases, render the template contents below as actual Markdown prose,
starting at the left margin without the templates' list indentation, surrounding
code fence or blockquote. Do not introduce them as samples or future output.
The code fences here only delimit the field templates.

**Check for extension hooks (before checklist generation)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_checklist` key
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, render the following block in user-visible output,
  substituting the actual extension, description, prompt and normalized command
  ID. A statement that hooks were offered or executed is not a substitute for
  the block. Keep the displayed command ID distinct from any local invocation
  used to run that command. Select the block based on its `optional` flag:
  - **Optional hook** (`optional: true`): Offer it without running it unless the
    user has explicitly authorized that optional hook. Continue checklist work
    without waiting for approval to an optional offer.

    ```text
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Description: {description}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Execution Steps.
    ```

    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Execution Steps

1. **Setup**: After the pre-hook checkpoint, run `.specify/scripts/bash/check-prerequisites.sh --json --template checklist-template` from repo root and parse its returned JSON for FEATURE_DIR, AVAILABLE_DOCS list, and TEMPLATE_CONTENT.
   - Use the script's executable/shebang or an interpreter justified by its
     contents. Report failures only when an actual tool result records them;
     do not infer an attempted command or error from the filename.
   - All file paths must be absolute.
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Project principles**: Independently check the repo-root path
   `.specify/memory/constitution.md` and read it if present, before generating
   or appending checklist items. `AVAILABLE_DOCS` describes feature documents;
   it is not an inventory of project governance files. Perform this check for
   append operations as well as new files. Do not treat a missing entry in
   `AVAILABLE_DOCS` as proof that the constitution is absent.

3. **Clarify intent (dynamic)**: Derive up to THREE initial contextual clarifying questions (no pre-baked catalog). They MUST:
   - Be generated from the user's phrasing + extracted signals from spec/plan/tasks
   - Only ask about information that materially changes checklist content
   - Be skipped individually if already unambiguous in `$ARGUMENTS`
   - Prefer precision over breadth

   Generation algorithm:
   1. Extract signals: feature domain keywords (e.g., auth, latency, UX, API), risk indicators ("critical", "must", "compliance"), stakeholder hints ("QA", "review", "security team"), and explicit deliverables ("a11y", "rollback", "contracts").
   2. Cluster signals into candidate focus areas (max 4) ranked by relevance.
   3. Identify probable audience & timing (author, reviewer, QA, release) if not explicit.
   4. Detect missing dimensions: scope breadth, depth/rigor, risk emphasis, exclusion boundaries, measurable acceptance criteria.
   5. Formulate questions chosen from these archetypes:
      - Scope refinement (e.g., "Should this include integration touchpoints with X and Y or stay limited to local module correctness?")
      - Risk prioritization (e.g., "Which of these potential risk areas should receive mandatory gating checks?")
      - Depth calibration (e.g., "Is this a lightweight pre-commit sanity list or a formal release gate?")
      - Audience framing (e.g., "Will this be used by the author only or peers during PR review?")
      - Boundary exclusion (e.g., "Should we explicitly exclude performance tuning items this round?")
      - Scenario class gap (e.g., "No recovery flows detected—are rollback / partial failure paths in scope?")

   Question formatting rules:
   - If presenting options, generate a compact table with columns: Option | Candidate | Why It Matters
   - Limit to A–E options maximum; omit table if a free-form answer is clearer
   - Never ask the user to restate what they already said
   - Avoid speculative categories (no hallucination). If uncertain, ask explicitly: "Confirm whether X belongs in scope."

   Defaults when interaction impossible:
   - Depth: Standard
   - Audience: Reviewer (PR) if code-related; Author otherwise
   - Focus: Top 2 relevance clusters

   Output the questions (label Q1/Q2/Q3). After answers: if ≥2 scenario classes (Alternate / Exception / Recovery / Non-Functional domain) remain unclear, you MAY ask up to TWO more targeted follow‑ups (Q4/Q5) with a one-line justification each (e.g., "Unresolved recovery path risk"). Do not exceed five total questions. Skip escalation if user explicitly declines more.

4. **Understand user request**: Combine `$ARGUMENTS` + clarifying answers:
   - Derive checklist theme (e.g., security, review, deploy, ux)
   - Preserve explicit item counts and one-question-per-topic allocations. Map
     each requested topic to its own question before consolidating duplicates;
     do not combine two allocated topics or fill the count with a redundant item.
   - Map focus selections to category scaffolding
   - Infer any missing context from spec/plan/tasks (do NOT hallucinate)

5. **Load feature context**: Read from FEATURE_DIR:
   - spec.md: Feature requirements and scope
   - plan.md (if exists): Technical details, dependencies
   - tasks.md (if exists): Implementation tasks

   **Context Loading Strategy**:
   - Load only necessary portions relevant to active focus areas (avoid full-file dumping)
   - Prefer summarizing long sections into concise scenario/requirement bullets
   - Use progressive disclosure: add follow-on retrieval only if gaps detected
   - If source docs are large, generate interim summary items instead of embedding raw text

6. **Generate checklist** - Use TEMPLATE_CONTENT as the structural template and create "Unit Tests for Requirements":
   - Discover existing checklist files through the known-existing `FEATURE_DIR`
     inventory (for example, `rg --files FEATURE_DIR`), not a direct listing of a
     possibly absent `checklists/` directory. Create the directory within the
     allowed workspace if needed; its initial absence is normal checklist setup.
   - Generate unique checklist filename:
     - Use short, descriptive name based on domain (e.g., `ux.md`, `api.md`, `security.md`)
     - Format: `[domain].md`
   - File handling behavior:
     - If file does NOT exist: Create new file and number items starting from CHK001
     - If file exists: Append new items to existing file, continuing from the last CHK ID (e.g., if last item is CHK015, start new items at CHK016)
   - Before appending, read the existing file. Preserve its bytes as an exact
     prefix, including reviewer notes, whitespace and mixed checkbox states.
     Append new content; never delete, replace or reformat existing content.
   - **Write checkpoint**: Use the available native `apply_patch` or file-edit
     tool first for both creation and append. Keep the edit inside the allowed
     project workspace. Under restricted temporary-file permissions, do not
     try heredocs, here-strings, permission probes, or retries of denied shell
     writes; their hidden temporary files may be outside the allowed workspace.
     Do not broaden permissions or change the temporary-directory policy.
   - If no native edit tool is available, use direct file I/O that needs no
     temporary file and fits the existing permissions. For append, open in
     binary append mode and write only the new bytes, preserving the complete
     existing prefix; do not reconstruct the old file through text conversion.
     If no permitted method is available, report the blocker without claiming
     the file was written.
   - Read back the final artifact and verify exact new items, IDs and unchecked
     states, plus the unchanged prefix for append. Complete this verification
     before the post-hook checkpoint. A successful-looking shell exit does not
     erase a write error printed in its output.
   - Leave every newly generated item unchecked (`[ ]`); checkbox state belongs to the reviewer

   **CORE PRINCIPLE - Test the Requirements, Not the Implementation**:
   Every checklist item MUST evaluate the REQUIREMENTS THEMSELVES for:
   - **Completeness**: Are all necessary requirements present?
   - **Clarity**: Are requirements unambiguous and specific?
   - **Consistency**: Do requirements align with each other?
   - **Measurability**: Can requirements be objectively verified?
   - **Coverage**: Are all scenarios/edge cases addressed?

   **Category Structure** - Group items by requirement quality dimensions:
   - **Requirement Completeness** (Are all necessary requirements documented?)
   - **Requirement Clarity** (Are requirements specific and unambiguous?)
   - **Requirement Consistency** (Do requirements align without conflicts?)
   - **Acceptance Criteria Quality** (Are success criteria measurable?)
   - **Scenario Coverage** (Are all flows/cases addressed?)
   - **Edge Case Coverage** (Are boundary conditions defined?)
   - **Non-Functional Requirements** (Performance, Security, Accessibility, etc. - are they specified?)
   - **Dependencies & Assumptions** (Are they documented and validated?)
   - **Ambiguities & Conflicts** (What needs clarification?)

   **HOW TO WRITE CHECKLIST ITEMS - "Unit Tests for English"**:

   ❌ **WRONG** (Testing implementation):
   - "Verify landing page displays 3 episode cards"
   - "Test hover states work on desktop"
   - "Confirm logo click navigates home"

   ✅ **CORRECT** (Testing requirements quality):
   - "Are the exact number and layout of featured episodes specified?" [Completeness]
   - "Is 'prominent display' quantified with specific sizing/positioning?" [Clarity]
   - "Are hover state requirements consistent across all interactive elements?" [Consistency]
   - "Are keyboard navigation requirements defined for all interactive UI?" [Coverage]
   - "Is the fallback behavior specified when logo image fails to load?" [Edge Cases]
   - "Are loading states defined for asynchronous episode data?" [Completeness]
   - "Does the spec define visual hierarchy for competing UI elements?" [Clarity]

   **ITEM STRUCTURE**:
   Each item should follow this pattern:
   - Question format asking about requirement quality
   - Focus on what's WRITTEN (or not written) in the spec/plan
   - Include quality dimension in brackets [Completeness/Clarity/Consistency/etc.]
   - Reference spec section `[Spec §X.Y]` when checking existing requirements
   - Use `[Gap]` when checking for a missing policy or requirement, including
     when the item also cites a related existing requirement. A spec citation
     alone does not identify the missing part.

   **EXAMPLES BY QUALITY DIMENSION**:

   Completeness:
   - "Are error handling requirements defined for all API failure modes? [Gap]"
   - "Are accessibility requirements specified for all interactive elements? [Completeness]"
   - "Are mobile breakpoint requirements defined for responsive layouts? [Gap]"

   Clarity:
   - "Is 'fast loading' quantified with specific timing thresholds? [Clarity, Spec §NFR-2]"
   - "Are 'related episodes' selection criteria explicitly defined? [Clarity, Spec §FR-5]"
   - "Is 'prominent' defined with measurable visual properties? [Ambiguity, Spec §FR-4]"

   Consistency:
   - "Do navigation requirements align across all pages? [Consistency, Spec §FR-10]"
   - "Are card component requirements consistent between landing and detail pages? [Consistency]"

   Coverage:
   - "Are requirements defined for zero-state scenarios (no episodes)? [Coverage, Edge Case]"
   - "Are concurrent user interaction scenarios addressed? [Coverage, Gap]"
   - "Are requirements specified for partial data loading failures? [Coverage, Exception Flow]"

   Measurability:
   - "Are visual hierarchy requirements measurable/testable? [Acceptance Criteria, Spec §FR-1]"
   - "Can 'balanced visual weight' be objectively verified? [Measurability, Spec §FR-2]"

   **Scenario Classification & Coverage** (Requirements Quality Focus):
   - Check if requirements exist for: Primary, Alternate, Exception/Error, Recovery, Non-Functional scenarios
   - For each scenario class, ask: "Are [scenario type] requirements complete, clear, and consistent?"
   - If scenario class missing: "Are [scenario type] requirements intentionally excluded or missing? [Gap]"
   - Include resilience/rollback when state mutation occurs: "Are rollback requirements defined for migration failures? [Gap]"

   **Traceability Requirements**:
   - MINIMUM: ≥80% of items MUST include at least one traceability reference
   - Each item should reference: spec section `[Spec §X.Y]`, or use markers: `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`
   - If no ID system exists: "Is a requirement & acceptance criteria ID scheme established? [Traceability]"

   **Surface & Resolve Issues** (Requirements Quality Problems):
   Ask questions about the requirements themselves:
   - Ambiguities: "Is the term 'fast' quantified with specific metrics? [Ambiguity, Spec §NFR-1]"
   - Conflicts: "Do navigation requirements conflict between §FR-10 and §FR-10a? [Conflict]"
   - Assumptions: "Is the assumption of 'always available podcast API' validated? [Assumption]"
   - Dependencies: "Are external podcast API requirements documented? [Dependency, Gap]"
   - Missing definitions: "Is 'visual hierarchy' defined with measurable criteria? [Gap]"

   **Content Consolidation**:
   - Soft cap: If raw candidate items > 40, prioritize by risk/impact
   - Merge near-duplicates checking the same requirement aspect only within
     the user's requested topic allocation. A one-question-per-topic request
     takes precedence over the general consolidation rules.
   - If >5 low-impact edge cases, create one item: "Are edge cases X, Y, Z addressed in requirements? [Coverage]"

   **🚫 ABSOLUTELY PROHIBITED** - These make it an implementation test, not a requirements test:
   - ❌ Any item starting with "Verify", "Test", "Confirm", "Check" + implementation behavior
   - ❌ References to code execution, user actions, system behavior
   - ❌ "Displays correctly", "works properly", "functions as expected"
   - ❌ "Click", "navigate", "render", "load", "execute"
   - ❌ Test cases, test plans, QA procedures
   - ❌ Implementation details (frameworks, APIs, algorithms)

   **✅ REQUIRED PATTERNS** - These test requirements quality:
   - ✅ "Are [requirement type] defined/specified/documented for [scenario]?"
   - ✅ "Is [vague term] quantified/clarified with specific criteria?"
   - ✅ "Are requirements consistent between [section A] and [section B]?"
   - ✅ "Can [requirement] be objectively measured/verified?"
   - ✅ "Are [edge cases/scenarios] addressed in requirements?"
   - ✅ "Does the spec define [missing aspect]?"

7. **Structure Reference**: Generate the checklist following the canonical template in `.specify/templates/checklist-template.md` for title, meta section, category headings, ownership note, notes section, and ID formatting. If template is unavailable, use: H1 title, purpose/created meta lines, an ownership note explaining that `[x]` means reviewer approval of requirements quality, `##` category sections containing `- [ ] CHK### <requirement item>` lines with globally incrementing IDs starting at CHK001, and notes that `/speckit-implement` reads checklist state but does not modify markers.

8. **Post-hook checkpoint**: Stop after final-file verification and perform
   these actions before the final report:
   - Send a completed commentary message containing the actual configured
     automatic announcements and optional offers below. The message itself must
     contain the substituted blocks; “I am rendering/offering the hooks” is only
     a plan and does not complete this action.
   - Check that the sent message includes every selected hook's block. Only then
     invoke automatic hooks in configuration order and wait for their results.
   - Verify the artifact again if a post-hook changed it.

   **Check for extension hooks (after checklist generation)**:
   Check if `.specify/extensions.yml` exists in the project root.

   - If it exists, read it and look for entries under the `hooks.after_checklist` key
   - If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally
   - Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
   - For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
     - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
     - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
   - When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
   - For each executable hook, render the following block in user-visible output,
     substituting the actual extension, description, prompt and normalized command
     ID. A statement that hooks were offered or executed is not a substitute for
     the block. Keep the displayed command ID distinct from any local invocation
     used to run that command. Select the block based on its `optional` flag:
     - **Optional hook** (`optional: true`): Offer it without running it unless the
       user has explicitly authorized that optional hook. Continue checklist work
       without waiting for approval to an optional offer.

       ```text
       ## Extension Hooks

       **Optional Hook**: {extension}
       Command: `/{command}`
       Description: {description}

       Prompt: {prompt}
       To execute: `/{command}`
       ```

     - **Mandatory hook** (`optional: false`):

       ```text
       ## Extension Hooks

       **Automatic Hook**: {extension}
       Description: {description}
       Executing: `/{command}`
       EXECUTE_COMMAND: {command}
       ```

       After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
   - If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

9. **Report**: Report the full checklist path, new item count, whether it was
   created or appended, focus, depth, actor/timing, and explicit must-have items
   incorporated. Before adding a verification or limitation claim, match it to
   evidence already returned in this session: final bytes for file claims, a
   completed sent block for an offer, and a completed tool result for an execution
   outcome. Omit a claim that has no such evidence; do not add exploratory commands
   merely to support an unnecessary report detail. Missing metadata or an untried
   tool is not evidence that a comparison or capability was unavailable. Report
   only confirmed failures as failures; label any relevant unresolved check as
   unverified. An announced intent is neither an offer displayed nor a hook run.

**Important**: Each `/speckit-checklist` command invocation uses a short, descriptive checklist filename and either creates a new file or appends to an existing one. This allows:

- Multiple checklists of different types (e.g., `ux.md`, `test.md`, `security.md`)
- Simple, memorable filenames that indicate checklist purpose
- Easy identification and navigation in the `checklists/` folder

To avoid clutter, use descriptive types and clean up obsolete checklists when done.
