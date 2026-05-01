# BUG-001 - Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal
Deleting a `Todo` from an active `TodoList` must update the sidebar incomplete-count immediately, without a full page reload. The fix should follow the existing HTMX out-of-band swap pattern already used by completion toggles so the delete flow remains consistent with the rest of the app.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/PRODUCT-BACKLOG.md` - "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `AGENTS.md` - "The stack - and why it matters for edits"
<!-- source: AGENTS.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.
> - Redirects for HTMX requests use the `HX-Redirect` response header (not a 302), because HTMX swaps fragments - a normal redirect would replace the fragment, not the page. See the 401 handler in `src/app/main.py` and the post-login flow in `src/app/routes/auth.py` for the pattern.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### From `AGENTS.md` - "Visual Validation Workflow"
<!-- source: AGENTS.md#visual-validation-workflow -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> 4. When altering interactions that update multiple DOM regions (counts, sidebar, row), verify the OOB swap still fires - check both the primary target and any region marked with `hx-swap-oob`.


## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` - canonical meanings for `Partial`, `OOB Swap`, and `Error Partial`.
- `AGENTS.md#cross-cutting-conventions` - ownership-check-first convention and current 403/404 error-handling expectations for todo routes.


## Success Criteria (Must Be TRUE)
- [ ] Deleting an incomplete `Todo` returns an HTMX-compatible HTML response that includes an OOB update for the matching sidebar incomplete-count element, so the count decrements without a full page reload.
- [ ] Deleting a completed `Todo` still removes the row, but the sidebar incomplete-count value does not change because only incomplete todos are counted.
- [ ] Missing-todo and unauthorized delete behavior remains unchanged: the fix does not broaden the bug into auth or error-handling changes.

### Health Metrics (Must NOT Regress)
- [ ] Existing todo route tests continue to pass.
- [ ] The delete flow keeps the existing route shape and does not introduce JSON endpoints or client-side count recalculation.
- [ ] Existing toggle-based OOB count behavior remains unchanged.


## Scenarios

### Delete Incomplete Todo Updates Sidebar Count
- **Given** a `TodoList` with an incomplete-count badge showing `1` for one incomplete `Todo`
- **When** the user deletes that incomplete `Todo` through the existing HTMX delete action
- **Then** the response removes the deleted row and includes an OOB swap for `id="list-{list_id}-count"` with the value `0`

### Delete Completed Todo Leaves Incomplete Count Unchanged
- **Given** a `TodoList` with one completed `Todo` and one incomplete `Todo`, and the sidebar incomplete-count shows `1`
- **When** the user deletes the completed `Todo`
- **Then** the response still includes the OOB sidebar count update, and the count remains `1`

### Delete Missing Todo Preserves Existing Error Contract
- **Given** a request to delete a `Todo` ID that does not exist
- **When** the delete route is called
- **Then** the route returns `404` and does not emit a misleading sidebar count update

### Delete Unauthorized Todo Preserves Ownership Boundary
- **Given** a `Todo` inside another user's `TodoList`
- **When** a different authenticated user calls the delete route
- **Then** the route returns `403` and does not delete the `Todo` or emit an OOB count update


## Scope & Boundaries

### In Scope
- Return the sidebar incomplete-count OOB swap from the delete flow using the existing server-rendered partial pattern.
- Recompute the incomplete count from persisted state after delete commit so the returned count reflects the current database value.
- Add automated coverage for the delete response payload and count semantics for incomplete vs completed todo deletion.

### What We're NOT Doing
- Adjusting how HTMX removes the deleted row client-side - row removal already works and is not part of `BUG-001`.
- Refactoring todo-route error responses into shared helpers - the bug is about stale sidebar state, not route cleanup.
- Changing toggle behavior or count semantics - toggle is the reference pattern and must remain the baseline.
- Introducing JavaScript-side count mutation - the server-rendered partial remains the source of truth for UI state.

### Agent Decision Authority
- **Autonomous**: Reuse the existing delete-specific partial or another existing partial-only pattern if it satisfies the same OOB contract and keeps the flow HTML-first.
- **Escalate**: Any change that would alter delete auth/error semantics, count definition, or HTMX target structure outside the sidebar count span.


## Architecture Decision

**We will**: keep delete handling in `src/app/routes/todos.py` and return a server-rendered partial containing the updated sidebar count via `hx-swap-oob` after the delete commit - this matches the existing toggle pattern and reuses current HTMX conventions over JSON responses or client-side DOM math.


