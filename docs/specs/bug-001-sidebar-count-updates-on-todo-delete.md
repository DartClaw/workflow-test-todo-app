# BUG-001 – Sidebar count updates on todo delete

## Feature Overview and Goal

When a user deletes a `Todo` from an active `TodoList`, the sidebar incomplete-count badge must update in the same HTMX response instead of waiting for a full page reload. This restores parity with the existing toggle behavior while keeping the fix inside the repo's HTMX-first, server-rendered OOB pattern.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, route/test seams, implementation constraints)_

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – `Known Defects`
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – HTMX fragment and OOB contract
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.
> - Redirects for HTMX requests use the `HX-Redirect` response header (not a 302), because HTMX swaps fragments – a normal redirect would replace the fragment, not the page. See the 401 handler in `src/app/main.py` and the post-login flow in `src/app/routes/auth.py` for the pattern.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

## Deeper Context

- `CLAUDE.md#visual-validation-workflow` – run-book for validating HTMX interactions that update multiple DOM regions, including explicit OOB verification guidance.
- `docs/ROADMAP.md#phase-2-defect-triage` – current project phase and non-regression expectation for backlog bug fixes.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – canonical terms for `Partial`, `OOB Swap`, and `Error Partial` used throughout this FIS.

## Success Criteria (Must Be TRUE)

