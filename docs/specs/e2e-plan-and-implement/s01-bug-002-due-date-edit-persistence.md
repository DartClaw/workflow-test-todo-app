# BUG-002 Due Date Edit Persistence

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Restore the edit-todo due-date round-trip so the server honors the dialog's posted date value instead of silently dropping it.

**Expected Outcomes**:

- [OC01] Saving a due date from the Edit Todo dialog persists that date on the `Todo` record when the dialog submits its date-only form value.
- [OC02] A persisted due date round-trips through the returned todo fragment so the row display and reopened Edit Todo dialog stay in sync.
- [OC03] A non-empty due-date value outside the dialog contract fails explicitly instead of being silently ignored.

## Required Context

### From `docs/specs/e2e-plan-and-implement/plan.json` - "S01 story scope"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories.0 -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> "scope": "Restore the due-date edit flow so a date saved from the todo edit dialog persists in storage, re-renders on the todo item, and is still present when the dialog is reopened. Includes the update endpoint and its regression coverage. Excludes broader due-date styling or timezone behavior changes.",
>
> "notes": "Honor the PRD isolation rule by keeping this story on the due-date update path and its own regression surface."

### From `docs/specs/e2e-plan-and-implement/prd.md` - "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.

### From `docs/specs/e2e-plan-and-implement/prd.md` - "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.

### From `docs/specs/e2e-plan-and-implement/prd.md` - "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> | BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | - | Open |

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI03] Saving a due date from Edit Todo persists and reopens with the same value**
  - **Given** an authenticated user edits an existing `Todo` from the Edit Todo dialog and submits `due_date=2025-12-31`
  - **When** `PUT /api/todos/{todo_id}` processes the dialog form
  - **Then** the stored `Todo.due_date` resolves to calendar date `2025-12-31`, the returned todo fragment shows `Dec 31, 2025`, the fragment exposes `2025-12-31` for the next dialog reopen, and reopening Edit Todo sets `#edit-todo-due-date.value` to `2025-12-31`

- [x] **S02 [OC02] [TI01,TI03] Clearing a previously saved due date removes it from storage and the reopen surface**
  - **Given** an authenticated user edits a `Todo` that already has a stored due date
  - **When** the dialog submits an empty `due_date`
  - **Then** the stored due date becomes `None`, the returned todo fragment no longer renders the due-date badge, and the reopened dialog field is empty

- [x] **S03 [OC03] [TI02,TI03] A malformed non-empty due-date submission is rejected instead of silently ignored**
  - **Given** an authenticated user edits a `Todo` that already has a stored due date
  - **When** `PUT /api/todos/{todo_id}` receives a non-empty `due_date` value outside the dialog's `YYYY-MM-DD` contract
  - **Then** the response is the HTML error partial with a due-date validation error, and the previously stored due date is unchanged

## Structural Criteria

- [x] `src/app/routes/todos.py#update_todo` preserves the existing HTMX partial contract: success returns `partials/todo_item.html`, while malformed non-empty due-date input returns `partials/error.html`.
- [x] BUG-002 regression coverage proves the date-only save path, clear-on-empty path, and malformed-input rejection path; the old silent-drop behavior must fail that coverage.
- [x] S01 remains isolated to BUG-002 surfaces and does not alter quick-add priority behavior or overdue/due-today styling/time-comparison logic.

## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#update_todo` - due-date parsing, validation, persistence, and success/error partial selection
- `tests/test_todos.py#TestTodos` - focused BUG-002 regression coverage

### What We're NOT Doing
- Changing quick-add default priority behavior - that is S02 / BUG-003 scope
- Changing overdue or due-today styling logic - BUG-004 owns the date-comparison defect
- Introducing timezone-aware due-date storage - the story explicitly excludes broader timezone behavior changes
- Redesigning the Edit Todo dialog inputs or adding new fields - the fix is a contract repair, not a UI expansion
- Changing auth, ownership checks, or non-due-date validation flows - those are working behavior outside BUG-002

## Architecture Decision

