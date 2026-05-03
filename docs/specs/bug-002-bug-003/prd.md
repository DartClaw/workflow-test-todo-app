# Product Requirements Document: BUG-002 and BUG-003 Defect Fixes

> **Context**: `docs/PRODUCT-BACKLOG.md` Known Defects (`BUG-002`, `BUG-003`), `docs/ROADMAP.md` Phase 2: Defect triage
> **Related Assets**: `README.md`, `docs/STATE.md`


## Executive Summary

- **Problem**: Two core todo-editing behaviors are broken in the authenticated todo workflow. Due dates entered in the edit dialog disappear after save and reopen, which makes date-based planning unreliable. Todos created through quick-add also lack the documented default priority, leaving newly created items in an incomplete metadata state.
- **Vision**: Users can trust that lightweight todo entry and later editing preserve the same expected task metadata every time, without needing workaround edits or manual correction.
- **Target Users**: Authenticated todo-app users who create todos quickly and later manage them through the edit dialog.
- **Success Metrics**:
  - 100% of edited todos retain a saved due date when the todo row re-renders and when the edit dialog is reopened.
  - 100% of quick-add todos open in the edit dialog with `Low` already selected unless the user later changes it.
  - Both fixes ship as independent thin stories with no required overlap in planned file ownership.
  - Existing authenticated todo create and edit flows remain green in automated tests after each fix.

### Capabilities at a Glance
- **FR1: Persist Edited Due Dates** _(Must / P0)_ – Saving a due date from the existing edit dialog must preserve that value across render, reopen, and later edits.
- **FR2: Apply Quick-Add Default Priority** _(Must / P0)_ – Todos created through quick-add must immediately carry the documented default priority state used elsewhere in the product.

### Scope Highlights
- **In scope**: due-date persistence in the existing todo edit workflow, default-priority behavior for quick-add todo creation, regression coverage for both flows
- **Out of scope**: new date/time UX, new priority options, backlog items beyond `BUG-002` and `BUG-003`
- **MVP boundary**: fix only the broken persistence and defaulting behaviors while preserving the existing authenticated todo UX and route structure

### Key Constraints, Assumptions & Dependencies
- **Constraint**: This project remains HTMX-first and keeps current authenticated todo flows and existing UI controls rather than redesigning them.
- **Constraint**: The two backlog defects must be planned as separate thin stories that can merge without conflict, with isolated file ownership where practical.
- **Assumption**: The intended default priority is `low`, because the edit dialog already presents `Low` as the default selection and the backlog describes the current empty state as defective.
- **Dependency**: Downstream planning and implementation depend on the existing todo create/edit behavior in `src/app/routes/todos.py`, the edit dialog in `src/app/templates/app.html`, and current todo rendering patterns.


## Problem Definition

### Problem Statement
Authenticated users rely on the edit dialog and quick-add flow to manage task metadata with minimal friction. Today, the due date field appears editable but does not reliably persist after save, so users cannot trust date-based organization. Separately, quick-add creates todos without the documented default priority, so newly created tasks enter the system with inconsistent metadata that becomes visible as soon as the edit dialog is opened. If these defects remain, the product continues to undermine confidence in core task-management behaviors during the roadmap's defect-triage phase.

### Evidence & Context
- `BUG-002` in `docs/PRODUCT-BACKLOG.md` states that due dates saved from the edit dialog disappear when the dialog is reopened.
- `BUG-003` in `docs/PRODUCT-BACKLOG.md` states that quick-add todos show an empty priority selector instead of the documented default.
- The roadmap marks defect triage as the active phase, with success criteria tied to resolving known defects without regressions.
- The current app presents due dates and priorities as first-class todo attributes in user-facing product documentation.


## Scope

### In Scope
- Restoring reliable persistence of due dates set through the existing todo edit dialog.
- Ensuring todos created through quick-add immediately receive the documented default priority.
- Adding regression coverage for the two defect scenarios so future changes do not silently reintroduce them.
- Defining the work as two independent stories for downstream planning and execution.

### Out of Scope
- Redesigning the edit dialog, quick-add interaction, or broader todo metadata UX.
- Changing the allowed priority set (`low`, `medium`, `high`).
- Fixing unrelated defects such as overdue styling or incomplete-count OOB swap behavior.
- Converting the app away from server-rendered HTML partial responses.

### MVP Boundary
The smallest acceptable release resolves `BUG-002` and `BUG-003` in the existing authenticated todo flow, proves the expected behavior through regression tests, and keeps the two fixes independently deliverable.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As an authenticated user, I want a due date saved from the todo edit dialog to still be present later, so that I can trust date-based planning. | After saving a valid due date in the existing edit dialog, the todo row displays the saved date and reopening the dialog shows the same date value. | Must / P0 |
| US02 | As an authenticated user, I want quick-add todos to start with the documented default priority, so that newly created tasks are immediately in a valid and predictable state. | After creating a todo through quick-add, reopening it in the edit dialog shows `Low` selected unless the user has explicitly changed the priority later. | Must / P0 |

### Feature Specifications

#### FR1: Persist Edited Due Dates
**Description**: The product must preserve a due date entered through the existing todo edit dialog when the user saves changes to a todo.

