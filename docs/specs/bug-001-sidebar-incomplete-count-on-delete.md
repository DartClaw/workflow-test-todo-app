# BUG-001 – Sidebar Incomplete Count Stays In Sync After Todo Delete

## Feature Overview and Goal

**Intent**: Keep the sidebar’s incomplete-count badge accurate during todo deletion so users can trust list state without reloading the page.

**Expected Outcomes**

- [OC01] Deleting an incomplete `Todo` updates the active `TodoList` sidebar incomplete-count in the same HTMX response that removes the row.
- [OC02] Deleting a completed `Todo` removes the row but leaves the sidebar incomplete-count unchanged.
- [OC03] Todo-delete responses preserve the existing auth/not-found behavior and the current HTMX row-delete interaction.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `AGENTS.md` – "The stack — and why it matters for edits"
<!-- source: AGENTS.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

## Deeper Context

- `docs/STACK.md#frameworks--libraries` – Confirms the FastAPI + Jinja2 + HTMX server-rendered fragment stack this fix must stay inside.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical terms for `Partial`, `OOB Swap`, and `Error Partial`.
- `AGENTS.md#visual-validation-workflow` – Browser validation flow to confirm the OOB response updates the sidebar badge after deletion.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02,TI03] Incomplete todo deletion refreshes the sidebar count without reload**
  - **Given** a `TodoList` shows two incomplete `Todo` rows and the sidebar badge `id="list-<list_id>-count"` shows `2`
  - **When** the user confirms deletion for one incomplete `Todo`
  - **Then** the deleted row is removed, the response includes an OOB swap for the same sidebar badge, and the badge shows `1` without a full page reload

- [ ] **S02 [OC02] [TI01,TI02,TI03] Completed todo deletion leaves the incomplete count unchanged**
  - **Given** a `TodoList` contains one incomplete `Todo` and one completed `Todo`, and the sidebar badge shows `1`
  - **When** the user confirms deletion for the completed `Todo`
  - **Then** the completed row is removed and the sidebar badge still shows `1`

- [ ] **S03 [OC01] [TI01,TI02,TI03] Deleting the last incomplete todo drives the badge to zero**
  - **Given** a `TodoList` has exactly one incomplete `Todo` and the sidebar badge shows `1`
  - **When** the user confirms deletion for that `Todo`
  - **Then** the deleted row is removed and the OOB response updates the sidebar badge to `0`

- [ ] **S04 [OC03] [TI01,TI03] Unauthorized or missing todo deletes do not emit a success fragment**
  - **Given** the delete request targets a missing `Todo` or a `Todo` in another user’s `TodoList`
  - **When** `DELETE /api/todos/{todo_id}` is submitted
  - **Then** the route keeps returning `404` or `403`, does not return the success OOB count fragment, and does not broaden access

## Structural Criteria