## Technical Overview

### UI/UX Design
The user-facing behavior stays the same except the sidebar count updates immediately after a delete. The response should continue to support HTMX-driven row removal while also updating the badge outside the main target in the same request cycle.

### Data Models
`Todo` deletion must continue to operate within the owning `TodoList`. The sidebar badge reflects the count of rows where `Todo.is_completed == False` for that `TodoList`.

### Integration Points
The delete route integrates with the existing `_get_list_todo_count()` helper and an existing OOB partial template. Test coverage should integrate with the current `authenticated_client` fixture and todo-route test module.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:33-37           | Existing incomplete-count query helper to reuse
file   | src/app/routes/todos.py:243-283         | Canonical OOB response pattern from toggle flow
file   | src/app/routes/todos.py:286-306         | Delete route to align with the toggle pattern
file   | src/app/templates/partials/todo_item_with_oob.html:1-4 | Existing OOB markup contract for the sidebar count span
file   | src/app/templates/partials/todo_deleted_oob.html:1-2   | Existing delete-specific OOB partial likely intended for this defect
file   | tests/test_todos.py:84-92               | Current delete test to extend with payload assertions
file   | tests/test_integration.py:179-194       | Existing OOB integration assertion pattern
```


## Constraints & Gotchas
- **Constraint**: The app is HTMX-first and routes return HTML fragments, not JSON - Workaround: return a partial response from delete, not a bare success payload with client-side count logic.
- **Avoid**: Computing the count before the delete commit - Instead: delete, commit, then recompute so the count matches persisted state.
- **Critical**: Delete currently uses plain `Response` objects for `404` and `403` - Must handle by: preserving those non-happy-path contracts unless a separate defect explicitly changes them.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Delete responses update the sidebar incomplete-count through the existing OOB partial contract
  - Follow the mutate-commit-recount pattern at `src/app/routes/todos.py:243-283`, but adapt it to the delete flow at `src/app/routes/todos.py:286-306`; reuse `src/app/templates/partials/todo_deleted_oob.html:1-2` or an equivalent existing partial-only response.
  - **Verify**: `uv run pytest tests/test_todos.py -k "delete_todo"` proves deleting an incomplete todo returns HTTP 200, removes the row from the database, and includes both 'hx-swap-oob' and 'id="list-{list_id}-count"' with the decremented count in the response body`

- [ ] **TI02** Delete coverage proves count semantics and preserved non-happy-path behavior
  - Extend existing todo-route coverage at `tests/test_todos.py:84-92` and mirror the OOB assertion style from `tests/test_integration.py:179-194`; this task depends on TI01's response contract.
  - **Verify**: `uv run pytest tests/test_todos.py -k "delete_todo or cannot_modify_other_users_todo" tests/test_integration.py -k "todo_completion_updates_count"` proves deleting a completed todo leaves the incomplete-count unchanged, unauthorized delete still returns 403 without deleting data, and existing toggle OOB behavior still passes`

### Testing Strategy
- [TI01] Scenario: Delete Incomplete Todo Updates Sidebar Count -> route test deletes an incomplete todo, asserts database removal, `hx-swap-oob`, the `list-{list_id}-count` target, and the decremented count value in the returned HTML
- [TI02] Scenario: Delete Completed Todo Leaves Incomplete Count Unchanged -> route test deletes a completed todo from a list that still has one incomplete todo and asserts the OOB count remains `1`
- [TI02] Scenario: Delete Missing Todo Preserves Existing Error Contract -> route test calls delete with an unknown ID and asserts `404` with no OOB payload requirements
- [TI02] Scenario: Delete Unauthorized Todo Preserves Ownership Boundary -> access-control test confirms `403`, no deletion, and no count-update side effects

### Validation
- Run the delete-focused route tests plus the existing toggle OOB integration assertion.
- Perform one browser validation pass using the project workflow: delete an incomplete todo after logging in with `demo@example.com` / `demo123` and confirm the sidebar badge changes without a full reload.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact - implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research - spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature - build/tests/lint-analysis where those checks exist and are relevant - and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion - do not batch.


## Final Validation Checklist

- [ ] **All success criteria** met
- [ ] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements


## Implementation Observations

_No observations recorded yet._
