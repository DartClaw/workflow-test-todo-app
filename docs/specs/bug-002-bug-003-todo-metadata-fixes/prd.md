# Product Requirements Document: Todo App - BUG-002 and BUG-003 Metadata Fixes

> **Context**: `docs/PRODUCT-BACKLOG.md` Known Defects (`BUG-002`, `BUG-003`)
> **Related Assets**: `README.md`, `tests/test_todos.py`, `tests/test_models.py`


## Executive Summary
- **Problem**: Two todo metadata workflows are not trustworthy. Due dates saved from the edit dialog do not persist, and quick-add todos can be created without the documented default priority. Users can save or create a todo successfully yet reopen it and see missing metadata.
- **Vision**: Todo metadata behaves consistently across quick-add, edit, render, and reopen flows so users can trust saved due dates and default priority values.
- **Target Users**: Authenticated Todo App users who create todos from the quick-add form and edit them through the dialog.
- **Success Metrics**:
  - 100% of todos saved from the edit dialog with a valid due date reopen with that same date populated.
  - 100% of todos created through quick-add without an explicit priority persist with `low` priority and reopen with `low` selected.
  - Both fixes ship as independent thin stories that can be planned and merged without cross-story file conflicts.


## Problem Definition

### Problem Statement
The current todo workflow breaks user trust in saved metadata. When a user sets a due date in the edit dialog and saves, the todo appears to save successfully but the due date is gone when the dialog is reopened. When a user creates a todo through the quick-add form, the app can persist the todo without the documented default priority, which later appears as an empty selector in the edit dialog. Both defects create silent inconsistency between what the UI implies and what the stored todo data actually contains.

### Evidence & Context
- `BUG-002` in `docs/PRODUCT-BACKLOG.md` reports that due dates entered via the edit dialog do not persist and notes that the current parsing path silently swallows format mismatches.
- `BUG-003` in `docs/PRODUCT-BACKLOG.md` reports that quick-add todos have no default priority even though the documented default is `low`.
- `tests/test_todos.py` and `tests/test_models.py` already encode `low` as the expected default priority for todo creation.
- The current app uses HTMX partial swaps and a shared edit dialog, so missing metadata is visible immediately on reopen even when the initial save request appears successful.


## Scope

### In Scope
- Restore persistence of date values saved through the existing todo edit dialog.
- Ensure quick-add todo creation applies the documented default priority when the user provides only a title.
- Preserve consistent metadata display when the todo row rerenders and when the edit dialog is reopened.
- Capture the two fixes as separate thin stories with isolated delivery scope for downstream planning.

### Out of Scope
- Redesigning the edit dialog or quick-add UI.
- Adding new priority values or a priority control to the quick-add form.
- Expanding due dates into time-of-day scheduling.
- Changing authentication, authorization, database ownership rules, or unrelated todo behaviors.

### MVP Boundary
The smallest acceptable release fixes the existing edit and quick-add defects without changing surrounding workflows: valid date-only due dates entered in the current edit dialog must save and reappear, and quick-add todos created with only a title must persist as `low` priority everywhere the todo is later viewed or edited.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As a user editing a todo, I want a due date I save in the dialog to still be there when I reopen the todo so that I can trust my schedule data. | Saving an existing todo with a valid date-only due date persists the date, rerenders the todo with that due date, and prepopulates the same date when the edit dialog is reopened. | Must / P0 |
| US02 | As a user using quick-add, I want new todos to start with the documented default priority so that later edits show a consistent initial state. | Creating a todo through quick-add with only a title persists `low` priority and shows `low` as selected when the edit dialog is opened. | Must / P0 |

### Feature Specifications

#### FR1: Persist Due Dates From the Edit Dialog
**Description**: Users must be able to save a due date from the existing edit dialog and see that same value across subsequent renders and edits.

**Acceptance Criteria**:
- [ ] When a user saves an existing todo with a valid date chosen in the edit dialog, the todo record persists that date.
- [ ] After a successful save, the returned todo row shows the saved due date in the existing due-date display area.
- [ ] Reopening the edit dialog for that todo shows the same saved date already populated.
- [ ] If the user clears the due date and saves, the due date is removed and the reopened dialog remains blank.

**Inputs / Outputs**:
- **Inputs**: Existing todo ID, edited title, optional note, optional date value from the current date input, optional priority.
- **Outputs**: Updated HTML partial for the todo row, persisted due-date state, consistent dialog prefill on reopen.

**Validation**:
- Accept the date format produced by the current edit dialog control.
- Treat an empty due-date field as an explicit clear action.
- Continue existing title validation rules.

