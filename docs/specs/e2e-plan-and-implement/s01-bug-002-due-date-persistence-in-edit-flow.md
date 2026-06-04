# BUG-002 due date persistence in edit flow

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S01`

## Feature Overview and Goal

**Intent**: Restore the edit-dialog Due Date flow so a saved todo date survives the server round-trip and is still present when the same Todo is rendered and reopened later.

**Expected Outcomes**

- [OC01] Saving a Todo from the existing edit dialog with a valid `YYYY-MM-DD` Due Date persists that date in storage and shows it back in the rendered row.
- [OC02] Reopening the edit dialog after a successful save pre-fills the same Due Date value from the rendered Todo fragment.
- [OC03] Optional Due Date behavior remains intentional: an empty date clears the stored value, while malformed non-dialog input does not silently replace an existing stored date.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches.

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S01 scope"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#"stories.S01.scope" -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> Restore due-date persistence for todos edited through the existing dialog so a saved date remains stored, rendered back into the todo row, and available when the dialog is reopened. Includes the edit submission path and rendered todo fragment for that path; excludes due-date styling corrections and any changes to quick-add or priority behavior.

## Deeper Context

- `CLAUDE.md#architecture` – HTMX routes return HTML partials, the server is the source of truth for UI state, and the edit flow should stay inside the existing fragment-swap contract.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical definitions for `Todo` and `Due Date`; keep the FIS and implementation language aligned to those terms.
- `src/app/static/js/app.js#openEditTodoDialog` – read-only dialog-prefill seam that must consume the row payload after the server-side fix lands.

## Acceptance Scenarios

- [ ] **S01 [OC01,OC02] [TI01,TI02] Edit-dialog save persists and round-trips a Due Date**
  - **Given** an authenticated user editing an existing `Todo` from the current edit dialog
  - **When** the user submits `PUT /api/todos/{todo_id}` with `due_date=2025-12-31`
  - **Then** the stored `Todo.due_date` remains `2025-12-31`, the returned row partial renders the due-date badge for that date, and the rendered fragment carries `2025-12-31` back into the reopen path

- [ ] **S02 [OC02] [TI02,TI03] Reopening the saved Todo pre-fills the same date**
  - **Given** a rendered todo row returned from a successful edit that includes a persisted Due Date
  - **When** the user invokes `openEditTodoDialog(...)` from that row's edit control
  - **Then** the dialog's `edit-todo-due-date` field is seeded with the same `YYYY-MM-DD` value rather than an empty string

- [ ] **S03 [OC03] [TI01,TI04] Empty Due Date input clears an existing stored date**
  - **Given** an existing `Todo` whose `due_date` is already set
  - **When** the edit flow submits the same todo with `due_date=` and a valid title
  - **Then** the stored `due_date` becomes `None`, the returned row omits the due-date badge, and reopening the dialog shows an empty date field

- [ ] **S04 [OC03] [TI01,TI04] Malformed non-dialog date input does not overwrite the stored date**
  - **Given** an existing `Todo` whose `due_date` is already `2025-12-31`
  - **When** `PUT /api/todos/{todo_id}` receives a malformed `due_date` string outside the dialog contract such as `2025/12/31`
  - **Then** the request does not replace the stored due date with blank state, and the returned row continues to carry the last valid `2025-12-31` value

## Structural Criteria

- [ ] The `PUT /api/todos/{todo_id}` edit flow keeps the current HTMX row-swap contract by returning the todo row partial shape expected by `hx-target="#todo-{id}"`.
- [ ] BUG-002 regression coverage is owned in the todo update test surface and does not require shared quick-add or priority test changes.
- [ ] Persisted Due Date values continue to round-trip through the existing `format_date_input()` and visible row-display formatting contracts.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py#update_todo` – edit submission parsing and persistence rules for `due_date`
- Rendered todo-row output for the due-date edit path – preserve the existing `data-todo-due-date` and visible-date contract without widening into priority ownership
- `tests/test_todo_due_dates.py` – story-owned regression coverage for persist, clear, malformed-input preservation, and dialog-prefill proof

### What We're NOT Doing

- Overdue or due-today styling fixes – BUG-004 already owns the calendar-date styling defect
- Quick-add creation behavior or default priority selection – BUG-003 is a separate story with separate ownership
- Dialog redesign or new client-side state management – the existing HTMX partial flow remains the source of truth
- Authentication, session, or authorization changes – unrelated to BUG-002 and intentionally simplified elsewhere in the app

## Architecture Decision

