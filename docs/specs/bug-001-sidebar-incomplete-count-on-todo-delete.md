# BUG-001 - Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal

**Intent**: Keep the sidebar's incomplete-count trustworthy after a todo delete by using the same server-rendered HTMX OOB pattern that already works for completion toggles.

**Expected Outcomes**:

- [OC01] Successful todo deletes update the sidebar incomplete-count immediately, without a full page reload.
- [OC02] The post-delete count stays correct for incomplete, completed, and zero-remaining edge cases.
- [OC03] The todo delete flow keeps the current HTMX row-removal and auth/not-found behavior while adding the sidebar update.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

### From `AGENTS.md` - "Architecture"
<!-- source: AGENTS.md#architecture -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### From `AGENTS.md` - "Visual Validation Workflow"
<!-- source: AGENTS.md#visual-validation-workflow -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> When altering interactions that update multiple DOM regions (counts, sidebar, row), verify the OOB swap still fires - check both the primary target and any region marked with `hx-swap-oob`.


## Deeper Context

- `docs/STACK.md#technology-stack` - Baseline stack and the HTML-fragment route model this bug fix must stay within.
- `docs/UBIQUITOUS_LANGUAGE.md#ubiquitous-language` - Canonical usage of Todo, TodoList, Partial, and OOB Swap.
- `docs/guidelines/WEB-DEV-GUIDELINES.md#web-development-guidelines` - Frontend changes should stay thin and HTMX-driven rather than shifting count logic into bespoke client state.


## Acceptance Scenarios

- [x] **S01 [OC01,OC03] [TI01,TI02] Deleting an incomplete todo updates both the row and the sidebar count**
  - **Given** an authenticated user is viewing a `TodoList` whose sidebar badge shows `3` incomplete todos
  - **When** the user deletes one incomplete `Todo` from that list
  - **Then** the deleted row is removed and the sidebar badge updates to `2` without a full page reload

- [x] **S02 [OC02] [TI02] Deleting a completed todo does not decrement the incomplete-count**
  - **Given** a `TodoList` contains both incomplete and completed todos and the sidebar badge reflects only the incomplete ones
  - **When** the user deletes a completed `Todo`
  - **Then** the deleted row is removed and the sidebar badge value stays unchanged

- [x] **S03 [OC01,OC02] [TI01,TI02] Deleting the last incomplete todo can render a zero count through OOB markup**
  - **Given** a `TodoList` has exactly one remaining incomplete `Todo` and the sidebar badge shows `1`
  - **When** the user deletes that `Todo`
  - **Then** the delete response includes the OOB update for the existing sidebar count target and the UI shows `0` without a page reload

- [x] **S04 [OC03] [TI01] Rejected deletes do not emit a misleading count update**
  - **Given** a delete request targets a missing `Todo` or a `Todo` owned by another user
  - **When** the route rejects the request
  - **Then** it preserves the current `404` or `403` behavior and does not send a sidebar count swap


## Structural Criteria

