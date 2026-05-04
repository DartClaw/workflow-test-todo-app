# Product Requirements Document: Todo App – BUG-002 and BUG-003 Defect Fixes

> **Context**: `docs/PRODUCT-BACKLOG.md` Known Defects entries `BUG-002` and `BUG-003`; `docs/ROADMAP.md` Phase 2: Defect triage
> **Related Assets**: `README.md`, `docs/STATE.md`


## Executive Summary

- **Problem**: Two core todo-editing behaviors are inconsistent with the product contract. Edited due dates do not persist after save, which makes due-date management unreliable. Todos created from quick add lack the documented default priority, which leaves follow-up editing in an ambiguous state.
- **Vision**: Users can trust lightweight todo creation and later editing to preserve expected metadata without surprise resets or missing defaults.
- **Target Users**: Authenticated Todo App users who create todos from a list view and later manage details from the edit dialog.
- **Success Metrics**:
  - 100% of valid due dates saved from the edit dialog reappear when the same todo is reopened for editing.
  - 100% of todos created through quick add are assigned the default priority immediately at creation.
  - 0 silent save failures for invalid due-date input; the user receives a visible error state instead.
  - Existing authenticated todo create and update flows remain green in the automated test suite.

### Capabilities at a Glance
- **FR1: Persist Edited Due Dates** _(Must / P0)_ – Saving a valid due date from the edit dialog must update the todo and repopulate that same date on later reopen.
- **FR2: Apply Default Priority on Quick Add** _(Must / P0)_ – Creating a todo through quick add must assign the documented default priority so downstream UI always shows a valid value.

### Scope Highlights
- **In scope**: restoring due-date persistence in the edit flow, applying a default priority in the quick-add flow, visible handling for invalid due-date submissions, regression protection for both defects.
- **Out of scope**: redesigning the edit dialog, changing the documented default priority value, adding new priority levels, broader due-date timezone behavior changes.
- **MVP boundary**: a release is complete when each defect is fixed independently, each flow behaves consistently in the UI, and each story can be implemented and merged without conflict.

### Key Constraints, Assumptions & Dependencies
- *Constraint:* This work is limited to two independent, thin defect-fix stories mapped to `BUG-002` and `BUG-003`.
- *Constraint:* The app remains HTMX-first and must preserve existing HTML-fragment response behavior for create and update flows.
- *Assumption:* The documented default priority remains `low`, matching current product copy and existing test expectations.
- *Dependency:* Final acceptance depends on automated tests covering both flows and confirming no regression in existing todo create/update behavior.


## Problem Definition

### Problem Statement
Users cannot rely on todo metadata to remain stable across quick creation and later editing. When a due date is set in the edit dialog and appears to save successfully, reopening the same todo shows an empty date field instead of the stored value. Separately, quick-added todos are created without the documented default priority, so the edit dialog later shows an empty selector. Both defects undermine trust in lightweight list management because the UI implies valid metadata support while failing to preserve or initialize it consistently.

### Evidence & Context
- `BUG-002` in `docs/PRODUCT-BACKLOG.md` is marked High severity because due-date edits appear to save but do not persist in the edit experience.
- `BUG-003` in `docs/PRODUCT-BACKLOG.md` is marked Medium severity because quick add skips the documented default priority, producing inconsistent downstream UI state.
- The roadmap marks defect triage as the active phase and requires fixes to preserve the green test suite and avoid regressions.


## Scope

### In Scope
- Fixing the user-visible persistence contract for due dates edited through the todo edit dialog.
- Ensuring quick-add todo creation assigns the documented default priority at the moment of creation.
- Returning a visible error outcome when due-date input cannot be accepted instead of silently ignoring it.
- Verifying each defect as its own independently shippable story.

### Out of Scope
- Reworking the todo data model beyond what is required to satisfy the two defects.
- Changing how priorities are presented or introducing configurable defaults.
- Expanding quick add to capture more fields than title.
- Addressing unrelated known defects such as sidebar count refresh or overdue styling.

### MVP Boundary
The smallest acceptable release fixes `BUG-002` and `BUG-003` as separate stories, restores consistent user-visible metadata behavior for both flows, and adds regression coverage that allows each story to merge independently.


## Functional Requirements

### User Stories

| ID | Story | Acceptance Criteria | Priority |
|----|-------|---------------------|----------|
| US01 | As a user editing a todo, I want a due date I save to still be present when I reopen the edit dialog so that I can trust the app to retain scheduling details. | A valid saved due date is shown again on later reopen; invalid due-date input never fails silently. | Must / P0 |
| US02 | As a user creating a todo from quick add, I want the todo to start with the documented default priority so that later editing and list display always begin from a valid baseline. | A quick-added todo is created with priority `low`, and later editing shows that same default unless the user changes it. | Must / P0 |

### Feature Specifications

#### FR1: Persist Edited Due Dates
**Description**: The todo edit flow must preserve a valid due date entered by the user and reflect the saved value consistently anywhere the existing UI exposes that field.

**Acceptance Criteria**:
- [ ] When a user saves a valid due date from the edit dialog, the todo record retains that date after save.
- [ ] When the same todo is reopened in the edit dialog, the due-date field is prefilled with the saved date.
- [ ] When the due date is intentionally cleared and saved, reopening the dialog shows the field empty.
- [ ] When the submitted due-date value is invalid or unsupported, the system does not silently ignore the problem; it returns a visible error response and leaves the previous saved value unchanged.

