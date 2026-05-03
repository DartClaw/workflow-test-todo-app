# BUG-001 – Sidebar Incomplete Count Updates On Todo Delete

**Status**: Draft  
**Bug ID**: `BUG-001`  
**Date**: 2026-05-03

## Feature Overview and Goal

When a User deletes an incomplete Todo from an active TodoList, the sidebar count badge for that TodoList must refresh immediately in the same HTMX response. The existing delete flow removes the Todo row from the main content area, but it does not send the OOB Swap payload needed to update `list-{{ list.id }}-count`, so the sidebar remains stale until a full reload.

This fix stays inside the existing HTMX-first server-rendered pattern. It does not change the delete confirmation interaction, persistence model, or sidebar rendering model.

## Scenarios

### Scenario 1 – Deleting an incomplete Todo updates the sidebar count immediately

Given an authenticated User viewing a TodoList with two incomplete Todos  
When the User deletes one of those Todos from the current list view  
Then the deleted Todo row is removed from the page  
And the delete response includes an OOB Swap targeting that TodoList's sidebar count badge  
And the sidebar incomplete count decreases from `2` to `1` without a full page reload

### Scenario 2 – Deleting the last incomplete Todo shows zero in the sidebar badge

Given an authenticated User viewing a TodoList with exactly one incomplete Todo  
When the User deletes that Todo  
Then the delete response includes an OOB Swap for the same TodoList count badge  
And the sidebar badge renders `0` after the swap  
And the Todo no longer exists in persistence

### Scenario 3 – Deleting a completed Todo leaves the sidebar count unchanged but refreshed

Given an authenticated User viewing a TodoList with one completed Todo and two incomplete Todos  
When the User deletes the completed Todo  
Then the delete response still includes an OOB Swap targeting the sidebar count badge  
And the sidebar incomplete count remains `2`  
And the completed Todo is removed from persistence

### Scenario 4 – Unauthorized or missing Todo delete does not emit a misleading count update

Given a delete request for a Todo the current User does not own or that no longer exists  
When the server rejects the request  
Then the server does not return a success OOB count update payload  
And the sidebar count is not changed by that failed request

## Success Criteria

1. Successful `DELETE /api/todos/{todo_id}` responses return an HTML Partial that includes an OOB Swap for the matching TodoList sidebar count badge.
2. The OOB Swap count always reflects the post-delete number of incomplete Todos for that TodoList, including the `0` case.
3. The existing client-side delete interaction continues to remove the Todo row via HTMX `swap: 'delete'`; this bug fix does not require a new client-side flow.
4. A regression test proves the delete response now carries the correct OOB payload and that persistence still deletes the Todo.

## Required Context

<!-- source: docs/PRODUCT-BACKLOG.md:25 -->
<!-- extracted: 2026-05-03 -->
> Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

<!-- source: AGENTS.md:33-38 -->
<!-- extracted: 2026-05-03 -->
> Routes return HTML fragments, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM.
>
> Out-of-Band (OOB) swaps are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers.

## Deeper Context

- `AGENTS.md:152-155` – HTMX-first project rule and backlog-first handling for `BUG-*` work.
- `AGENTS.md:160-163` – visual validation workflow for multi-region updates and OOB swaps.
- `docs/UBIQUITOUS_LANGUAGE.md:24-26` – canonical definitions for `Partial`, `OOB Swap`, and `Error Partial`.
- `docs/specs/.technical-research.md` – companion analysis for current route, template, and test patterns.

## What We Are Not Doing

- Changing the delete confirmation dialog UX in `src/app/static/js/app.js`.
- Refactoring create/toggle OOB behavior into a new shared abstraction unless needed as a minimal implementation detail.
- Normalizing unrelated 403/404 delete error responses to HTML partials as part of this bug fix.

## Code Patterns and References

- `src/app/routes/todos.py:33-37` – `_get_list_todo_count` query to reuse for post-delete counts.
- `src/app/routes/todos.py:276-283` – `toggle_todo` success response pattern with `partials/todo_item_with_oob.html`.
- `src/app/routes/todos.py:286-306` – current `delete_todo` route to update.
- `src/app/templates/partials/todo_item_with_oob.html:1-4` – existing OOB count markup shape.
- `src/app/templates/partials/todo_deleted_oob.html:1-2` – existing delete-specific OOB count partial, currently unused.
- `src/app/templates/partials/todo_list_item.html:20` – sidebar badge id contract for the OOB target.
- `src/app/static/js/app.js:166-173` – HTMX delete request config using `target: #todo-{id}` and `swap: 'delete'`.
- `tests/test_todos.py:84-92` – current delete coverage to extend.
- `tests/conftest.py:71-113` – authenticated Todo/TodoList fixtures for regression coverage.

## Implementation Tasks

### Task 1 – Successful Todo delete returns the expected OOB count Partial

Outcome:
`DELETE /api/todos/{todo_id}` keeps the current ownership and persistence behavior, and on success returns an HTML Partial that updates the matching TodoList sidebar incomplete count via `hx-swap-oob="true"`.

Constraints:
- Preserve the existing client-side `swap: 'delete'` behavior for row removal.
- Use the existing TodoList count id contract.
- Keep the response HTMX-first and server-rendered.

Verify:
- Route-level test proves the success response body contains `hx-swap-oob="true"` and the correct `list-{id}-count` target.

### Task 2 – Post-delete count reflects incomplete Todos only

Outcome:
The OOB count rendered after delete matches the persisted number of incomplete Todos in that TodoList after deletion, including when the deleted Todo was completed and when the list reaches zero incomplete Todos.

Constraints:
- Follow the same incomplete-count semantics already used by create/toggle flows and sidebar rendering.
- Do not introduce a parallel count definition in JavaScript.

Verify:
- Automated test covers at least one incomplete-delete case and asserts the rendered count value.
- Implementation is coherent with the existing incomplete-count query used elsewhere in the Todo routes.

### Task 3 – Regression coverage locks the behavior in place

Outcome:
Test coverage fails if a future change removes the OOB payload from successful Todo deletes or renders the wrong count after deletion.

Constraints:
- Keep coverage focused on observable route behavior plus persistence.
- Use existing FastAPI test fixtures rather than browser-only validation for proof of work.

Verify:
- `uv run pytest tests/test_todos.py`

## Acceptance Notes

- Scenario 1 and Scenario 2 prove the primary behavior change.
- Scenario 3 can be covered either as a dedicated automated test or by demonstrating the chosen implementation computes incomplete counts independently of the deleted Todo's completion state.
- Scenario 4 is satisfied if failed delete responses remain non-success responses without the success OOB payload.

## Open Risks

- The delete route currently returns bare 403/404 responses instead of the HTML Error Partial described elsewhere in project guidance. This spec does not widen scope to normalize that inconsistency.
- Because the front-end uses `swap: 'delete'`, the server response must stay valid even though the primary target element is removed; the regression test should focus on the OOB payload rather than DOM behavior only.
