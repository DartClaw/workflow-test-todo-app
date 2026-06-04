# BUG-001 – Sidebar incomplete-count updates after todo deletion

## Feature Overview and Goal

**Intent**: Keep the sidebar incomplete-count badge truthful during HTMX delete flows so a User does not need a full page reload to see the current TodoList state.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo from an open TodoList refreshes the sidebar incomplete-count immediately, without a full page reload.
- [OC02] Deleting a completed Todo does not change the sidebar incomplete-count, but the delete response still keeps the sidebar badge synchronized with server state.
- [OC03] Todo deletion keeps the app's current response contracts intact: successful deletes stay HTMX-compatible HTML, while unauthorized or missing-todo deletes stay status-only failures.


## Required Context

> Load-bearing upstream spans inlined verbatim from PRD, plan, ADRs, or guidelines.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – "The stack — and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.
> - Redirects for HTMX requests use the `HX-Redirect` response header (not a 302), because HTMX swaps fragments – a normal redirect would replace the fragment, not the page.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

> Anchored pointers for supplementary context; read on demand.

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical terms for `Partial`, `OOB Swap`, and `Error Partial`; use these names in implementation notes and review.
- `CLAUDE.md#visual-validation-workflow` – Manual/browser validation steps for HTMX interactions that update both a primary target and an OOB sidebar region.
- `docs/STACK.md#frameworks--libraries` – Confirms the FastAPI + Jinja2 + HTMX baseline this fix must stay within.


## Acceptance Scenarios

- [x] **S01 [OC01] [TI01,TI02] Deleting an incomplete Todo decrements the active TodoList count**
  - **Given** an authenticated User is viewing `/app/lists/{list_id}` and the sidebar badge for that TodoList currently shows `2`
  - **When** the User deletes one incomplete Todo from the active list
  - **Then** `DELETE /api/todos/{todo_id}` returns `200`, includes `hx-swap-oob="true"` for `id="list-{list_id}-count"`, and the sidebar badge becomes `1` without a full page reload

- [x] **S02 [OC02] [TI01,TI02] Deleting a completed Todo leaves the incomplete-count unchanged**
  - **Given** an authenticated User is viewing a TodoList with one incomplete Todo, one completed Todo, and the sidebar badge currently shows `1`
  - **When** the User deletes the completed Todo
  - **Then** the delete response returns `200`, includes `id="list-{list_id}-count">1<`, and the sidebar badge still shows `1`

- [x] **S03 [OC01,OC02] [TI01,TI02] Deleting the last incomplete Todo drives the badge to zero**
  - **Given** the Todo being deleted is the only remaining incomplete Todo in the active TodoList
  - **When** the User deletes that Todo
  - **Then** the delete response returns `200` with `id="list-{list_id}-count">0<` and the sidebar badge shows `0` immediately

- [x] **S04 [OC03] [TI03] Failed delete requests do not emit a sidebar count fragment**
  - **Given** a delete request targets a missing Todo ID or a Todo owned by another User
  - **When** the request is sent to `DELETE /api/todos/{todo_id}`
  - **Then** the response keeps the existing `404` or `403` status-only contract and does not include `hx-swap-oob` or a `list-{list_id}-count` fragment


## Structural Criteria

> Non-behavioral proof requirements: invariants, regression guards, and structural checks that hold true when done. Each criterion is proved by a task Verify line, not a scenario.

- [x] Successful delete responses stay HTMX-first HTML fragments rather than introducing JSON or client-side count recalculation.
- [x] The sidebar count after delete is derived from the existing incomplete-only count helper so create, toggle, and delete share one counting rule.
- [x] Regression coverage exercises incomplete delete, completed delete, and rejection delete paths.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#delete_todo` – successful and failed delete response behavior
- `src/app/routes/todos.py#_get_list_todo_count` – canonical incomplete-only count calculation
- `src/app/templates/partials/todo_deleted_oob.html` – delete-specific OOB count fragment surface
- `src/app/templates/partials/todo_list_item.html` – sidebar badge target contract `id="list-{{ list.id }}-count"`
- `tests/test_todos.py` and `tests/test_integration.py` – route-level and HTMX response regression coverage

### What We're NOT Doing
- Create, toggle, or search Todo flows – those are already behaving correctly for sidebar counts and are out of scope for BUG-001.
- Client-side JavaScript count bookkeeping – the fix stays server-rendered and HTMX-driven to match the current architecture.
- Error-path response shape changes beyond preserving existing `403` and `404` status behavior – BUG-001 is about successful delete synchronization, not error UX redesign.
- Sidebar markup redesign – the existing count target and list-item structure remain the contract this fix must satisfy.


## Architecture Decision

