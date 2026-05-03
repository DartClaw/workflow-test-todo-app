# BUG-001: Sidebar incomplete count updates on Todo delete

## Feature Overview and Goal
When a user deletes a Todo, the sidebar count for that TodoList must stay in sync without requiring a full page reload. The fix should follow the codebase's existing HTMX out-of-band swap pattern that already works for create and toggle flows.

> **Technical Research**: [.technical-research.md](./.technical-research.md) (codebase patterns, architecture analysis)


## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

### From `CLAUDE.md` - "The stack -- and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

- `CLAUDE.md#visual-validation-workflow` - Manual validation steps for authenticated flows and explicit guidance to verify both the primary swap target and any `hx-swap-oob` regions.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` - Canonical terms for `Todo`, `TodoList`, `Priority`, and `Position`.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` - Canonical meaning of Partial, OOB Swap, and Error Partial in this codebase.


## Success Criteria (Must Be TRUE)
 - [x] Deleting an incomplete Todo updates the matching sidebar `list-{id}-count` badge in the same HTMX response, without a full page reload.
 - [x] Deleting a completed Todo still removes the Todo row but leaves the sidebar incomplete count unchanged.
 - [x] Successful delete responses remain HTML-fragment based and follow the existing server-rendered OOB pattern; existing `403` and `404` delete response semantics do not widen in scope.

### Health Metrics (Must NOT Regress)
 - [x] Existing create/toggle count-update behavior continues to use the same OOB pattern and remains covered by tests.
 - [x] The existing delete confirmation flow in `src/app/static/js/app.js` still works with `swap: 'delete'`; no client-side state bookkeeping is introduced.
 - [x] Regression coverage proves incomplete, completed, zero-count, and failure-path delete behavior.


## Scenarios

### Delete an incomplete Todo from a list with remaining incomplete items
- **Given** a `TodoList` sidebar badge currently shows `2` incomplete Todos
- **When** the user confirms deletion of one incomplete Todo from that `TodoList`
- **Then** the deleted Todo row is removed and the same response updates `#list-{list_id}-count` to `1` via `hx-swap-oob`

### Delete the last incomplete Todo in a TodoList
- **Given** a `TodoList` sidebar badge currently shows `1` incomplete Todo
- **When** the user confirms deletion of that Todo
- **Then** the deleted Todo row is removed and the same response updates `#list-{list_id}-count` to `0`

### Delete a completed Todo
- **Given** a `TodoList` has one or more incomplete Todos plus a separate completed Todo
- **When** the user confirms deletion of the completed Todo
- **Then** the completed Todo row is removed and the sidebar incomplete count value stays the same

### Delete a Todo that does not exist
- **Given** the client issues `DELETE /api/todos/{todo_id}` for a missing Todo ID
- **When** the server handles the request
- **Then** the response remains `404` and does not emit an OOB count fragment that could corrupt sidebar state

### Delete another user's Todo
- **Given** an authenticated user targets a Todo owned through another user's `TodoList`
- **When** the client issues the delete request
- **Then** the response remains `403` and no sidebar count fragment is returned


## Scope & Boundaries

### In Scope
- Successful Todo delete responses include the sidebar incomplete-count OOB update.
- The count value is recomputed from persisted incomplete Todos after the delete commit.
- Route and integration coverage proves the delete response contract for incomplete, completed, zero-count, and failure-path cases.

### What We're NOT Doing
- Reworking the delete confirmation dialog or `htmx.ajax` wiring in `app.js` -- the existing client flow is already the intended interaction.
- Re-rendering the full sidebar or main content -- the defect is limited to the count badge and the codebase already prefers narrow OOB swaps.
- Changing create or toggle behavior -- those flows remain the reference pattern for this fix.
- Changing successful delete behavior into JSON or broadening `403`/`404` failures into new HTML partial contracts -- the bug scope is the successful delete path only.
- Altering auth/session behavior or the database schema -- unrelated to BUG-001.


## Architecture Decision

**We will**: make successful Todo deletes return a dedicated HTML partial containing only the sidebar count OOB swap, reusing the existing count helper and delete-specific partial -- this matches the established HTMX-first pattern and preserves the existing client-side delete contract (over returning an empty `200`, re-rendering the full sidebar, or moving count logic into JavaScript).


## Technical Overview

### UI/UX Design
No new controls or flows are introduced. After the user confirms delete, the Todo row should disappear exactly as it does today, with the sidebar count updating immediately when the deleted Todo affected that count.

### Data Models
No schema changes are required. The sidebar badge remains a derived count of Todos where `Todo.list_id` matches the active `TodoList` and `Todo.is_completed == False`.