**Inputs / Outputs**:
- **Inputs**: Todo title, optional note, optional due-date value submitted from the edit dialog.
- **Outputs**: Updated todo row state, reopened edit dialog state that matches the saved record, visible error partial for invalid submissions.

**Validation**:
- Due-date input must either be empty or match the date format accepted by the edit dialog.
- Title validation rules remain unchanged and continue to apply during update.

**Error Handling**:
- Invalid due-date submissions must surface a visible error state rather than appearing successful.
- On invalid due-date submission, the system must not replace a previously saved valid due date with an unintended value.

**Priority**: Must / P0

#### FR2: Apply Default Priority on Quick Add
**Description**: The quick-add create flow must assign the documented default priority automatically so every newly created todo begins with a valid priority state.

**Acceptance Criteria**:
- [ ] When a user creates a todo through quick add with only a title, the todo is stored with priority `low`.
- [ ] The newly rendered todo row shows the default priority state immediately after creation.
- [ ] When the same quick-added todo is opened in the edit dialog, the priority selector is prefilled with `low`.
- [ ] Existing non-quick-add update behavior continues to allow the user to change the priority later.

**Inputs / Outputs**:
- **Inputs**: List identifier and todo title submitted from quick add.
- **Outputs**: Created todo row with a valid default priority, consistent edit dialog state on later reopen.

**Validation**:
- Quick add must continue to require a non-empty title within the existing title length limit.
- The default priority value must be one of the app's supported priority options.

**Error Handling**:
- If the system cannot assign a valid default priority, it must not create a partially initialized todo silently.
- Any create failure must continue to return a visible HTML error response consistent with current app patterns.

**Priority**: Must / P0

### User Flows
1. User opens an existing todo, sets or clears a due date, saves, and later reopens the todo to confirm the edit dialog matches the saved state.
2. User creates a todo from quick add, sees the new row appended to the list, and later opens the edit dialog to confirm the default priority is already selected.
3. User submits an invalid due-date value during edit, receives a visible error outcome, and the previously saved due date remains unchanged.

### UI Wireframes _(if applicable)_
- No new wireframes required. Existing list view and edit dialog remain the reference UI.

### Data Requirements _(if applicable)_
- Todo items must continue to support an optional due date.
- Todo items must always have a valid priority value from the supported set `low`, `medium`, `high`.
- Newly created quick-add todos must satisfy the same data completeness expectations as todos later shown in the edit dialog.


## Non-Functional Requirements

| Category | Requirement | Threshold / Target |
|----------|-------------|--------------------|
| Reliability | Todo metadata changes must round-trip consistently between save and reopen. | 100% pass rate for automated regression coverage of the two defect flows |
| Usability | Users must receive explicit feedback when a due-date submission cannot be accepted. | No silent due-date save failures in the covered edit flow |
| Compatibility | Defect fixes must preserve current HTMX fragment-based interaction patterns. | No change to full-page navigation requirements for create or update |
| Maintainability | Each defect fix must remain independently deliverable. | Story implementations avoid cross-story merge conflicts |


## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves a todo edit with an empty due-date field | The due date is cleared and later reopen shows the field empty |
| User submits a malformed due-date value | The update is rejected visibly and the prior saved due date remains intact |
| User quick-adds a todo and opens it immediately for edit | The priority selector shows `low` without requiring any manual correction |
| User edits the priority later on a quick-added todo | The later explicit user choice overrides the initial default normally |


## Constraints & Assumptions

### Constraints
- Delivery is limited to two thin stories: `BUG-002` and `BUG-003`.
- The stories must remain isolated enough to merge without conflict.
- Existing HTML-partial, HTMX-first interaction patterns must remain intact.
- The intentionally simple authentication and broader educational architecture are unchanged by this effort.

### Assumptions
- The product's canonical default priority is `low`.
- The edit dialog's due-date input is the canonical UI for managing due dates in this scope.
- Users interpret a successful save as confirmation that metadata has been stored exactly as shown.

### Dependencies

| Dependency | Why It Matters |
|------------|----------------|
| `docs/PRODUCT-BACKLOG.md` defect definitions | Defines the canonical user-facing scope and severity for `BUG-002` and `BUG-003` |
| Existing todo create and update test suite | Provides the baseline regression signal required by the roadmap |
| Existing list view and edit dialog UI | Serves as the current product contract that the fixes must make consistent |


## Decisions Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|-------------------------|
| Treat the work as two separate stories in one PRD | Matches the user's request for thin, independent fixes while keeping one planning artifact for the pair | Separate PRDs per bug, rejected as unnecessary overhead for tightly related defect triage |
| Require visible failure for invalid due-date input | The backlog explicitly calls out silent mismatch handling as part of the defect, so the product contract must reject silent failure | Preserve silent fallback behavior, rejected because it leaves the user without a trustworthy save result |
| Keep the default priority fixed at `low` | Matches existing documentation and current test expectations, and resolves ambiguity around quick-add initialization | Introducing configurable or context-sensitive defaults, rejected as out of scope |
