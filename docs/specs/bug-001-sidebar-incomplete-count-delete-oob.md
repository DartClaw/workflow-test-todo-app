# BUG-001 - Sidebar Incomplete Count Updates On Todo Delete

## Feature Overview and Goal
BUG-001 closes the gap between todo completion and todo deletion so the sidebar incomplete-count badge stays correct after a successful todo delete. The fix must follow the codebase's existing HTMX out-of-band swap pattern and preserve the current delete confirmation flow.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, test surface)_

## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

### From `AGENTS.md` - "The stack - and why it matters for edits"
<!-- source: AGENTS.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

## Deeper Context

- `AGENTS.md#visual-validation-workflow` - browser validation steps, including the requirement to verify both the primary delete target and any `hx-swap-oob` region after interaction changes.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` - canonical definitions for `Partial`, `OOB Swap`, and `Error Partial` used in this spec.

## Success Criteria (Must Be TRUE)

- [ ] Deleting an incomplete `Todo` updates `#list-{list_id}-count` in the same HTMX interaction that removes `#todo-{todo_id}`, with no full page reload.
- [ ] Deleting a completed `Todo` or the last remaining incomplete `Todo` keeps the sidebar badge correct by recomputing the post-delete incomplete count, including rendering `0` when appropriate.
- [ ] Successful todo delete stays aligned with the app's HTML-partial/OOB conventions and preserves current not-found / unauthorized behavior instead of introducing JSON or client-side count math.

### Health Metrics (Must NOT Regress)

- [ ] `uv run pytest tests/test_todos.py tests/test_integration.py` stays green after the change.
- [ ] The existing `toggle_todo` OOB badge update continues to work unchanged.
- [ ] The current delete confirmation flow still removes the targeted todo row without a redirect or full sidebar refresh.

## Scenarios

### Delete Incomplete Todo Updates Sidebar Immediately

- **Given** the active `TodoList` shows `#list-{list_id}-count` for at least one incomplete `Todo`
- **When** the user confirms delete for `/api/todos/{todo_id}`
- **Then** `#todo-{todo_id}` is removed and the same response includes an OOB update that decrements `#list-{list_id}-count` without a full page reload

### Delete Last Incomplete Todo Renders Zero

- **Given** the active `TodoList` has exactly one incomplete `Todo` remaining
- **When** that `Todo` is deleted
- **Then** the sidebar badge is re-rendered as `0` in the same HTMX interaction instead of waiting for a page reload

### Delete Completed Todo Leaves Incomplete Count Unchanged

- **Given** a completed `Todo` exists in the active `TodoList` and the sidebar badge already reflects only incomplete todos
- **When** the user deletes that completed `Todo`
- **Then** the todo row disappears and the OOB badge update keeps `#list-{list_id}-count` at the same value

### Delete Rejection Does Not Emit A Success OOB Update

- **Given** the delete request targets a missing `Todo` id or a `Todo` not owned by the current `User`
- **When** `/api/todos/{todo_id}` handles the request
- **Then** the route keeps the existing `404` / `403` rejection behavior and does not return a successful sidebar count update fragment

## Scope & Boundaries

### In Scope

- Successful todo delete returns an HTMX-compatible HTML response that updates the sidebar incomplete-count badge via OOB markup.
- The post-delete incomplete count is correct for incomplete, completed, and last-incomplete delete cases.
- Regression coverage proves the OOB response contract and preserves rejection-path behavior for missing and unauthorized deletes.

### What We're NOT Doing

- Recomputing sidebar counts in JavaScript - server-rendered HTMX partials are the established architecture.
- Redesigning the delete confirmation dialog or changing its copy - BUG-001 is about synchronization, not UX copy.
- Reloading the full page or re-rendering the full sidebar after delete - that would bypass the documented OOB-swap pattern.
- Changing auth/session behavior or other defect areas in `todos.py` - those are out of scope for this targeted bug fix.

### Agent Decision Authority

- **Autonomous**: keep the current `403` / `404` behavior, reuse the existing count helper and delete partial, and make the smallest HTMX-compatible adjustment needed if browser validation shows the current `swap: 'delete'` contract suppresses OOB processing.
- **Escalate**: any approach that would require a full page reload, a full sidebar refresh, or client-side count calculation to make the badge update.

## Architecture Decision

**We will**: mirror `toggle_todo`'s server-rendered OOB swap pattern for successful todo deletes, using the existing delete-specific partial and the current incomplete-count helper, over client-side count recomputation or a broader sidebar reload - this stays aligned with the app's HTMX-first server-truth architecture.

## Technical Overview

### UI/UX Design

The delete confirmation dialog and row-removal behavior stay as they are today. The only user-visible change is that the sidebar incomplete-count badge updates immediately after a successful todo delete, including the `0` state.

### Data Models

No schema or model changes are needed. The sidebar badge remains derived from incomplete `Todo` rows associated with the deleted todo's owning `TodoList`.

