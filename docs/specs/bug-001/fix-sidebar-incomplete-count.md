# Fix Sidebar Incomplete Count After Todo Deletion

## Feature Overview and Goal

**Intent**: Keep the TodoList summary trustworthy after deletion so users can rely on the sidebar without reloading the page.

**Expected Outcomes**:

- [OC01] Deleting a Todo immediately leaves its TodoList sidebar count showing the current number of incomplete Todos through the existing HTMX interaction.
- [OC02] The fix preserves Todo deletion, ownership enforcement, and missing-Todo behavior.

## Required Context

- `docs/PRODUCT-BACKLOG.md#known-defects` – BUG-001 defines the defect, severity, and required OOB Swap behavior.
- `CLAUDE.md#the-stack--and-why-it-matters-for-edits` – follow the project's HTML Partial and OOB Swap response conventions.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – use the canonical Partial and OOB Swap terminology.

## Deeper Context

- `docs/STACK.md#frameworks--libraries` – consult only if framework or test-baseline details are needed during execution.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02] Deleting an incomplete Todo decrements its TodoList sidebar count without a page reload**
  - **Given** a TodoList has two incomplete Todos and its sidebar count shows `2`
  - **When** the user deletes one of those incomplete Todos
  - **Then** the Todo row disappears and an OOB Swap changes that TodoList's sidebar count to `1` in the same response

- [ ] **S02 [OC01] [TI01,TI02] Deleting a completed Todo preserves the current incomplete count without a page reload**
  - **Given** a TodoList has one incomplete Todo, one completed Todo, and its sidebar count shows `1`
  - **When** the user deletes the completed Todo
  - **Then** the Todo row disappears and an OOB Swap leaves that TodoList's sidebar count at `1` in the same response

- [ ] **S03 [OC02] [TI01,TI02] A missing or inaccessible Todo is not deleted and produces no sidebar count swap**
  - **Given** the authenticated User requests deletion of a Todo that does not exist or belongs to another User
  - **When** the deletion request is handled
  - **Then** the existing `404` or `403` response is preserved, no Todo is deleted, and no OOB Swap is returned

## Structural Criteria

- [ ] The deletion response remains an HTML response compatible with the existing HTMX target swap.
- [ ] Incomplete counts continue to come from persisted Todo state rather than client-maintained arithmetic.
- [ ] Existing Todo deletion and toggle-count behavior remains green.

## Scope & Boundaries

### Work Areas

- Todo deletion response in `src/app/routes/todos.py`
- Existing delete-specific OOB Partial in `src/app/templates/partials/todo_deleted_oob.html`
- Todo route and user-journey coverage in `tests/test_todos.py` and `tests/test_integration.py`

### What We're NOT Doing

- Changing Todo creation or completion-toggle count behavior – those flows already use the established OOB Swap pattern.
- Changing TodoList deletion or sidebar layout – BUG-001 is limited to Todo deletion count synchronization.
- Redesigning deletion confirmation or adding undo – no interaction redesign is required for this defect.
- Changing authentication or ownership rules – their current behavior is an explicit regression boundary.

## Architecture Decision

**Approach**: After a successful deletion is persisted, return the existing delete-specific HTML Partial with the TodoList ID and authoritative incomplete count so HTMX removes the primary target and applies the sidebar OOB Swap.
**Why this over alternatives**: It matches the working toggle flow and the repository's server-as-source-of-truth model without adding client-side count state.

## Code Patterns & External References

```
# type | path#anchor                                                   | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo                           | Working post-commit count query and OOB response pattern
file   | src/app/routes/todos.py#_get_list_todo_count                  | Authoritative incomplete-count calculation
file   | src/app/routes/todos.py#delete_todo                           | Defective route and preserved status/ownership behavior
file   | src/app/templates/partials/todo_deleted_oob.html              | Existing delete-specific OOB Partial contract
file   | src/app/templates/partials/todo_item_with_oob.html            | Working sidebar count element and OOB Swap marker pattern
file   | tests/test_todos.py#TestTodos.test_delete_todo                | Existing deletion persistence regression pattern
file   | tests/test_integration.py#TestUserJourneys.test_todo_completion_updates_count | Existing OOB count assertion pattern
```

## Constraints & Gotchas

- **Critical**: The count must be queried after the deletion commit so it reflects persisted state for both incomplete and completed Todo deletion.
- **Avoid**: Returning the OOB count element as ordinary target content – the response must retain `hx-swap-oob` so the Todo row's normal delete swap and sidebar update both occur.
- **Assumption**: The missing requested path is the intended standalone FIS destination, and the matching trusted-local BUG-001 backlog entry is the requirements source.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful Todo deletion synchronizes the affected TodoList's authoritative incomplete count in the same HTMX response
  - Follow `src/app/routes/todos.py#toggle_todo` and reuse `src/app/templates/partials/todo_deleted_oob.html`; preserve `src/app/routes/todos.py#delete_todo` ownership checks and failure responses.
  - **Verify**: S01 and S02 pass; S03 preserves `404` and `403` behavior without an OOB Swap; the response is HTML and the persisted Todo is deleted only on success.

- [ ] **TI02** Automated coverage distinguishes incomplete-Todo deletion, completed-Todo deletion, and rejected deletion
  - Extend the existing pytest fixtures and route/integration patterns; assertions must verify the affected count element's ID, `hx-swap-oob`, and rendered count rather than merely checking for generic response markup.
  - **Verify**: Tests fail against the pre-fix empty successful deletion response, pass after TI01, and the existing deletion and toggle-count tests remain green.

## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see the AndThen FIS Mutability Contract. Spec authors leave this section empty._

_No observations recorded yet._
