# Product Requirements Document: BUG-002 and BUG-003 Todo Defect Fixes

> **Context**: `docs/PRODUCT-BACKLOG.md` (`BUG-002`, `BUG-003`), `docs/ROADMAP.md` (Phase 2: Defect triage), `docs/STATE.md`
> **Related Assets**: `README.md`, `src/app/routes/todos.py`, `src/app/templates/app.html`, `src/app/templates/partials/todo_list_content.html`, `tests/test_todos.py`


## Executive Summary

- **Problem**: Two core todo-authoring flows behave inconsistently with the product’s documented model. Edited due dates can disappear after save, and quick-added todos can be created without the default priority the app already presents elsewhere. This makes todo details unreliable and undermines confidence in the edit dialog.
- **Vision**: Todo metadata entered or implied by the UI should persist predictably, so users can trust both the quick-add flow and the edit dialog without reopening items to verify what was saved.
- **Target Users**: Authenticated todo users managing lists through the main app UI, especially users who rely on due dates and priority badges to organize work quickly.
- **Success Metrics**:
  - 100% of saved valid due dates remain visible when the same todo is reopened in the edit dialog.
  - 100% of quick-added todos are stored with the documented default priority and render with a selected priority in the edit dialog.
  - Both defects are covered by automated route-level tests that fail before the fix and pass after it.
  - The existing todo CRUD test suite remains green after both stories land.

### Capabilities at a Glance
- **FR1: Persist Edited Due Dates** _(Must / P0)_ – Saving a valid due date from the edit dialog must store it and repopulate the same date when the dialog is reopened.
- **FR2: Apply Default Priority on Quick Add** _(Must / P0)_ – Creating a todo through quick add must assign the standard default priority immediately, even when the user only supplies a title.

### Scope Highlights
- **In scope**: fix due-date persistence for edit flow, apply default priority in quick-add creation flow, add regression coverage for both defects, preserve story isolation so each fix can land independently.
- **Out of scope**: redesigning the edit dialog, changing priority options, adding time-of-day support, refactoring unrelated todo CRUD behavior, changing auth or session behavior.
- **MVP boundary**: the release is complete when a user can quick-add a todo and edit a due date using today’s UI, then reopen the item and see both fields persisted exactly as expected.

### Key Constraints, Assumptions & Dependencies
- **Constraint:** The app is HTMX-first and server-rendered; the fix must preserve current fragment-based flows rather than introduce JSON APIs or a new client-side state model.
- **Constraint:** BUG-002 and BUG-003 must remain two independent, thin stories whose code changes can merge without conflict.
- **Assumption:** The documented default priority is `low`, because the edit dialog defaults to `low` and existing route tests already expect new todos to have `low`.
- **Dependency:** Existing route and UI patterns in `src/app/routes/todos.py`, `src/app/templates/app.html`, and `tests/test_todos.py` remain the canonical source for acceptance behavior.


## Problem Definition

### Problem Statement
Users can currently enter or infer todo metadata that the system does not reliably retain. In the edit flow, a user can choose a due date, save, and later discover the field empty when reopening the dialog. In the quick-add flow, a user can create a todo from the lightweight composer and later find the priority selector unset, even though the product documents and presents a default priority. If left unresolved, users cannot trust the app’s lightweight authoring flows for basic planning data.

### Evidence & Context
- `BUG-002` in the backlog identifies that edit-dialog due dates do not persist and notes that the parsing path silently swallows format mismatches.
- `BUG-003` in the backlog identifies that quick-add todos have no default priority and that reopening the edit dialog reveals an empty selector.
- The README and current UI position due dates and priority as supported todo fields, so missing persistence is a product regression, not a new feature request.
- Phase 2 of the roadmap is active defect triage, so these fixes should be scoped as stabilization work rather than broader UX redesign.


## Scope

