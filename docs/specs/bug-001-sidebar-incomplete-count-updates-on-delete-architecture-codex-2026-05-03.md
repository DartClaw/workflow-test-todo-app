# Architecture Review: BUG-001 delete-flow OOB update

Target path: `docs/specs/bug-001-sidebar-incomplete-count-updates-on-delete.md`
Scope: review only files changed vs base ref (`docs/specs/...`, `src/app/routes/todos.py`, `tests/test_todos.py`, `tests/test_integration.py`).
Decision trace: **tier 2 spec-directory match** (`docs/specs/`).

## 1. Executive Summary

This scoped review found **no critical/high/medium architectural findings** in the bug-fix diff.
The change is localized to the existing HTMX `app.routes.todos` delete path and its existing test contract, with no cross-package dependency graph changes and no new coupling boundaries.
Per ADP (Martin), no new cycles were introduced and the route-to-DB/view/deps dependency orientation remains acyclic and stable.
The most impactful outcome is that successful delete semantics were aligned with the established OOB pattern used by create/toggle without widening 403/404 contracts.

## 2. How to Read This Report

- **Ca**: inbound package dependents.
- **Ce**: outbound package dependencies.
- **I**: instability = `Ce / (Ca + Ce)` where 0 = stable, 1 = volatile.
- **A**: abstractness proxy from package boundary analysis (0.0 here for all concrete runtime packages).
- **D**: distance from main sequence = `|A + I - 1|`; values near 0 are healthiest.
- **C4 levels**: Context, Container, Component, Code.
- **ADP**: Acyclic Dependencies Principle.
- **SDP**: Stable Dependencies Principle (dependencies should point toward more volatile packages).
- **SAP**: Stable Abstractions Principle (stable packages should be abstract; this is flagged only when stable and heavily depended on).
- **Connascence notation**: CoN/CoM/CoP are static forms; CoE/CoV/CoI are dynamic and materially stronger across package boundaries.

## 3. Metrics Dashboard

Scope graph considered: `app.main`, `app.routes`, `app.core`, `app.database`, `app.utils`.

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| app.main | 0 | 3 | 1.00 | 0.00 | 0.00 | OK | Application entrypoint/wiring, expected leaf volatility |
| app.routes | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | HTTP controllers; stable behavior boundary |
| app.core | 1 | 0 | 0.00 | 0.00 | 1.00 | Warning | Invariant auth/session helpers consumed by routes |
| app.database | 2 | 0 | 0.00 | 0.00 | 1.00 | Warning | Storage foundation package with stable concrete API surface |
| app.utils | 2 | 0 | 0.00 | 0.00 | 1.00 | Warning | Formatting/date helper foundation |

Graph-level metrics for scope: 5 package nodes, 6 package edges, estimated CCD = 12, ACD = 2.40. For this small app, this reflects a thin, highly linear runtime graph with no transitive tangling.

## 4. Findings

### Finding count: 0 (all severities below gate)

No new architecture findings were identified on this branch delta.

- `src/app/routes/todos.py` now stores `list_id`, commits deletion, recomputes count via `_get_list_todo_count`, and returns `partials/todo_deleted_oob.html` for successful deletes. This keeps delete flow within the existing server-rendered partial contract and does not add new package boundaries.
  - Evidence references: `src/app/routes/todos.py` (DELETE handler change), `src/app/templates/partials/todo_deleted_oob.html`.
  - Principle check: ADP/SAP/SDP behavior unchanged by dependency orientation.
- `tests/test_todos.py` and `tests/test_integration.py` now assert success-path OOB presence plus failure-path no-OOB, which constrains cross-layer behavior without creating new coupling.
  - Evidence references: `tests/test_todos.py` tests for incomplete/completed/404/403 delete behavior; `tests/test_integration.py::test_todo_delete_updates_count_oob`.

### Connascence Scan (this scope)

- No dynamic connascence introduced across package boundaries (no CoE/CoV/CoI patterns in the new code path).
- Existing HTMX contract coupling (`#todo-{id}` target plus `list-{list_id}-count` OOB id convention) remains static naming coupling and unchanged in direction/format from prior create/toggle behavior.

## 5. Dependency Graph Description

Condensed DAG in this scope:
- `app.main -> app.routes`
- `app.main -> app.database`
- `app.main -> app.utils`
- `app.routes -> app.core`
- `app.routes -> app.database`
- `app.routes -> app.utils`

Foundational graph properties:
- Acyclic (no SCCs > 1 node).
- No upward volatile-to-stable inversion introduced by this change.
- `app.core`, `app.database`, and `app.utils` behave as foundation-style leaves for this feature.

## 6. Decomposition Recommendations

No decomposition or merge action is warranted from this bug-fix change.

## 7. Proposed Fitness Functions

1. **Delete OOB Contract Guard (Component scope)**
   - Check: For every successful `DELETE /api/todos/{id}` path in tests, assert response contains `hx-swap-oob="true"` and exact list-count shape, and that 403/404 paths return empty body.
   - Implementation: route/integration tests already added; keep as required checks in the relevant test module.
   - Prevents: silent reversion to status-only responses that would desync sidebar count.

2. **Scoped Package DAG Gate (Component scope)**
   - Check: periodic audit of import edges under `src/app` must remain acyclic and include no `app.routes -> app.main` reverse edge.
   - Implementation: lightweight grep-based edge check in CI (simple shell/regex pass), or dedicated dependency audit script.
   - Prevents: ADP regressions and accidental controller-to-main coupling.

3. **Boundary Contract Drift Gate (Component scope)**
   - Check: include an explicit test asserting `hx-swap-oob` ID and route response patterns are intentionally coupled at one shared template contract boundary (route + partial).
   - Implementation: keep the two response-shape assertions in `tests/test_todos.py` as non-removable regression gates.
   - Prevents: contract drift between HTMX delete client behavior and server fragments.