**Error Handling**:
- If the due-date value cannot be interpreted, the system must not silently drop or ignore the user change while presenting a successful save.
- The user must receive visible error feedback in the standard HTML error pattern, and the existing stored todo state must remain unchanged.

**Priority**: Must / P0

#### FR2: Apply Default Priority to Quick-Add Todos
**Description**: Todos created through the quick-add form must inherit the documented default priority without requiring additional user input.

**Acceptance Criteria**:
- [ ] When a user submits the quick-add form with only a title, the created todo persists with priority `low`.
- [ ] The newly rendered todo row reflects the `low` priority state consistently with existing priority badges and styling.
- [ ] Opening the edit dialog for a quick-add-created todo shows `low` as the selected priority.
- [ ] Existing flows that explicitly set `medium` or `high` priority continue to preserve the user-selected value.

**Inputs / Outputs**:
- **Inputs**: List ID and title from the quick-add form.
- **Outputs**: Created todo HTML partial, persisted default priority, consistent priority preselection in later edits.

**Validation**:
- Quick-add continues to require only a non-empty title.
- When priority is omitted in this flow, the system applies `low` automatically.
- Existing priority validation remains restricted to `low`, `medium`, and `high`.

**Error Handling**:
- Existing quick-add validation errors for blank or overlong titles remain unchanged.
- The system must not create a quick-add todo with a missing or empty priority value.

**Priority**: Must / P0

### User Flows
1. User opens an existing todo, selects a due date in the edit dialog, saves, and later reopens the dialog to confirm the same date is still present.
2. User clears a previously saved due date in the edit dialog, saves, and later reopens the dialog to confirm the field is blank.
3. User creates a todo from quick-add with only a title, sees the new todo render, and later opens the edit dialog to confirm `low` priority is selected.
4. User submits an invalid due-date payload from the edit path and receives visible error feedback instead of a silent partial success.

### Data Requirements
- `Todo.due_date` remains optional and must support the date-only values emitted by the current edit dialog.
- `Todo.priority` remains limited to `low`, `medium`, and `high`.
- Todos created through quick-add must never persist with a null or empty priority.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Performance | Edit-save and quick-add interactions remain lightweight HTMX requests. | No additional user-visible round trip or full-page reload is introduced. |
| Reliability | Todo metadata is not silently lost in the covered flows. | 0 known cases where a valid edit-dialog due date or quick-add default priority disappears after a reported successful save. |
| Security | Existing auth and ownership protections remain intact. | No change to authenticated access rules for todo create or update routes. |
| Usability | Saved and default metadata remain obvious to the user. | Due dates and priorities are visible immediately after save and prefilled correctly on reopen. |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves an edit-dialog due date in the current date-only input format. | The date persists and reappears on reopen. |
| User clears an existing due date and saves. | The due date is removed and the field stays blank on reopen. |
| User quick-adds a todo and opens edit immediately. | The priority selector shows `low` selected. |
| Client submits an unsupported due-date format to the update flow. | The save does not silently succeed; the user sees an error and the todo keeps its prior stored value. |
| User later edits a quick-add-created todo and changes priority to `medium` or `high`. | The explicitly chosen priority persists normally. |


## Constraints & Assumptions

### Constraints
- The app remains HTMX-first and must continue returning HTML partials rather than introducing new JSON API behavior for these flows.
- The downstream plan must keep `BUG-002` and `BUG-003` as two independent thin stories with non-overlapping file ownership where feasible so they can merge without conflict.
- The intentionally simple authentication and session model must remain unchanged.

### Assumptions
- The documented default priority for new todos is `low`, based on existing tests and model defaults.
- The current edit dialog remains a date-only experience; users do not need time-of-day support in this fix.
- Existing todo ownership checks and route-level validation patterns remain the baseline for both stories.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| `docs/PRODUCT-BACKLOG.md` defect definitions | Defines the user-visible problem statement and severity for both stories. |
| Existing todo create/edit flows | The fixes must preserve current HTMX partial behavior and dialog interactions. |
| Existing tests and documented defaults | Provide the expected default-priority contract and guard against regression. |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Capture `BUG-002` and `BUG-003` in one PRD with two separate P0 stories. | The defects affect the same product area but can still be planned and implemented independently. | Two standalone PRDs, which would add process overhead for two thin fixes. |
| Keep the due-date fix limited to persistence of the current date-only dialog input. | This resolves the reported user pain without expanding scope into scheduling redesign. | Adding datetime support or a different input control, which is outside the defect scope. |
| Require quick-add to inherit the documented `low` default without exposing extra controls. | This matches existing expectations and keeps the story thin. | Adding a quick-add priority selector or deferring default resolution until first edit. |
