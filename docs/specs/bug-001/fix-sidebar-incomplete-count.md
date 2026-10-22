# Fix sidebar incomplete-count on todo deletion

## Feature Overview and Goal

**Intent**: Close BUG-001 — the sidebar incomplete-count is not updated when a todo is deleted; the delete response must refresh the same count via the existing HTMX out-of-band swap pattern.

## Acceptance Scenarios

- When a todo is deleted, the sidebar incomplete-count decreases via an out-of-band swap, mirroring how toggle_todo updates it.

## Implementation Plan

- Update the delete_todo handler to return the same out-of-band count fragment that toggle_todo returns.

## Implementation Observations

- ASSUMPTION: no `**Plan**:`/`**Story-ID**:` header and no `plan.json` sit beside this FIS – ran it as a standalone direct story with no plan row to update. If a plan is added later for this FIS, backfill its story row from this commit's trailers.
- ASSUMPTION: read the Acceptance Scenario, not the Implementation Plan prose, as authoritative for "the same out-of-band count fragment" – see the DRIFT line below for the reasoning. If the literal full-item re-render matters for a reason not visible in the code, switch to it instead.
- NOTICED BUT NOT TOUCHING: `uv run pytest` has 2 pre-existing failures unrelated to this change – `test_create_todo` (BUG-003: no default priority) and `test_update_todo` (BUG-002: due date not persisted). Confirmed present on `main` before this diff; out of this story's scope.
- NOTICED BUT NOT TOUCHING: the OOB swap was not click-tested in a real browser – this sandbox blocks network access to `localhost` even with the sandbox override, so `./run.sh` could not be started here. Verified instead via an HTTP-level regression test (`tests/test_todos.py::test_delete_todo_updates_sidebar_count_via_oob_swap`) asserting the response body, plus HTMX's documented OOB-processing behavior (OOB fragments apply independent of the main `swap` mode, matching the existing `toggle_todo`/`create_todo` pattern). Someone with browser access should run the project's Visual Validation Workflow step 4 against this change.

#### DRIFT

- spec-stale: Implementation Plan said to reuse the same fragment `toggle_todo` returns (`todo_item_with_oob.html`, which re-renders the full todo item); re-rendering a deleted item makes no sense since `swap:'delete'` already removes it from the DOM and the ORM row is gone after `commit()`. Used the pre-existing, previously-unwired `partials/todo_deleted_oob.html` partial instead – it produces the identical `<span id="list-{id}-count" hx-swap-oob="true">` fragment the Acceptance Scenario requires. | Stale targets: this FIS's Implementation Plan | –
