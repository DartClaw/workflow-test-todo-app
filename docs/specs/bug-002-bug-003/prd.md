# Product Requirements Document: Todo App Defect Fixes for BUG-002 and BUG-003

> **Context**: `docs/PRODUCT-BACKLOG.md` Known Defects (`BUG-002`, `BUG-003`); `docs/ROADMAP.md` Phase 2: Defect triage
> **Related Assets**: `AGENTS.md`, `CLAUDE.md`, `tests/test_todos.py`


## Executive Summary

- **Problem**: Two todo-editing behaviors break expected task metadata management. Due dates entered through the edit dialog are not reliably saved or shown when the dialog is reopened, and todos created through quick add do not consistently surface the documented default priority. These defects make todo state feel untrustworthy and force users to re-check or re-enter metadata.
- **Vision**: Todo metadata behaves predictably across creation and editing so users can trust that quick capture and later refinement preserve due dates and priority without extra correction.
- **Target Users**: Authenticated Todo App users managing tasks through the list page, especially users who quick-add tasks and later enrich them in the edit dialog.
- **Success Metrics**:
  - 100% of todos saved with a valid date through the edit dialog reopen with the same date populated.
  - 100% of quick-added todos reopen with `Low` selected as the priority default unless the user later changes it.
  - Invalid or unsupported date input from the edit flow never silently clears or mutates an existing due date.
  - Regression coverage exists for both defects in the automated test suite.

### Capabilities at a Glance
- **FR1: Persist Todo Due Date Updates** _(Must / P0)_ – Saving a valid due date from the edit dialog preserves that value in stored todo state and shows it again on subsequent edits.
- **FR2: Apply Default Priority on Quick Add** _(Must / P0)_ – Todos created through quick add start with the documented default priority so the edit dialog and rendered row stay consistent.

### Scope Highlights
- **In scope**: fix due-date persistence in the edit flow, fix quick-add default priority behavior, add regression checks for both defects
- **Out of scope**: redesigning the edit dialog, changing priority options, changing date/time semantics beyond this defect, productionizing authentication
- **MVP boundary**: a release that makes due-date edits persist correctly and makes quick-added todos consistently default to low priority without changing unrelated todo flows

### Key Constraints, Assumptions & Dependencies
- **Constraint:** The app is HTMX-first and returns HTML fragments, so defect fixes must preserve fragment-based interaction patterns rather than introduce JSON APIs.
- **Constraint:** `BUG-002` and `BUG-003` must be delivered as two thin stories with isolated file ownership so they can merge independently without conflicts.
- **Assumption:** The intended quick-add priority default is `low`, matching the documented and tested product expectation.
- **Dependency:** Existing todo CRUD tests remain the primary regression harness for these fixes.


## Problem Definition

### Problem Statement
Users rely on quick capture followed by later refinement of todo metadata. Today that workflow is unreliable in two places. First, when a user sets a due date in the edit dialog and saves, reopening the dialog may show the date field blank because the save path rejects or ignores the submitted format without surfacing an error. Second, when a user creates a todo through quick add, the resulting todo can lack the expected default priority, causing the edit dialog to show an empty selector instead of a predictable starting value. If left unresolved, users cannot trust whether important task metadata was actually saved.

### Evidence & Context
- `BUG-002` in `docs/PRODUCT-BACKLOG.md` identifies silent due-date persistence failure after edit-save-reopen.
- `BUG-003` in `docs/PRODUCT-BACKLOG.md` identifies missing default priority on quick-added todos.
- The project roadmap marks defect triage as the active phase, so restoring baseline behavior is the current product priority.
- Current route behavior already distinguishes quick add from full edit, which supports fixing the defects as two small, independent stories.


## Scope

### In Scope
- Ensure the edit flow accepts the date value shape emitted by the current due-date UI and stores it without silent loss.
- Ensure reopening the edit dialog for a saved todo shows the persisted due date in the due-date field.
- Ensure quick-added todos are created with the documented default priority.
- Ensure the todo row and edit dialog stay consistent about the quick-add default priority after creation.
- Add automated regression coverage that proves both flows work and stay isolated.

### Out of Scope
- Changing the set of supported priority levels.
- Expanding quick add to accept note, date, or priority input directly.
- Introducing timezone normalization or changing broader overdue/due-today logic.
- Refactoring unrelated todo CRUD behavior or template structure beyond what the defect fixes require.

### MVP Boundary
Users can quick-add a todo, open it for editing, and trust that it starts at low priority; users can also set or change a due date in the edit dialog, save it, and see the same date when reopening the same todo.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As a user editing a todo, I want a saved due date to remain attached to the todo so that I do not need to re-enter scheduling information. | After saving a valid due date, the todo re-renders with that date and the edit dialog reopens with the same date populated. Invalid date submission does not silently wipe or alter an existing saved date. | Must / P0 |
| US02 | As a user creating a todo from quick add, I want the todo to start with the standard default priority so that later edits begin from a predictable baseline. | A quick-added todo stores `low` priority immediately and the edit dialog shows `Low` selected until the user changes it. | Must / P0 |

### Feature Specifications

#### FR1: Persist Todo Due Date Updates
**Description**: The todo edit workflow must preserve valid due-date updates entered through the current edit dialog and must reflect the saved value consistently in both the rendered todo row and the dialog when reopened.

