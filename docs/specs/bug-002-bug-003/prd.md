# Product Requirements Document: Todo App – BUG-002 and BUG-003 Defect Fixes

> **Context**: `docs/PRODUCT-BACKLOG.md` Known Defects entries `BUG-002` and `BUG-003`
> **Related Assets**: `README.md`, `docs/STATE.md`, `AGENTS.md`


## Executive Summary

- **Problem**: Two core todo-editing behaviors are broken. Due dates entered in the edit dialog do not persist after save, and todos created through quick-add do not carry the documented default priority. Both defects create silent data loss or incomplete task metadata in everyday flows.
- **Vision**: Users can trust the app’s two fastest task-management paths: editing a due date preserves the selected calendar date, and quick-added todos consistently start with the expected default priority.
- **Target Users**: Authenticated Todo App users managing tasks through the list view, especially users relying on quick capture and later editing.
- **Success Metrics**:
  - 100% of edited todos with a valid saved due date show the same date when the edit dialog is reopened.
  - 100% of quick-added todos open in the edit dialog with `Low` selected by default unless the user later changes it.
  - 0 known regressions to manual todo editing for title, note, or priority caused by this release.
  - Both defects can be verified through automated route-level tests and manual UI validation in the authenticated app flow.

### Capabilities at a Glance
- **FR1: Persist Edited Due Dates** _(Must / P0)_ – Saving a due date from the edit dialog must store and round-trip the selected calendar date back into the dialog.
- **FR2: Apply Default Priority on Quick Add** _(Must / P0)_ – Creating a todo through quick-add must assign the documented default priority so later edits start from a valid value.

### Scope Highlights
- **In scope**: fix due-date persistence for the edit-todo dialog, fix default priority for quick-add todo creation, add verification coverage for both defects.
- **Out of scope**: redesigning todo forms, changing the meaning of priority levels, changing the intentionally simple auth/session model, broader due-date styling defects such as `BUG-004`.
- **MVP boundary**: a release is complete when both defects are fixed in their existing user flows with no change to surrounding product behavior.

### Key Constraints, Assumptions & Dependencies
- **Constraint:** The app is HTMX-first and server-rendered; fixes must preserve existing fragment-based flows rather than introduce new API patterns.
- **Constraint:** `BUG-002` and `BUG-003` must be planned as independent thin stories that can merge without conflicts.
- **Assumption:** The documented default priority for newly created todos is `low`, matching the existing product copy and data model expectations.
- **Dependency:** Downstream implementation and planning must respect the current educational project boundaries, including intentionally simple authentication.


## Problem Definition

### Problem Statement
The Todo App’s main task-entry and task-editing flows currently violate user expectations in two ways. First, a user can choose a due date in the edit dialog, save successfully, and later find the date field empty when reopening the dialog. This makes the save action unreliable and risks missed deadlines because the UI does not reflect the user’s prior input. Second, quick-add creates todos without a valid default priority, so later editing exposes an empty selector instead of the documented default. This weakens consistency across todo creation paths and leaves task metadata incomplete unless the user notices and repairs it manually.

### Evidence & Context
- `BUG-002` in `docs/PRODUCT-BACKLOG.md` states that due dates entered through the edit dialog do not persist and that the parsing path silently swallows format mismatches.
- `BUG-003` in `docs/PRODUCT-BACKLOG.md` states that quick-add todos have no default priority and later show an empty priority selector.
- The app’s primary authenticated screen exposes both flows prominently: quick-add in the list content area and edit actions on each todo row.
- These are defect fixes, not feature expansion. The product intent already exists and should be restored with minimal surface-area change.


## Scope

### In Scope
- Restore persistence of valid due dates entered through the existing edit-todo dialog.
- Ensure quick-add todo creation assigns the documented default priority to new records.
- Preserve existing behavior for title, note, completion state, and list ownership checks while fixing these defects.
- Add verification artifacts sufficient for downstream planning and implementation to prove each defect is fixed independently.

### Out of Scope
- Changing due-date semantics beyond persistence in the edit dialog.
- Revising quick-add UI to expose more fields or user-configurable defaults.
- Fixing unrelated known defects, including overdue/due-today styling and sidebar count refresh behavior.
- Reworking data models, session handling, or the HTMX rendering pattern.

### MVP Boundary
The smallest acceptable release fixes exactly two user-visible defects in existing flows: edited due dates survive save-and-reopen, and quick-add todos default to low priority with no empty priority state when later edited.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As a user editing a todo, I want a saved due date to still appear when I reopen the dialog so that I can trust the app to preserve scheduling details. | A valid date chosen in the edit dialog remains associated with the todo after save and is shown again when the dialog is reopened. | Must / P0 |
| US02 | As a user creating a todo with quick-add, I want the todo to start with the default priority so that later edits always begin from a complete, documented state. | A todo created through quick-add is stored with the default priority and the edit dialog shows that default selected unless changed later. | Must / P0 |

### Feature Specifications

#### FR1: Persist Edited Due Dates
**Description**: The edit-todo workflow must store a valid due date selected through the existing dialog and must round-trip that date back into the UI when the same todo is edited again.