**Acceptance Criteria**:
- [ ] When a user saves a valid due date from the existing edit dialog, the todo row re-renders with that due date visible.
- [ ] When the same todo is reopened in the edit dialog after save, the due date control shows the previously saved value.
- [ ] Editing a todo without changing its already saved due date does not clear that due date.
- [ ] Saving a blank due date intentionally clears the due date.

**Inputs / Outputs**:
- **Inputs**: authenticated user, existing todo, due date value supplied from the current edit dialog, optional blank due date to clear
- **Outputs**: updated todo record, re-rendered todo row, reopened edit dialog state that reflects the saved due date

**Validation**:
- The system accepts only due-date values supported by the current edit control.
- Blank due date input is treated as an intentional clear action.
- Invalid due-date input must not produce a silent success that leaves the user believing a new value was saved when it was not.

**Error Handling**:
- If the submitted due-date value is invalid for the current control, the response must preserve user trust by not reporting a successful save of a value that was not actually stored.
- Existing auth and ownership protections remain unchanged for todo updates.

**Priority**: Must / P0

#### FR2: Apply Quick-Add Default Priority
**Description**: The product must assign the documented default priority to todos created through the quick-add flow so that new todos begin in a predictable valid state.

**Acceptance Criteria**:
- [ ] When a user creates a todo through quick-add with title only, the created todo is stored with the default priority.
- [ ] Opening that todo in the existing edit dialog shows `Low` selected immediately after creation.
- [ ] The rendered todo row displays the default priority consistently with other todos using the same priority value.
- [ ] Users can still change the priority later through the existing edit dialog.

**Inputs / Outputs**:
- **Inputs**: authenticated user, target list, quick-add title
- **Outputs**: newly created todo record with default priority, rendered todo row, reopened edit dialog state with default priority selected

**Validation**:
- The quick-add flow continues to require a non-empty title and honor existing title limits.
- The default priority value must match the documented product default already communicated in the UI.

**Error Handling**:
- Existing quick-add validation errors for missing or oversized titles remain unchanged.
- Failure to create the todo must continue to return the existing HTML error handling pattern.

**Priority**: Must / P0

### User Flows
1. User opens an existing todo, sets a due date in the current edit dialog, saves, and later reopens the todo to find the same due date preserved.
2. User creates a todo through quick-add, sees the todo appear in the list, and later opens the edit dialog to confirm `Low` is already selected.
3. User clears a previously saved due date and saves, after which the todo no longer displays a due date and the dialog reopens with the date field blank.

### Data Requirements
- Todo records must continue to support `due_date` as an optional value.
- Todo records must store a valid priority value on creation through quick-add.
- Rendered todo metadata must remain consistent between stored values and edit-dialog values.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Reliability | Saved due dates and default priorities remain consistent across create, save, render, and reopen flows. | 100% pass rate for automated regression coverage of the two defect scenarios |
| Usability | The existing edit and quick-add flows remain understandable without new user training or new steps. | No additional required fields or interaction steps added to either flow |
| Compatibility | Fixes preserve the current server-rendered HTMX partial workflow. | No new JSON-first flow introduced for these defects |
| Delivery | The two fixes remain independently deliverable. | Planning assigns each story a separate thin scope with merge-safe file ownership |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves a todo with a valid due date, then reopens it later. | The previously saved due date is still present in the edit dialog and rendered todo row. |
| User saves a todo with the due date field blank. | Any existing due date is cleared intentionally. |
| User submits a due-date value that the current control does not support. | The system does not silently imply success for a value that was not persisted. |
| User creates a todo through quick-add and immediately edits it. | The edit dialog shows `Low` selected by default. |
| User later changes the priority of a quick-add todo. | The new explicit user-selected priority replaces the default and persists normally. |


## Constraints & Assumptions

### Constraints
- The fixes must preserve the current authenticated todo flows, route structure, and server-rendered HTML partial behavior.
- The work covers only `BUG-002` and `BUG-003` and must not absorb unrelated backlog defects.
- Downstream planning must keep the two stories thin and independent, with isolated file ownership wherever possible so they can merge without conflict.

### Assumptions
- `Low` is the canonical default priority for new todos created without explicit priority input.
- Users expect the due date field in the current edit dialog to persist exactly the value they selected unless they intentionally clear it.
- Existing auth, ownership, and title validation behaviors are already correct for these two defect flows and do not need product changes in this effort.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| `docs/PRODUCT-BACKLOG.md` | Defines the accepted defect scope and severity for `BUG-002` and `BUG-003`. |
| Existing authenticated todo create/edit workflows | These defects occur inside the current product flow and must be fixed without changing its overall interaction model. |
| Downstream planning artifacts in `docs/specs/bug-002-bug-003/` | The PRD must provide enough separation and clarity for a later plan to produce two non-conflicting thin stories. |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Keep `BUG-002` and `BUG-003` as two independent stories in one PRD. | The user explicitly requested two thin, isolated stories while both defects belong to the same defect-triage slice. | Separate PRDs per bug; single combined story |
| Treat `Low` as the required quick-add default priority. | The backlog calls the empty selector defective, and the existing edit dialog already communicates `Low` as the default state. | Leave priority unset; infer a different default later |
| Limit scope to behavioral fixes and regression coverage. | The defects are specific workflow regressions during an active defect-triage phase, and broader UX or data-model changes would expand scope unnecessarily. | Redesign the edit UX; add broader metadata management changes |
