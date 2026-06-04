# Architecture Review – e2e-plan-and-implement

## Executive Summary

The reviewed change set is narrowly scoped and fixes two defect stories (BUG-002 and BUG-003) without introducing new modules, packages, or cross-module coupling. No dependency cycles, service-style boundaries, or import-layer migrations were added. I found one low-severity architectural maintenance issue and no medium-or-higher findings.

- Findings count: 2 total
- Medium-or-higher findings: 0
- Most impactful issue: priority-default meaning is represented in multiple layers (`database`, `route`, `template`), creating a repeated domain rule.
- Most impactful recommendation: centralize priority fallback values/constants to one domain location to keep model, route, and render behavior aligned.

## How to Read This Report

- `Ca` = inbound dependencies (afferent).
- `Ce` = outbound dependencies (efferent).
- `I` = instability (`Ce / (Ca + Ce)`, 0 stable, 1 volatile).
- `A` = abstractness fraction (abstract types / total types).
- `D` = `|A + I - 1|`.
- `C4 Level`: Context / Container / Component / Code.

This review is scoped to files changed on branch vs base that are covered by `docs/specs/e2e-plan-and-implement/plan.json` (no full-project refactor scope).

## Metrics Dashboard (Scoped)

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `src/app/routes/todos.py` | 1 | 4 | 0.80 | 0.00 | 0.20 | OK | HTMX route boundary; no new imports introduced in this change set. |
| `src/app/database.py` | 4 | 1 | 0.20 | 0.00 | 0.80 | Zone of Pain warning band (pre-existing domain model role) | Default added to `Todo.priority`; no new outbound package edges. |
| `src/app/templates/partials/todo_item.html` | 0 | 0 | N/A | N/A | N/A | Template boundary | New render-time `effective_priority` fallback centralizes only one field at fragment boundary. |
| `tests/test_todos.py` (scope-removed assertions) | 0 | 0 | N/A | N/A | N/A | Test layer | Regression ownership moved into bug-specific suites intentionally. |

## Findings

### ARCH-001: Duplicate Priority Default Contract Across Domain, Route, and Render Layers

**Severity**: LOW
**Dimension**: coupling
**C4 Level**: Code
**Category**: Convention

**Evidence**: `src/app/database.py` sets `Todo.priority` default as `"low"`; `src/app/routes/todos.py` hardens missing/invalid priority to `"low"`; `src/app/templates/partials/todo_item.html` adds template-level fallback `effective_priority = todo.priority if todo.priority else 'low'`.

**Connascence** (if applicable): `CoM` – Strength: 3, Degree: 3, Locality: 3 → Severity: 3.0 (intra-file convention coupling amplified across three architectural surfaces)

**Impact**: Priority default value is duplicated in at least three places. A future domain change (e.g., default value, synonym, or enum extension) requires coordinated edits and risks drifting behavior between create-time persistence and render-time behavior.

**Recommendation**: Per CUPID and Page-Jones locality rules, define a single domain constant set (default and allowed values) and reference it from model default, route validation, and template normalization (`effective_priority`). This keeps semantic alignment and reduces convention drift.

**Fitness Function**: Add a small test/CI check that asserts `Todo.priority` default, update-route fallback, and template render contract all resolve through the same constant set (for example `ALLOWED_PRIORITIES = ("low", "medium", "high")`, `DEFAULT_PRIORITY = "low"`).

**Fix Prompt**: Create a shared constants module (e.g., `src/app/domain/priorities.py`) with `PRIORITY_LOW = "low"` and `PRIORITY_CHOICES`; replace hard-coded `"low"` literals in `database.py`, `routes/todos.py`, and `templates/partials/todo_item.html`.

### ARCH-002: No New Structural Coupling Introduced in Scope

**Severity**: INFO
**Dimension**: coupling
**C4 Level**: Component
**Category**: Convention

**Evidence**: Diff between base and branch shows only localized edits in `src/app/routes/todos.py` (date parser), `src/app/database.py` (column default), and `src/app/templates/partials/todo_item.html` (normalization for render), plus test refactors. No new module or package imports were introduced outside existing layers.

**Impact**: No added architecture risk from coupling growth is observed.

**Recommendation**: Keep route/model/template edits in a single vertical slice and retain one regression test bundle per defect as currently done.

**Fitness Function**: Per change set, compare import graph snapshots and fail CI on new edges crossing previously disjoint modules.

**Fix Prompt**: Add an architecture-lint check in CI that requires `src/app/routes/todos.py` dependency set to remain a superset of the allowed package imports list.

## Dependency Graph (Condensed DAG)

```text
app.main -> app.routes -> {app.core.deps, app.database, app.utils}
app.main -> app.database
app.main -> app.utils
app.routes.auth -> {app.core.deps, app.database}
app.routes.pages -> {app.core.deps, app.database, app.utils}
app.routes.todo_lists -> {app.core.deps, app.database, app.utils}
```

No cycles introduced by this plan. The `todo_item` fragment sits below route responses and receives only already-resolved model data.

## Decomposition Recommendations

No decomposition changes warranted. Keep this as-is for now: the defects are intentionally thin, and boundaries remain aligned with the current HTMX-first architecture.

## Proposed Fitness Functions

1. **Priority Contract Single Source Check**
- **What it checks**: All priority defaults/allowed values come from a single constant source.
- **Threshold**: Any hard-coded default/allowed priority literal not sourced from `app.domain.priorities` fails.
- **Governance level**: 3 (component)
- **Implementation**: Static grep + minimal parser test in CI.
- **Findings addressed**: ARCH-001

2. **Scoped Dependency Delta Check**
- **What it checks**: Plan-scoped changes must not add new package/module dependencies outside an allow-list.
- **Threshold**: No new package edges outside existing `app.routes` -> `app.database`/`app.core.deps`/`app.utils` graph.
- **Governance level**: 3
- **Implementation**: Lightweight import graph snapshot in CI for `src/app/routes` and `src/app/database.py`.
- **Findings addressed**: ARCH-002

## Decision Trace

Report path resolved via review-report-location tier 2 spec-directory match: `docs/specs/e2e-plan-and-implement`.