**Acceptance Criteria**:
- [ ] When a user saves a todo with a valid due date from the edit dialog, the todo record retains that date after the save completes.
- [ ] When the user reopens the edit dialog for that todo, the due-date input displays the previously saved date.
- [ ] Saving a todo without a due date continues to clear the due date as it does today.
- [ ] A malformed due-date submission does not create a misleading success state with silently lost user input.

**Inputs / Outputs**:
- **Inputs**: edited todo title, optional note, optional due-date value submitted from the edit dialog.
- **Outputs**: persisted todo due date, updated todo row rendering, reopened edit dialog showing the current stored date.

**Validation**:
- Accept valid calendar-date input from the existing edit dialog.
- Preserve current title validation rules.
- Treat empty due-date input as an intentional clear action.

**Error Handling**:
- If due-date input is invalid for the supported edit flow, the app must not imply that the submitted date was saved successfully.
- Existing HTML-based error handling patterns remain the user-facing contract.

**Priority**: Must / P0

#### FR2: Apply Default Priority on Quick Add
**Description**: The quick-add workflow must create todos with the documented default priority so that all todos created through the main entry path start in a valid, editable state.

**Acceptance Criteria**:
- [ ] When a user creates a todo through quick-add without explicitly setting priority, the new todo is stored with priority `low`.
- [ ] When the user opens the edit dialog for that todo, the priority selector shows `Low` selected.
- [ ] Existing non-quick-add creation or edit flows continue to support valid `low`, `medium`, and `high` priorities.
- [ ] The fix does not require any additional input from the user during quick-add.

**Inputs / Outputs**:
- **Inputs**: quick-add title and the current list context.
- **Outputs**: newly created todo with default priority, todo row rendering consistent with that priority, edit dialog prepopulated with the stored value.

**Validation**:
- Quick-add remains a minimal-entry path with title as the only required user input.
- Default priority must be a valid supported priority value.

**Error Handling**:
- If quick-add creation fails for existing reasons such as invalid title, the app continues to return its existing HTML error behavior.
- The absence of a submitted priority from quick-add must not result in an empty or null effective priority state.

**Priority**: Must / P0

### User Flows
1. User edits an existing todo, selects a due date, saves, then reopens the dialog and sees the same date still present.
2. User quick-adds a todo with only a title, opens the edit dialog, and sees `Low` already selected.
3. User clears a previously set due date in the edit dialog and the todo remains without a due date after save.
4. If an unsupported due-date payload reaches the server, the app avoids falsely presenting the save as a successful persisted date change.

### Data Requirements
- Todo records must continue to support an optional due-date field that can be set, retained, or cleared.
- Todo records created through quick-add must always have one of the supported priority values, with `low` as the default for this flow.
- No new entities, user preferences, or configuration surfaces are required for this effort.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Reliability | Both defect fixes behave consistently across repeated save-and-reopen cycles. | 0 known repros for `BUG-002` and `BUG-003` after verification. |
| Usability | The fixes preserve the current low-friction quick-add and edit flows. | No extra user steps added to either flow. |
| Maintainability | Each defect is implemented and testable as an independent thin story. | Story-level changes can merge without file conflicts in downstream execution planning. |
| Compatibility | Existing HTMX fragment responses and server-rendered dialog patterns remain intact. | No new JSON endpoints or client-side state stores introduced. |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves the edit dialog with the due date left blank. | The todo due date is cleared and the dialog later reopens with no date selected. |
| User quick-adds a todo and never opens the edit dialog. | The todo still carries the default `low` priority in stored state and rendered output. |
| User edits title or note while also saving a due date. | The due date persists without regressing existing title or note updates. |
| Unsupported or malformed due-date payload reaches the save route. | The app does not silently claim the entered date persisted when it did not. |


## Constraints & Assumptions

### Constraints
- The app uses HTMX plus server-rendered HTML partials; requirements must fit the current request/response interaction model.
- Authentication, session storage, and plain-text password handling are intentional educational simplifications and are not part of this effort.
- Downstream planning must keep `BUG-002` and `BUG-003` as separate thin stories with isolated file ownership so they can merge cleanly.

### Assumptions
- `Low` is the intended default priority for newly created todos, based on existing product documentation and model defaults.
- Users expect calendar-date persistence, not time-of-day editing, from the current due-date dialog control.
- Restoring the intended existing behavior is sufficient; no additional product discovery is needed for these defects.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| `docs/PRODUCT-BACKLOG.md` defect definitions | Provides the canonical scope and severity for `BUG-002` and `BUG-003`. |
| Existing authenticated todo list UI | Both fixes are exercised through this surface and must preserve its interaction model. |
| Downstream `andthen-plan` and story-spec generation | Must translate the PRD into two non-conflicting implementation stories. |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Treat `BUG-002` and `BUG-003` as two Must/P0 defect stories in one PRD. | The user requested one PRD covering both defects while keeping execution independent. | Separate PRDs per defect; rejected because a single paired artifact was explicitly requested. |
| Define the MVP as restoring intended current behavior only. | These are defect fixes with known expected behavior already reflected in backlog and UI defaults. | Expanding into form redesign or configurable defaults; rejected as scope creep. |
| Record merge-isolation as a planning constraint rather than a user-facing feature. | It materially affects downstream execution but is not a product capability users interact with. | Omitting it from the PRD; rejected because the user explicitly required isolated stories. |