**Acceptance Criteria**:
- [ ] When a user saves a todo with a valid due date from the edit dialog, the stored todo record retains that due date.
- [ ] When the same todo is reopened in the edit dialog after a successful save, the due-date field is pre-populated with the saved value.
- [ ] Clearing the due-date field intentionally removes the due date from the todo.
- [ ] If the submitted due-date value is invalid or unsupported, the system does not silently replace an existing due date with an unintended value.

**Inputs / Outputs**:
- **Inputs**: todo edit submission with title, optional note, optional due date, and priority
- **Outputs**: updated todo HTML fragment, persisted due-date state, reopened dialog state matching persisted data

**Validation**:
- Accept the date format emitted by the current due-date input control.
- Preserve existing title validation and existing optional-field behavior.
- Treat an intentionally blank due-date submission as a request to clear the due date.

**Error Handling**:
- Invalid due-date input must not create silent data loss.
- If the due-date value cannot be accepted, the response must preserve user trust by leaving previously saved due-date data unchanged or by surfacing a normal error partial rather than pretending the save succeeded with altered data.

**Priority**: Must / P0

#### FR2: Apply Default Priority on Quick Add
**Description**: The quick-add creation workflow must assign the documented default priority to new todos so that the stored record, rendered row, and edit dialog all agree on the initial priority state.

**Acceptance Criteria**:
- [ ] When a user creates a todo through quick add with only a title, the stored todo record is created with `low` priority.
- [ ] The newly rendered todo row reflects the same default priority value used in storage.
- [ ] When the user opens the edit dialog for a quick-added todo, the priority selector shows `Low` selected.
- [ ] Existing edit behavior for manually changing priority after creation remains unchanged.

**Inputs / Outputs**:
- **Inputs**: quick-add submission with list ID and title
- **Outputs**: created todo HTML fragment, persisted default priority, edit dialog state that matches persisted priority

**Validation**:
- The quick-add flow still requires a non-empty title of 200 characters or fewer.
- The default priority is applied automatically when the quick-add form does not provide a priority value.

**Error Handling**:
- Validation failures in quick add still return the standard HTML error partial.
- The absence of an explicit priority in quick add is treated as normal input, not an error condition.

**Priority**: Must / P0

### User Flows
1. User opens an existing todo, enters a due date in the edit dialog, saves, and later reopens the dialog to confirm the same date is still present.
2. User opens an existing todo with a saved due date, clears the due-date field, saves, and later reopens the dialog to confirm the date is removed.
3. User quick-adds a new todo with title only, sees the todo appear in the list, opens the edit dialog, and finds `Low` already selected.
4. User encounters malformed due-date input during edit submission; the system avoids silent corruption and keeps saved metadata trustworthy.

### Data Requirements
- Todo records must continue to store an optional due-date value and a required effective priority value for all user-visible todos.
- Todos created through quick add must no longer rely on an undefined or blank priority state.
- The UI representation used to reopen the edit dialog must reflect persisted todo metadata, not an inferred fallback that masks storage defects.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Reliability | The two defect fixes must not break existing authenticated todo CRUD flows. | Relevant todo tests remain green after the fixes. |
| Usability | Metadata shown in the todo row and edit dialog must stay internally consistent after save and reopen. | No mismatch between persisted values and dialog defaults for the covered flows. |
| Maintainability | Each defect is implemented as an independent thin story. | Story 1 and Story 2 can merge without file conflicts. |
| Performance | Defect fixes must preserve the current interaction pattern and response feel. | No additional full-page reloads; fragment responses remain in use. |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves a todo with an empty due-date field | Existing due date is cleared intentionally. |
| User submits an invalid due-date format through the edit path | The system does not silently overwrite a saved due date with bad data. |
| User quick-adds multiple todos in succession | Every created todo receives the same default low priority. |
| User later changes a quick-added todo to medium or high | The user-selected priority persists normally after edit-save-reopen. |


## Constraints & Assumptions

### Constraints
- The app must keep its HTMX + FastAPI + Jinja fragment pattern; fixes are limited to current server-rendered todo flows.
- Authentication remains intentionally simple and is not part of this work.
- `BUG-002` and `BUG-003` must be planned as separate, thin stories with isolated file ownership so parallel or sequential merges do not conflict.
- Date handling outside the scoped persistence defect, including overdue styling semantics, is not to be changed here.

### Assumptions
- The product intent for due dates in this UI is date-only capture, because the current edit control exposes a date input rather than a date-time input.
- The expected default priority for newly created todos is `low`, based on the backlog wording and existing test expectation.
- Existing todo edit and quick-add flows should remain visually and behaviorally familiar apart from the defect corrections.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| `docs/PRODUCT-BACKLOG.md` defect definitions | Establishes the source scope and severity for both fixes. |
| Existing todo route and template behavior | Defines the current user flow that must be corrected without widening scope. |
| Automated tests under `tests/test_todos.py` and related todo coverage | Provide regression proof for the fixed behaviors. |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Treat `BUG-002` and `BUG-003` as two separate Must / P0 stories in one PRD | The user explicitly requested independent thin stories while keeping a shared product artifact for this milestone. | One combined story was rejected because it would blur scope and complicate merge-safe planning. |
| Keep the PRD focused on behavior and regression outcomes, not implementation mechanics | The downstream `andthen-plan` step is responsible for technical decomposition. | Embedding route-level code changes in the PRD was rejected as too implementation-specific. |
| Call out merge-safe isolation as a formal constraint | Independent delivery is part of the requested outcome, not just a coding preference. | Leaving isolation implicit was rejected because downstream planning could otherwise assign overlapping files. |
