# BUG-001 - Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal

**Intent**: Keep the sidebar's `TodoList` count trustworthy during HTMX todo deletion so users see the remaining incomplete work immediately without reloading the page.

**Expected Outcomes**:

- [OC01] Deleting a `Todo` through the existing HTMX flow updates the sidebar count for that `TodoList` in the same round trip.
- [OC02] The count shown after delete always matches the remaining persisted incomplete `Todo` rows for that list, including when completed todos are deleted.
- [OC03] The current delete interaction keeps its in-place row removal and existing 403/404 failure semantics.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response.

### From `CLAUDE.md` - "The stack - and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` - Canonical terms for `Partial`, `OOB Swap`, and `Error Partial`; use these names in tests and implementation notes.
- `docs/STACK.md#frameworks--libraries` - Confirms the FastAPI + Jinja2 + HTMX fragment stack and the pytest/httpx test harness.


## Acceptance Scenarios

- [x] **S01 [OC01,OC03] [TI01,TI02] Deleting the only incomplete todo refreshes the sidebar count in the same HTMX round trip**
  - **Given** a `TodoList` contains one incomplete `Todo` and the sidebar shows `id="list-<list_id>-count"` with text `1`
  - **When** the user confirms delete for that `Todo`
  - **Then** HTMX deletes `#todo-<todo_id>` and applies an OOB swap to `id="list-<list_id>-count"` with text `0` in the same response

- [x] **S02 [OC01,OC02] [TI01,TI02] Deleting one incomplete todo leaves the count at the remaining incomplete total**
  - **Given** a `TodoList` contains two incomplete `Todo` rows and the sidebar count shows `2`
  - **When** the user deletes one of those todos
  - **Then** the OOB swap updates `id="list-<list_id>-count"` to `1`, matching the remaining persisted incomplete row

- [x] **S03 [OC02,OC03] [TI01,TI02] Deleting a completed todo does not decrement the incomplete count**
  - **Given** a `TodoList` contains one completed `Todo`, one incomplete `Todo`, and the sidebar count shows `1`
  - **When** the user deletes the completed `Todo`
  - **Then** the todo is removed and the OOB swap leaves `id="list-<list_id>-count"` at `1`

- [x] **S04 [OC03] [TI03] Delete failures keep current HTMX behavior**
  - **Given** a delete request targets a missing or unauthorized `Todo`
  - **When** the route rejects the request
  - **Then** it returns the existing failure status without an OOB count fragment and without changing unrelated sidebar counts


## Structural Criteria

- [x] Successful `DELETE /api/todos/{todo_id}` responses remain compatible with `htmx.ajax(..., { target: "#todo-<id>", swap: "delete" })` in `src/app/static/js/app.js`.
- [x] The shared sidebar count target remains `id="list-<list_id>-count"` so create, toggle, and delete all address the same node.
- [x] Automated tests explicitly prove the delete success response contains `hx-swap-oob` and the expected count text for incomplete-todo and completed-todo deletes.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py` delete success path and `_get_list_todo_count` reuse
- `src/app/templates/partials/todo_deleted_oob.html` delete-specific OOB count fragment
- `src/app/templates/partials/todo_list_item.html` sidebar count DOM contract
- `tests/test_todos.py` delete route coverage
- `tests/test_integration.py` HTMX count-synchronization regression coverage

### What We're NOT Doing
- Full sidebar rerenders after delete -- BUG-001 is scoped to the existing targeted OOB swap pattern, not broader fragment replacement.
- Client-side counter bookkeeping in `src/app/static/js/app.js` -- server-rendered count remains the source of truth for sidebar state.
- Changes to list delete behavior or other sidebar interactions -- the defect only covers todo deletion.
- Auth, session, or error-partial redesign -- separate concerns outside this defect.


## Architecture Decision

**Approach**: `delete_todo` reuses `_get_list_todo_count` after `db.commit()` and returns a minimal delete-specific partial that only emits the sidebar count OOB swap, while HTMX keeps `swap: "delete"` for the primary row removal.
**Why this over alternatives**: It matches the existing create/toggle pattern, keeps count derivation on persisted server state, and avoids duplicating counter logic in the browser.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. Leave empty when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                                  | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo                 | Existing OOB-count pattern after a todo state change
file   | src/app/routes/todos.py#_get_list_todo_count        | Canonical incomplete-count query to reuse after delete
file   | src/app/templates/partials/todo_item_with_oob.html  | OOB fragment shape used by the toggle/create flows
file   | src/app/templates/partials/todo_deleted_oob.html    | Delete-specific OOB fragment that should stay minimal
file   | src/app/templates/partials/todo_list_item.html      | Sidebar count DOM contract: `id="list-{{ list.id }}-count"`
file   | src/app/static/js/app.js#confirmDeleteTodo          | HTMX delete path uses `swap: "delete"` on `#todo-<id>`
```


## Constraints & Gotchas

- **Critical**: The delete client path in `src/app/static/js/app.js#confirmDeleteTodo` uses `swap: "delete"` on `#todo-<id>` -- Must handle by returning an OOB fragment that coexists with row deletion rather than a full replacement body.
- **Avoid**: Manually decrementing the sidebar count or assuming every deleted `Todo` is incomplete -- Instead: recompute with `src/app/routes/todos.py#_get_list_todo_count` after the delete commit.
- **Constraint**: `delete_todo` currently returns bare `Response` objects for 403/404 paths -- Keep those failure contracts unless BUG-001 scope is expanded.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful todo deletes expose the current incomplete count for the owning `TodoList`
  - Follow `src/app/routes/todos.py#toggle_todo` and reuse `src/app/routes/todos.py#_get_list_todo_count`; compute the count after `db.commit()` so the response reflects the remaining persisted incomplete rows.
  - **Verify**: deleting the only incomplete todo returns `200`, removes the row from the database, and includes `hx-swap-oob` targeting `id="list-<list_id>-count"` with text `0`

- [x] **TI02** Delete-specific OOB markup matches the existing sidebar count contract
  - Follow `src/app/templates/partials/todo_item_with_oob.html` for OOB shape and `src/app/templates/partials/todo_list_item.html` for the target id; keep the delete fragment limited to the count swap needed alongside `swap: "delete"`.
  - **Verify**: deleting a completed todo returns an OOB fragment whose only target is `id="list-<list_id>-count"` and whose text stays at the remaining incomplete count

- [x] **TI03** Delete regression coverage makes the HTMX contract explicit
  - Extend `tests/test_todos.py#test_delete_todo` and add a delete-count integration path near `tests/test_integration.py#test_todo_completion_updates_count`; keep current 404/403 status behavior under test rather than inferred.
  - **Verify**: the automated delete tests fail if the response drops `hx-swap-oob`, points at a different id, or changes the current missing/unauthorized status contract

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. Leave empty when this is sufficient; fill only when the test approach is non-obvious - level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. Leave empty when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract
> Generic exec-spec discipline - task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy - is enforced by exec-spec. Leave empty when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. Leave empty when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


## Implementation Observations

#### NOTICED BUT NOT TOUCHING

- Full `uv run pytest` currently fails pre-existing in `tests/test_todos.py::test_create_todo` (default priority assertion expects `"low"` for new todos) and `tests/test_todos.py::test_update_todo` (date input parser expectation still expects a date-only value to populate `due_date`).
