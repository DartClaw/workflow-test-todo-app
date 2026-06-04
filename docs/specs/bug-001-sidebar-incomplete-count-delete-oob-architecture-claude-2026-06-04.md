# Architecture Review – bug-001-sidebar-incomplete-count-delete-oob

## Executive Summary
The scope of this review is the current branch delta for `bug-001-sidebar-incomplete-count-delete-oob` (`src/app/routes/todos.py`, `tests/test_todos.py`, `tests/test_integration.py`).
The architecture remains structurally healthy in this slice: no new coupling cycles, no dynamic connascence across new boundaries, and no unstable-to-stable dependency reversals.
Finding count is 0 total; **0** are MEDIUM+.
The only notable improvement is retained: delete now reuses the existing OOB count-update pattern already used by toggle, minimizing new architectural surface area.

## How to Read This Report
- C4 levels use this report convention: **Context** (system), **Container** (runtime unit), **Component** (module/API slice), **Code** (function/file).
- Package metrics: `Ca` = inbound dependents, `Ce` = outbound dependencies, `I = Ce / (Ca + Ce)` when `Ca + Ce > 0`, `A` = abstractness (0.0 here for concrete modules), `D = |A + I - 1|`.
- This review targets only files changed on the branch versus `origin/main`, and applies source-code guardrails from the review mode template.
- Conventions: `ADP` = acyclic dependency principle, `SDP` = stable dependencies principle, `SAP` = stable abstractions principle.

## Metrics Dashboard

### Dependency snapshot (touched modules)

| Module | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| app.routes.todos | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | New behavior stays within existing `app.routes.*` + database/core/utils flow |
| tests.test_todos | 0 | 1 | 1.00 | 0.00 | 0.00 | OK | Adds behavioral assertions only; no new production coupling |
| tests.test_integration | 0 | 1 | 1.00 | 0.00 | 0.00 | OK | Adds scenario coverage for delete-count OOB contract |

*Assumption:* `Ca`/`Ce` here are scoped to in-repo package-level edges plus key internal callers.

## Findings

No architectural findings met threshold for reporting.

## Dependency Graph

- `app.main` -> `app.routes.todos`
- `app.routes.todos` -> `app.core.deps`
- `app.routes.todos` -> `app.database`
- `app.routes.todos` -> `app.utils`
- `app.routes.todos` -> external framework packages (`fastapi`, `sqlalchemy`)

No import cycles were introduced in this delta.

## Decomposition Recommendations

No decomposition changes are recommended from the reviewed delta.

## Proposed Fitness Functions

1. **FF-ARCH-001: HTMX mutation response contract for todo delete**
   - What it checks: Every successful `DELETE /api/todos/{id}` response should include an OOB badge fragment while 403/404 paths remain status-only (no OOB marker), enforced with a focused test assertion set.
   - Threshold: All new/updated tests for this route must assert mutually exclusive success/failure response shapes.
   - Evidence source: `tests/test_todos.py`, `tests/test_integration.py`, and `src/app/routes/todos.py`.
   - Governance level: 2 (module-level behavior contracts in request handlers)

2. **FF-ARCH-002: Single source of truth for incomplete count on todo mutations**
   - What it checks: `toggle_todo`, `create_todo`, and `delete_todo` must all derive badge updates from `_get_list_todo_count`.
   - Threshold: no route in `app.routes.todos` should add bespoke incomplete-count SQL.
   - Evidence source: changed and existing implementations in `src/app/routes/todos.py`.

## Decision Trace

Tier resolved: 2 (spec-directory match: docs/specs/ bug artifact), with filename emitted alongside the spec file.