- [x] Successful `DELETE /api/todos/{todo_id}` responses remain compatible with the current `htmx.ajax(..., { target: '#todo-{id}', swap: 'delete' })` contract in `src/app/static/js/app.js`.
- [x] Sidebar count updates continue targeting the existing `id="list-<list_id>-count"` element rendered by `src/app/templates/partials/todo_list_item.html`.
- [x] Automated regression coverage proves delete responses carry OOB count markup and the existing toggle-count OOB behavior still passes.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py` delete flow and shared incomplete-count helper usage
- `src/app/templates/partials/todo_deleted_oob.html` plus the existing sidebar count target in `src/app/templates/partials/todo_list_item.html`
- `tests/test_todos.py` and `tests/test_integration.py` coverage for delete and toggle count updates

### What We're NOT Doing
- Refactoring the delete confirmation dialog or broader `src/app/static/js/app.js` flow - the defect is about count synchronization, not delete UX.
- Changing create or toggle count-update behavior beyond regression protection - those paths already define the approved OOB pattern.
- Introducing JSON APIs or client-side count bookkeeping - this project keeps UI state server-rendered through HTMX partials.
- Addressing unrelated backlog defects such as `BUG-002`, `BUG-003`, or `BUG-004` - they need separate specs and verification.


## Architecture Decision

**Approach**: Keep todo delete aligned with the existing server-rendered HTMX pattern by returning a delete response that carries the sidebar count OOB swap after the database commit.
**Why this over alternatives**: Client-side decrement logic would duplicate server truth and drift on completed-todo or zero-state edge cases, while `toggle_todo` already demonstrates the accepted pattern.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. **Leave empty** when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                                  | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo                 | Existing post-mutation OOB count pattern for todo state changes
file   | src/app/routes/todos.py#delete_todo                 | Delete route entry point; preserve current 404/403 behavior while adding the count update
file   | src/app/templates/partials/todo_item_with_oob.html  | Composite row + sidebar-count OOB response shape used by toggle/create
file   | src/app/templates/partials/todo_deleted_oob.html    | Delete-specific sidebar-count partial already present in the repo
file   | src/app/templates/partials/todo_list_item.html      | Authoritative sidebar badge target id: `list-{{ list.id }}-count`
file   | src/app/static/js/app.js#confirmDeleteTodo          | Current HTMX delete target and `swap: 'delete'` contract
file   | tests/test_integration.py#test_todo_completion_updates_count | Existing regression example for OOB count markup
```


## Constraints & Gotchas

- **Constraint**: Todo delete is triggered through `htmx.ajax('DELETE', ...)` with `swap: 'delete'` - the response must add only the secondary OOB update, not a new primary swap contract.
- **Avoid**: Recomputing the sidebar badge from DOM state or client-side counters - instead compute the post-delete incomplete-count on the server with `_get_list_todo_count`.
- **Critical**: The route needs the owning `list_id` after the `Todo` is deleted - capture the list context before `db.delete(todo)` and render the OOB partial from preserved state.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful delete responses remove the todo row and carry the sidebar count OOB update
  - Follow `src/app/routes/todos.py#toggle_todo`, `src/app/templates/partials/todo_item_with_oob.html`, and `src/app/static/js/app.js#confirmDeleteTodo`; reuse `src/app/templates/partials/todo_deleted_oob.html` if it satisfies the current `swap: 'delete'` contract.
  - **Verify**: A delete test proves `DELETE /api/todos/{todo_id}` returns `200` with `hx-swap-oob` markup that targets `id="list-<list_id>-count"`, and the existing delete interaction still removes the `#todo-{id}` row.

- [x] **TI02** Post-delete counts reflect the remaining incomplete todos in the owning `TodoList`
  - Reuse `_get_list_todo_count` in `src/app/routes/todos.py`; compute the count after commit from the deleted todo's preserved `list_id` so incomplete, completed, and zero-state branches stay server-authoritative.
  - **Verify**: Route tests cover three cases - deleting an incomplete todo decrements the sidebar count, deleting a completed todo leaves it unchanged, and deleting the last incomplete todo returns an OOB badge value of `0`.

- [x] **TI03** Regression coverage locks the shared count-update contract across delete and toggle flows
  - Extend the existing route/integration tests in `tests/test_todos.py` and `tests/test_integration.py` instead of creating a parallel harness; keep the toggle OOB assertion green while adding delete-specific OOB assertions.
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "toggle or delete"` passes with delete responses asserting `hx-swap-oob` and toggle responses still asserting the same marker.

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. **Leave empty** when this is sufficient; fill only when the test approach is non-obvious - level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. **Leave empty** when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract
> Generic exec-spec discipline - task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy - is enforced by exec-spec. **Leave empty** when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. **Leave empty** when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


## Implementation Observations

> _Managed by exec-spec post-implementation - append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

_No observations recorded yet._
