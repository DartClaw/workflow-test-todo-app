# Architecture Review Report - bug-001-sidebar-incomplete-count-delete

## Executive Summary
The review is focused on the changed files for `docs/specs/bug-001-sidebar-incomplete-count-delete.md`, and no architecture-level regressions were introduced by the fix.
Findings count is 0 across all severities. The route currently remains a leaf orchestration module that now reuses existing count and OOB patterns instead of introducing new coupling.
The highest-impact outcome is that `delete_todo` now returns an OOB badge fragment on success while preserving existing error contracts.
The strongest recommendation is to keep this pattern localized in the todo routes and avoid moving count logic into the client.

## How to Read This Report
- **Ca**: number of local packages that depend on this package.
- **Ce**: number of local packages this package depends on.
- **I**: instability, `I = Ce / (Ca + Ce)`.
- **A**: abstractness (not measured here because route modules are concrete handlers).
- **D**: distance from the ideal main sequence, `D = |A + I - 1|`.
- **C4 Level**: `Context`, `Container`, `Component`, `Code`.
- The review uses package-level review lenses plus file-level coupling checks at the HTMX/OOB boundary.

## Metrics Dashboard (Scope: changed package set)

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| app.routes | 1 | 3 | 0.75 | 0.00 | 0.25 | Balanced | Orchestrates HTMX endpoints; stable wiring layer with one inbound consumer (`app.main`). |

Graph-level metrics (local scope):
- CCD: 4
- ACD: 4.00
- NCCD: 1.00 (proxy from 1-node local scope)

## Findings
No validated architecture findings in the changed scope.

## Dependency Graph
- `app.main` -> `app.routes` (existing, pre-change)
- `app.routes` -> `app.core`, `app.database`, `app.utils`

No cycles detected in the touched package boundary. No new import chains were introduced by the patch.

## Decomposition Recommendations
No decomposition action is warranted for the touched scope.

## Proposed Fitness Functions
- Add a route contract regression test that asserts every successful mutation endpoint that updates sidebar state (`toggle_todo`, `delete_todo`) returns a fragment containing the expected `hx-swap-oob` target under `id="list-<list-id>-count"`.
- Add a mutation-path static lint rule/check for `_get_list_todo_count` usage on all todo state mutations to avoid divergent counting logic.