**Approach**: Align the server-side `due_date` parse/store contract with the existing HTML `type="date"` and `format_date_input()` round-trip, then keep the current row partial and dialog reopen path unchanged.
**Why this over alternatives**: This is the smallest story-isolated fix that resolves the defect at the actual server/UI contract boundary without widening into client-side dialog rework or adjacent BUG-003/BUG-004 behavior.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor                                   | why needed (intent)
file   | src/app/routes/todos.py#update_todo          | Existing edit submission path, auth checks, and row-partial response contract
file   | src/app/templates/partials/todo_item.html    | Rendered row carries visible Due Date output plus dialog reopen seed values
file   | src/app/utils.py#format_date_input           | Canonical `YYYY-MM-DD` serialization for HTML date inputs
file   | src/app/static/js/app.js#openEditTodoDialog  | Dialog field-seeding contract that must keep consuming the rendered row value
file   | tests/test_todo_due_dates.py                 | Story-owned regression surface for BUG-002 without sharing quick-add tests
```

## Constraints & Gotchas

- **Constraint**: The edit dialog submits a plain HTML date value from `type="date"` – use the `YYYY-MM-DD` contract end-to-end rather than the current `%Y-%m-%dT%H:%M` parse expectation.
- **Avoid**: Solving BUG-002 by changing the dialog workflow or adding new JS state – instead keep the existing server-rendered partial flow and fix the persistence boundary in the edit/update path.
- **Critical**: `Todo.due_date` is stored as a SQLAlchemy `DateTime`, while `format_date_input()` and `format_date()` normalize the UI contract to dates – preserve that round-trip so the row badge and reopen field stay aligned.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01 Due Date edits use one supported input contract across save, clear, and malformed-input paths**
  - Follow `src/app/routes/todos.py#update_todo` and the edit form at `src/app/templates/app.html#edit-todo-dialog`; valid `due_date` input is `YYYY-MM-DD`, blank input clears, and malformed non-dialog input must not overwrite an existing stored date
  - **Verify**: `PUT /api/todos/{todo_id}` with `due_date=2025-12-31` persists `2025-12-31`; `due_date=` clears the stored value; `due_date=2025/12/31` leaves the prior stored `2025-12-31` unchanged

- [ ] **TI02 Rendered todo rows carry the persisted Due Date through visible text and reopen data**
  - Follow `src/app/templates/partials/todo_item.html` and `src/app/utils.py#format_date_input`; the returned fragment must keep `data-todo-due-date="2025-12-31"` and the edit-button payload aligned with the stored value after save
  - **Verify**: the successful update response includes `data-todo-due-date="2025-12-31"`, the edit-button `openEditTodoDialog(..., '2025-12-31', ...)` payload, and the displayed label `Dec 31, 2025`

- [ ] **TI03 The existing HTMX edit response contract remains row-swap compatible**
  - Follow `src/app/routes/todos.py#update_todo`, `src/app/templates/app.html#edit-todo-dialog`, and `src/app/static/js/app.js#openEditTodoDialog`; keep the `PUT` response as the todo row partial used by `hx-target="#todo-{id}"`
  - **Verify**: after saving `due_date=2025-12-31`, opening the same row's edit control sets `#edit-todo-due-date` to `2025-12-31`, and the successful edit still returns the todo row fragment with `id="todo-{id}"` without any new redirect, modal, or OOB-swap behavior

- [ ] **TI04 BUG-002 regression coverage proves the story without touching BUG-003 surfaces**
  - Add `tests/test_todo_due_dates.py` as the story-owned update-path regression surface; cover valid persist, clear, malformed-input preservation, and the reopen-dialog proof without changing quick-add or priority-default tests
  - **Verify**: `uv run pytest tests/test_todo_due_dates.py` passes with assertions for `2025-12-31`, the cleared `None` state, malformed-input preservation, and the dialog-prefill proof

### Testing Strategy

### Validation
- Run a narrow browser or DOM-level check for BUG-002 after the route/test work lands: save a Due Date, reopen the same Todo from the returned row, and assert `#edit-todo-due-date.value === "2025-12-31"`.

### Execution Contract

## Final Validation Checklist

## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

Discovered Requirements entries use this shape:

- **Title**: short imperative phrase
- **Description**: 1-2 sentences on the discovered requirement
- **Rationale**: why it was missed in original spec
- **Interpretation** (AUTO_MODE only): the conservative interpretation chosen and why
- **Traced from**: task ID where the discovery occurred
- **Date**: YYYY-MM-DD

_No observations recorded yet._
