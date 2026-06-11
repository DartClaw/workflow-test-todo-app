# Architecture Review – bug-001-sidebar-incomplete-count-delete-oob

## Executive Summary

Scope is the diff from `5cc022878c28af49d723f55ca70343f0b979ec0d` to `07b569e80c8c8c810edc8b4513bcfdf0cdc9e4ee`, limited to `src/app/routes/todos.py`, `tests/test_integration.py`, `tests/test_todos.py`, and `docs/specs/bug-001-sidebar-incomplete-count-delete-oob.md`. The review found **0 findings**. Most quality risks remain in functional behavior rather than structure; no architectural coupling or layering regressions were detected in the touched module surface. The change aligns delete behavior with the established OOB interaction contract without widening the swap surface. The remaining recommendation is to keep the route-level contract tests tightly scoped and stable.

## How to Read This Report

`Ca`/`Ce` are inbound/outbound import dependencies at package scope. `I = Ce/(Ca+Ce)` is instability, `A` is abstractness, and `D = |A + I - 1|` is distance from the main sequence. `C4 Level` is `Context`, `Container`, `Component`, or `Code`.

This review is scoped and does not compute full-repo graph metrics. Labels only apply where evidence exists in changed artifacts.

## Metrics Dashboard

| Package/Scope | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `src.app.routes` | 5 | 4 | 0.44 | 0.00 | 0.56 | Warning | Focus area; route imports `core`, `database`, `utils`, templates |
| `tests` | 2 | 8 | 0.80 | 0.00 | 0.20 | OK | New tests extend existing coverage for OOB contract |
| `docs.specs.bug-001-sidebar-incomplete-count-delete-oob` | N/A | N/A | N/A | N/A | N/A | N/A | Doc artifact with implementation and acceptance updates |

Graph-level metrics were not recomputed across the full repository for this scoped review.

## Findings

No architectural findings were identified at MEDIUM or above for this scoped change set.

## Dependency Graph

- `src.app.routes.todos` depends on `app.core.deps`, `app.database`, `app.utils`, and Jinja2 templates.
- `tests.test_todos` depends on `app.database` and route-facing behavior.
- `tests.test_integration` depends on `app.database` plus the test client stack.
- No new cross-module cycles were introduced by this change set.

## Decomposition Recommendations

None required from this change set. The fix remains in the existing `todos` route surface and its established HTMX response pathway.

## Proposed Fitness Functions

1. Add a route-contract test that ensures successful delete returns HTMX OOB markup and failure paths return bare non-HTML status responses. Scope: `src.app.routes.todos`. Check: incomplete delete, completed delete, and missing ID response shapes. Prevents regression: accidental replacement of the OOB-only success contract.
2. Add a fragment contract assertion for `partials/todo_deleted_oob.html` usage. Scope: `src.app.routes.todos` and `tests`. Check: presence of `id="list-<list_id>-count"` and `hx-swap-oob` in successful delete payloads. Prevents regression: swapped target IDs or missing OOB marker changes.

Report location resolution: tier 2 spec-directory match (same feature spec directory).