### Integration Points
- `confirmDeleteTodo()` in `src/app/static/js/app.js` continues to send the delete request with `swap: 'delete'`.
- `delete_todo()` in `src/app/routes/todos.py` becomes responsible for returning the success-path OOB fragment after the database delete commits.
- `partials/todo_deleted_oob.html` remains the fragment that updates `#list-{list_id}-count` outside the deleted Todo row.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:33-37               | Shared helper for recomputing incomplete count from persisted data
file   | src/app/routes/todos.py:243-283             | Existing toggle flow that updates the Todo row and sidebar count with OOB markup
file   | src/app/routes/todos.py:286-306             | Current delete flow that deletes correctly but returns an empty 200 response
file   | src/app/templates/partials/todo_item_with_oob.html:1-4 | Reference structure for OOB count markup on create/toggle
file   | src/app/templates/partials/todo_deleted_oob.html:1-2   | Existing delete-specific OOB fragment to reuse
file   | src/app/templates/partials/todo_list_item.html:20      | Canonical sidebar count DOM id contract
file   | src/app/static/js/app.js:170-173            | Existing HTMX delete request contract that must stay intact
file   | tests/test_todos.py:84-92                   | Baseline delete test to extend with response-content assertions
file   | tests/test_integration.py:164-179           | Existing integration proof that OOB count swaps are expected behavior
```


## Constraints & Gotchas
- **Constraint**: The primary client swap for Todo delete is `swap: 'delete'` in `src/app/static/js/app.js:170-173` -- Workaround: return only the OOB markup needed outside the deleted row, not a replacement row fragment.
- **Avoid**: Counting from stale in-memory relationship state after delete -- Instead: recompute via `_get_list_todo_count()` after the delete commit so completed-Todo and zero-count cases stay correct.
- **Critical**: Successful delete responses must remain HTML partials, not JSON, to stay aligned with `CLAUDE.md`'s HTMX-first architecture.
- **Preserve**: Existing `403` and `404` delete responses stay narrow and must not emit misleading OOB fragments.


## Implementation Plan

### Implementation Tasks

 - [x] **TI01** Successful Todo deletes emit the sidebar count OOB update
  - Follow the existing create/toggle response pattern at `src/app/routes/todos.py:125-131` and `src/app/routes/todos.py:243-283`, but use the delete-specific fragment at `src/app/templates/partials/todo_deleted_oob.html:1-2`.
  - **Verify**: Deleting an incomplete Todo returns `200` with `hx-swap-oob="true"` and `id="list-{list_id}-count"` in the response body, the response count is decremented, and the Todo row is deleted from the database.

 - [x] **TI02** Delete count semantics stay correct for completed-Todo and zero-count cases
  - Count recomputation must use `_get_list_todo_count()` from `src/app/routes/todos.py:33-37`; this task depends on TI01's success-response contract.
  - **Verify**: Deleting a completed Todo returns the same sidebar count value as before; deleting the last incomplete Todo returns `<span id="list-{list_id}-count" hx-swap-oob="true">0</span>`.

 - [x] **TI03** Regression coverage proves the delete response contract without changing failure-path scope
  - Extend `tests/test_todos.py:84-92` and `tests/test_integration.py:164-179`, and preserve the existing `403`/`404` semantics in `src/app/routes/todos.py:294-301`.
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete_todo or todo_completion_updates_count"` passes, with assertions covering incomplete delete, completed delete, last-incomplete-to-zero, and `403`/`404` no-OOB cases.

### Testing Strategy
- [TI01] Scenario: Delete an incomplete Todo from a list with remaining incomplete items -> route test proves the response body includes the OOB fragment and the decremented count.
- [TI02] Scenario: Delete the last incomplete Todo in a TodoList -> route test proves the response body updates the sidebar count to `0`.
- [TI02] Scenario: Delete a completed Todo -> route test proves the response body keeps the sidebar incomplete count unchanged.
- [TI03] Scenario: Delete a Todo that does not exist -> route test proves `404` with no OOB count markup.
- [TI03] Scenario: Delete another user's Todo -> access-control test proves `403` with no OOB count markup.
- [TI03] Scenario: Delete flow mirrors existing OOB count behavior -> integration coverage proves delete now emits the same class of OOB count update already expected from toggle.

### Validation
- Run `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete_todo or todo_completion_updates_count"` after implementation.
- Run `./run.sh`, log in as `demo@example.com` / `demo123`, delete one incomplete Todo and one completed Todo, and confirm the sidebar count changes only for the incomplete Todo without a page reload.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (DOM ids, response fragment shape, file paths, and status semantics) are exact and should be implemented verbatim.
- Use the existing server-rendered HTMX pattern; do not move count bookkeeping into client-side state.
- After all tasks: run the relevant project validation gates for this feature and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion; do not batch.


## Final Validation Checklist

 - [x] **All success criteria** met
 - [x] **All tasks** fully completed, verified, and checkboxes checked
 - [x] **No regressions** or breaking changes introduced
 - [x] **UI verified** to match requirements


## Implementation Observations

#### NOTICED BUT NOT TOUCHING

- `tests/test_todos.py`: `test_create_todo` expects `created.priority == "low"` and `test_update_todo` expects `test_todo.due_date.year == 2025`, but `Todo.priority` and `due_date` defaults/parsing behavior make these assertions fail in unrelated test scope (pre-existing).
- `src/app/routes/todos.py:33`: `_get_list_todo_count` uses `Todo.is_completed == False` instead of `Todo.is_completed.is_(False)`; not changed here but should be considered if linting hardens boolean style rules.
- `src/app/routes/todos.py:315-362`: `reorder_todo` does not clamp out-of-range `position` values; this is outside BUG-001 scope and pre-existing.

#### Run

- **2026-05-03**: Implemented BUG-001 by returning `partials/todo_deleted_oob.html` from successful deletes with recomputed incomplete count; added route-integrity and failure-path coverage in `tests/test_todos.py` and OOB contract coverage in `tests/test_integration.py`.
