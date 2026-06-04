# Architecture Review: bug-001-sidebar-incomplete-count-delete

## Scope
- Target: `docs/specs/bug-001-sidebar-incomplete-count-delete.md`
- Reviewed files vs `origin/main`: `src/app/routes/todos.py`, `src/app/templates/partials/todo_deleted_oob.html`, `tests/test_todos.py`, `tests/test_integration.py`
- Scope note: packages outside `src/app/routes/todos.py` and related HTMX-count tests are out of scope.
- Decision trace: tier 2 spec-directory match (`docs/specs`)

## Executive Summary
The review was clean for the current bug-fix deltas. No new architectural anti-patterns or principle violations were introduced in the touched files. The change keeps behavior aligned with existing HTMX partial and OOB patterns in `routes/todos.py`, and uses a shared count query that avoids client-side counter drift. Severity summary is zero across all buckets: 0 critical, 0 high, 0 medium, 0 low, 0 info. The most important observation is that the branch appears internally consistent with surrounding route-layer conventions. The highest-impact recommendation is already in place: keep delete count updates derived from persisted data via `_get_list_todo_count` in the same response that drives HTMX interaction state.

## How to Read This Report
- C4 level: Context (system), Container (deployable runtime unit), Component (module/package), Code (route function / template / test).
- Metrics: `Ca` inbound component dependencies, `Ce` outbound component dependencies, `I = Ce / (Ca + Ce)` where higher means more volatile, `A` abstractness, `D = |A + I - 1|`.
- Principle labels used when referenced:
  - `Per SAP` = Stable Abstractions Principle (Martin)
  - `Per ADP` = Acyclic Dependency Principle
  - `Per SDP` = Stable Dependencies Principle
  - `Zone of Pain/Uselessness` from component/main-sequence distance.
- Connascence shorthand: `CoN`, `CoT`, `CoM`, `CoP`, `CoA` (static), `CoV` (variable type), `CoTm` (time), `CoI` (identity).

## Metrics Dashboard

| Component | Ca | Ce | I | A | D | Zone | Notes |
|-----------|----|----|---|---|---|------|-------|
| app.routes.todos | 1 | 3 | 0.75 | 0.00 | 0.25 | Healthy | New delete OOB path reuses existing helper and template style; no new cycle created |
| tests.test_todos | 0 | 0 | 0.00 | 0.00 | 1.00 | Neutral | Unit/integration-level coverage additions only |
| tests.test_integration | 0 | 0 | 0.00 | 0.00 | 1.00 | Neutral | Added regression scenarios only |

## Findings

No architectural findings.

## Dependency Graph
- `app.main` -> `app.routes.todos`
- `app.routes.todos` -> `app.core.deps`, `app.database`, `app.utils`
- `app.routes.todos` -> external packages (`fastapi`, `sqlalchemy`)

No dependency cycles were introduced. The new OOB flow keeps all arrows directed from the todo route layer to domain/data utilities and from application startup wiring into routes.

## Decomposition Recommendations
No decomposition changes required for this scope.

## Proposed Fitness Functions

1. **Delete-path contract consistency for HTMX OOB updates**
   - What: lint or test check to ensure all `delete_todo`-like success responses in `src/app/routes` that rely on `hx-swap="delete"` still include an OOB span for sidebar count when the action mutates list aggregate state.
   - Threshold: every route covered by HTMX delete handlers touching shared aggregates must return count OOB or a defined equivalent fragment.
   - Stack: 3
   - Why: prevents regressions to count drift in single-page HTMX interactions.

2. **Failure-path shape parity in API routes with UI contracts**
   - What: test rule to ensure 403/404 delete failures for routes with client-side contracts keep non-OOB status-only responses unless the contract explicitly requires error partials.
   - Threshold: explicit contract mismatch count must remain 0.
   - Stack: 4
   - Why: avoids accidental route contract regressions in mixed-response UI endpoints.
