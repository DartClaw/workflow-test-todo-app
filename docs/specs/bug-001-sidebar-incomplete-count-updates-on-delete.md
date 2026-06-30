# BUG-001 – Sidebar Incomplete Count Updates On Todo Delete

## Feature Overview and Goal

**Intent**: Keep the sidebar TodoList badge truthful during HTMX delete flows so users do not need a full page reload to see the current incomplete Todo count.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo immediately refreshes the owning TodoList sidebar count in the same HTMX interaction.
- [OC02] Delete-driven count refresh continues to represent incomplete Todos only, including zero-count and completed-Todo cases.
- [OC03] The existing HTMX delete interaction still removes the targeted Todo row without changing unrelated TodoList badges.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – "The stack – and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### From `CLAUDE.md` – "Visual Validation Workflow"
<!-- source: CLAUDE.md#visual-validation-workflow -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> 4. When altering interactions that update multiple DOM regions (counts, sidebar, row), verify the OOB swap still fires – check both the primary target and any region marked with `hx-swap-oob`.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "UI / HTMX Concepts"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | OOB Swap | Out-of-Band HTMX swap — updates a region outside the main target in one response | side-update, secondary update | Web |


## Deeper Context

- `src/app/routes/todos.py#toggle_todo` – existing count-refresh pattern after a Todo state change; delete should mirror this server-side contract.
- `src/app/routes/todos.py#delete_todo` – current delete path verifies ownership, deletes, then returns a bare `200` with no sidebar update.
- `src/app/templates/partials/todo_item_with_oob.html` – composite response shape combining the primary Todo swap with the sidebar OOB badge update.
- `src/app/templates/partials/todo_deleted_oob.html` – delete-specific sidebar badge partial already present; align its usage and markup with the sidebar badge contract.
- `src/app/templates/partials/todo_list_item.html` – source of truth for the sidebar badge id format: `list-{{ list.id }}-count`.
- `src/app/static/js/app.js#confirmDeleteTodo` – client delete requests target `#todo-{id}` with `swap: delete`; the fix must preserve that interaction without JS-side recounting.


## Acceptance Scenarios

- [x] **S01 [OC01,OC03] [TI01,TI02] Incomplete Todo deletion decrements the owning sidebar badge without a page reload**
  - **Given** an authenticated user is viewing a TodoList with multiple incomplete Todos and the sidebar badge shows that list's current incomplete count
  - **When** the user confirms deletion for one incomplete Todo from that list
  - **Then** the deleted Todo row is removed by the existing HTMX delete flow and the response also updates `list-<todo_list_id>-count` to the decremented value via `hx-swap-oob`

- [x] **S02 [OC01,OC02] [TI01,TI02] Deleting the last incomplete Todo renders a zero badge**
  - **Given** a TodoList has exactly one incomplete Todo remaining and its sidebar badge shows `1`
  - **When** the user deletes that Todo
  - **Then** the response updates `list-<todo_list_id>-count` to `0` via the delete response's OOB fragment and no full page reload is required

- [x] **S03 [OC02,OC03] [TI01,TI03] Completed Todo deletion leaves the incomplete badge unchanged**
  - **Given** a TodoList contains at least one completed Todo and at least one other incomplete Todo, and the sidebar badge reflects only the incomplete Todos
  - **When** the user deletes a completed Todo from that list
  - **Then** the deleted Todo row is removed and the sidebar badge value stays the same because completed Todos do not contribute to the incomplete count

- [x] **S04 [OC03] [TI01,TI03] Delete responses do not retarget unrelated TodoList badges**
  - **Given** the authenticated user owns two TodoLists with different incomplete counts visible in the sidebar
  - **When** the user deletes a Todo from the first TodoList
  - **Then** only the first list's `list-<id>-count` badge changes and the second list's badge remains untouched


## Structural Criteria

- [x] Todo delete responses remain compatible with the current HTMX `swap: delete` request against `#todo-<todo_id>` while also delivering the sidebar OOB badge fragment.
- [x] Sidebar badge values continue to be derived from server-side incomplete-Todo counts, including `0` and completed-Todo deletions.
- [x] Regression coverage proves delete-count behavior without weakening the existing toggle-count OOB contract.


