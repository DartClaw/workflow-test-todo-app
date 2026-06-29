# BUG-003 Quick-Add Default Priority

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Restore the documented low-priority default for quick-add-created todos so users do not see a blank priority state when they later reopen the edit dialog.

**Expected Outcomes**:

- [OC01] A todo created through quick-add with only `list_id` and `title` persists `priority="low"` without extra user input.
- [OC02] The HTMX response for a quick-add-created todo immediately renders a low-priority row contract, including the low badge and low-priority data attributes.
- [OC03] Reopening the edit dialog for a quick-add-created todo shows `Low` selected on later renders as well, not an empty selector.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> | BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | - | Open |

### From `docs/specs/e2e-plan-and-implement/prd.md` - "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/specs/e2e-plan-and-implement/plan.json` - "S02 scope and notes"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 52fd546bba2b09d6faac9786bfd42888d50023d0 -->
> `"scope": "Ensure todos created through quick-add receive the documented default priority so the created item and subsequent edit-dialog reopen both show a low priority without extra user input. Excludes new quick-add inputs and unrelated todo edit behavior.",`
>
> `"notes": "Honor the PRD isolation rule by keeping this story out of the due-date parsing surface and verifying the quick-add round-trip through a non-overlapping test path."`

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Quick-add create response renders a low-priority todo immediately**
  - **Given** an authenticated user with an existing todo list
  - **When** `/api/todos` receives a quick-add POST containing only `list_id` and `title`
  - **Then** the created `Todo` persists with `priority="low"` and the returned row includes `data-todo-priority="low"`, `priority-low`, and visible `Low` priority UI

- [x] **S02 [OC01,OC03] [TI01,TI02] Low priority survives the create-to-reopen round-trip**
  - **Given** a todo was created through quick-add with no explicit priority input
  - **When** the user later loads the list again and reopens the todo in the existing Edit Todo dialog flow
  - **Then** the rendered row still supplies `data-todo-priority="low"` and the dialog shows `Low` selected instead of a blank selector

- [x] **S03 [OC03] [TI01,TI02] Omitted priority input no longer yields an invalid blank selector**
  - **Given** the quick-add form sends no `priority` field at all
  - **When** the created todo is fed through `todo_item` rendering and `openEditTodoDialog()`
  - **Then** the selector must resolve to the valid existing `low` option, not an empty state caused by a null or invalid stored priority

## Structural Criteria

- [x] The quick-add form remains title-only for users; this story does not add new quick-add inputs or hidden priority plumbing.
- [x] BUG-003 lands without edits to the BUG-002 due-date conflict surface in `src/app/routes/todos.py`, `src/app/templates/partials/todo_item.html`, `src/app/templates/app.html`, or `tests/test_todos.py`.
- [x] Regression proof for BUG-003 lives on an isolated integration path that exercises create response plus later reopen rendering, matching the story note about a non-overlapping test path.

## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo` - persistence/default seam for todos created without an explicit priority
- `tests/test_integration.py#TestUserJourneys` - isolated regression path for quick-add create -> render -> reopen behavior

### What We're NOT Doing
- Due-date persistence, parsing, or dialog round-trip fixes - BUG-002 owns that surface and parallel merge safety depends on no overlap
- New quick-add UI fields, hidden inputs, or user-facing priority controls - the story scope is restoring the documented default without extra user input
- Unrelated todo edit behavior changes - this slice fixes only the missing default-priority contract for quick-add-created todos
- Backfilling or migrating pre-existing null-priority rows - BUG-003 is scoped to creation behavior, not historical data repair

## Architecture Decision

**Approach**: Supply the missing default at the shared persistence/model seam so quick-add-created `Todo` records materialize with `priority="low"` without changing the quick-add form or touching the due-date route surface.
**Why this over alternatives**: The UI and model intent already point to `low` as the default; restoring that value below the form fixes both immediate row rendering and later dialog reopen through existing templates and JS while keeping S02 merge-isolated from S01.

## Technical Overview

The quick-add form posts only `list_id` and `title`, so any default priority must come from an existing backend/model seam rather than new form input. The created record is immediately rendered by `partials/todo_item.html`, which drives both the visible badge and the `data-todo-priority` value later consumed by `openEditTodoDialog()`. Existing unit coverage in `tests/test_todos.py#TestTodos.test_create_todo` already expects `created.priority == "low"`, but this story must add its own isolated integration proof because the visible bug is the create -> render -> reopen round-trip, not just the stored row.

## Code Patterns & External References

