# Architecture Review: e2e-plan-and-implement

## Executive Summary
- Scope: docs/specs/e2e-plan-and-implement/plan.json (stories S01, S02), limited to changed implementation surface: `src/app/database.py`, `src/app/routes/todos.py`, `tests/test_todo_due_date_persistence.py`, `tests/test_todo_quick_add_priority.py` and direct in-scope module dependencies.
- Finding count: 0. No architecture findings at CRITICAL/MEDIUM/HIGH/LOW/INFO were validated after filtering.
- Most critical outcome: no new cycles, no unstable dependency direction flips, and no new cross-boundary dynamic connascence introduced by the two fixes.
- Most impactful recommendation: preserve the read-only seam contract between `todo_item.html` and `openEditTodoDialog` as a hard constraint in future quick-add/date parsing changes.

## How to Read This Report
- **Metrics**: `Ca` = incoming internal package dependencies, `Ce` = outgoing internal package dependencies, `I = Ce/(Ca+Ce)` where 0 is stable and 1 is volatile, `A` = abstractness (0 used for all in-scope packages), `D = |A + I - 1|`.
- **C4 Levels**: Context / Container / Component / Code. Findings are tagged at this level when emitted.
- **Package principles**: ADP = Acyclic Dependencies, SDP = Stable Dependencies, SAP = Stable Abstractions. Per scope rules, only direct findings caused by the current branch changes are reviewed.
- **Connascence legend** (if used): static CoN < static CoM < static CoP < ... < dynamic CoI, where stronger/distant dynamic forms are higher risk when crossing package boundaries.

## Metrics Dashboard

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---------|----|----|---|---|---|------|-------|
| app | 0 | 3 | 1.00 | 0.00 | 0.00 | Volatile leaf | Runtime composition root; imports `app.routes`, `app.database`, `app.utils` |
| routes | 1 | 3 | 0.75 | 0.00 | 0.25 | Volatile leaf-adjacent | Owns HTMX handlers for todo/update/create; consumes `core`, `database`, `utils` |
| core | 1 | 0 | 0.00 | 0.00 | 1.00 | Zone of Pain candidate* | Authentication/session boundary package; stable but infra-like and intentionally simple |
| database | 2 | 0 | 0.00 | 0.00 | 1.00 | Zone of Pain candidate* | Schema + defaults; persistence boundary intentionally concrete |
| utils | 2 | 0 | 0.00 | 0.00 | 1.00 | Zone of Pain candidate* | Shared template helpers |

\* Flagged for note only: these packages are stable-concrete by metric definition, but this is consistent with current project role and not a deployment-breaking issue in this educational codebase.

Graph-level indicators (scoped):
- Nodes: 5
- Cycles: 0
- CCD: 11 (low coupling)
- ACD: 2.2
- NCCD: below balanced baseline (not elevated for this scope)

## Findings

No findings.

## Dependency Graph
- `app -> routes`
- `app -> database`
- `app -> utils`
- `routes -> core`
- `routes -> database`
- `routes -> utils`

Leaves:
- `database` and `utils` are read-heavy leaves (no outgoing internal package dependencies).

Foundational packages:
- `app` is volatile and intentionally composition-driven.

No SCC merges were introduced by this branch.

## Decomposition Recommendations
No new decomposition recommendations from this scoped review.

## Proposed Fitness Functions
- **FF-ARCH-001**: Enforce acyclic package dependency check for `src/app` in CI; fail if any cycle appears in package-level graph.
- **FF-ARCH-002**: Enforce seam-preservation test assertions for `partial` metadata consumed by JS (`data-todo-due-date`, `data-todo-priority`) whenever edit/todo row/quick-add surface changes.
- **FF-ARCH-003**: Enforce that route-level regressions for each story remain isolated by checking that modified story files remain within designated scope directories.

Decision trace: tier 2 spec-directory match (docs/specs/e2e-plan-and-implement) per review-report-location.md