### Integration Points

The successful `DELETE /api/todos/{todo_id}` path must become an HTML-partial response that HTMX can process for both the targeted row removal and the OOB badge update. Authorization and not-found branches retain their current status-code contract.

## Code Patterns & External References

> Code-pattern pointers only. Upstream intent documents are covered in `Required Context` / `Deeper Context`.

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:33-37                 | Existing incomplete-count helper to reuse for delete responses
file   | src/app/routes/todos.py:243-283               | Reference OOB response pattern from toggle_todo
file   | src/app/routes/todos.py:286-306               | Current delete route gap to close
file   | src/app/templates/partials/todo_deleted_oob.html:1-2 | Existing delete-specific OOB fragment already available
file   | src/app/templates/partials/todo_list_item.html:20     | Sidebar badge DOM contract to preserve
file   | src/app/static/js/app.js:166-173              | Current HTMX delete confirmation and target/swap contract
file   | tests/test_integration.py:163-179             | Existing OOB regression-test pattern for count updates
```

## Constraints & Gotchas

- **Constraint**: the current delete flow uses `htmx.ajax('DELETE', ...)` with `swap: 'delete'` against `#todo-{id}` - Workaround: the successful response must remain compatible with row removal while still allowing the OOB badge fragment to be processed.
- **Avoid**: returning a bare `200` on successful todo delete - Instead: return an HTML partial containing the updated `id="list-{list_id}-count"` OOB fragment.
- **Critical**: the sidebar badge counts incomplete todos only - Must handle by: recomputing from `_get_list_todo_count()` after delete so completed-todo deletes keep the badge unchanged.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful todo delete returns the post-delete incomplete count as an HTMX OOB update
  - Reuse `_get_list_todo_count()` and the `toggle_todo` response pattern at `src/app/routes/todos.py:33-37` and `src/app/routes/todos.py:243-283`; render `src/app/templates/partials/todo_deleted_oob.html:1-2` for successful deletes while keeping current `403` / `404` branches.
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodos::test_delete_todo_includes_oob_count_update` proves a successful delete returns `200` HTML containing `hx-swap-oob` and `id="list-{list_id}-count"` with the decremented incomplete count, and the deleted `Todo` no longer exists in the database.

- [ ] **TI02** Todo delete keeps sidebar counts correct for zero-count and completed-todo boundaries
  - Stay compatible with `src/app/static/js/app.js:166-173` and the sidebar badge contract at `src/app/templates/partials/todo_list_item.html:20`; if TI01's server response is not enough for HTMX to process the OOB fragment, make the smallest client adjustment that preserves targeted row removal.
  - **Verify**: `uv run pytest tests/test_integration.py::TestUserJourneys::test_delete_incomplete_todo_updates_count tests/test_integration.py::TestUserJourneys::test_delete_completed_todo_keeps_count` proves deleting the last incomplete todo renders `0`, and deleting a completed todo keeps the badge value unchanged.

- [ ] **TI03** Regression coverage preserves rejection-path behavior and the reference OOB contract
  - Extend the current delete/toggle coverage at `tests/test_todos.py:64-92`, `tests/test_integration.py:163-179`, and fixture setup at `tests/conftest.py:71-113`; missing or unauthorized deletes must not masquerade as successful count updates.
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodoAccess::test_cannot_delete_other_users_todo tests/test_todos.py::TestTodos::test_delete_missing_todo_returns_404` proves rejection responses keep `403` / `404` behavior and do not include `hx-swap-oob`.

### Testing Strategy

- [TI01] Scenario: Delete Incomplete Todo Updates Sidebar Immediately -> route test asserts the delete response includes `hx-swap-oob`, the correct `list-{id}-count` target, and a decremented badge value.
- [TI02] Scenario: Delete Last Incomplete Todo Renders Zero -> integration test deletes the final incomplete todo and asserts the returned badge value is `0`.
- [TI02] Scenario: Delete Completed Todo Leaves Incomplete Count Unchanged -> integration test deletes a completed todo and asserts the badge value is unchanged.
- [TI03] Scenario: Delete Rejection Does Not Emit A Success OOB Update -> access and not-found tests assert `403` / `404` responses with no success OOB fragment.

### Validation

- Run `./run.sh`, log in with `demo@example.com` / `demo123`, delete one incomplete todo and one completed todo, and verify both the row removal and the `#list-{list_id}-count` OOB update happen without a full page reload.

### Execution Contract

- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (`hx-swap-oob`, `id="list-{list_id}-count"`, `403`, `404`) are exact and must be preserved verbatim.
- Proactively use sub-agents for non-coding needs where available; keep the change surgical and centered on BUG-001.
- After all tasks: run the relevant project validation gates and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion - do not batch.

## Final Validation Checklist

- [ ] **All success criteria** met
- [ ] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements

## Implementation Observations

_No observations recorded yet._
