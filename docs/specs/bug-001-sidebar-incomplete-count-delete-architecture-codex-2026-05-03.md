# Architecture Review: BUG-001 Sidebar incomplete-count updates on todo delete

## Executive Summary
This review is narrowly scoped to `docs/specs/bug-001-sidebar-incomplete-count-delete.md` and the files changed against base (`src/app/routes/todos.py`, `tests/test_todos.py`, plus linked spec artifacts). Overall architecture risk is low: the change keeps the existing HTMX OOB-first pattern inside the same module boundary and does not introduce new modules, dependencies, or cross-boundary coupling.
Architecture findings: 1 total (including 1 LOW), 0 medium-or-higher.
The key strength is reuse of an established response contract (`partials/todo_deleted_oob.html`) rather than creating a new interaction model.
The most impactful recommendation is to keep the response contract explicit in both implementation and tests as a single invariant (success emits `hx-swap-oob="true"`, failures do not).

## How to Read This Report
- `I` = instability (`0` stable, `1` volatile), `Ce` = efferent dependencies, `Ca` = afferent dependencies. In this scoped review we only report qualitative dependency notes; no full package metrics run was executed because the change footprint is isolated.
- C4 levels used: `Code` = a single file/function boundary, `Component` = route module (`src.app.routes.*`).
- Principles used: **ADP** (acyclic dependencies), **SDP** (stable dependencies), **SAP** (stable abstractions) from package-principle conventions.
- `hx-swap-oob` means HTMX out-of-band swap marker used to update non-target DOM regions in one response.
- A finding is `Code` level if it affects a specific route/test path; `Component` level if it changes module contracts shared across multiple routes.

## Metrics Dashboard (scope: `src.app.routes.todos`)
| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `src.app.routes` | 3 | 3 | 0.50 | 0.00* | 0.25* | OK | Route module is a leaf-like HTML API; imports are one-way (`app.core.deps`, `app.database`, `app.utils`) and unchanged by this fix. |
| `app` (boundary) | n/a | n/a | n/a | n/a | n/a | n/a | No new edges added by this change. |

3/4 values are qualitative placeholders in this scoped, non-computational pass.

## Findings
No MEDIUM+ findings in this scoped architecture pass.

### ARCH-001: Response contract boundary remains implicit for successful delete OOB updates

**Severity**: LOW
**Dimension**: Modularity
**C4 Level**: Code
**Category**: Convention

**Evidence**: `src/app/routes/todos.py:286-313` now returns `partials/todo_deleted_oob.html` on success while unauthorized/missing paths still return empty `Response(403/404)` bodies. The success path encodes the UI contract only in tests and template naming.

**Connascence**: CoN (naming) — Strength: 2, Degree: 1, Locality: 1 -> Severity: LOW

**Impact**: New implicit coupling exists between route behavior and frontend expectations (`hx-swap-oob="true"` plus `list-{list_id}-count`) but remains within existing BUG-001 scope.

**Recommendation**: Per the OOB-swap convention in `CLAUDE.md`, add/retain a short local contract comment or dedicated helper documenting that delete success must return OOB badge markup while 403/404 responses are intentionally body-less.

**Fitness Function**: Add a regression test gate (already partially present) that asserts success responses for delete include OOB count span and that 403/404 responses do not.

**Fix Prompt**: Keep delete behavior in `src/app/routes/todos.py` and add one invariant test in `tests/test_todos.py` verifying the response contract for each outcome.

## Dependency Graph (condensed)
- `src.app.routes.todos` → `app.core.deps`, `app.database`, `app.utils`, `fastapi`, `sqlalchemy`.
- `src.app.routes.todo_lists` imports a similar helper style and existing OOB helpers.
- No cycles are introduced by this change.
- Leaves/foundations in this scope: `src.app.core.deps`, `app.database` remain foundational for route modules.

## Decomposition Recommendations
No decomposition or split/merge recommendations. The change correctly reuses the existing route module and template contract.

## Proposed Fitness Functions
1. **Name**: `todo-delete-oob-contract`
   - **Checks**: Every successful `DELETE /api/todos/{id}` response should contain `hx-swap-oob="true"` and `#list-{list_id}-count`.
   - **Threshold**: 100% for tests covering delete success.
   - **Governance level**: 1
   - **Implementation**: Pytest contract assertions in `tests/test_todos.py` (already added).
   - **Addresses**: ARCH-001.

2. **Name**: `todo-delete-error-no-oob`
   - **Checks**: 403/404 delete responses must not include OOB swap markup.
   - **Threshold**: 100% for unauthorized/missing-delete scenarios.
   - **Governance level**: 1
   - **Implementation**: Pytest assertions in `tests/test_todos.py`.
   - **Addresses**: ARCH-001.

3. **Name**: `todo-count-post-delete-accuracy`
   - **Checks**: Deleting completed todos leaves count unchanged, incomplete todos decrements.
   - **Threshold**: 100% for both cases.
   - **Governance level**: 1
   - **Implementation**: DB + response assertions in `tests/test_todos.py`.
   - **Addresses**: Business-correctness drift.

**Decision Trace**: Report written to spec directory (tier 2 spec-directory match in `docs/specs/<feature>/`).
