# Fix Sidebar Incomplete Count After Todo Deletion

## Feature Overview and Goal

**Intent**: Keep the sidebar's TodoList state trustworthy after a Todo is deleted so users do not need a full-page reload to see the correct incomplete count.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo immediately decreases its TodoList's displayed incomplete count.
- [OC02] Every successful Todo deletion leaves the displayed incomplete count equal to the server's remaining incomplete Todo count, without a full-page reload.

## Required Context

- `docs/PRODUCT-BACKLOG.md#known-defects` – BUG-001 defines the defect, severity, and required delete-response OOB-swap behavior.
- `CLAUDE.md#the-stack-and-why-it-matters-for-edits` – preserve the HTMX-first HTML-partial and multi-region OOB-swap architecture.

## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – use the project's canonical Partial and OOB Swap terminology.

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Deleting one of two incomplete Todos removes its row and changes the sidebar incomplete count from 2 to 1 through an OOB Swap**
  - **Given** an authenticated User is viewing a TodoList containing two incomplete Todos and its sidebar count is `2`
  - **When** the User deletes either incomplete Todo
  - **Then** the deleted Todo row disappears and the response replaces that TodoList's sidebar count with `1` through an `hx-swap-oob` element, without a full-page reload
  - **Proof**: `tests/test_todos.py#TestTodos.test_delete_todo` – green – parity/regression for successful deletion persistence; the sidebar response behavior is not covered at spec time

- [x] **S02 [OC02] [TI01,TI02] Deleting a completed Todo preserves the sidebar incomplete count through an OOB Swap**
  - **Given** an authenticated User is viewing a TodoList containing one incomplete Todo and one completed Todo and its sidebar count is `1`
  - **When** the User deletes the completed Todo
  - **Then** the deleted Todo row disappears and the response replaces that TodoList's sidebar count with `1` through an `hx-swap-oob` element, without a full-page reload

- [x] **S03 [OC02] [TI01,TI02] A failed Todo deletion does not emit a misleading sidebar count replacement**
  - **Given** an authenticated User requests deletion of a Todo that does not exist or belongs to another User
  - **When** the delete request is rejected
  - **Then** the existing `404` or `403` response is preserved, no Todo is deleted, and no sidebar count OOB Swap is returned

## Structural Criteria

- [x] The Todo deletion endpoint continues to return an HTML-fragment response for successful HTMX requests; it does not introduce a JSON count contract or client-owned count calculation.
- [x] Existing Todo creation and completion-toggle OOB count behavior remains unchanged.

## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py` Todo deletion response and incomplete-count calculation seam
- `tests/test_todos.py` Todo deletion response and persistence coverage
- `tests/test_integration.py` OOB count synchronization regression coverage where cross-route parity belongs

### What We're NOT Doing

- TodoList deletion behavior -- BUG-001 concerns deleting an individual Todo.
- Todo creation or completion-toggle behavior -- these are existing parity patterns, not defective scope.
- Client-side count state or JavaScript arithmetic -- the server remains the source of truth.
- Styling or layout changes to the sidebar count -- the defect is state synchronization, not presentation.

## Architecture Decision

**Approach**: After a successful Todo deletion, derive the remaining incomplete count on the server and return the existing deletion OOB Partial for the affected TodoList.
**Why this over alternatives**: It matches the established create/toggle response pattern and keeps count ownership in the server-rendered HTMX flow.

## Code Patterns & External References

```
# type | path#anchor                                                | why needed (intent)
file   | src/app/routes/todos.py#_get_list_todo_count               | Canonical server-side incomplete-count query
file   | src/app/routes/todos.py#toggle_todo                         | Established post-mutation OOB response pattern
file   | src/app/routes/todos.py#delete_todo                         | Defective endpoint and ownership/error contract
file   | src/app/templates/partials/todo_deleted_oob.html            | Existing successful-delete count replacement Partial
file   | src/app/templates/partials/todo_item_with_oob.html          | Established OOB element shape for create/toggle responses
file   | tests/test_integration.py#TestUserJourneys.test_todo_completion_updates_count | Green OOB parity pattern
```

## Constraints & Gotchas

- **Critical**: HTMX `swap: 'delete'` removes the primary Todo row, but the response must still carry the separate `hx-swap-oob` count element so HTMX can reconcile the sidebar region.
- **Constraint**: Compute the count only after the deletion is committed, using `_get_list_todo_count`; deleting a completed Todo must not decrement the incomplete count.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Todo deletion response behavior has executable regression coverage
  - Extend the existing authenticated route fixtures and deletion patterns in `tests/test_todos.py#TestTodos.test_delete_todo`; use `tests/test_integration.py#TestUserJourneys.test_todo_completion_updates_count` only as the OOB assertion pattern.
  - **Verify**: Focused tests prove S01-S03, including the affected TodoList ID, exact remaining incomplete value, successful persistence, and unchanged `403`/`404` behavior.

- [x] **TI02** Successful Todo deletion reconciles the affected sidebar incomplete count from server state
  - Follow `src/app/routes/todos.py#toggle_todo` and reuse `src/app/templates/partials/todo_deleted_oob.html`; preserve `src/app/routes/todos.py#delete_todo` ownership and missing-Todo outcomes.
  - **Verify**: Successful responses are HTML containing the affected TodoList's `hx-swap-oob` count with the post-delete value, creation/toggle OOB regression tests remain green, and failed deletions contain no OOB count replacement.

## Implementation Observations

### Run: 2026-08-28T07:17:21Z – observations

#### NOTICED BUT NOT TOUCHING

- `tests/test_todos.py::TestTodos::test_create_todo` currently fails because creation leaves priority unset (BUG-003).
- `tests/test_todos.py::TestTodos::test_update_todo` currently fails because due-date persistence is broken (BUG-002).
