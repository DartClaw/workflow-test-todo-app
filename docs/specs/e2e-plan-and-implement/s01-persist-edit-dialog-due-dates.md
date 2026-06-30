# Persist edit-dialog due dates

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S01`

## Feature Overview and Goal

**Intent**: Make the Edit Todo dialog reliably round-trip a user's chosen Due Date so saved dates remain visible and editable instead of appearing lost on reopen.

**Expected Outcomes**:

- [OC01] Saving `Due Date` from the existing Edit Todo dialog persists the selected calendar date on the Todo.
- [OC02] Reopening the Edit Todo dialog after save, reload, or row re-render shows the same `YYYY-MM-DD` value that was last saved.
- [OC03] Clearing the `Due Date` field removes the persisted date instead of leaving stale row or dialog state behind.

## Required Context

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S01 scope and notes"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 8c4b71ffe6c3cf2887422be2781f616bd0916ba7 -->
> `"scope": "Persist the date selected in the Todo edit dialog through save, reload, and re-open so users see the same due date they chose. Includes the date-only input round-trip and clear-date behavior for the existing update flow; excludes overdue or due-today styling fixes from BUG-004 and any quick-add priority changes."`
>
> `"notes": "Keep regression coverage in a file S02 does not need to edit; do not widen into due-date styling semantics."`

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 8c4b71ffe6c3cf2887422be2781f616bd0916ba7 -->
> `BUG-002` – `Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches.`

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 8c4b71ffe6c3cf2887422be2781f616bd0916ba7 -->
> `Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.`
>
> `Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.`
>
> `Keep each story isolated to its own files; they must merge without conflict.`

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Saved edit-dialog due dates survive immediate reopen**
  - **Given** an authenticated user opens the existing Edit Todo dialog for a Todo with no due date
  - **When** the user saves the dialog with `due_date=2025-12-31`
  - **Then** the returned Todo row shows the due date, and reopening Edit Todo immediately pre-fills the date input with `2025-12-31`

- [x] **S02 [OC02] [TI01,TI02] Persisted due dates survive later row re-render**
  - **Given** a Todo already has a persisted due date of `2025-12-31`
  - **When** the app later renders that Todo row again and the user reopens Edit Todo
  - **Then** the row metadata and reopened dialog input still show `2025-12-31`

- [x] **S03 [OC03] [TI01,TI02] Clearing the due date removes persisted state**
  - **Given** an authenticated user opens Edit Todo for a Todo whose due date is currently `2025-12-31`
  - **When** the user clears the `Due Date` field and saves the dialog
  - **Then** the Todo no longer renders a due-date badge, and reopening Edit Todo shows an empty date input

## Structural Criteria

- [x] The existing HTMX partial contract remains server-rendered HTML, and `todo_item.html` stays the source of truth for dialog rehydration via `data-todo-due-date`.
- [x] BUG-002 regression coverage lands in `tests/test_todos.py`, keeping S01 ownership separate from S02's quick-add surfaces.
- [x] S01 does not change quick-add priority defaults, overdue styling, or due-today styling semantics owned by BUG-003 and BUG-004.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py#update_todo` due-date parsing and persistence for the existing edit flow
- `src/app/templates/partials/todo_item.html` row metadata and inline edit trigger that carry persisted due-date state
- `tests/test_todos.py` regression coverage for save/reopen and clear-date behavior

### What We're NOT Doing

- `BUG-003` quick-add priority defaulting or empty priority-selector behavior -- owned by S02 and explicitly isolated by the plan
- `BUG-004` overdue or due-today styling semantics -- story scope excludes styling fixes even though they also touch due dates
- Schema changes to `Todo.due_date` or timezone normalization -- the current naive `DateTime` column remains the storage contract for this story
- New JSON endpoints, client-side state caches, or dialog-only persistence helpers -- the app stays HTMX-first with the row partial as the source of truth
- New user-facing validation copy for malformed non-dialog `due_date` submissions -- this story fixes the dialog round-trip contract, not the broader validation model