## Scope & Boundaries

### Work Areas
- Todo delete response handling in `src/app/routes/todos.py#delete_todo`
- Delete-specific OOB badge markup in `src/app/templates/partials/todo_deleted_oob.html`
- Sidebar badge id/value contract in `src/app/templates/partials/todo_list_item.html`
- Regression coverage for Todo delete count behavior in `tests/test_todos.py` and `tests/test_integration.py`

### What We're NOT Doing
- Reworking the client-side delete confirmation flow in `src/app/static/js/app.js` – the existing HTMX delete target/swap behavior is already the correct transport.
- Changing create or toggle count-refresh behavior – those flows already prove the intended OOB pattern for this bug.
- Introducing JSON responses or client-side recount logic – the project is HTMX-first and keeps UI state server-rendered.
- Addressing unrelated backlog defects `BUG-002`, `BUG-003`, or `BUG-004` – they need separate specs and validation.


## Architecture Decision

**Approach**: Keep Todo deletion in the existing HTMX server-rendered flow and return a delete response that includes the refreshed incomplete-count OOB fragment for the owning TodoList after the delete commit.
**Why this over alternatives**: Reusing the server-side OOB pattern from create/toggle keeps count logic authoritative in one place and avoids fragile client-side DOM recounting.


## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                          | why needed (intent)
file   | src/app/routes/todos.py#_get_list_todo_count | Server-side incomplete count source – reuse for delete refresh
file   | src/app/routes/todos.py#toggle_todo          | Existing OOB response pattern for Todo state changes
file   | src/app/routes/todos.py#delete_todo          | Current delete ownership + response path to preserve while adding count refresh
file   | src/app/templates/partials/todo_item_with_oob.html | Composite OOB markup pattern for primary swap plus sidebar badge update
file   | src/app/templates/partials/todo_deleted_oob.html | Delete response fragment target – keep badge markup aligned with sidebar contract
file   | src/app/templates/partials/todo_list_item.html | Sidebar badge DOM id contract `list-{{ list.id }}-count`
file   | src/app/static/js/app.js#confirmDeleteTodo   | HTMX delete request target/swap contract that must remain unchanged
```


## Constraints & Gotchas

- **Constraint**: Todo delete requests are sent with `swap: delete` against `#todo-<todo_id>` – the server response must still carry the OOB badge fragment without depending on a visible replacement row payload.
- **Avoid**: Recomputing remaining counts in JavaScript – Instead: use `_get_list_todo_count` after the delete commit so the sidebar badge matches persisted state.
- **Critical**: The sidebar badge target id is `list-<todo_list_id>-count` – any mismatch between the response fragment id and `todo_list_item.html` causes HTMX to skip the OOB update silently.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Todo delete responses carry the refreshed incomplete count for the owning TodoList
  - Follow `src/app/routes/todos.py#toggle_todo` for the server-side OOB pattern and preserve `src/app/routes/todos.py#delete_todo` ownership checks plus delete semantics.
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodos::test_delete_todo tests/test_todos.py::TestTodos::test_delete_todo_updates_incomplete_count_response` passes, and the delete response body includes `hx-swap-oob="true"` with the owning list badge id.

- [x] **TI02** Delete OOB badge markup matches the sidebar contract for decremented and zero-count cases
  - Keep `src/app/templates/partials/todo_deleted_oob.html` aligned with `src/app/templates/partials/todo_list_item.html`; the response must render `list-<todo_list_id>-count` with the server-calculated count, including `0`.
  - **Verify**: deleting the last incomplete Todo yields `<span id="list-<todo_list_id>-count" hx-swap-oob="true">0</span>` in the response fragment and the sidebar badge shows `0` after visual validation.

- [x] **TI03** Regression coverage proves delete-count behavior across incomplete, completed, and multi-list cases
  - Extend the existing Todo and integration tests around `tests/test_integration.py#test_todo_completion_updates_count` to cover incomplete delete decrement, completed delete no-op on count, and unrelated TodoList badge stability.
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete and count"` passes with assertions for OOB markup, count values, and unchanged second-list badge content.

### Testing Strategy


### Validation


### Execution Contract


## Final Validation Checklist


## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

_No observations recorded yet._
