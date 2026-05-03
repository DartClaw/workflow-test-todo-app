# Product Requirements Document: BUG-002 and BUG-003 Todo Metadata Fixes

> **Context**: `docs/PRODUCT-BACKLOG.md` Known Defects `BUG-002` and `BUG-003`
> **Related Assets**: `README.md`, `docs/STATE.md`, `docs/UBIQUITOUS_LANGUAGE.md`


## Executive Summary

- **Problem**: Two metadata defects break trust in basic todo editing. Users can set a due date in the edit dialog and appear to save successfully, but the value disappears when they reopen the dialog. Users can also create a todo through quick add and later find no priority selected in the edit dialog, despite the product documenting priority levels and expecting a default.
- **Vision**: Todo metadata behaves consistently across quick add, edit, save, and reopen flows, so users can rely on due dates and priority without re-entering or correcting missing values.
- **Target Users**: Logged-in todo users who create tasks quickly and later refine them in the edit dialog.
- **Success Metrics**:
  - 100% of todos saved with a due date from the edit dialog show the same date when reopened immediately.
  - 100% of todos created through quick add open in the edit dialog with `low` selected unless the user later changes it.
  - 0 silent-save cases where the UI reports success but due date or priority metadata is missing after save for the covered flows.
  - Both defects can be implemented and verified as two independent stories with no required overlap in touched files.

### Capabilities at a Glance
- **FR1: Persist Edited Due Date** _(Must / P0)_ - A due date saved from the edit dialog remains attached to the todo and is shown again when the dialog is reopened.
- **FR2: Apply Quick-Add Default Priority** _(Must / P0)_ - A todo created through quick add receives the documented default priority so later editing starts from a valid selected value.

### Scope Highlights
- **In scope**: fixing due-date persistence when saving from the edit dialog, assigning a default priority to quick-add todos, preserving existing HTMX server-rendered flows, keeping the fixes separable into two thin stories
- **Out of scope**: redesigning the edit dialog, changing priority options beyond the existing `low`/`medium`/`high` set, changing how due dates are displayed elsewhere in the app, broader date-logic defects such as overdue vs due-today styling
- **MVP boundary**: A user can quick-add a todo, edit it, save a due date, reopen it, and see both due date and priority populated correctly without any other behavior change.

### Key Constraints, Assumptions & Dependencies
- Constraint: The app is HTMX-first and server-rendered, so fixes must preserve existing fragment-based interaction patterns.
- Constraint: Story 1 and Story 2 must remain isolated enough to merge without conflict, which limits shared-file edits in downstream planning.
- Assumption: The intended default priority for newly created todos is `low`, based on existing models, UI defaults, and product language.
- Dependency: Existing authenticated todo create and update flows remain the entry points for both fixes.


## Problem Definition

### Problem Statement
Todo metadata currently behaves inconsistently in two common workflows. In the edit flow, a user can choose a due date and save, yet the value does not persist when the item is reopened. In the quick-add flow, a user can create a todo with only a title, then later discover the todo has no selected priority in the edit dialog. These failures matter because due date and priority are core task-management signals. When they disappear or start blank unexpectedly, users lose confidence that the app saved what they entered and must spend time checking or re-entering metadata.

### Evidence & Context
- `BUG-002` in the backlog explicitly states that due dates set via the edit dialog do not persist and that the current parsing path silently swallows format mismatches.
- `BUG-003` in the backlog explicitly states that quick-add todos have no default priority and that the edit dialog shows an empty selector instead of the documented default.
- The README lists due dates and priority levels as product features, so both defects are regressions against user expectations.
- Both defects sit in routine daily flows: quick capture first, refine later.


## Scope

### In Scope
- Make due dates saved from the todo edit dialog persist across save and reopen.
- Ensure todos created via quick add carry the default priority expected by the product.
- Preserve current user-facing flows for quick add, edit, save, and reopen.
- Define story boundaries so each bug can be implemented and tested independently.

### Out of Scope
- New priority choices, custom defaults, or per-list default priority behavior.
- Changes to list creation, todo search, reorder, completion toggle, or delete behaviors.
- Broader date handling cleanup outside the edit-dialog persistence defect.
- Changes to the intentionally simple authentication model.

### MVP Boundary
The smallest acceptable release fixes the two reported defects only: edited due dates persist, and quick-add todos default to `low` priority, with no unrelated UI or workflow changes.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As a logged-in user editing a todo, I want a saved due date to still be present when I reopen the edit dialog, so that I can trust that my change was stored. | After saving a valid due date from the edit dialog, reopening the same todo shows that same date populated; clearing the date and saving removes it on reopen; invalid input does not create a false-success persistence gap. | Must / P0 |
| US02 | As a logged-in user creating a todo with quick add, I want the todo to start with the default priority, so that later edits begin from a valid, predictable priority state. | A quick-added todo opens in the edit dialog with `low` selected unless the user has since changed the priority; no quick-added todo covered by this flow reopens with an empty priority selector. | Must / P0 |

### Feature Specifications

#### FR1: Persist Edited Due Date
**Description**: When a user saves a todo from the edit dialog with a due date, the todo must retain that date and present it again when the same dialog is reopened later.

**Acceptance Criteria**:
- [ ] Saving a valid due date from the edit dialog stores the date on the todo and shows the same value when the dialog is reopened.
- [ ] Saving other editable fields alongside a due date does not cause the due date to be dropped.
- [ ] Clearing the due date intentionally removes it, and reopening the dialog shows an empty due-date field.
- [ ] The save flow must not silently report success while discarding a user-entered due date.