- [ ] `delete_todo` still checks list ownership before any success response is returned.
- [ ] The delete-response OOB fragment targets the existing sidebar badge id contract: `list-{{ list.id }}-count`.
- [ ] Regression tests prove delete-count updates without weakening existing toggle-count coverage.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py` delete-route response and incomplete-count lookup
- `src/app/templates/partials/todo_deleted_oob.html` delete-specific OOB fragment contract
- `src/app/templates/partials/todo_list_item.html` sidebar badge id and count target surface
- `src/app/static/js/app.js` HTMX delete target and `swap: 'delete'` compatibility surface
- `tests/test_todos.py` and `tests/test_integration.py` delete-count regression coverage

### What We're NOT Doing

- List deletion behavior is unchanged – BUG-001 is limited to deleting a single `Todo`.
- Client-side count math is out of scope – the server remains the source of truth for sidebar counts.
- OOB partial consolidation is out of scope – reuse the existing delete-specific partial unless the current fix requires otherwise.
- Authentication/session behavior is unchanged – existing `403`/`404` handling must remain intact.

## Architecture Decision

**Approach**: `DELETE /api/todos/{todo_id}` computes the surviving list’s incomplete-count after commit and returns the delete-specific OOB partial while the existing HTMX `swap: 'delete'` interaction removes the targeted row.
**Why this over alternatives**: It matches the existing `toggle_todo`/`todo_item_with_oob.html` pattern and avoids duplicating count logic in client-side JavaScript.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor                                | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo       | Existing count-refresh pattern – reuse the same server-side count + OOB response shape
file   | src/app/routes/todos.py#delete_todo       | Delete route entry point – preserve auth/not-found behavior while adding the count fragment
file   | src/app/templates/partials/todo_item_with_oob.html | Existing combined row + sidebar OOB fragment pattern for toggle/create
file   | src/app/templates/partials/todo_deleted_oob.html   | Delete-specific OOB fragment – sidebar badge update without replacing row HTML
file   | src/app/templates/partials/todo_list_item.html     | Sidebar badge id contract – response OOB target must stay aligned
file   | src/app/static/js/app.js#confirmDeleteTodo         | Delete interaction contract – target remains `#todo-{id}` with `swap: 'delete'`
file   | tests/test_todos.py#TestTodos.test_delete_todo     | Current delete regression entry point – extend to prove OOB count behavior
file   | tests/test_integration.py#TestUserJourneys.test_todo_completion_updates_count | Existing OOB-count regression pattern – mirror for delete coverage
```

## Constraints & Gotchas

- **Constraint**: The delete flow already uses `htmx.ajax(..., { target: "#todo-{id}", swap: "delete" })` – the response must stay compatible with row deletion while still carrying `hx-swap-oob="true"` for the sidebar badge.
- **Avoid**: Hard-coding count decrements in JavaScript – recompute with the server-side incomplete-count query after commit so completed-todo deletes and zero-count edges stay correct.
- **Critical**: The sidebar badge target id is owned by `partials/todo_list_item.html` – the delete fragment must keep the exact `list-{{ list.id }}-count` contract or HTMX will silently miss the OOB update.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo-delete success responses carry the refreshed sidebar incomplete-count for the owning list
  - Follow `src/app/routes/todos.py#toggle_todo` for count lookup timing and OOB-response shape; keep `_verify_list_access` and existing `403`/`404` outcomes intact in `src/app/routes/todos.py#delete_todo`
  - **Verify**: `uv run pytest tests/test_todos.py -k delete_todo` proves `DELETE /api/todos/{id}` still deletes owned todos, still returns `403`/`404` for unauthorized or missing todos, and includes `hx-swap-oob="true"` only on the `200` success response

- [ ] **TI02** The delete OOB fragment targets the existing sidebar badge contract while the row-delete interaction still works
  - Keep `src/app/templates/partials/todo_deleted_oob.html` aligned with `src/app/templates/partials/todo_list_item.html`; preserve `src/app/static/js/app.js#confirmDeleteTodo` targeting `#todo-{id}` with `swap: 'delete'`
  - **Verify**: A delete success response contains `id="list-<list_id>-count"` and `hx-swap-oob="true"` and the browser still removes `#todo-<todo_id>` instead of replacing it with response HTML

- [ ] **TI03** Regression coverage proves the sidebar badge changes only when the deleted todo was incomplete
  - Extend `tests/test_todos.py` and `tests/test_integration.py` with incomplete, completed, and last-incomplete delete cases; keep `TestIntegration.test_todo_completion_updates_count` as the reference guard for the shared OOB-count pattern
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete_todo or todo_completion_updates_count"` passes with assertions that delete responses drive badge values from `2` to `1`, keep `1` after deleting a completed todo, and drive `1` to `0` when the last incomplete todo is deleted

### Testing Strategy

### Validation

### Execution Contract

## Final Validation Checklist

## Implementation Observations

_No observations recorded yet._
