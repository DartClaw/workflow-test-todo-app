# BUG-001 - Delete Refreshes Sidebar Incomplete Count

## Feature Overview and Goal

**Intent**: Keep the sidebar incomplete-count trustworthy during Todo deletion so users do not need a full page reload to see the current state of a TodoList.

**Expected Outcomes**

- [OC01] Deleting an incomplete Todo updates that TodoList's sidebar incomplete-count immediately in the same interaction.
- [OC02] The existing delete confirmation flow still removes the targeted Todo row in place, with the server remaining the source of truth for the sidebar badge value.
- [OC03] Delete count semantics stay correct for completed Todos, zero remaining incomplete Todos, and existing 403/404 delete failures.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc0228 -->
> Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

### From `AGENTS.md` - "Architecture"
<!-- source: AGENTS.md#architecture -->
<!-- extracted: 5cc0228 -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

## Deeper Context

- `AGENTS.md#project-specific-guidelines` - HTMX-first rule and BUG-ID scoping rules that keep this fix on the existing server-rendered path.
- `AGENTS.md#visual-validation-workflow` - Local browser validation steps for interactions that update both the Todo row and the sidebar badge.
- `docs/STACK.md#frameworks--libraries` - FastAPI, Jinja2, HTMX, and pytest baseline for route responses and test coverage.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` - Canonical terms for Partial, OOB Swap, and Error Partial used throughout this spec.

## Acceptance Scenarios

- [ ] **S01 [OC01,OC02] [TI01,TI03] Incomplete Todo delete refreshes the sidebar count in place**
  - **Given** an authenticated user is viewing a TodoList whose sidebar badge shows `3` incomplete Todos and the targeted Todo is incomplete
  - **When** the user confirms deletion for that Todo through the existing delete dialog
  - **Then** the Todo row is removed and the sidebar badge for that TodoList updates to `2` in the same interaction without a full page reload

- [ ] **S02 [OC01,OC03] [TI01,TI02] Deleting the last incomplete Todo renders a zero badge**
  - **Given** an authenticated user is viewing a TodoList with exactly one incomplete Todo remaining
  - **When** the user deletes that Todo
  - **Then** the delete response updates the sidebar badge for that TodoList to the literal value `0` and the list remains usable without reload

- [ ] **S03 [OC03] [TI01,TI02] Deleting a completed Todo leaves the incomplete-count unchanged**
  - **Given** an authenticated user deletes a Todo that is already completed while the same TodoList still has other incomplete Todos
  - **When** the delete succeeds
  - **Then** the Todo row is removed but the sidebar incomplete-count for that TodoList does not decrement

- [ ] **S04 [OC03] [TI03] Delete failures preserve the current contract**
  - **Given** a delete request targets a missing Todo or a Todo owned by another user
  - **When** the request is processed
  - **Then** the route keeps the current `404` or `403` response semantics and does not emit a success-path sidebar count update

## Structural Criteria

- [ ] Successful Todo deletes keep the server as the single source of truth for sidebar incomplete-count values; no client-side count arithmetic is introduced.
- [ ] The existing delete confirmation flow and `swap: 'delete'` target contract still remove the Todo row while allowing HTMX to process any returned OOB fragment.
- [ ] Unauthorized and missing-Todo delete responses preserve their current bare `403` / `404` semantics.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py` delete success path, parent-list lookup, and post-delete incomplete-count recomputation
- `src/app/templates/partials/todo_deleted_oob.html` or an equivalent delete-response partial that carries the sidebar badge OOB markup
- `src/app/static/js/app.js` existing confirm-delete HTMX flow and its `swap: 'delete'` row-removal behavior
- `tests/test_todos.py` route coverage for delete success, unchanged-count, zero-count, and access-control semantics

### What We're NOT Doing

- List deletion or broader sidebar refresh behavior - BUG-001 is scoped to deleting a single Todo from an existing TodoList.
- Client-side sidebar count bookkeeping in JavaScript - the established pattern keeps this value server-rendered and OOB-swapped.
- Authentication, session, or generic error-response redesign - the existing educational auth model and delete error contracts stay as-is.
- Broad create/toggle/delete template consolidation - reuse is acceptable, but behavior parity matters more than refactoring partial structure.

