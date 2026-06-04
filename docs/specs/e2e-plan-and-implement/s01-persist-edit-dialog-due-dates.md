# Persist edit-dialog due dates

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Ensure the existing todo edit dialog can save and later reopen a Due Date without losing the user-entered value.

**Expected Outcomes**:

- [OC01] The edit dialog's date-only `due_date` submission persists on the Todo instead of being ignored.
- [OC02] The updated todo row and reopened edit dialog both reflect the same saved Due Date.
- [OC03] Clearing the Due Date from the edit dialog still removes the stored value without widening the story into unrelated todo behavior.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: cf989b6db61b05b650b2f23368680c09e535c68b -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: cf989b6db61b05b650b2f23368680c09e535c68b -->
> BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |

## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical Todo, Due Date, and Priority terminology for the spec and regression names.
- `docs/specs/e2e-plan-and-implement/plan.json` – Story ownership split showing S01 owns the edit-save Due Date path while S02 stays on quick-add Priority defaults.

## Acceptance Scenarios

> Scenario IDs are local to this FIS.

- [x] **S01 [OC01,OC02] [TI01,TI02] Editing a todo saves a date-only Due Date**
  - **Given** an authenticated User opens Edit for an existing Todo and enters `2025-12-31` into the current Due Date field
  - **When** the dialog submits the existing `PUT /api/todos/{id}` HTMX request
  - **Then** the Todo persists the same calendar date and the returned todo row exposes `data-todo-due-date="2025-12-31"` for the next dialog open

- [x] **S02 [OC02] [TI01,TI02] Reopening the edited todo preserves the same Due Date**
  - **Given** a Todo was just updated through the edit dialog with a Due Date of `2025-12-31`
  - **When** the user triggers Edit again from the re-rendered todo row
  - **Then** the existing dialog handoff surface carries the saved date instead of an empty Due Date value

- [x] **S03 [OC03] [TI01,TI03] Clearing the Due Date still removes the stored value**
  - **Given** an existing Todo already has a Due Date
  - **When** the edit dialog submits the same update flow with a blank `due_date`
  - **Then** the Todo saves with no Due Date and the returned row no longer carries a Due Date value

## Structural Criteria

- [x] The expected `YYYY-MM-DD` edit-dialog contract no longer falls through the silent parse-failure path in `src/app/routes/todos.py#update_todo`.
- [x] BUG-002 proof lives in a dedicated Due Date regression surface so S02 can own quick-add Priority defaults without sharing test files.
- [x] Existing title validation, Priority handling, and HTMX partial-response behavior in `src/app/routes/todos.py#update_todo` remain unchanged outside the Due Date fix.

## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#update_todo` Due Date parsing and persistence behavior
- The existing todo-row Due Date handoff contract exposed through `data-todo-due-date` after an update
- Dedicated BUG-002 regression coverage in `tests/test_todo_due_date_persistence.py`

### What We're NOT Doing
- Quick-add default Priority behavior from `BUG-003` – owned by S02 and excluded to preserve merge safety
- Overdue or due-today styling logic – separate defect surface with no causal link to edit-save persistence
- New dialog controls, datetime-local inputs, or JSON endpoints – the story stays inside the current HTMX HTML-partial flow
- Broad datetime utility refactors – only the edit dialog's existing date-only contract is in scope

## Architecture Decision

**Approach**: Align `src/app/routes/todos.py#update_todo` with the existing edit dialog's `type="date"` contract so the server accepts the date-only value the UI already submits and re-renders.
**Why this over alternatives**: Changing the dialog contract or adding client-side transformations would widen the surface, create avoidable risk, and break the PRD's isolated-story constraint.

## Technical Overview

The current dialog and row handoff already operate on a date-input-friendly value, but `update_todo` still expects a different format and silently keeps the old state on `ValueError`. Fixing the save boundary is the narrowest change: the route accepts the date-only value, the existing template continues rendering the stored Due Date, and the edit dialog can reopen with the same value without any new UI behavior.

## Code Patterns & External References

