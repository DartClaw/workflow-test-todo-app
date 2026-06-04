# Architecture Review – BUG-001 (Scope-Limited)

**Scope**: `docs/specs/bug-001-sidebar-incomplete-count-on-delete.md` and changed implementation in `src/app/routes/todos.py`, `src/app/templates/partials/todo_deleted_oob.html`, `tests/test_todos.py`.
**Date**: 2026-06-04
**Mode**: review
**Language**: Python / HTMX template rendering
**Decision Trace**: tier 2 spec-directory match (`docs/specs`)

## Executive Summary
This focused change has no additional architectural debt in the changed slice relative to `origin/main`.
Findings are clean across the requested scope: **0 total findings** and **0 MEDIUM-or-higher** findings.
The mutation path now aligns the delete flow with existing OOB counter-update conventions (matching toggle/create behavior) without introducing new package dependencies or coupling across new boundaries.
The most impactful outcome is that sidebar count synchronization is now co-owned by the same route-level boundary already responsible for todo mutations (`app.routes`).

## How to Read This Report
- **Scale**: Context | Container | Component | Code. This report maps all evidence to **Component/Code** for touched code in `app.routes`, route templates, and tests.
- **Metric legend**:
  - `Ca`: afferent coupling (incoming dependents)
  - `Ce`: efferent coupling (outgoing dependencies)
  - `I`: instability (`Ce/(Ca+Ce)`) where 0.0 is stable, 1.0 volatile
  - `A`: abstractness (abstract types / total types)
  - `D`: distance from main sequence (`abs(A+I-1)`) where <0.3 is generally healthy
- **Architecture principles**: ADP (acyclic deps), SDP (dependencies toward instability), SAP (stable packages should be more abstract), and per-package connascence minimization across boundaries.
- **Severity mapping**: CRITICAL, HIGH, MEDIUM, LOW, INFO.

## Metrics Dashboard
| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.routes` | 1 | 3 | 0.75 | 0.00 | 0.25 | OK (expected for route wiring) | Imports `app.core.deps`, `app.database`, `app.utils`; no outbound import of `app.routes` modules. |

## Findings
No findings. (0/0)

### Architecture Findings Filter
- No ADP violations in touched scope: no new cycles introduced.
- No SDP/SAP violations introduced in touched package boundaries.
- No dynamic cross-boundary connascence introduced (no new cross-boundary execution/value/identity assumptions).

## Dependency Graph
```
main
 └── routes
     ├── core.deps
     ├── database
     └── utils
```
- `app.routes` remains a leaf-level composition package with `I≈0.75`, expected for route handlers.
- `main` remains the only changed-scope importer of `app.routes` in the local graph.
- No cycles in the touched dependency subgraph.
- Foundation and leaf roles are preserved: `main` orchestrates, `routes` binds HTMX requests to shared utility/data/dependency packages.

## Decomposition Recommendations
No decomposition or merge recommendation is warranted for the changed scope. Keep counter recompute and OOB response logic in `app.routes` to maintain shared request-handler ownership and avoid introducing new coupling through a cross-cutting counter service.

## Proposed Fitness Functions
1. **Response contract co-location for HTMX mutating endpoints**
   - Check: all successful mutating endpoints under `app.routes` that mutate shared aggregate-derived UI state include corresponding `hx-swap-oob` updates for every shared fragment they mutate.
   - Why: prevents silent divergence between fragment updates and sidebar or aggregate badges after a future delete/reorder/create mutation.
   - Enforcement: add a focused integration test convention or static assertion on shared templates in `tests/test_todos.py`-style coverage.

2. **Template target-contract lint rule**
   - Check: shared OOB fragments targeting sidebar count must use `id="list-{{ list.id }}-count"` consistently and never fallback to a missing context key.
   - Why: prevents runtime ID drift and OOB no-op regressions.
   - Enforcement: add a template render smoke test that renders OOB fragments with representative list fixture and asserts target IDs.
