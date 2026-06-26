# BUG-001 - Delete Todo Updates Sidebar Count

## Feature Overview and Goal

**Intent**: Keep the sidebar incomplete count trustworthy during todo deletion so users do not need a full page reload to see current list state.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo updates the owning TodoList sidebar count in the same HTMX response that removes the row.
- [OC02] Sidebar counts stay correct for delete edge cases, including deleting the last incomplete Todo and deleting a completed Todo.
- [OC03] Failed delete requests do not emit a misleading success-style count update, and successful delete requests keep the existing HTMX row-removal flow.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `AGENTS.md` - "Architecture"
<!-- source: AGENTS.md#architecture -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### From `AGENTS.md` - "Visual Validation Workflow"
<!-- source: AGENTS.md#visual-validation-workflow -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> 4. When altering interactions that update multiple DOM regions (counts, sidebar, row), verify the OOB swap still fires - check both the primary target and any region marked with `hx-swap-oob`.

## Acceptance Scenarios

- [x] **S01 [OC01] [TI01,TI02] Incomplete todo deletion refreshes the sidebar count immediately**
  - **Given** a TodoList sidebar item shows `2` incomplete Todos and one visible Todo row is incomplete
  - **When** the user confirms deletion for that Todo from the current list view
  - **Then** the deleted row is removed and the same response updates `list-<list_id>-count` from `2` to `1` without a full page reload

- [x] **S02 [OC02] [TI01,TI03] Deleting the last incomplete todo shows zero instead of a stale count**
  - **Given** a TodoList has exactly one incomplete Todo remaining and the sidebar count shows `1`
  - **When** the user deletes that Todo
  - **Then** the row is removed and the sidebar count updates to `0` in the delete response

- [x] **S03 [OC02] [TI01,TI03] Completed todo deletion leaves the incomplete count unchanged**
  - **Given** a TodoList contains at least one completed Todo and the sidebar count reflects only incomplete Todos
  - **When** the user deletes a completed Todo
  - **Then** the row is removed and the sidebar count is re-rendered with the same numeric value rather than decremented blindly

- [x] **S04 [OC03] [TI02,TI03] Failed deletes do not masquerade as successful count updates**
  - **Given** a delete request targets a missing Todo or one the current user does not own
  - **When** the request is processed
  - **Then** the response keeps the existing failure status and does not include a success-path OOB sidebar count fragment

## Structural Criteria

- [x] Successful todo deletes still work with the existing `htmx.ajax(... swap: 'delete')` row-removal flow from `src/app/static/js/app.js`
- [x] The delete-path OOB fragment targets the existing sidebar count element contract `id="list-<list_id>-count"` with `hx-swap-oob="true"`
- [x] Existing create and toggle count-refresh behavior remains unchanged

## Scope & Boundaries

### Work Areas

- Successful delete handling in `src/app/routes/todos.py`
- Delete-specific OOB count fragment in `src/app/templates/partials/todo_deleted_oob.html`
- Sidebar count contract in `src/app/templates/partials/todo_list_item.html`
- Regression coverage for delete/count behavior in `tests/test_todos.py` and `tests/test_integration.py`

### What We're NOT Doing

- Reworking list sidebar rendering beyond the existing count target contract - BUG-001 is limited to the stale count on todo delete
- Changing the delete confirmation dialog or overall JS delete interaction unless required to preserve the current HTMX swap contract
- Normalizing todo delete 403/404 failures into HTML error partials - current status-only behavior is outside this defect
- Fixing unrelated backlog defects `BUG-002`, `BUG-003`, or `BUG-004` - separate defect scopes

## Architecture Decision

**Approach**: Keep the server as the source of truth by recomputing the owning TodoList incomplete count after a successful delete and returning it in the existing delete response via an OOB fragment.
**Why this over alternatives**: This matches the create/toggle pattern already used in `todos.py`, avoids brittle client-side count math, and preserves the current HTMX `swap: 'delete'` row-removal behavior.

## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. Leave empty when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                              | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo            | Existing OOB response pattern for sidebar count refresh
file   | src/app/routes/todos.py#_get_list_todo_count   | Count source - reuse the incomplete-only query after delete commit
file   | src/app/templates/partials/todo_item_with_oob.html | Existing OOB fragment shape and target contract
file   | src/app/templates/partials/todo_deleted_oob.html   | Delete-specific count fragment to align with the same target contract
file   | src/app/templates/partials/todo_list_item.html | Sidebar count element id and rendering contract
file   | src/app/static/js/app.js                       | Todo delete HTMX target and `swap: 'delete'` contract that must keep working
file   | tests/test_integration.py#test_todo_completion_updates_count | Existing OOB assertion pattern to mirror for delete
```

## Constraints & Gotchas

- **Constraint**: The delete flow already relies on `htmx.ajax('DELETE', ...)` with `swap: 'delete'` for Todo rows - the response must still let HTMX delete the row while applying the sidebar update OOB.
- **Avoid**: Client-side decrement logic based on the deleted Todo's prior state - instead recompute from the database after commit so completed-Todo deletes and zero-count transitions stay correct.
- **Critical**: The sidebar count renders from the existing `list-<list_id>-count` span - any new fragment must keep that id and `hx-swap-oob="true"` or the update will silently miss the DOM target.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful todo deletes return the authoritative incomplete count for the owning TodoList
  - Follow `src/app/routes/todos.py#toggle_todo` and reuse `src/app/routes/todos.py#_get_list_todo_count`; recompute after `db.commit()` so incomplete, completed, and zero-count cases all come from persisted state
  - **Verify**: `Test: DELETE /api/todos/<incomplete-id> returns 200 and the response body includes the owning list count fragment with the decremented value; deleting the last incomplete Todo returns the same fragment with >0 replaced by 0`

- [x] **TI02** Successful delete responses preserve the current HTMX row-removal contract while refreshing the sidebar count out-of-band
  - Follow `src/app/static/js/app.js` and `src/app/templates/partials/todo_item_with_oob.html`; the delete path must keep working with `swap: 'delete'` and target `id="list-<list_id>-count"` via `hx-swap-oob="true"`
  - **Verify**: `Test: a successful todo DELETE response contains hx-swap-oob="true" and id="list-<list_id>-count" while the client still deletes #todo-<todo_id> as the primary swap target`

- [x] **TI03** Delete/count regression coverage distinguishes successful refreshes from failure paths
  - Extend the current route/integration coverage in `tests/test_todos.py` and `tests/test_integration.py`; cover incomplete delete, completed delete, last-incomplete delete, and a failed delete that keeps 403/404 without a success-path count fragment
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count"` proves the delete response includes the OOB count fragment only on successful deletes and that existing toggle-count coverage still passes`

### Testing Strategy

> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. Leave empty when this is sufficient; fill only when the test approach is non-obvious - level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation

> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. Leave empty when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract

> Generic exec-spec discipline - task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy - is enforced by exec-spec. Leave empty when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist

> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. Leave empty when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to ~/.claude/", "no orphan migration files in db/migrate/").


## Implementation Observations

> Managed by exec-spec post-implementation - append-only. Tag semantics: see `data-contract.md` (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see `automation-mode.md`. Spec authors: leave this section empty.

_No observations recorded yet._