### In Scope
- Ensure a valid due date submitted from the existing edit dialog is saved in the todo record and shown again when the dialog is reopened.
- Ensure a todo created from the existing quick-add form receives the standard default priority without requiring extra user input.
- Define acceptance conditions and regression tests for each bug independently.
- Preserve existing user-visible flows, response shapes, and HTMX fragment behavior outside the defect area.

### Out of Scope
- Adding or changing fields on todos beyond due date persistence and default priority assignment.
- Introducing advanced date parsing, time selection, timezone normalization, or calendar UX changes.
- Changing the priority taxonomy (`low`, `medium`, `high`) or adding user-configurable defaults.
- Bundling these fixes into a broad refactor of todo routes, templates, or JavaScript.

### MVP Boundary
The smallest acceptable release fixes both reported defects in place: edited due dates persist through save and reopen, and quick-added todos always carry the default priority that the UI and tests already assume.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As a user editing a todo, I want a due date I save to still be present when I reopen the edit dialog, so that I can trust the app to retain my scheduling changes. | Saving a valid date through the edit dialog stores it on the todo and the same date is shown when the item is rendered and reopened. | Must / P0 |
| US02 | As a user adding a todo quickly, I want the app to assign the standard default priority automatically, so that lightweight entry still produces a complete todo state. | A quick-added todo is stored with default priority `low` and the edit dialog shows `low` as selected until the user changes it. | Must / P0 |

### Feature Specifications

#### FR1: Persist Edited Due Dates
**Description**: The existing todo edit flow must accept the date value emitted by the current due-date input and persist that value on save without silent loss.

**Acceptance Criteria**:
- [ ] When a user saves a valid due date from the edit dialog, the todo record stores a due date value.
- [ ] After saving, the todo row renders the saved due date in its normal display region.
- [ ] When the user reopens the edit dialog for that same todo, the due-date input is prefilled with the saved value.
- [ ] If the user clears the due-date input and saves, the todo no longer has a due date.
- [ ] If the submitted due-date value is invalid for the supported input format, the system must not silently convert it into a different date.

**Inputs / Outputs**:
- **Inputs**: existing edit dialog submission, todo title, optional note, optional due-date field value, existing todo identifier.
- **Outputs**: updated todo record, updated todo-row partial, reopened dialog state showing the saved date when rendered from the stored record.

**Validation**:
- Accept the date format produced by the current edit-dialog control.
- Continue requiring a non-empty title and valid priority values.
- Clearing the date field is a valid action and removes the due date.

**Error Handling**:
- Invalid due-date submissions must not create a misleading persisted value.
- Existing authorization and not-found behaviors for todo updates remain unchanged.
- The route should continue to return the standard HTML error partial for validation failures already handled by the flow.

**Priority**: Must / P0

#### FR2: Apply Default Priority on Quick Add
**Description**: The quick-add todo flow must create todos with the same default priority the product already presents in the full edit experience.

**Acceptance Criteria**:
- [ ] When a user creates a todo through quick add with only a title, the stored todo priority is `low`.
- [ ] The newly rendered todo row exposes priority data consistent with a `low` priority todo.
- [ ] When the user opens the edit dialog for a quick-added todo, the priority selector shows `low` selected.
- [ ] Existing quick-add behavior for title validation, list ownership, insertion order, and OOB count updates remains unchanged.

**Inputs / Outputs**:
- **Inputs**: quick-add form submission with list identifier and title.
- **Outputs**: created todo record with default priority, rendered todo-row fragment, unchanged list-count OOB swap behavior.

**Validation**:
- The default applies when no explicit priority is collected by quick add.
- Existing title validation rules continue to apply.

**Error Handling**:
- If quick-add validation fails, the route continues returning the standard HTML error partial.
- Default-priority assignment must not interfere with existing authorization or list-not-found responses.

**Priority**: Must / P0

### User Flows
1. User opens an existing todo in the edit dialog, selects a due date, saves, and later reopens the dialog to confirm the same date is still present.
2. User creates a todo from quick add, sees the item appended to the list, then opens edit and sees `low` already selected as the priority.
3. User clears an existing due date and saves; reopening the dialog shows the field empty and the todo no longer displays a due date badge/text.
4. User submits invalid quick-add or edit data already covered by existing validations; the flow still returns the standard HTML error partial without changing unrelated behavior.

