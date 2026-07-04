# Persist Edit-Dialog Due Dates

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Restore trust in the Todo edit dialog by ensuring a Due Date selected there is actually persisted and shown again after saving.

**Expected Outcomes**:

- [OC01] A user can set a Todo Due Date in the edit dialog, save it, and reopen the Todo with the same date still populated.
- [OC02] A user can clear a Todo Due Date in the edit dialog and the Todo remains without a Due Date after save.
- [OC03] Existing Todo edit behavior for title, notes, priority, ownership, and HTML partial responses remains intact.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Story S01 Scope"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> Ensure a due date chosen in the edit dialog survives save-and-reopen by aligning the edit form's date value with the server persistence path, while keeping the fix limited to todo edit behavior and a dedicated BUG-002 regression file. Excludes priority-default behavior, due-date styling, and broader todo-creation changes.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Applicable Shared Decisions"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> S01 owns the todo edit/update route surface; S02 must avoid `src/app/routes/todos.py` and restore the default priority through a different persistence seam so the stories do not collide.
>
> Each story gets its own focused regression test file so parallel execution does not force both stories into the same test module.
>
> Both fixes preserve the existing HTML-partial and ad-hoc route-validation architecture; no story introduces JSON responses, Pydantic wiring, or auth changes.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Applicable Binding Constraints"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
>
> Keep each story isolated to its own files; they must merge without conflict.

## Deeper Context

- `docs/STACK.md#technology-stack` – Confirms FastAPI, HTMX, Jinja2, SQLAlchemy, SQLite, pytest, and TestClient baseline.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical terms: Todo, TodoList, Priority, Due Date.
- `CLAUDE.md#architecture` – HTMX routes return HTML partials; route validation is ad-hoc; do not introduce JSON or Pydantic wiring.
- `docs/guidelines/WEB-DEV-GUIDELINES.md#html--semantics` – Preserve existing semantic form and external JS/CSS separation if touching templates.
- `docs/guidelines/UX-UI-GUIDELINES.md#forms` – Preserve labeled single-column form controls and keyboard-accessible edit dialog behavior.

## Acceptance Scenarios

- [x] **S01 [OC01,OC03] [TI01,TI02,TI03] Date-only edit-dialog submission persists and reopens populated**
  - **Given** an authenticated user owns a Todo with no Due Date
  - **When** the edit Todo form submits `due_date=2025-12-31` to `PUT /api/todos/{todo_id}` with valid title, note, and priority fields
  - **Then** the response is the updated `partials/todo_item.html` HTML partial, the stored Todo has Due Date `2025-12-31`, and the returned Todo row exposes `data-todo-due-date="2025-12-31"` for the next edit-dialog open

- [x] **S02 [OC02,OC03] [TI01,TI02,TI03] Blank edit-dialog due date clears an existing Due Date**
  - **Given** an authenticated user owns a Todo with Due Date `2025-12-31`
  - **When** the edit Todo form submits a blank `due_date` to `PUT /api/todos/{todo_id}` with otherwise valid edit fields
  - **Then** the response is the updated Todo HTML partial, the stored Todo has no Due Date, and the returned Todo row has an empty `data-todo-due-date` value

- [x] **S03 [OC03] [TI01,TI03] Existing edit fields and access checks still work**
  - **Given** an authenticated user owns a Todo and another authenticated user does not
  - **When** the owner edits title, note, Due Date, and priority, and the non-owner attempts to edit the same Todo
  - **Then** the owner edit persists all submitted fields through the existing HTML partial response, and the non-owner still receives the existing `403` Error Partial behavior

## Structural Criteria

- [x] The BUG-002 regression lives in a dedicated test file, not in `tests/test_todos.py` or another shared S02-owned test module.
- [x] S01 does not change quick-add Todo creation, model-level Priority defaults, Priority selector defaults, Due Date styling, or overdue/today date classification.
- [x] `PUT /api/todos/{todo_id}` continues returning server-rendered HTML partials and ad-hoc route validation errors; no JSON endpoint, Pydantic route wiring, or auth/session changes are introduced.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py` Todo edit/update route surface, especially `update_todo`
- `src/app/templates/partials/todo_item.html` returned row contract for `data-todo-due-date`
- `src/app/templates/app.html` existing edit Todo dialog form contract, only if needed to keep the form value aligned with persistence
- `src/app/static/js/app.js#openEditTodoDialog` existing data population contract, only if needed to keep save-and-reopen behavior intact
- Dedicated BUG-002 regression test file under `tests/`

### What We're NOT Doing

- BUG-003 quick-add Priority default behavior – owned by S02 and must avoid this story's edit/update route work.
- Todo creation route or model default changes – outside S01 and risks merge conflict with S02.
- Due Date styling, overdue behavior, or due-today behavior – explicitly excluded by S01 scope.
- Broad edit dialog redesign – the defect is persistence, not UX layout.
- Production auth, session, or JSON API changes – contrary to current project architecture.

## Architecture Decision

**Approach**: Keep the existing HTMX edit route and returned Todo partial contract, but make the server persistence path accept the date value actually submitted by the edit dialog.
**Why this over alternatives**: The bug is a format mismatch in the edit/update surface; changing creation defaults, data models, or response types widens scope and violates the disjoint-write plan decision.

