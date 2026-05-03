# BUG-001 - Sidebar Incomplete Count Updates on Todo Delete

## Feature Overview and Goal

When a `User` deletes a `Todo` from an open `TodoList`, the sidebar incomplete-count badge for that same `TodoList` must update immediately in the same HTMX exchange, without a full page reload. The fix should follow the repository's existing OOB Swap pattern used by `toggle_todo()`, while preserving the current delete interaction that removes the targeted `Todo` row from the DOM.

## Scenarios

### Scenario 1 - Delete an incomplete Todo from the active list

Given an authenticated `User` viewing a `TodoList` whose sidebar badge shows `3`
When the user confirms deletion of one incomplete `Todo` in that `TodoList`
Then the deleted `Todo` row is removed
And the sidebar badge for that `TodoList` updates to `2` from the same delete response via OOB Swap
And the page does not perform a full reload

### Scenario 2 - Delete a completed Todo

Given an authenticated `User` viewing a `TodoList` whose sidebar badge shows `2`
And the selected `Todo` is already completed
When the user confirms deletion of that completed `Todo`
Then the deleted `Todo` row is removed
And the sidebar badge remains `2`
And the delete response still carries the authoritative sidebar count via OOB Swap

### Scenario 3 - Delete the final incomplete Todo

Given an authenticated `User` viewing a `TodoList` with exactly one incomplete `Todo`
When the user confirms deletion of that `Todo`
Then the deleted `Todo` row is removed
And the sidebar badge updates to `0` via OOB Swap
And the badge remains bound to the same `TodoList` count anchor in the sidebar

### Scenario 4 - Reject deletion for missing or unauthorized Todos

Given a delete request for a `Todo` that does not exist or does not belong to the current `User`
When the server handles the request
Then the response keeps the current failure status behavior for that case
And no sidebar count update is emitted for another `TodoList`

## Success Criteria

- `SC-1` Deleting an incomplete `Todo` updates the sidebar incomplete-count badge for the affected `TodoList` in the same HTMX response. Proof: Scenario 1.
- `SC-2` Deleting a completed `Todo` does not decrement the incomplete count, but the sidebar badge still reflects server truth immediately after deletion. Proof: Scenario 2.
- `SC-3` Deleting the final incomplete `Todo` renders a visible `0` count rather than leaving the previous badge value in place. Proof: Scenario 3.
- `SC-4` The existing delete interaction remains HTMX-first: the targeted `Todo` row is removed without full page reload, and missing/unauthorized delete behavior is preserved. Proof: Scenario 4 and Task 2 verification.
- `SC-5` Regression coverage proves the delete-count behavior in automated tests. Proof: Task 3 verification.

## Required Context

<!-- source: docs/PRODUCT-BACKLOG.md:25 -->
<!-- extracted: 2026-05-03 -->
> BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

<!-- source: CLAUDE.md:33-38 -->
<!-- extracted: 2026-05-03 -->
> Routes return HTML fragments, not JSON. The server is the source of truth for UI state. OOB swaps are a core idiom for multi-region updates.

## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md:18-23` defines `Partial`, `OOB Swap`, and `Error Partial`; use those terms as written.
- `CLAUDE.md:158-163` requires visual validation for interactions that update multiple DOM regions and explicitly calls out `hx-swap-oob` checks.
- `CLAUDE.md:88-89` states that ownership checks come first on `/api/todos/{id}` routes; this fix must preserve that contract.
- `README.md:17-26` keeps the repository in its educational FastAPI + HTMX context; this defect does not justify auth, persistence, or architecture changes.

## Research Companion

Implementation context lives in `docs/specs/.technical-research.md`. Read it together with this FIS before coding.

## Code Patterns & External References

- `src/app/routes/todos.py:243-283` - established server-side pattern for mutating a `Todo`, recomputing the incomplete count, and returning an HTML partial with an OOB badge update.
- `src/app/templates/partials/todo_item_with_oob.html:1-4` - composite partial used when a primary target update and sidebar count update happen in one response.
- `src/app/templates/partials/todo_deleted_oob.html:1-2` - existing delete-specific OOB partial aligned to the delete flow.
- `src/app/static/js/app.js:166-173` - current client contract for deleting a `Todo`: HTMX target is `#todo-{id}` and swap mode is `delete`.
- `src/app/templates/partials/todo_list_item.html:20` - sidebar badge DOM anchor that the OOB update must target.
- `tests/test_integration.py:163-179` - existing OOB-count proof pattern for `toggle_todo()`.
- `tests/conftest.py:29-76` - authenticated test setup and in-memory SQLite harness for focused regression tests.

## Tasks

### Task 1 - Delete responses keep sidebar count authoritative

Done when:
- Deleting an owned `Todo` returns an HTML fragment that includes the current incomplete-count value for that `TodoList` as an OOB update in the same response.
- The returned count matches persisted server state after the delete commit.

Follow pattern:
- `src/app/routes/todos.py:243-283`
- `src/app/templates/partials/todo_deleted_oob.html:1-2`

Verify:
- `uv run pytest tests/test_todos.py::TestTodos::test_delete_todo`
- `uv run pytest tests/test_integration.py -k "delete and count"`

### Task 2 - Todo row removal behavior stays intact

Done when:
- The existing delete confirmation flow still removes the targeted `Todo` row through the current HTMX delete swap behavior.
- The sidebar badge updates in the same exchange without requiring a full page reload.

Follow pattern:
- `src/app/static/js/app.js:166-173`
- `src/app/templates/partials/todo_deleted_oob.html:1-2`

Verify:
- `./run.sh`
- In the browser, sign in as `demo@example.com` / `demo123`, delete one incomplete `Todo`, then delete one completed `Todo`; confirm row removal plus immediate sidebar badge refresh in both cases.

### Task 3 - Regression coverage proves count-changing and count-preserving paths

Done when:
- Automated tests assert the delete response contains an OOB marker targeting the sidebar badge.
- Tests prove the count decrements for incomplete `Todo` deletion, remains unchanged for completed `Todo` deletion, and reaches `0` for the final incomplete `Todo`.

Follow pattern:
- `tests/test_todos.py:84-92`
- `tests/test_integration.py:163-179`

Verify:
- `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count"`

## Assumptions

- This defect remains scoped to `Todo` deletion only; list deletion behavior is unchanged.
- Current `403`/`404` behavior for delete routes remains unchanged for this spec.
- The existing delete-specific OOB partial is the conservative fit for this flow; no new client-side delete mechanism is needed.

## What We're Not Doing

- Refactoring the shared delete confirmation dialog or the broader HTMX event wiring.
- Normalizing delete-route failure responses to use `partials/error.html`.
- Changing `TodoList` count rendering outside the delete path.

## NOTICED BUT NOT TOUCHING

- `src/app/templates/partials/todo_deleted_oob.html` already exists but is not wired into `delete_todo()` today. This FIS uses that existing artifact rather than introducing a new partial.

## Implementation Observations

_This section records implementation observations and non-blocking notes.

### Run: 2026-05-03 12:29 UTC — observations

#### NOTICED BUT NOT TOUCHING
- Pre-existing failures in tests/test_todos.py::test_create_todo and ::test_update_todo are existing defects and not introduced by this FIS.
- Multiple high-priority findings reported by dartclaw-review are pre-existing defects outside BUG-001 scope.