## Architecture Decision

**Approach**: Keep the fix on the existing edit/update path: accept the dialog's date-only `due_date` payload in `update_todo`, persist it in the current `Todo.due_date` column, and continue rehydrating the dialog from `format_date_input(todo.due_date)` on the rendered row.
**Why this over alternatives**: It fixes BUG-002 where the server already owns UI state, preserves the HTMX partial/data-attribute contract, and avoids cross-story edits to quick-add or due-date styling code.

## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                      | why needed (intent)
file   | src/app/routes/todos.py#update_todo    | Existing edit handler – keep route-level validation and HTML partial response shape
file   | src/app/utils.py#format_date_input     | Date-input formatting – round-trip persisted due dates as YYYY-MM-DD
file   | src/app/static/js/app.js#openEditTodoDialog | Dialog hydration – keep reading server-rendered row data into the edit form
file   | src/app/templates/app.html#edit-todo-dialog | Edit form surface – `sl-input` submits the existing `due_date` field
file   | src/app/templates/partials/todo_item.html:1-40 | Row contract – `data-todo-due-date` and inline edit trigger must stay aligned
file   | tests/test_todos.py#TestTodos.test_update_todo | Existing route test to extend with BUG-002 regression proof
```

## Constraints & Gotchas

- **Constraint**: `Todo.due_date` is stored in a naive `DateTime` column while the dialog submits a date-only string -- Workaround: normalize the `type="date"` payload at the route boundary and keep using `format_date_input()` for row-to-dialog round-trip
- **Avoid**: widening this story into due-date styling behavior -- Instead: limit S01 to persistence, rendered-row state, and dialog rehydration only
- **Critical**: the edit dialog is repopulated from the rendered Todo row, not from hidden client state -- Must handle by: ensuring the save response and later row renders emit the same persisted `data-todo-due-date` value

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Existing edit updates persist date-only `due_date` submissions and still clear on blank input
  - Follow `src/app/routes/todos.py#update_todo` and the current route-level validation pattern; accept the dialog's `YYYY-MM-DD` payload without widening into BUG-004 styling logic or unrelated request-model changes
  - **Verify**: `uv run pytest tests/test_todos.py -k "persist_due_date or clear_due_date"` proves PUT `/api/todos/{id}` with `due_date=2025-12-31` stores a value whose `date().isoformat()` is `2025-12-31`, and PUT with `due_date=` clears `Todo.due_date` to `None`

- [x] **TI02** Rendered Todo rows rehydrate Edit Todo with the persisted due-date value
  - Keep the existing HTMX fragment contract across `src/app/templates/partials/todo_item.html:1-40`, `src/app/templates/app.html#edit-todo-dialog`, and `src/app/static/js/app.js#openEditTodoDialog`; the dialog must keep reading `data-todo-due-date="{{ format_date_input(todo.due_date) }}"`
  - **Verify**: response assertions or targeted tests confirm the saved-row HTML contains `data-todo-due-date="2025-12-31"`, and browser validation shows reopening Edit Todo pre-fills `#edit-todo-due-date` with `2025-12-31`

- [x] **TI03** BUG-002 proof and change ownership stay isolated on S01 surfaces
  - Extend `tests/test_todos.py#TestTodos.test_update_todo`; keep regression coverage out of S02 quick-add flows and out of BUG-004 styling assertions so the stories remain merge-safe
  - **Verify**: `uv run pytest tests/test_todos.py -k "update_todo or persist_due_date or clear_due_date"` passes, and the implementation diff is limited to `src/app/routes/todos.py`, `src/app/templates/partials/todo_item.html`, and `tests/test_todos.py`

### Testing Strategy


### Validation


### Execution Contract


## Final Validation Checklist


## Implementation Observations

_No observations recorded yet._
