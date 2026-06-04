# Architecture Review: BUG-001 Delete Refreshes Sidebar Incomplete Count

Date: 2026-06-04
Mode: review
Scope path: `docs/specs/bug-001-delete-refreshes-sidebar-incomplete-count.md`
Scope strategy: current branch diff vs `origin/main`; touched artifacts only.
Source:
- `docs/specs/bug-001-delete-refreshes-sidebar-incomplete-count.md`
- `src/app/routes/todos.py`
- `src/app/templates/partials/todo_deleted_oob.html`
- `tests/test_todos.py`

Tier decision: **tier 2 spec-directory match** (`docs/specs/`), per review-report-location.

## Executive Summary
Implemented changes are narrowly scoped to BUG-001 and do not introduce architectural regressions on the reviewed diff. The edit keeps the existing HTMX-first contract while adding server-rendered out-of-band sidebar count updates on todo delete. No new cycles, coupling reversals, or API-boundary risk patterns were introduced in the changed files. Findings count is **0** (CRITICAL=0, HIGH=0, MEDIUM=0, LOW=0, INFO=0).

## How to Read This Report
- **C4 Level**: Context (system), Container (service/runtime boundary), Component (module/file group), Code (individual function/file).
- **Metric legend**: `Ca` = afferent dependents, `Ce` = efferent dependencies, `I = Ce/(Ca+Ce)`, `A` = abstractness (0 when concrete only), `D = |A + I - 1|`.
- **Architecture principles**: ADP (acyclic dependencies), SDP (dependencies should point toward less stable code), SAP (stable packages should be abstract).
- **Connascence**: only static forms are used for this path, with no boundary-crossing dynamic connascence added.

## Metrics Dashboard
| Artifact | Type | Ca | Ce | I | A | D | Zone | Notes |
|---|---|---:|---:|---:|---:|---:|---|---|
| `app.routes.todos` | Component | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Added OOB return from delete; depends on `app.core.deps`, `app.database`, `app.utils` only. |
| `tests.test_todos` | Component | 0 | 1 | 1.00 | 0.00 | 0.00 | OK | Test-only consumer path; no new inbound coupling introduced. |
| `todo_deleted_oob.html` | Partial | n/a | n/a | n/a | n/a | n/a | N/A | Template artifact, OOB span id contract aligned with existing UI contract. |

No new package-level cycle was introduced by the diff. Pre-existing external package graph shape is unchanged in this scope.

## Findings
No architectural findings were identified in the touched scope.

### Notes on unchanged-semantics risk
- The spec explicitly required preserving 403/404 semantics. The review confirms the route still returns bare `Response(status_code=403/404)` for failed delete pre-conditions and only returns TemplateResponse on success.
- The existing `swap: 'delete'` contract is preserved for HTMX because success payload remains HTML plus `hx-swap-oob` marker; delete target removal still executes on the client side.

## Dependency Graph
`app.routes.todos` (target) → `app.core.deps`, `app.database`, `app.utils`.

`tests.test_todos` (target) → `app.database`, `app` model classes.

No reverse edges were added from low-level data/model modules to route logic by this change. No cycle in reviewed scope.

## Decomposition Recommendations
No decomposition changes required for this scoped fix.

## Proposed Fitness Functions
- **Route contract test coverage (container-level)**
  - Check: `tests/test_todos.py` must include a success delete test asserting `hx-swap-oob="true"`, id-target presence `list-<id>-count`, and expected count values for at least three state transitions (incomplete, completed, zero remaining).
  - Purpose: prevent regression of OOB sidebar update semantics after future delete flow edits.

- **Boundary contract stability (code-level)**
  - Check: on delete failures (missing/unauthorized), response must stay non-HTML body status semantics (`404`/`403`) while success responses remain UI-processable HTMX fragments.
  - Purpose: keep contract symmetry across UX and permission failures.

- **Template-ID contract (component-level)**
  - Check: all count-update OOB fragments targeting sidebar use canonical id `list-<list_id>-count`.
  - Purpose: avoid silent DOM divergence from existing selector contract in `todos.html`/rendered list containers.
