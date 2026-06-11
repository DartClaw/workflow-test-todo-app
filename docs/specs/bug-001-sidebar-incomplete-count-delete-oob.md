# BUG-001 – Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal

**Intent**: Ensure deleting a Todo keeps the sidebar incomplete-count accurate immediately, so users do not need a full page reload to trust list state.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo updates the active TodoList's sidebar incomplete-count immediately in the same HTMX interaction.
- [OC02] Deleting a completed Todo removes the row without changing the sidebar incomplete-count.
- [OC03] Successful delete responses follow the existing server-rendered OOB swap pattern, while current non-success delete semantics remain unchanged.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `AGENTS.md` – "The stack — and why it matters for edits"
<!-- source: AGENTS.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

- `docs/STACK.md#frameworks--libraries` – Confirms the server-rendered FastAPI + Jinja2 + HTMX stack the delete response must stay within.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical meanings for `Partial`, `OOB Swap`, and `Error Partial`.
- `AGENTS.md#visual-validation-workflow` – Required manual validation flow for HTMX interactions that update OOB-marked regions.


## Acceptance Scenarios

- [x] **S01 [OC01,OC03] [TI01,TI02] Deleting an incomplete Todo refreshes the sidebar count without reload**
  - **Given** an authenticated user is viewing a TodoList whose sidebar count target `#list-<list_id>-count` shows `3` incomplete Todos
  - **When** the user deletes one incomplete Todo through `/api/todos/{todo_id}`
  - **Then** the Todo row is removed, and the same response includes an HTMX OOB swap that updates `#list-<list_id>-count` to `2` without a full page reload

- [x] **S02 [OC02,OC03] [TI01,TI02] Deleting a completed Todo leaves the incomplete count unchanged**
  - **Given** an authenticated user is viewing a TodoList that contains both completed and incomplete Todos
  - **When** the user deletes a completed Todo through `/api/todos/{todo_id}`
  - **Then** the Todo row is removed, and the response updates `#list-<list_id>-count` with the same value it showed before the delete

- [x] **S03 [OC03] [TI01,TI03] Deleting a missing Todo keeps the rejection path unchanged**
  - **Given** an authenticated delete request targets a Todo ID that does not exist
  - **When** `/api/todos/{todo_id}` receives the delete request
  - **Then** the route returns `404` and does not emit an OOB count update that would imply a successful delete


## Structural Criteria

- [x] Successful Todo delete responses emit an HTMX OOB swap for `#list-<list_id>-count` while preserving the existing row-removal flow driven by `swap: delete`.
- [x] Toggle and delete both derive sidebar incomplete-count values from `src/app/routes/todos.py#_get_list_todo_count`.
- [x] Automated coverage proves incomplete-delete decrement, completed-delete stability, and missing-todo rejection on the delete path.


## Scope & Boundaries

### Work Areas
- Successful delete response contract in `src/app/routes/todos.py#delete_todo`
- Delete-path OOB fragment compatibility with the sidebar count target in `src/app/templates/partials/todo_deleted_oob.html` and `src/app/templates/partials/todo_list_item.html`
- Regression coverage for delete behavior and count-refresh behavior in `tests/test_todos.py` and `tests/test_integration.py`

### What We're NOT Doing
- Changing `src/app/routes/todos.py#toggle_todo` or the shared count helper contract beyond reusing its existing pattern – the defect is isolated to the delete success path.
- Reworking delete confirmation JavaScript or replacing HTMX with client-side count bookkeeping – the project standard is server-rendered partials with OOB swaps.
- Altering 403/404 delete semantics or introducing JSON error payloads – bug scope is successful delete count refresh only.
- Refreshing the entire sidebar or main content after delete – that would bypass the existing targeted HTMX interaction and expand scope unnecessarily.


## Architecture Decision

**Approach**: Successful Todo deletes return the existing `partials/todo_deleted_oob.html` fragment with a recomputed incomplete count from `src/app/routes/todos.py#_get_list_todo_count`, mirroring `src/app/routes/todos.py#toggle_todo`.
**Why this over alternatives**: It keeps server-rendered state authoritative, matches the established HTMX OOB idiom, and avoids brittle client-side DOM arithmetic.


## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                                 | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo               | Canonical successful OOB count-refresh response for the same sidebar target
file   | src/app/routes/todos.py#delete_todo               | Delete success/error flow and ownership checks to preserve
file   | src/app/routes/todos.py#_get_list_todo_count      | Shared server-side definition of incomplete-count
file   | src/app/templates/partials/todo_deleted_oob.html  | Existing delete-only OOB fragment to wire into the success response
file   | src/app/templates/partials/todo_list_item.html    | Sidebar count target ID contract: `list-{{ list.id }}-count`
file   | src/app/static/js/app.js#confirmDeleteTodo        | Delete requests target `#todo-<id>` with `swap: delete`; response must stay OOB-only
file   | tests/test_todos.py#TestTodos.test_delete_todo    | Baseline delete regression to extend with response-contract assertions
file   | tests/test_integration.py#test_todo_completion_updates_count | Existing OOB-count regression pattern to mirror for delete
```


## Constraints & Gotchas

- **Critical**: `src/app/static/js/app.js#confirmDeleteTodo` already drives row removal with `swap: delete` – the success response must add only OOB companion markup, not a full replacement fragment.
- **Constraint**: Sidebar count correctness must continue to come from server-side recomputation, not client-side decrement logic – reuse `src/app/routes/todos.py#_get_list_todo_count`.
- **Avoid**: Changing the missing/unauthorized branches to template responses just to carry count markup – only successful deletes should emit the OOB swap.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful Todo deletes return the same sidebar count-refresh contract used by toggle
  - Follow `src/app/routes/todos.py#toggle_todo` and reuse `src/app/routes/todos.py#_get_list_todo_count`; preserve the current ownership check and the existing bare `404`/`403` `Response` branches in `src/app/routes/todos.py#delete_todo`
  - **Verify**: `DELETE /api/todos/{incomplete_todo_id}` returns `200`, removes the Todo row from the database, and the response body contains `hx-swap-oob` plus `id="list-<list_id>-count"` with the decremented incomplete-count value

- [x] **TI02** Delete-path OOB markup targets the existing sidebar count element without widening the swap surface
  - Match `src/app/templates/partials/todo_item_with_oob.html` and `src/app/templates/partials/todo_list_item.html`; the delete success payload should remain compatible with `swap: delete` by emitting only the count update fragment from `src/app/templates/partials/todo_deleted_oob.html`
  - **Verify**: deleting a completed Todo leaves `#list-<list_id>-count` unchanged, and the delete response does not include unrelated sidebar or main-content markup

- [x] **TI03** Delete-path regression coverage proves the bug fix and guards the rejection path
  - Extend `tests/test_todos.py#TestTodos.test_delete_todo` and add integration coverage alongside `tests/test_integration.py#test_todo_completion_updates_count`; this task depends on TI01 and TI02 defining the successful response contract
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count"` passes with assertions for incomplete delete decrement, completed delete count stability, and missing-Todo `404` behavior without OOB success markup

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. **Leave empty** when this is sufficient; fill only when the test approach is non-obvious – level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. **Leave empty** when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract
> Generic exec-spec discipline – task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy – is enforced by exec-spec. **Leave empty** when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. **Leave empty** when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

_No observations recorded yet._