**Approach**: Align `update_todo` with the existing `sl-input type="date"` contract by accepting `YYYY-MM-DD` submissions, persisting a stable naive datetime value that round-trips through `format_date_input(...)`, and treating malformed non-empty values as HTML validation errors.
**Why this over alternatives**: The defect is a server-side contract mismatch in an otherwise working HTMX dialog flow, so fixing the update path and its regression surface keeps S01 thin and avoids unrelated template, JS, or timezone changes.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor or url                          | why needed (intent)
file   | src/app/routes/todos.py#update_todo         | Existing todo update flow - preserve ownership, HTML partial, and field-validation patterns
file   | src/app/templates/app.html#edit-todo-dialog | Edit Todo contract - `due_date` is posted from a `type="date"` field
file   | src/app/templates/partials/todo_item.html   | Todo row round-trip - due date is rendered for display and for dialog reopen
file   | src/app/static/js/app.js#openEditTodoDialog | Dialog reopen behavior - saved date string is assigned directly back into the due-date input
file   | src/app/utils.py#format_date_input          | Canonical date-input formatter - saved values must round-trip to `YYYY-MM-DD`
file   | tests/test_todos.py#TestTodos.test_update_todo | Existing regression surface - currently red because BUG-002 drops the due date
```

## Constraints & Gotchas

- **Constraint**: `sl-input type="date"` posts a date-only value, while `Todo.due_date` is stored as a naive datetime - Workaround: normalize the route to the date-only contract and persist a value that `format_date_input(...)` returns as the same calendar date
- **Avoid**: swallowing `ValueError` for a non-empty `due_date` submission - Instead: surface the failure through `partials/error.html` and leave the stored due date unchanged
- **Critical**: S01 excludes broader due-date behavior changes - Must handle by: keeping changes off `is_overdue`, `is_due_today`, styling classes, and quick-add creation logic

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Edit-dialog date submissions persist as `Todo` due dates
  - In `src/app/routes/todos.py#update_todo`, keep the existing access, title, note, and priority flow but accept the `YYYY-MM-DD` value posted by `src/app/templates/app.html#edit-todo-dialog`; store it in a stable naive datetime shape that `src/app/utils.py#format_date_input` round-trips back to the same day
  - **Verify**: `Test: PUT /api/todos/{id}` with `title=Updated Title`, `note=Updated note`, `due_date=2025-12-31`, and `priority=high` leaves `todo.due_date` non-null and `todo.due_date.date().isoformat()` equal to `2025-12-31`

- [x] **TI02** Malformed non-empty due-date submissions fail explicitly instead of silently no-oping
  - In `src/app/routes/todos.py#update_todo`, treat any non-empty `due_date` outside the `YYYY-MM-DD` contract as invalid input; reuse the existing HTML error-partial pattern already used for title validation and keep the previously stored due date unchanged
  - **Verify**: `Test: PUT /api/todos/{id}` with a pre-existing due date and `due_date=2025-12-31T09:30` returns the error partial with a due-date validation error, and the stored due date is still `2025-12-31`

- [x] **TI03** Returned todo fragments round-trip the saved due date back into the next dialog reopen
  - Reuse the existing render surfaces in `src/app/templates/partials/todo_item.html`, `src/app/templates/app.html#edit-todo-dialog`, and `src/app/static/js/app.js#openEditTodoDialog`; after TI01 and TI02, the success fragment must still expose the saved date through the rendered due-date text and the dialog reopen payload without requiring template or dialog edits
  - **Verify**: `Test: successful todo update response` for `due_date=2025-12-31` contains `Dec 31, 2025` and `data-todo-due-date="2025-12-31"`; `Manual/browser: save due_date=2025-12-31`, reopen Edit Todo for that row, and confirm `document.getElementById("edit-todo-due-date").value === "2025-12-31"`; `Test: successful clear response` contains no rendered due-date badge and no non-empty `data-todo-due-date`

- [x] **TI04** BUG-002 regression coverage proves save, clear, and invalid-input handling without crossing into other stories
  - Extend `tests/test_todos.py#TestTodos` instead of creating a new test module; keep the coverage isolated to the due-date update path and its returned fragment, not quick-add priority or overdue styling behavior
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodos::test_update_todo tests/test_todos.py::TestTodos::test_update_todo_clears_due_date tests/test_todos.py::TestTodos::test_update_todo_rejects_invalid_due_date -q` passes

### Testing Strategy

- [TI03] Add manual/browser proof for the dialog reopen step because the backlog defect is a user-visible reopen regression and the current Python test surface only proves the server fragment contract

### Validation

- On `http://localhost:8000`, log in as `demo@example.com` / `demo123`, edit a todo to save `2025-12-31`, reopen Edit Todo, and confirm the due-date field is still `2025-12-31`

### Execution Contract

- Treat `src/app/templates/app.html`, `src/app/templates/partials/todo_item.html`, and `src/app/static/js/app.js#openEditTodoDialog` as read-only contract references for S01 unless the route-only fix proves impossible; if a template or JS edit becomes necessary, stop and re-check plan isolation before widening the story

## Final Validation Checklist

## Implementation Observations

_No observations recorded yet._