## Architecture Decision

**Approach**: Successful owned `DELETE /api/todos/{todo_id}` responses continue to let HTMX remove `#todo-{id}` via `swap: 'delete'`, and also return a server-rendered OOB fragment that refreshes `#list-{list_id}-count` from database state after the delete commits.
**Why this over alternatives**: It matches the `toggle_todo` / `todo_item_with_oob.html` pattern already used in the app, avoids duplicating count logic in `app.js`, and keeps completed-versus-incomplete semantics anchored to the database instead of DOM math.

## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                              | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo            | Existing Todo mutation pattern that returns OOB count markup on success
file   | src/app/routes/todos.py#delete_todo            | Delete ownership checks and success/error contract to preserve while changing the success response
file   | src/app/routes/todos.py#_get_list_todo_count   | Server-side incomplete-count source of truth shared by Todo mutations
file   | src/app/templates/partials/todo_item_with_oob.html | Canonical OOB count span shape and DOM id contract used by toggle/create
file   | src/app/templates/partials/todo_deleted_oob.html   | Existing delete-specific OOB fragment already present in the repo
file   | src/app/static/js/app.js#confirmDeleteTodo     | Delete dialog flow feeding the HTMX DELETE request and `swap: 'delete'` behavior
file   | tests/test_todos.py#TestTodos.test_delete_todo | Existing delete coverage to extend with response-body and count assertions
file   | tests/conftest.py#authenticated_client         | Authenticated test harness for route-level delete scenarios
```

## Constraints & Gotchas

- **Constraint**: Todo delete is issued from `htmx.ajax('DELETE', ...)` with `target: #todo-{id}` and `swap: 'delete'` - successful responses must still be HTMX-processible HTML rather than an empty body or JSON.
- **Avoid**: Deriving the sidebar badge by decrementing DOM state in `app.js` - instead recompute the incomplete-count from the database after the delete commits and emit the OOB fragment from the server.
- **Critical**: Completed Todos and last-incomplete Todos both pass through the same delete path - cover both unchanged-count and literal-`0` outcomes so falsy assumptions do not regress the badge.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful Todo deletes emit the sidebar incomplete-count OOB fragment
  - Follow `src/app/routes/todos.py#toggle_todo`, `src/app/routes/todos.py#_get_list_todo_count`, and `src/app/templates/partials/todo_item_with_oob.html`; after deleting an owned Todo, recompute the parent TodoList incomplete-count and return HTMX-processible markup that targets `id="list-<list_id>-count"` with `hx-swap-oob="true"`
  - **Verify**: A route test deleting an incomplete Todo returns `200`, the response body contains `hx-swap-oob="true"` and `id="list-<list_id>-count"`, and the deleted Todo is gone from the database

- [ ] **TI02** Delete count semantics stay correct for completed and zero-remaining cases
  - Use the same server-side incomplete-count definition as create/toggle so deleting a completed Todo leaves the sidebar badge unchanged and deleting the final incomplete Todo renders the literal value `0`
  - **Verify**: Route coverage shows deleting a completed Todo leaves the sidebar badge value unchanged, and deleting the last incomplete Todo returns OOB markup whose badge text is exactly `0`

- [ ] **TI03** Delete failure contracts and in-place UX remain unchanged
  - Preserve `src/app/routes/todos.py#delete_todo` missing/ownership guards and the existing `src/app/static/js/app.js#confirmDeleteTodo` `swap: 'delete'` flow; only successful owned deletes should emit the OOB fragment
  - **Verify**: Route coverage keeps `403` for unauthorized delete and `404` for missing Todo, and browser validation through the existing delete dialog shows the Todo row disappears while the sidebar badge updates without a full page reload

### Testing Strategy


### Validation


### Execution Contract


## Final Validation Checklist


## Implementation Observations

_No observations recorded yet._