### UI Wireframes _(if applicable)_
- No new wireframes. This effort preserves the current quick-add form and edit dialog layout.

### Data Requirements _(if applicable)_
- `Todo.due_date` remains the persisted field for saved due dates.
- `Todo.priority` remains the persisted field for priority and must contain one of the existing values: `low`, `medium`, `high`.
- Quick-add-created todos must leave persistence in the same shape as todos created or edited through the fuller todo flow.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Reliability | Saving valid due dates and quick-added priorities must be deterministic across repeated create/edit/reopen cycles. | 0 known repros for BUG-002 and BUG-003 after fix verification |
| Compatibility | The fixes must preserve existing HTMX partial rendering and OOB swap behavior in the todo list experience. | No change to fragment contract outside the defect scope |
| Testability | Each defect must be protected by automated tests that exercise the current route layer. | At least 1 regression test per bug, suite green |
| Maintainability | The two fixes must be isolated enough to land as separate thin stories without merge conflicts. | Story-specific changes remain in separate files or non-overlapping hunks |
| Usability | Users should not need to perform extra fields or confirmation steps to get correct saved state. | Existing one-submit flows remain unchanged |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves a todo edit with a blank due-date field. | The due date is removed and reopening the dialog shows the field empty. |
| User quick-adds multiple todos in succession. | Every created todo receives default priority `low`; count updates and ordering remain unchanged. |
| User reopens a quick-added todo before making any manual edits. | The edit dialog shows `low` as the selected priority. |
| User submits malformed due-date input outside the supported control format. | The system does not persist an incorrect date and does not silently transform the value into another date. |
| Existing todo already has `medium` or `high` priority. | Editing other fields does not reset priority to `low`. |


## Constraints & Assumptions

### Constraints
- The project is an educational FastAPI + HTMX app that returns HTML fragments, not JSON, for todo interactions.
- The existing edit dialog currently uses a date-only control; the requirement is to make persistence work with that current control, not to expand the control’s capabilities.
- BUG-002 and BUG-003 must be executable as two independent, thin stories and must merge without conflict.
- Validation remains primarily route-level and ad hoc in existing handlers; this effort should not require a broad validation architecture change.

### Assumptions
- The correct default priority for new todos is `low`.
- Persisting the calendar date the user selected is sufficient; preserving a time-of-day component is not part of this defect fix.
- Existing automated route tests are the primary regression safety net for these fixes.
- Users expect quick-add and edit flows to produce the same persisted todo shape for shared fields.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| `docs/PRODUCT-BACKLOG.md` bug definitions | Defines the defect scope and expected user-visible outcome for BUG-002 and BUG-003. |
| Existing todo routes and templates | The PRD assumes current quick-add and edit-dialog flows remain in place and are corrected in situ. |
| Automated test suite in `tests/test_todos.py` | Provides the regression boundary needed to prove both defects are fixed without broader regressions. |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Treat BUG-002 and BUG-003 as one PRD with two thin stories. | The user asked for one PRD draft but explicitly wants two independent implementation stories. | Separate PRDs per bug; rejected because the requested workflow step is a single PRD draft. |
| Anchor the default priority requirement to `low`. | The current edit dialog defaults to `low`, and existing tests already assert that new todos should default to `low`. | Leaving the default unspecified; rejected because it would keep the defect ambiguous. |
| Keep the scope at defect correction, not UX redesign. | The roadmap phase is defect triage, and both backlog items describe regressions in existing flows. | Expand into broader date/priority UX improvements; rejected as scope creep. |
| Make story isolation an explicit requirement. | The user requires both stories to merge without conflict, so separation must be part of the product contract for downstream planning. | Treat isolation as an implementation note only; rejected because it materially shapes planning and file ownership. |
