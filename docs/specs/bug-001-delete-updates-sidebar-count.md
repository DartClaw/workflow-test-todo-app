# BUG-001 - Delete updates sidebar incomplete count

## Feature Overview and Goal

**Intent**: Keep the sidebar TodoList count trustworthy during Todo deletion so users do not need a full page reload to reconcile list state.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo immediately decrements the matching TodoList sidebar count in the same HTMX interaction.
- [OC02] Deleting a completed Todo leaves the matching sidebar count unchanged while still removing the Todo row.
- [OC03] Todo delete keeps the existing HTMX delete flow and current 403/404 behavior while adopting the same server-rendered count contract already used by create and toggle flows.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | - | Open |

### From `AGENTS.md` - "Architecture"
<!-- source: AGENTS.md#architecture -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> Routes return HTML fragments, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM.
>
> Out-of-Band (OOB) swaps are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response.


## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` - Canonical definitions for Partial, OOB Swap, and Error Partial terms used in this spec.
- `docs/STACK.md#frameworks--libraries` - Confirms the FastAPI + Jinja2 + HTMX fragment stack this fix must stay within.
- `AGENTS.md#visual-validation-workflow` - Demo login and browser-validation steps for checking the delete interaction without a reload.


## Acceptance Scenarios

- [x] **S01 [OC01,OC03] [TI01,TI03] Incomplete Todo delete refreshes the sidebar count**
  - **Given** an authenticated User is viewing a TodoList whose sidebar badge shows `3`, and the Todo being deleted is incomplete
  - **When** the User confirms deletion for that Todo
  - **Then** the Todo row is removed by the current HTMX delete flow, and the server response includes an OOB swap targeting `id="list-{todo.list_id}-count"` with the rendered count `2`

- [x] **S02 [OC02,OC03] [TI01,TI02,TI03] Completed Todo delete preserves the sidebar count**
  - **Given** an authenticated User is viewing a TodoList whose sidebar badge shows `2`, and the Todo being deleted is already completed
  - **When** the User confirms deletion for that Todo
  - **Then** the Todo row is removed, and the server response includes an OOB swap targeting `id="list-{todo.list_id}-count"` with the rendered count still `2`

- [x] **S03 [OC03] [TI02,TI03] Failed deletes do not advertise a count change**
  - **Given** a delete request targets a missing Todo or a Todo outside the current User's TodoList
  - **When** the server rejects the delete
  - **Then** the response keeps the existing `404` or `403` behavior and does not return a success fragment claiming a sidebar count refresh


## Structural Criteria

