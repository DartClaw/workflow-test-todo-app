# Fix Sidebar Incomplete Count After Todo Deletion

## Feature Overview and Goal

**Intent**: Keep the sidebar's incomplete Todo count trustworthy immediately after a Todo is deleted, without requiring a full page reload.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo immediately decreases its TodoList's sidebar incomplete-count by one.
- [OC02] Deleting a completed Todo leaves the sidebar incomplete-count unchanged and accurate.
- [OC03] Todo deletion retains its existing persistence, ownership, and missing-resource behavior.

## Required Context

- `docs/PRODUCT-BACKLOG.md#known-defects` – BUG-001 defines the defect, severity, and required HTMX OOB Swap mechanism.
- `CLAUDE.md#the-stack--and-why-it-matters-for-edits` – deletion responses must remain server-rendered HTML fragments and use an OOB Swap for secondary-region updates.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – use the project's canonical Partial and OOB Swap terminology.
- `src/app/routes/todos.py#delete_todo` – current deletion, ownership, and transaction boundary that this FIS changes.

## Deeper Context

- `src/app/routes/todos.py#toggle_todo` – established route pattern for computing the committed incomplete count and returning an OOB-enabled Partial.
- `src/app/templates/partials/todo_deleted_oob.html` – existing delete-response Partial with the sidebar count target and `hx-swap-oob` marker.
- `tests/test_integration.py#TestUserJourneys.test_todo_completion_updates_count` – parity proof that toggle responses already carry an OOB Swap.

## Acceptance Scenarios

- [ ] **S01 [OC01,OC03] [TI01,TI02] Deleting one incomplete Todo persists the deletion and returns its TodoList's decremented incomplete count as an OOB Swap**
  - **Given** an authenticated User owns a TodoList containing two incomplete Todos and its sidebar count is 2
  - **When** the User deletes either incomplete Todo
  - **Then** the response is successful, the Todo no longer exists, and the response contains an OOB Swap targeting that TodoList's count with value 1

- [ ] **S02 [OC02,OC03] [TI01,TI02] Deleting a completed Todo persists the deletion and returns the unchanged incomplete count as an OOB Swap**
  - **Given** an authenticated User owns a TodoList containing one incomplete Todo and one completed Todo and its sidebar count is 1
  - **When** the User deletes the completed Todo
  - **Then** the response is successful, the completed Todo no longer exists, and the response contains an OOB Swap targeting that TodoList's count with value 1

- [ ] **S03 [OC03] [TI01] Missing and unauthorized Todo deletions retain their existing status behavior without exposing a sidebar count**
  - **Given** an authenticated User requests deletion of either a nonexistent Todo or a Todo in another User's TodoList
  - **When** the delete route evaluates the request
  - **Then** it returns the existing 404 or 403 status respectively, does not delete the Todo, and does not return an OOB count fragment

## Structural Criteria

- [ ] The delete response reuses the existing `todo_deleted_oob.html` Partial and `_get_list_todo_count` helper rather than introducing duplicate count or fragment logic.
- [ ] Existing Todo route and integration tests remain green alongside the BUG-001 regression coverage.

## Scope & Boundaries

### Work Areas

- Todo delete-route response and committed incomplete-count calculation in `src/app/routes/todos.py`.
- Existing delete OOB Partial in `src/app/templates/partials/todo_deleted_oob.html` as the response contract.
- Todo route or integration regression coverage under `tests/`.

### What We're NOT Doing

- Changing toggle or create behavior – those routes already implement the expected OOB count pattern.
- Changing TodoList deletion behavior – BUG-001 concerns deletion of a Todo within an existing TodoList.
- Changing sidebar markup, styling, or count semantics – the existing count target and incomplete-only definition remain authoritative.
- Refactoring authentication or ownership checks – their intentionally simple implementation and current response statuses are preserved.

## Architecture Decision

**Approach**: After the authorized deletion is committed, return the existing delete-specific Partial with the TodoList identifier and freshly queried incomplete count.
**Why this over alternatives**: It matches the established HTMX server-as-source-of-truth pattern and updates the primary deletion target plus sidebar region in one response without client-side state.

## Code Patterns & External References

```text
# type | path#anchor                                          | why needed (intent)
file   | src/app/routes/todos.py#_get_list_todo_count         | Canonical incomplete-count query
file   | src/app/routes/todos.py#toggle_todo                  | OOB response pattern after a committed state change
file   | src/app/templates/partials/todo_deleted_oob.html     | Existing delete-specific OOB count response
file   | tests/test_todos.py#TestTodos.test_delete_todo       | Existing persistence regression pattern
```

## Constraints & Gotchas

- **Critical**: The count must be queried after the deletion commit so the returned value reflects persisted server state.
- **Avoid**: Returning JSON or adding client-side count arithmetic – return the existing server-rendered OOB Partial.
- **Assumption**: The missing input path is the requested destination, and BUG-001 in the local backlog is the authoritative requirements source.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo deletion regression coverage proves incomplete, completed, missing, and unauthorized count behavior
  - Extend the existing authenticated route/integration test patterns in `tests/test_todos.py#TestTodos.test_delete_todo` and preserve current persistence/status assertions.
  - **Verify**: Tests demonstrate S01–S03, including exact TodoList count target/value and absence of an OOB fragment on 403/404 responses.

- [ ] **TI02** Successful Todo deletion responses carry the committed TodoList incomplete count through the established OOB Partial
  - Follow `src/app/routes/todos.py#toggle_todo`; reuse `_get_list_todo_count` and `src/app/templates/partials/todo_deleted_oob.html` after the deletion commit.
  - **Verify**: The focused BUG-001 tests prove S01 and S02, and the existing `TestTodos.test_delete_todo` persistence assertion remains green.

## Implementation Observations

_No observations recorded yet._