```text
# type | path#anchor or url | why needed (intent)
file   | src/app/database.py#Todo | Persistence default seam for todos created without explicit priority
file   | src/app/templates/partials/todo_list_content.html:46-62 | Quick-add contract - preserve title-only input, no new priority field
file   | src/app/templates/partials/todo_item.html:1-40 | Rendered row contract - badge text, CSS class, and data attributes all read stored priority
file   | src/app/templates/app.html:121-149 | Edit dialog contract - existing selector already defaults to `low`
file   | src/app/static/js/app.js#openEditTodoDialog | Reopen flow copies row priority directly into `#edit-todo-priority.value`
file   | tests/test_todos.py#TestTodos.test_create_todo | Existing unit expectation for low default; read for intent, do not widen this file for S02
file   | tests/test_integration.py#TestUserJourneys.test_register_create_list_add_todo_logout_login_verify | Existing journey pattern to extend or parallel for non-overlapping round-trip coverage
```

## Constraints & Gotchas

- **Constraint**: `src/app/templates/partials/todo_list_content.html:46-62` sends no `priority` field - Workaround: restore the default below the form, not by widening the request payload
- **Avoid**: touching `src/app/routes/todos.py` or shared due-date templates while fixing BUG-003 - Instead: keep the change on the persistence/default seam and isolated integration coverage
- **Critical**: `openEditTodoDialog()` writes the rendered row's priority straight into `#edit-todo-priority.value` - Must handle by ensuring quick-add-created rows render `low`, never null/invalid priority data

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick-add-created todos persist `priority="low"` when no explicit priority is supplied
  - Use `src/app/database.py#Todo` as the default seam; align with the existing `low` intent already present in `src/app/templates/app.html:121-149` and `src/app/models/todo.py#TodoCreate`, while leaving the quick-add request contract unchanged
  - **Verify**: `tests/test_integration.py::TestUserJourneys::test_quick_add_todo_defaults_priority_low_round_trip` proves POST `/api/todos` with only `list_id` and `title` stores `priority == "low"` and returns `data-todo-priority="low"`, `priority-low`, and `Low`

- [x] **TI02** Quick-add priority round-trip stays visible on later render and dialog reopen
  - Add the BUG-003 regression in `tests/test_integration.py#TestUserJourneys`, not `tests/test_todos.py`, and exercise create response plus a later list render that still feeds `src/app/static/js/app.js#openEditTodoDialog` a valid `low` value through `src/app/templates/partials/todo_item.html:1-40`
  - **Verify**: `uv run pytest tests/test_integration.py::TestUserJourneys::test_quick_add_todo_defaults_priority_low_round_trip -vv`

- [x] **TI03** BUG-003 ships on a merge-isolated surface
  - Keep S02 edits out of `src/app/routes/todos.py`, `src/app/templates/partials/todo_item.html`, `src/app/templates/app.html`, and `tests/test_todos.py`; if the fix cannot land within the isolated S02 surface, stop and re-split instead of overlapping BUG-002
  - **Verify**: `git diff --name-only HEAD -- src/app/routes/todos.py src/app/templates/partials/todo_item.html src/app/templates/app.html tests/test_todos.py` returns no paths, and `uv run pytest tests/test_integration.py::TestUserJourneys::test_quick_add_todo_defaults_priority_low_round_trip -vv` stays green

### Testing Strategy

- [TI02] Prefer integration coverage in `tests/test_integration.py` because this defect spans persistence, HTMX fragment rendering, later list rendering, and the dialog's `data-todo-priority` contract, and the plan explicitly requires a non-overlapping test path from S01

### Validation

- Quick manual/browser validation on `http://localhost:8000`: log in as `demo@example.com` / `demo123`, quick-add a todo, confirm the created row shows `Low`, then reopen Edit Todo and confirm `Priority` is set to `Low`

### Execution Contract

- Treat `src/app/templates/partials/todo_list_content.html`, `src/app/templates/partials/todo_item.html`, `src/app/templates/app.html`, and `src/app/static/js/app.js#openEditTodoDialog` as read-only contract references for S02. If implementation requires editing `src/app/routes/todos.py`, `src/app/templates/partials/todo_item.html`, `src/app/templates/app.html`, or `tests/test_todos.py`, stop and escalate for re-splitting instead of widening S02 into BUG-002's merge surface

## Final Validation Checklist

- [x] Quick-add-created todo rows show `Low` immediately after the HTMX create response
- [x] Reopening Edit Todo for that row shows `Low` selected, not a blank selector
- [x] S02 changes remain isolated from BUG-002's shared file surface

## Implementation Observations

_No observations recorded yet._