- [x] Successful delete responses compute the sidebar count from persisted incomplete Todo rows using the same rule as create and toggle flows.
- [x] The Todo row-removal mechanism remains the existing HTMX `swap: 'delete'` path from `src/app/static/js/app.js#confirmDeleteTodo`; the server response only augments it with the sidebar OOB fragment.
- [x] Automated regression coverage proves both decrement and no-change delete cases, plus the current failure semantics.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py` delete success path and shared incomplete-count helper usage
- `src/app/templates/partials/todo_deleted_oob.html` delete-specific OOB fragment returned on success
- `src/app/templates/partials/todo_list_item.html` sidebar count DOM target contract
- `tests/test_todos.py` delete-route coverage for incomplete, completed, and rejected deletes
- `tests/test_integration.py` HTMX-visible OOB regression coverage for delete responses

### What We're NOT Doing
- No client-side counter math in `src/app/static/js/app.js` - the server-rendered count remains the source of truth.
- No changes to TodoList deletion behavior - BUG-001 is scoped to Todo deletion only.
- No full sidebar rerender or full page reload fallback - the existing OOB fragment pattern should solve this defect directly.
- No redesign of delete authentication or missing-resource error contracts - preserving current `403` and `404` behavior is part of the fix boundary.


## Architecture Decision

**Approach**: Make `src/app/routes/todos.py#delete_todo` return `partials/todo_deleted_oob.html`, populated from `src/app/routes/todos.py#_get_list_todo_count` after the delete commit, while keeping HTMX's current row-targeted `swap: 'delete'` behavior.
**Why this over alternatives**: It matches the already-working toggle/create pattern, keeps incomplete-count rules server-side, and avoids duplicating state logic in JavaScript.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. Leave empty when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                               | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo             | Working OOB count pattern for Todo state changes
file   | src/app/routes/todos.py#_get_list_todo_count    | Canonical incomplete-count query to reuse for delete responses
file   | src/app/routes/todos.py#delete_todo             | Delete endpoint surface; preserve access and status behavior while changing success payload
file   | src/app/templates/partials/todo_item_with_oob.html | Existing row-plus-OOB response shape used by create and toggle
file   | src/app/templates/partials/todo_deleted_oob.html | Delete-specific OOB fragment already present in the repo
file   | src/app/templates/partials/todo_list_item.html  | Sidebar count DOM id contract: `list-{{ list.id }}-count`
file   | src/app/static/js/app.js#confirmDeleteTodo      | Current HTMX delete mechanism; response must cooperate with `swap: 'delete'`
file   | tests/test_integration.py#test_todo_completion_updates_count | Existing OOB assertion style to mirror for delete coverage
```


## Constraints & Gotchas

- **ASSUMPTION**: Todo row removal continues to be driven by `swap: 'delete'` in `src/app/static/js/app.js#confirmDeleteTodo` - the server response only needs the sidebar OOB fragment, not a replacement for `#todo-{id}`.
- **Avoid**: Client-side decrement assumptions - Instead: render the fresh count from `src/app/routes/todos.py#_get_list_todo_count` after commit so completed and incomplete deletes both stay correct.
- **Critical**: `src/app/routes/todos.py#delete_todo` currently returns bare `403` and `404` responses on failure - Must handle by preserving those semantics unless the feature scope explicitly expands.


## Implementation Plan

### Implementation Tasks

- [x] **TI01 Successful Todo deletes carry the sidebar count refresh contract**
  - Reuse `src/app/routes/todos.py#_get_list_todo_count` after the delete commit and return `src/app/templates/partials/todo_deleted_oob.html` using the same DOM target contract as `src/app/templates/partials/todo_item_with_oob.html`.
  - **Verify**: `DELETE /api/todos/{id}` for an incomplete Todo returns `200` content containing `hx-swap-oob="true"` and `id="list-{list.id}-count"`, and the rendered count is one less than before delete.

- [x] **TI02 Completed deletes and rejected deletes keep the count truthful**
  - The success payload must render the persisted incomplete count whether the deleted Todo was complete or incomplete; `src/app/routes/todos.py#delete_todo` must keep current `403` and `404` behavior for unauthorized or missing Todos.
  - **Verify**: Automated coverage proves a completed Todo delete returns the unchanged count, and missing or unauthorized deletes return `404` or `403` without a false success fragment.

- [x] **TI03 Regression proof covers the server contract and the HTMX-visible outcome**
  - Extend `tests/test_todos.py` and `tests/test_integration.py` so the delete path is guarded at both route-response and interaction-contract levels, mirroring the existing OOB assertion style used for toggle responses.
  - **Verify**: Test assertions confirm successful delete responses include `hx-swap-oob`, and browser validation with the demo User shows deleting an incomplete Todo removes the row and updates the matching sidebar count without a full page reload.

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. Leave empty when this is sufficient; fill only when the test approach is non-obvious - level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. Leave empty when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract
> Generic exec-spec discipline - task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy - is enforced by exec-spec. Leave empty when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. Leave empty when these are sufficient; fill only for feature-specific final gates not already covered (for example, "no new writes to ~/.claude/" or "no orphan migration files in db/migrate/").


## Implementation Observations

> Managed by exec-spec post-implementation - append-only. Tag semantics: see `data-contract.md` (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see `automation-mode.md`. Spec authors: leave this section empty.

_No observations recorded yet._