```text
# type | path#anchor or url                              | why needed (intent)
file   | src/app/routes/todos.py#update_todo             | Existing edit-save path, validation flow, and Due Date persistence boundary
file   | src/app/templates/app.html#edit-todo-dialog     | Current dialog uses `type="date"` and defines the submitted field contract
file   | src/app/templates/partials/todo_item.html       | Todo row emits `data-todo-due-date` for the next dialog open
file   | src/app/static/js/app.js#openEditTodoDialog     | Existing dialog wiring consumes the row's Due Date metadata unchanged
file   | tests/test_todos.py#TestTodos.test_update_todo  | Existing route-level update test pattern to mirror in a focused BUG-002 regression file
```

## Constraints & Gotchas

- **Constraint**: The edit dialog submits a date-only value and the todo row reuses that value on reopen – Workaround: keep the fix anchored at the server parse boundary instead of changing the client contract.
- **Shared seam**: `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js#openEditTodoDialog` are read-only integration surfaces shared with S02 – If this story requires editing either seam, stop and re-scope or serialize execution.
- **Avoid**: Broadening this fix into Priority or overdue styling behavior – Instead: prove only Due Date persistence and blank-value clearing on the existing update route.
- **Critical**: `update_todo` returns `partials/todo_item.html` – Must handle by preserving the current partial shape while making the saved Due Date visible in the returned row metadata.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Existing todo updates accept and persist the edit dialog's date-only Due Date contract
  - Keep the change in `src/app/routes/todos.py#update_todo`; accept the current `YYYY-MM-DD` submission from `src/app/templates/app.html#edit-todo-dialog` and preserve the existing blank-value-clears-field behavior
  - **Verify**: `uv run pytest tests/test_todo_due_date_persistence.py::test_update_todo_persists_date_only_due_date -q`

- [x] **TI02** Updated todo rows expose the persisted Due Date back to the next edit-dialog open
  - Reuse `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js#openEditTodoDialog`; the updated row must emit `data-todo-due-date="2025-12-31"` without introducing new Priority or styling behavior
  - **Verify**: `uv run pytest tests/test_todo_due_date_persistence.py::test_update_todo_response_includes_persisted_due_date_metadata -q`

- [x] **TI03** BUG-002 proof remains isolated to a dedicated Due Date regression surface
  - Add or move the focused persistence tests into `tests/test_todo_due_date_persistence.py` so the story proves save, reopen, and clear semantics without sharing a regression file with S02
  - **Verify**: `uv run pytest tests/test_todo_due_date_persistence.py -q`

### Testing Strategy

- Keep proof at the route/fragment level in `tests/test_todo_due_date_persistence.py`: assert the persisted Todo state and returned HTML handoff together so the regression covers both save and reopen behavior.

### Validation

- Manual browser check: log in, edit an existing Todo, save `2025-12-31`, reopen the same Todo, and confirm the Due Date field still shows `2025-12-31`. Repeat with a blank Due Date to confirm the field clears.

### Execution Contract

- If satisfying a scenario appears to require changing quick-add creation or Priority defaults, stop and hand the work back to S02; S01 owns only the edit-save Due Date defect.
- If the fix appears to require editing `src/app/templates/partials/todo_item.html` or `src/app/static/js/app.js#openEditTodoDialog`, stop and re-scope or serialize with S02 because those seams are shared read-only integration surfaces in the plan.

## Final Validation Checklist

## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Spec authors: leave this section empty._

Discovered Requirements entries use this shape:

- **Title**: short imperative phrase
- **Description**: 1-2 sentences on the discovered requirement
- **Rationale**: why it was missed in original spec
- **Interpretation** (AUTO_MODE only): the conservative interpretation chosen and why
- **Traced from**: task ID where the discovery occurred
- **Date**: YYYY-MM-DD

_No observations recorded yet._

### Run: 2026-06-04 07:53 UTC – observations

#### NOTICED BUT NOT TOUCHING
- Full-suite baseline: `uv run pytest -q` still fails at `tests/test_todos.py::TestTodos::test_create_todo` because `Todo.priority` remains `None` for `POST /api/todos` creation; this is outside S01 scope and is attributed to BUG-003.
- S01 now addresses server-side parsing and row metadata; full UI reopen end-to-end handoff validation (dialog state prefill from `openEditTodoDialog`) is not executed in this story's backend-focused regression suite.
