# Architecture Review – BUG-001 Delete Count OOB Sync

## Executive Summary

Current branch changes are scoped to `src/app/routes/todos.py` and the two todo-related test modules, with architecture impact constrained to one route layer and its test package. No package-level architectural violations were identified in the changed surface. Found 0 findings across all severities; there are no medium-or-higher findings requiring gating action. The most important result is that the delete-path OOB synchronization is now aligned with the existing toggle OOB pattern without introducing new dependency cycles or instability. The most actionable recommendation is to keep a focused regression guard for `DELETE /api/todos/{id}` OOB markers to prevent drift between route responses and HTMX delete semantics.

## How to Read This Report

- `Ca` = number of in-project packages depending on this package.
- `Ce` = number of in-project package dependencies this package depends on.
- `I` = instability (`Ce / (Ca + Ce)`, range `0..1`).
- `A` = abstractness (`abstract_type_count / total_type_count`).
- `D` = distance from main sequence (`|A + I - 1|`).
- `I` is interpreted as `Context` package health only; no container or deployment split is introduced by this scope.
- `Zone of Pain` = stable + concrete (`I≈0`, `A≈0`, high change cost), `Zone of Uselessness` = volatile + abstract (`I≈1`, `A≈1`).
- `C4` levels used here: `Component` (route and test modules), `Code` (handler and helper boundaries).
- `Conventions`: ADP = acyclic dependencies, SDP = stable dependencies, SAP = stable abstractions.

## Scope and Method

- Reviewed scope: `origin/main...HEAD` diff for `src/app/routes/todos.py`, `tests/test_todos.py`, `tests/test_integration.py`, and `docs/specs/bug-001-sidebar-incomplete-count-on-todo-delete.md`.
- Skipped packages outside this boundary: `app.pages`, `app.todo_lists`, `app.core`, auth/static assets, and other test modules.
- Evidence sources: `git diff`, direct file inspection, and local import graph for changed modules.
- Review date: `2026-06-04`.

## Metrics Dashboard

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.routes` | 1 (`app.main`) | 3 (`app.core`, `app.database`, `app.utils`) | 0.75 | 0.00 | 0.25 | Healthy | Endpoint-level container; no stable-but-concrete pressure.
| `tests` | 0 | 1 (`app.database`) | 1.00 | 0.00 | 0.00 | Healthy | Short-lived verification package; volatile-by-design.

Graph-level check in changed scope:
- SCCs: none (acyclic).
- ADP: PASS (no dependency cycles).
- SDP: PASS (no edge from lower-`I` to higher-`I` package in changed dependency edge set).
- SAP: PASS (`app.routes` is volatile and concrete, not expected to be abstract).

## Findings

No validated architecture findings were raised for the scoped changes.

## Dependency Graph (Changed Scope)

`app.main` → `app.routes` → (`app.core`, `app.database`, `app.utils`)
`tests` → `app.database`

Leaves and foundations:
- Leaf: `tests` (no dependents in this scope, `I=1.00`).
- Foundation: `app.routes` depends only downward into utility/data/auth; no reverse lock-in observed.

## Decomposition Recommendations

No decomposition recommendation is warranted by current diff metrics.

## Proposed Fitness Functions

1. **`check_todo_delete_oob_contract`**
   - Level: Component / request contract
   - Check: For `delete_todo` success, assert response body contains `hx-swap-oob="true"` for `id="list-<list_id>-count"` and no HTML primary row payload with `swap='delete'` contract.
   - Threshold: must be true for all happy-path delete tests.
   - Suggested implementation: a route-focused pytest assertion in `tests/test_integration.py` and `tests/test_todos.py`.

2. **`check_error_body_absence_on_reject`**
   - Level: Component
   - Check: Missing/unauthorized delete requests return `403`/`404` with no OOB markers.
   - Threshold: zero unexpected `hx-swap-oob` bytes on error responses.
   - Suggested implementation: shared helper assertion in test suite.

3. **`check_count_recompute_source_of_truth`**
   - Level: Component / Code
   - Check: All post-mutation count updates use server-computed `_get_list_todo_count` rather than client-side heuristics.
   - Threshold: all delete/toggle count-update paths must source count from DB query.
   - Suggested implementation: static review plus assertion-focused tests.

## Decision Trace

Resolved path: review report directory via tier 2 spec-directory match (`docs/specs/`) for the requested scope `docs/specs/bug-001-sidebar-incomplete-count-on-todo-delete.md`.
