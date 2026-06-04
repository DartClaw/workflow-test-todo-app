# BUG-001 – Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal

**Intent**: Keep the sidebar's incomplete-count badge synchronized when a Todo is deleted so the HTMX UI stays trustworthy without requiring a full page reload.

**Expected Outcomes**

- [OC01] Successful todo deletion keeps the active Todo list and the sidebar incomplete-count badge synchronized in the same HTMX interaction.
- [OC02] The sidebar badge continues to count only incomplete Todos, so deleting a completed Todo leaves the badge value unchanged.
- [OC03] Failed delete requests preserve the current list state and do not emit misleading sidebar count updates.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

### From `AGENTS.md` – "Architecture"
<!-- source: AGENTS.md#architecture -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02] Incomplete todo deletion updates the sidebar badge immediately**
  - **Given** an authenticated User is viewing a TodoList whose sidebar badge and visible Todo list both reflect one incomplete Todo
  - **When** the User confirms deletion of that incomplete Todo
  - **Then** the Todo row is removed and the same delete response applies an OOB Swap that replaces `#list-<TodoList.id>-count` with `0` without a full page reload

- [ ] **S02 [OC01,OC02] [TI01,TI02] Completed todo deletion leaves the incomplete badge unchanged**
  - **Given** an authenticated User is viewing a TodoList with a visible sidebar badge count and the Todo being deleted is already completed
  - **When** the User confirms deletion of that completed Todo
  - **Then** the Todo row is removed and the delete response preserves the existing value rendered into `#list-<TodoList.id>-count`

- [ ] **S03 [OC03] [TI01,TI03] Unauthorized delete keeps the sidebar unchanged**
  - **Given** User A is authenticated and a Todo belongs to User B's TodoList
  - **When** User A sends `DELETE /api/todos/{todo_id}`
  - **Then** the route keeps the current forbidden behavior and does not return an OOB fragment that could mutate User A's sidebar badge

- [ ] **S04 [OC03] [TI01,TI03] Missing-todo delete returns no count mutation**
  - **Given** an authenticated User sends `DELETE /api/todos/{todo_id}` for a Todo that does not exist
  - **When** the request is processed
  - **Then** the route keeps the current `404` behavior and does not return an OOB fragment that could desynchronize the visible sidebar

## Structural Criteria

- [ ] Successful delete stays on the existing HTMX fragment path: no new full-page reload, redirect, or JSON response is introduced for the happy path.
- [ ] Sidebar badge updates keep using the established `id="list-<TodoList.id>-count"` contract already shared by create and toggle responses.
- [ ] Regression coverage proves delete-count synchronization for incomplete, completed, and failing delete cases.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py` delete route behavior and post-delete count recomputation
- `src/app/templates/partials/todo_deleted_oob.html` delete-specific OOB response fragment
- `src/app/templates/partials/todo_list_item.html` canonical sidebar badge target contract
- `tests/test_todos.py` delete-route regression coverage for sidebar count synchronization

### What We're NOT Doing

- Reworking the delete confirmation flow in `src/app/static/js/app.js` unless the current HTMX `swap: 'delete'` contract proves incompatible with OOB processing.
- Changing create or toggle count-update behavior, because BUG-001 is limited to the delete path.
- Introducing JSON responses or client-side count bookkeeping, because this app's UI contract is server-rendered HTMX partials.
- Altering delete authorization or missing-resource semantics beyond preserving their current `403` and `404` outcomes.

## Architecture Decision

**Approach**: Make successful `DELETE /api/todos/{todo_id}` responses mirror the existing HTMX OOB pattern by recomputing the TodoList's incomplete count after commit and returning a small HTML partial that targets `#list-<TodoList.id>-count`.
**Why this over alternatives**: It reuses the app's server-rendered fragment contract and avoids duplicating count logic in browser JavaScript.

## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                        | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo      | Existing post-mutation count recompute + OOB response pattern
file   | src/app/routes/todos.py#delete_todo      | Delete path whose success response must adopt the same count-sync contract
file   | src/app/templates/partials/todo_item_with_oob.html | Existing OOB badge fragment shape used by create/toggle responses
file   | src/app/templates/partials/todo_deleted_oob.html   | Delete-specific OOB fragment already present in the repo and available for reuse
file   | src/app/templates/partials/todo_list_item.html     | Canonical sidebar badge id contract: `list-{{ list.id }}-count`
file   | src/app/static/js/app.js#confirmDeleteTodo | HTMX `DELETE` invocation that already removes the row; count sync must layer on without changing that contract
```

## Constraints & Gotchas

- **Constraint**: Todo routes return HTML fragments for successful HTMX mutations, not JSON. -- Workaround: successful delete must answer with a partial-compatible response and keep failing paths on their current simple response behavior.
- **Avoid**: Recomputing the badge from browser DOM state. -- Instead: reuse the server-side incomplete-count query after the delete commit so completed-vs-incomplete semantics stay centralized.
- **Critical**: The OOB fragment must target the existing sidebar badge id `list-<TodoList.id>-count`. -- Must handle by returning that same id on successful delete while preserving the current row `swap: 'delete'` flow.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful todo deletion returns a count-synchronizing HTML response
  - Follow `src/app/routes/todos.py#toggle_todo` for the post-mutation count recompute pattern and `src/app/routes/todos.py#delete_todo` for the current guard-path order; emit the OOB fragment only after a committed delete.
  - **Verify**: With `./run.sh`, log in as `demo@example.com` / `demo123`, delete an incomplete Todo from a list with a visible sidebar badge, and confirm the row disappears and the sidebar badge decrements in the same interaction without a full page reload.

- [ ] **TI02** Delete-side OOB fragment uses the shared sidebar badge contract
  - Reuse `src/app/templates/partials/todo_deleted_oob.html` and the `id="list-{{ list.id }}-count"` contract from `src/app/templates/partials/todo_list_item.html`; do not add a second badge target shape or client-side count math.
  - **Verify**: `uv run pytest tests/test_todos.py -k "toggle_todo_complete or delete_todo"` passes with assertions that successful delete responses contain `hx-swap-oob="true"` and target the same `list-<list_id>-count` contract used by toggle responses.

- [ ] **TI03** Delete regression coverage proves count sync and guard paths
  - Extend `tests/test_todos.py` from the current delete happy-path check to cover completed-todo deletion plus at least one failing delete path, following the existing access-control patterns in `tests/test_todos.py#TestTodoAccess`.
  - **Verify**: `uv run pytest tests/test_todos.py -k "delete_todo or cannot_modify_other_users_todo"` passes with assertions that completed-todo deletion leaves the badge value unchanged and failing delete responses do not contain `hx-swap-oob`.

### Testing Strategy


### Validation


### Execution Contract


## Final Validation Checklist


## Implementation Observations

_No observations recorded yet._