**Approach**: Successful `DELETE /api/todos/{todo_id}` responses return a server-rendered HTML fragment that carries the refreshed incomplete-count badge via `hx-swap-oob`, reusing the app's existing count helper and sidebar target contract.
**Why this over alternatives**: It matches the established HTMX/OOB pattern used by `toggle_todo`, avoids duplicate client-side state, and fixes the defect without widening the response model.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. Leave empty when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                                      | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo                     | Existing successful HTMX OOB response pattern for count updates
file   | src/app/routes/todos.py#_get_list_todo_count            | Canonical incomplete-only count query shared across todo mutations
file   | src/app/static/js/app.js:170-173                        | Existing delete trigger already removes the Todo row with `swap: 'delete'`; the server response only needs the OOB sidebar fragment
file   | src/app/templates/partials/todo_item_with_oob.html:1-4  | Existing OOB markup shape and `hx-swap-oob` contract
file   | src/app/templates/partials/todo_deleted_oob.html:1-2    | Delete-specific OOB fragment surface already present in the repo
file   | src/app/templates/partials/todo_list_item.html:20       | Sidebar badge target contract `list-{{ list.id }}-count`
file   | tests/test_integration.py#test_todo_completion_updates_count | Existing HTMX count-response coverage pattern to mirror for delete
```


## Constraints & Gotchas

- **Constraint**: `delete_todo` currently returns bare `Response(status_code=404)` and `Response(status_code=403)` on failure – Workaround: only successful delete responses should switch to an HTML fragment.
- **Noticed**: `delete_todo` failure paths already diverge from the broader HTML error-partial guidance in `CLAUDE.md` – Scope choice: BUG-001 preserves that local `403/404` behavior instead of normalizing delete error UX.
- **Avoid**: Counting from in-memory `list.todos` after a delete – Instead: use `_get_list_todo_count` so completed Todos and database state stay aligned with create/toggle behavior.
- **Critical**: The sidebar badge target is `id="list-{{ list.id }}-count"` – Must handle by emitting an OOB fragment that targets that exact DOM id.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful todo deletions return the refreshed sidebar incomplete-count as an HTMX fragment
  - Follow `src/app/routes/todos.py#toggle_todo` and `src/app/templates/partials/todo_item_with_oob.html:1-4` for the OOB response contract; `src/app/static/js/app.js:170-173` already deletes the Todo row client-side, so the successful server response only needs the OOB sidebar fragment
  - **Verify**: `tests/test_todos.py::TestTodos::test_delete_incomplete_todo_returns_oob_count` proves `DELETE /api/todos/{todo_id}` returns `200`, includes `hx-swap-oob="true"`, and includes `id="list-{list_id}-count">0<` when the deleted Todo was the only incomplete Todo

- [x] **TI02** Delete count behavior stays aligned with the app's incomplete-only counting rule
  - Reuse `src/app/routes/todos.py#_get_list_todo_count` and the `src/app/templates/partials/todo_list_item.html:20` badge target so delete, create, and toggle all derive the sidebar count from the same incomplete-only contract
  - **Verify**: `tests/test_todos.py::TestTodos::test_delete_completed_todo_keeps_incomplete_count` proves deleting a completed Todo leaves `id="list-{list_id}-count">1<` unchanged while the Todo is removed from the database

- [x] **TI03** Failed delete requests preserve the current status-only contract
  - Keep `src/app/routes/todos.py#delete_todo` aligned with its existing `Response(status_code=404|403)` behavior for missing or unauthorized deletes, even though other routes often render `partials/error.html`; only successful deletes should emit the OOB fragment
  - **Verify**: `tests/test_todos.py::TestTodoAccess::test_delete_other_users_todo_returns_403_without_oob` and `tests/test_todos.py::TestTodos::test_delete_missing_todo_returns_404_without_oob` prove `403/404` delete responses have empty bodies and no `hx-swap-oob`

- [x] **TI04** Regression coverage proves delete-driven count refresh in route and integration flows
  - Extend the count-response coverage pattern at `tests/test_integration.py#test_todo_completion_updates_count` so delete is checked alongside toggle at the HTMX response level
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count"` passes with assertions covering incomplete delete, completed delete, and OOB markup presence

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. Leave empty when this is sufficient; fill only when the test approach is non-obvious – level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. Leave empty when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract
> Generic exec-spec discipline – task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy – is enforced by exec-spec. Leave empty when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. Leave empty when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


## Implementation Observations

Implemented delete-path OOB synchronization and count-derivation consistency in `delete_todo`, with no behavior change to 403/404 status-only failures.  
[TI01] `delete_todo` now returns `partials/todo_deleted_oob.html` after successful deletion, using the existing `list_obj` and recalculated incomplete count from `_get_list_todo_count`.  
[TI02] `todo_deleted_oob.html` now binds to `list.id` to match sidebar target `id="list-{list.id}-count"`; incomplete-only counting remains centralized in `_get_list_todo_count`.  
[TI03] Error contracts preserved with `Response(status_code=403|404)` and no body for unauthorized/missing deletes.  
[TI04] Regression tests added/updated in `tests/test_todos.py` and `tests/test_integration.py`, and delete count scenarios are covered by `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count"`.

_No observations recorded yet._
