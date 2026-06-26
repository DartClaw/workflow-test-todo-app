# Architecture Review: bug-001-sidebar-incomplete-count-updates-on-delete

## Executive Summary
Scope: review of branch changes vs `5cc0228` for `docs/specs/bug-001-sidebar-incomplete-count-updates-on-delete.md`, `src/app/routes/todos.py`, and `tests/test_todos.py` (no additional package scope).
This small HTMX-first fix remains aligned with the existing Todo-domain architecture: mutation responses still flow through HTML partials, and count updates are reused via the shared `_get_list_todo_count` helper.
No architectural regressions were found in the touched routing, template-contract, or test scope.
Findings count is 0 across all severities.

## How to Read This Report
- **Scope**: source-code review constrained to files changed in this branch and listed in the spec scope.
- **Severity/Dimension/C4**: kept only if a concrete finding exists; none were identified.
- **Mode context**: `review` mode, single-file deltas in Python route + test layer.
- **Finding legend**: `N/A` because no findings were validated.

## Metrics Dashboard
Per-package/package-equivalent metrics were not recomputed for this scoped delta review.

| Package/Module | Ca | Ce | I | A | D | Zone | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `src.app.routes.todos` | N/A | N/A | N/A | N/A | N/A | N/A | Scoped change only; no package-metric shift detected as part of this review. |
| `tests.test_todos` | N/A | N/A | N/A | N/A | N/A | N/A | Test suite extension only. |

## Findings
### No validated findings
No architecture-level findings passed the filtering gate.

### Archived Context (evidence reviewed)
- `src/app/routes/todos.py`
  - `delete_todo` now returns HTMX partial `partials/todo_deleted_oob.html` on successful delete.
  - Existing `404/403` error paths remain plain `Response(status_code=...)`, preserving prior semantics.
- `tests/test_todos.py`
  - New tests assert OOB badge fragment presence/count and unchanged count for completed deletes.
- Existing route contracts remain consistent with the established HTMX pattern (OOB count update via `hx-swap-oob` used for list/count mutations).

## Dependency Graph
- `src/app/routes/todos.py` → `app.database` (Todo, TodoList, session), `app.utils`, Jinja2 templates
- `tests/test_todos.py` → `app.database` (Todo model), fixture-provided DB/session/auth
- No new external dependencies, no new package cycles.

## Decomposition Recommendations
No decomposition recommendations generated.

## Proposed Fitness Functions
- [ ] Add a focused contract test for delete semantics: when `DELETE /api/todos/{todo_id}` returns 200, response must contain exactly one `hx-swap-oob="true"` badge fragment for `#list-<list_id>-count`; when `404`/`403`, response must contain no `hx-swap-oob` marker.
  - Governance level: 2 (route-level contract guard)
  - Tooling: existing pytest suite (`uv run pytest tests/test_todos.py -k delete_todo`)
  - Prevents reintroduction of sidebar desync and guards silent response-shape drift.