- [x] Deleting an incomplete `Todo` returns a successful HTML fragment response that updates `#list-{TodoList.id}-count` via `hx-swap-oob`, so the sidebar badge decrements without a full page reload.
- [x] Deleting a completed `Todo` leaves the sidebar badge unchanged, proving the delete path still counts incomplete todos only.
- [x] Deleting the final incomplete `Todo` in a `TodoList` updates the sidebar badge to `0` rather than leaving stale markup or requiring a reload.
- [x] Rejected delete requests (for example, deleting another user's `Todo`) do not emit a misleading sidebar count update.

### Health Metrics (Must NOT Regress)

- [x] Existing create/toggle count-update behavior continues to work and keeps using the current `#list-{id}-count` target contract.
- [x] Targeted delete/toggle pytest coverage for `tests/test_todos.py` and `tests/test_integration.py` remains green.
- [x] The client-side delete flow in `src/app/static/js/app.js` still removes the todo row with `swap: 'delete'`; no new client-side count math is introduced.

## Scenarios

### Delete incomplete todo updates sidebar immediately

- **Given** an authenticated user is viewing a `TodoList` whose sidebar badge shows `3` incomplete todos
- **When** the user deletes one incomplete `Todo` from that list
- **Then** the todo row is removed and the same successful HTMX response updates `#list-{list.id}-count` to `2`

### Delete completed todo keeps incomplete count stable

- **Given** an authenticated user has a `TodoList` with `2` incomplete todos and `1` completed todo
- **When** the user deletes the completed `Todo`
- **Then** the todo row is removed and the OOB badge update still shows `2`

### Delete last incomplete todo renders zero

- **Given** an authenticated user has a `TodoList` with exactly `1` incomplete `Todo`
- **When** the user deletes that `Todo`
- **Then** the sidebar badge updates to `0` in the delete response and no full page reload is required

### Unauthorized delete does not update the sidebar

- **Given** a user attempts to delete a `Todo` that belongs to another user's `TodoList`
- **When** the delete request reaches `/api/todos/{todo_id}`
- **Then** the server rejects the request and does not return an OOB sidebar count fragment

## Scope & Boundaries

### In Scope

- Successful `/api/todos/{todo_id}` delete responses for authenticated owners return the existing sidebar count target update as an OOB partial.
- Sidebar count recomputation continues to use the server-side incomplete-only count semantics already defined for the list badge.
- Automated tests cover the incomplete-delete happy path, completed-delete count stability, zero-count edge case, and rejected-delete guard.

### What We're NOT Doing

- Changing the delete dialog UX or the `htmx.ajax()` delete trigger in `src/app/static/js/app.js` – the client-side row removal contract already works.
- Refactoring create/toggle/delete into a new shared response abstraction – this defect only needs the existing delete route to honor the established OOB pattern.
- Changing sidebar markup or styling beyond the existing count span – the bug is stale state, not presentation.
- Expanding 403/404 delete responses into HTML error partials – the backlog item only requires the successful delete path to refresh the count.

## Architecture Decision

**We will**: render the existing `partials/todo_deleted_oob.html` from `delete_todo()` after commit, with the updated value from `_get_list_todo_count()`.

**Rationale**: this matches the current HTMX-first server-rendered OOB pattern, reuses markup that already targets the correct sidebar span, and keeps count semantics on the server where completed-todo deletes are handled correctly.

**Alternatives considered**:

1. **Client-side decrement in `app.js`** – rejected: duplicates server truth and produces wrong counts when the deleted todo was already completed.
2. **Return a larger composite partial or refresh the full sidebar** – rejected: broader DOM churn than needed when a dedicated delete OOB partial already exists.

## Technical Overview

### UI/UX Design

No visible redesign is required. A successful delete continues to remove `#todo-{id}` through the existing HTMX `swap: 'delete'` behavior while the response body also updates the sidebar badge out-of-band.

### Data Models

No schema or model changes are needed. `TodoList` ownership rules remain unchanged, and the sidebar badge continues to represent incomplete `Todo` rows only.

### Integration Points

- `src/app/routes/todos.py` – delete route behavior and count helper reuse
- `src/app/templates/partials/todo_deleted_oob.html` – OOB response fragment for sidebar badge refresh
- `src/app/static/js/app.js` – existing HTMX delete target/swap contract
- `tests/test_todos.py` and `tests/test_integration.py` – response-body and regression coverage

## Code Patterns & External References

> Code-pattern pointers only. Read surrounding code before implementation.

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:33-37                  | Existing incomplete-count helper to reuse for delete responses
file   | src/app/routes/todos.py:125-132                | Create-todo success path already returns count OOB update
file   | src/app/routes/todos.py:243-283                | Toggle success path is the primary OOB-response reference
file   | src/app/routes/todos.py:286-306                | Delete route defect location and current success/error contracts
file   | src/app/templates/partials/todo_item_with_oob.html:1-4 | Existing composite OOB fragment structure
file   | src/app/templates/partials/todo_deleted_oob.html:1-2   | Dedicated delete OOB fragment already targeting the sidebar badge
file   | src/app/templates/partials/todo_list_item.html:20      | Canonical `#list-{id}-count` badge target
file   | src/app/static/js/app.js:163-173               | HTMX delete request target and `swap: 'delete'` behavior
file   | tests/test_todos.py:84-92                      | Current delete baseline test to extend with response assertions
file   | tests/test_integration.py:163-179              | Existing OOB regression-test pattern for toggle
file   | tests/conftest.py:71-77                        | Authenticated client fixture for success-path tests
```

## Constraints & Gotchas

- **Constraint**: successful todo deletes are issued with `htmx.ajax('DELETE', url, { target: #todo-{id}, swap: 'delete' })` – Workaround: return only the OOB count fragment on success; HTMX will still delete the targeted row.
- **Avoid**: computing the new badge value from client-side DOM state or before the delete commit – Instead: recompute with `_get_list_todo_count()` after `db.commit()` so completed deletes and zero-count cases stay correct.
- **Critical**: `delete_todo()` currently returns bare `Response` objects for 403/404 – Must handle by: preserving those non-success contracts unless a separate requirement expands the error-rendering scope.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful todo deletes return an OOB sidebar count refresh from the server
  - Follow the success-path pattern in `src/app/routes/todos.py:243-283` and reuse `src/app/templates/partials/todo_deleted_oob.html:1-2`; keep the current delete request target/swap contract in `src/app/static/js/app.js:163-173`.
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodos::test_delete_todo_updates_sidebar_count -q` proves the response is `200`, the `Todo` row is removed from the database, the response body contains `hx-swap-oob`, and the badge value matches the remaining incomplete todo count.

- [x] **TI02** Delete-count semantics stay correct for completed and zero-state edge cases
  - Reuse `_get_list_todo_count()` from `src/app/routes/todos.py:33-37` and the badge target contract from `src/app/templates/partials/todo_list_item.html:20`; this task depends on TI01's success-response shape.
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodos::test_delete_completed_todo_keeps_sidebar_count tests/test_todos.py::TestTodos::test_delete_last_incomplete_todo_updates_sidebar_count_to_zero -q` proves completed deletes do not decrement the badge and deleting the last incomplete todo renders `0`.

- [x] **TI03** Regression coverage proves the HTMX delete flow aligns with existing OOB behavior and rejected deletes stay quiet
  - Mirror the toggle regression pattern at `tests/test_integration.py:163-179` and add a rejected-delete check without widening the route's current 403/404 contract; this task depends on TI01/TI02 response semantics.
  - **Verify**: `uv run pytest tests/test_integration.py::test_todo_delete_updates_count tests/test_todos.py::TestTodoAccess::test_cannot_delete_other_users_todo_does_not_emit_oob -q` proves successful deletes emit the badge update and rejected deletes do not contain `hx-swap-oob`.

### Testing Strategy

- [TI01] Scenario: Delete incomplete todo updates sidebar immediately → route test asserts DB deletion plus `hx-swap-oob` response content with the decremented count.
- [TI02] Scenario: Delete completed todo keeps incomplete count stable → route test seeds completed state, deletes it, and asserts the returned badge value is unchanged.
- [TI02] Scenario: Delete last incomplete todo renders zero → route test deletes the final incomplete todo and asserts the response contains the exact `0` badge value.
- [TI03] Scenario: Unauthorized delete does not update the sidebar → access-control test asserts the response is rejected and contains no OOB fragment.
- [TI03] Scenario: Delete incomplete todo updates sidebar immediately → integration test mirrors the existing toggle OOB assertion so delete and toggle both prove the shared HTMX contract.

### Validation

- Run `./run.sh` or `uv run uvicorn app.main:app --reload`, sign in as `demo@example.com` / `demo123`, then delete one incomplete todo, one completed todo, and the last remaining incomplete todo from an active list; confirm the sidebar badge updates immediately after each delete without a page reload.

### Execution Contract

- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.

## Final Validation Checklist

- [x] **All success criteria** met
- [x] **All tasks** fully completed, verified, and checkboxes checked
- [x] **No regressions** or breaking changes introduced
- [x] **UI verified** to match requirements

## Implementation Observations

### Run: 2026-05-03T14:45:22+02:00
#### NOTICED BUT NOT TOUCHING
- `uv run pytest` full-suite currently has pre-existing failures in `tests/test_todos.py::TestTodos::test_create_todo` and `tests/test_todos.py::TestTodos::test_update_todo`; they are unrelated to `BUG-001`.
- `ruff` is not installed in this environment, so no dedicated lint/type command is available here.
- `dartclaw-ops`/`/dartclaw-review`/`/dartclaw-visual-validation-specialist` are unavailable in this environment, so those prescribed ops/review commands were executed manually via available tooling.
- Non-scope findings surfaced during external review include unrelated defects in `docs/PRODUCT-BACKLOG.md` items (`BUG-002`, `BUG-003`, `BUG-004`) and CSRF concerns in `src/app/core/deps.py`; these are outside this FIS.