## Technical Overview

The edit Todo dialog currently uses a date input named `due_date`, and rendered Todo rows expose `data-todo-due-date` via `format_date_input(todo.due_date)` in `YYYY-MM-DD` form. `update_todo` must persist that date-only value and return the updated row so the next `openEditTodoDialog(...)` call receives the same value.

## Code Patterns & External References

```text
# type | path#anchor                               | why needed (intent)
file   | src/app/routes/todos.py#update_todo       | Edit/update route surface owned by S01; preserve HTML partial and validation patterns
file   | src/app/templates/partials/todo_item.html | Returned Todo row contract for visible date and data attributes used on reopen
file   | src/app/templates/app.html                | Edit Todo dialog form contract: `name="due_date"` and `type="date"`
file   | src/app/static/js/app.js#openEditTodoDialog | Reopen path: dialog field is populated from returned row data
file   | src/app/utils.py#format_date_input        | Existing `YYYY-MM-DD` date-input formatting contract
file   | tests/conftest.py#authenticated_client    | Authenticated route-test fixture and isolated in-memory DB setup
file   | tests/test_todos.py#TestTodos.test_update_todo | Existing update-route test style; do not add BUG-002 regression here
```

## Constraints & Gotchas

- **Constraint**: Preserve disjoint writes with S02 – S01 may touch the edit/update route surface but must not fix quick-add Priority defaults.
- **Avoid**: Treating this as a generic date/time redesign – Due Date is stored as a naive `DateTime`, and this story only needs date-only edit-dialog persistence.
- **Critical**: HTMX routes return HTML fragments – success and error behavior must remain `TemplateResponse` partials, not JSON.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Todo edit/update persists date-only Due Dates from the edit dialog
  - Follow `src/app/routes/todos.py#update_todo`; keep existing title, note, priority, ownership, commit, refresh, and `partials/todo_item.html` response behavior.
  - **Verify**: A BUG-002 regression submits `PUT /api/todos/{todo_id}` with `due_date=2025-12-31`, then asserts `response.status_code == 200`, `db_session.refresh(todo)`, `todo.due_date.date().isoformat() == "2025-12-31"`, and the response HTML contains `data-todo-due-date="2025-12-31"`.

- [x] **TI02** Clearing a Todo Due Date through the edit dialog remains supported
  - Blank or omitted edit-dialog Due Date values must result in no stored Due Date, preserving the current clear-field behavior in `src/app/routes/todos.py#update_todo`.
  - **Verify**: A BUG-002 regression starts from a Todo with `due_date=datetime(2025, 12, 31)`, submits a valid edit request with `due_date=""`, then asserts `todo.due_date is None` and the response HTML has an empty `data-todo-due-date` value.

- [x] **TI03** BUG-002 regression coverage is isolated from S02 and proves save-and-reopen behavior
  - Create a dedicated regression file such as `tests/test_bug_002_edit_dialog_due_date.py`; use `tests/conftest.py#authenticated_client` and do not add this story's assertions to `tests/test_todos.py`.
  - **Verify**: `uv run pytest tests/test_bug_002_edit_dialog_due_date.py -q` passes, and `rg "due_date=2025-12-31|data-todo-due-date" tests/test_bug_002_edit_dialog_due_date.py` finds the dedicated regression evidence.

- [x] **TI04** Existing Todo edit route contracts remain unchanged outside BUG-002
  - Preserve HTML partial responses, Error Partial behavior, auth ownership checks, ad-hoc validation, and Priority handling in `src/app/routes/todos.py#update_todo`.
  - **Verify**: `uv run pytest tests/test_bug_002_edit_dialog_due_date.py tests/test_todos.py::TestTodos::test_update_todo tests/test_todos.py::TestTodoAccess::test_cannot_modify_other_users_todo` passes.

### Testing Strategy

- BUG-002 gets its own focused route-level regression file because the plan requires per-bug regression files and merge-safe parallel execution.
- The regression should prove the same value chain a user experiences: edit-dialog date format submitted to `PUT /api/todos/{todo_id}`, persisted Todo Due Date, returned row `data-todo-due-date`, and reopen-ready value.

### Validation

- If implementation touches `app.html`, `todo_item.html`, or `app.js`, visually validate the edit dialog: run the app, log in with `demo@example.com` / `demo123`, set a Due Date, save, reopen the Todo, and confirm the field remains populated.

### Execution Contract

- Do not edit quick-add creation behavior or model-level Priority defaults while executing this FIS; surface any BUG-003 findings as out of scope for S02.

## Final Validation Checklist

- [x] `uv run pytest tests/test_bug_002_edit_dialog_due_date.py tests/test_todos.py::TestTodos::test_update_todo tests/test_todos.py::TestTodoAccess::test_cannot_modify_other_users_todo -q` passes.
- [x] No S01 change modifies quick-add Priority default behavior, Todo creation defaults, Due Date styling, overdue/today classification, auth/session handling, JSON response shape, or Pydantic route wiring.

## Implementation Observations

_No observations recorded yet._
