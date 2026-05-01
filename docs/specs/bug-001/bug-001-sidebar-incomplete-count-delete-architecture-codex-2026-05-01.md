# Architecture Review: bug-001-sidebar-incomplete-count-delete

- **Date**: 2026-05-01
- **Scope**: `5cc0228..HEAD` diff scoped to `src/app/routes/todos.py`, `tests/test_todos.py`, and `docs/specs/bug-001/*`
- **Location Decision**: tier 2 spec-directory match (review target path is inside `docs/specs/bug-001/...`)

## Executive Summary
1. This review covers only files introduced or modified on the current branch relative to `5cc0228` and intentionally skips untouched packages.
2. The change set is a localized repair in the existing HTMX + FastAPI todo route: `delete_todo` now returns a partial with an out-of-band sidebar-count update and tests were expanded to assert the intended payload semantics.
3. No new modules, cross-package dependencies, or architectural boundaries were added.
4. **No architecture findings** were identified at this scope; the design now better aligns route behavior with the established OOB pattern already used by `toggle_todo`.
5. The most impactful recommendation is to keep this behavior consistent by adding a focused regression test contract for all HTMX HTML-only responses (including successful and forbidden/error paths).

## How to Read This Report
- **C4 levels** used: `Component` (route layer, template/test layer), `Code` (function-level logic in `delete_todo` and related tests).
- **OOB**: Out-of-band HTMX swap marker (`hx-swap-oob="true"`) used to update regions outside the request target.
- **Scope markers**: `scope` = files changed in `5cc0228..HEAD`; unchanged files are out of scope.
- **Severity** scale follows `review-output.md`: `CRITICAL > HIGH > MEDIUM > LOW > INFO`.

## Metrics Dashboard
| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.routes.todos` (modified component) | n/a | n/a | n/a | n/a | n/a | n/a | HTML-first route + DB access unchanged; response type changed from `Response(200)` to `TemplateResponse` for success path only |
| `tests.test_todos` (modified component) | n/a | n/a | n/a | n/a | n/a | n/a | Added assertions validate OOB payload and count semantics for success and non-happy paths |

No dependency graph or package-level metric changes were introduced by this diff; only behavior wiring changed within an existing component boundary.

## Findings

No findings (0).

## Dependency Graph
Within the touched scope, edges remain internal:
- `delete_todo` (`src/app/routes/todos.py`) -> SQLAlchemy ORM (`Todo`, `TodoList`) and `_get_list_todo_count` helper (same module)
- `delete_todo` success response -> Jinja partial `partials/todo_deleted_oob.html`
- route tests -> ORM (`Todo`) and route contract assertions

No new inter-component edges, cycles, or fanout changes were introduced.

## Decomposition Recommendations
No decomposition/recomposition actions are warranted for this scoped change. Keeping logic in `src/app/routes/todos.py` preserves established routing cohesion and avoids unnecessary indirection.

## Proposed Fitness Functions
1. **HTMX Delete Contract Guard**
   - **What**: Assert successful `DELETE /api/todos/{id}` responses include OOB badge payload when a `count` context is returned and must not include that payload on `404/403`.
   - **Threshold**: 1 (every 200 response for `delete_todo` must include `hx-swap-oob` and matching list count `span` when response body is partial HTML).
   - **Governance Level**: 1 (route-level test + regression suite).
   - **Findings addressed**: None (prevention for future drift).

2. **Error Contract Stability Guard**
   - **What**: Require tests for `404` and `403` to continue asserting no OOB fragment in the delete error body.
   - **Threshold**: 1 (non-happy-path delete tests must assert absence of OOB markers and status code preservation).
   - **Governance Level**: 1.
   - **Findings addressed**: None (prevents accidental expansion of response contract).

## Fitness Function Mapping to Findings
No findings were recorded, so no mandatory remediations are required.