**Inputs / Outputs**:
- **Inputs**: Existing todo selected for edit, user-entered due date from the edit dialog, optional title and note edits in the same save action.
- **Outputs**: Updated todo metadata, reopened edit dialog with persisted due-date value, or a visible failure response when the submitted due-date value cannot be accepted.

**Validation**:
- Accept the due-date format produced by the existing edit dialog control.
- Treat an empty due-date submission as an intentional clear.
- Reject or surface invalid due-date input instead of silently discarding it.

**Error Handling**:
- If the todo does not exist or is not owned by the current user, return the existing authorization or not-found behavior.
- If the due-date submission is invalid, the user must receive a visible error response rather than an apparently successful save that loses data.

**Priority**: Must / P0

#### FR2: Apply Quick-Add Default Priority
**Description**: When a user creates a todo through quick add, the new todo must start with the product's default priority so the edit dialog and rendered item always reflect a valid priority state.

**Acceptance Criteria**:
- [ ] A todo created through quick add is assigned the default priority immediately on creation.
- [ ] Reopening that todo in the edit dialog shows `low` selected unless the user later saved a different priority.
- [ ] The rendered todo item continues to display priority styling and labels consistent with the assigned default.
- [ ] This behavior change applies only to quick-add creation and does not alter explicit priority choices made in the edit flow.

**Inputs / Outputs**:
- **Inputs**: Quick-add todo creation with title and list context only.
- **Outputs**: Newly created todo with valid default priority metadata, consistent edit-dialog selection state, and rendered priority display.

**Validation**:
- The default priority must be one of the existing valid values: `low`, `medium`, or `high`.
- For this release, the default value is `low`.

**Error Handling**:
- Existing title validation and authorization behavior remain unchanged.
- If todo creation fails for existing reasons, no partially created todo with missing priority metadata should appear in the UI.

**Priority**: Must / P0

### User Flows
1. User opens an existing todo, sets or updates the due date in the edit dialog, saves, then reopens the same todo and sees the saved date still populated.
2. User clears an existing due date in the edit dialog, saves, then reopens the todo and sees the due-date field empty.
3. User quick-adds a new todo with only a title, then opens the edit dialog and sees `low` already selected as the priority.
4. User quick-adds a new todo, later changes priority in the edit dialog, saves, and sees that explicit choice preserved on reopen.
5. User submits an invalid due-date value through the covered save path and receives a visible failure instead of a silent metadata drop.

### Data Requirements _(if applicable)_
- Todo records must continue to support an optional due date.
- Todo records must continue to support exactly one priority value from the existing set: `low`, `medium`, `high`.
- Newly quick-added todos must never persist with a missing or empty priority value.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Performance | Saving todo edits and quick-add creation should preserve current responsiveness | No perceptible regression from current fragment-update interactions |
| Reliability | Covered metadata fields must persist consistently across save and reopen | 100% pass rate for automated regression checks covering both defect flows |
| Usability | Users must receive clear feedback when a due-date submission cannot be saved | No silent failure in the covered due-date edit path |
| Compatibility | Existing HTMX partial update flows must continue to work without full-page redirects or new JSON APIs | 100% of covered flows remain fragment-based and server-rendered |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User clears a previously saved due date | Save succeeds and reopening the dialog shows no due date |
| User edits title and due date together | Both valid changes persist in the same save |
| User submits a malformed due-date value through the edit save path | User sees a visible error and the app does not imply the date was saved |
| User quick-adds a todo and never opens the edit dialog | Todo still carries the default priority for rendering and future edits |
| User later changes a quick-added todo's priority | The user's explicit selection overrides the default and persists normally |


## Constraints & Assumptions

### Constraints
- The application is server-rendered with HTMX partial responses; this effort must fit that interaction model.
- The defects must be planned as two independent, thin stories that can merge without conflict.
- The release should make surgical changes only and avoid adjacent feature work.

### Assumptions
- `low` is the canonical default priority for new todos.
- Users interact with due dates through the existing date-only control shown in the edit dialog.
- Visible error feedback for invalid due-date submission can reuse established HTML error response patterns.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| Existing authenticated todo create flow | Story 2 depends on the current quick-add create path remaining the source of new todos |
| Existing authenticated todo update flow | Story 1 depends on the current edit-save path remaining the source of due-date updates |
| Existing todo edit dialog | Both stories rely on reopening the current dialog as the primary user verification point |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Keep BUG-002 and BUG-003 in one PRD but as two separate stories and FRs | The user requested one PRD artifact while requiring independent, thin downstream implementation slices | Separate PRDs per bug, or one combined story that would blur ownership and merge boundaries |
| Treat both fixes as Must / P0 within this artifact | Both defects affect basic correctness in core todo flows, and BUG-002 is already marked High severity | Lower BUG-003 to P1 because its backlog severity is Medium |
| Define visible failure for invalid due-date submission | The backlog explicitly calls out silent swallowing as part of the defect, so preserving silent success is unacceptable | Preserve current silent behavior and only fix persistence for valid values |
| Freeze default priority at `low` for this scope | Existing UI defaults, models, and expected product language point to `low`, and introducing configurability would expand scope | Make default configurable, derive per list, or leave unspecified |
