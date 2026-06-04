# Default quick-add todos to low priority

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Ensure title-only quick-add creates a Todo with the documented default Priority so new rows and reopened edit dialogs never surface a blank selector state.

**Expected Outcomes**:

- [OC01] Quick-add creation persists `low` as the default Priority whenever the form omits a Priority field.
- [OC02] A quick-added Todo renders and reopens through the existing edit dialog with Low selected instead of a blank Priority state.
- [OC03] The current HTMX quick-add interaction still appends the row and count update, and blank-title validation still prevents creation.

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
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |

## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical Todo and Priority terminology for tests, tasks, and proof language.
- `docs/specs/e2e-plan-and-implement/plan.json` – Shared decision requiring S02 to keep the defaulting fix off S01's edit-save Due Date surface.

## Acceptance Scenarios

> Scenario IDs are local to this FIS.

- [x] **S01 [OC01,OC03] [TI01,TI02] Quick-add creates a new Todo with Low priority immediately visible**
  - **Given** an authenticated User submits the existing quick-add form with only `list_id` and `title`
  - **When** `/api/todos` creates the Todo through the current title-only flow
  - **Then** the new row is appended, the sidebar count update still returns, and the row renders with Low priority metadata instead of a blank Priority state

- [x] **S02 [OC01,OC02] [TI01,TI02] A newly quick-added Todo reopens with Low selected in Edit**
  - **Given** a Todo was created through quick-add without any explicit Priority input
  - **When** the user opens Edit on that newly rendered row
  - **Then** the row metadata driving the dialog resolves the selector to Low instead of an empty value

- [x] **S03 [OC03] [TI03] Blank-title quick-add rejection still prevents creation**
  - **Given** the quick-add form is submitted with a title containing only whitespace
  - **When** the request is processed
  - **Then** no new Todo is created and the existing title-required validation error still returns

## Structural Criteria

- [x] Newly quick-added Todos no longer persist `NULL` Priority values when creation omits the field.
- [x] BUG-003 proof lives in a dedicated quick-add regression surface so S02 remains merge-safe with S01.
- [x] Existing `create_todo` HTMX response behavior, including the appended row and OOB sidebar count update, remains intact while the default Priority becomes canonical.

## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo` creation-time Priority default for new Todo records
- The existing quick-add response contract that exposes row metadata for the edit dialog
- Dedicated BUG-003 regression coverage in `tests/test_todo_quick_add_priority.py`

### What We're NOT Doing
- `src/app/routes/todos.py#update_todo` Due Date parsing or edit-save behavior – owned by S01 and excluded to preserve merge safety
- Backfilling previously created Todos that already stored `NULL` Priority values – this story guarantees the default for new quick-add creation only
- Adding a new quick-add Priority input or broader Priority UX changes – BUG-003 requires the documented default, not a new control
- Client-only fallbacks that mask a persisted `NULL` value – the canonical fix must happen at creation time

## Architecture Decision

**Approach**: Make `low` a creation-time invariant at `src/app/database.py#Todo` so the stored record, rendered row metadata, and reopened edit dialog all agree without touching S01's update path.
**Why this over alternatives**: Route-level or client-side fallbacks would widen the change into shared handler or dialog surfaces and weaken the PRD's merge-safe isolation requirement.

## Technical Overview

The blank selector is a downstream symptom of quick-add creating a Todo with `priority == None`. The current row template and dialog wiring already render and consume `todo.priority`, and the existing edit dialog shell anchors the expected default with `value="low"`, so a narrow persistence-boundary default lets the current quick-add route and UI surfaces behave correctly without changing the edit-save flow.

## Code Patterns & External References

```text
# type | path#anchor or url                               | why needed (intent)
file   | src/app/database.py#Todo                         | Existing model-level default pattern for persisted Todo fields
file   | src/app/routes/todos.py#create_todo              | Current title-only quick-add creation and OOB response contract
file   | src/app/templates/app.html#edit-todo-priority    | Existing edit dialog shell anchors the expected Low default on reopen
file   | src/app/templates/partials/todo_item.html        | Todo row emits Priority badge and `data-todo-priority` metadata
file   | src/app/static/js/app.js#openEditTodoDialog      | Existing dialog wiring consumes the row's Priority metadata unchanged
file   | tests/test_todos.py#TestTodos.test_create_todo   | Existing quick-add regression seed to mirror in a dedicated BUG-003 test file
```

## Constraints & Gotchas

- **Constraint**: `openEditTodoDialog` trusts the row's `data-todo-priority` value – Workaround: ensure newly created rows carry `data-todo-priority="low"` by making the stored Todo default canonical.
- **Shared seam**: `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js#openEditTodoDialog` are read-only integration surfaces shared with S01 – If this story requires editing either seam, stop and re-scope or serialize execution.
- **Avoid**: Solving BUG-003 in `update_todo` or other edit-save code – Instead: keep the fix at the creation boundary and prove it through the quick-add response contract.
- **Critical**: Quick-add returns `partials/todo_item_with_oob.html` – Must handle by preserving both the appended row and the `hx-swap-oob` count update while introducing the default Priority.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Newly created Todo records default Priority to `low` when quick-add omits it
  - Center the change on `src/app/database.py#Todo`; keep `src/app/routes/todos.py#create_todo` as the title-only creation flow and avoid taking ownership of `src/app/routes/todos.py#update_todo`
  - **Verify**: `uv run pytest tests/test_todo_quick_add_priority.py::test_quick_add_defaults_priority_to_low -q`

- [x] **TI02** Newly quick-added todo rows expose the Low-priority metadata the existing dialog expects
  - Reuse `src/app/routes/todos.py#create_todo`, `src/app/templates/partials/todo_item.html`, and `src/app/static/js/app.js#openEditTodoDialog`; the created row must expose `priority-low`, `Low`, and `data-todo-priority="low"` without changing the dialog shell
  - **Verify**: `uv run pytest tests/test_todo_quick_add_priority.py::test_quick_add_response_includes_low_priority_metadata -q`

- [x] **TI03** BUG-003 proof remains isolated to a dedicated quick-add regression surface
  - Add or move the focused creation tests into `tests/test_todo_quick_add_priority.py` so the story proves defaulting, dialog metadata, and blank-title rejection without sharing a regression file with S01
  - **Verify**: `uv run pytest tests/test_todo_quick_add_priority.py -q`

### Testing Strategy

- Keep proof at the route/fragment level in `tests/test_todo_quick_add_priority.py`: assert persisted Todo state and returned HTML metadata together so the regression covers both creation and reopen behavior.

### Validation

- Manual browser check: log in, quick-add a Todo, open Edit on the new row, and confirm the Priority selector shows Low before any save action.

### Execution Contract

- If satisfying a scenario appears to require changes to `src/app/routes/todos.py#update_todo` or Due Date parsing, stop and hand the work back to S01; S02 owns only creation-time Priority defaulting plus its regression proof.
- If the fix appears to require editing `src/app/templates/partials/todo_item.html` or `src/app/static/js/app.js#openEditTodoDialog`, stop and re-scope or serialize with S01 because those seams are shared read-only integration surfaces in the plan.

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
