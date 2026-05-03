# Architecture Review: bug-002-bug-003

## 1) Executive Summary
No architectural regressions were identified in the branch delta for this plan. The change is scoped to the todo route module and its route-level regression tests, with behavior confined to existing request/response contracts and HTMX partial rendering paths. I found no package coupling changes, dependency-cycle risks, or layer-boundary violations introduced by the edits. The most impactful outcome is that due-date parsing and default-priority behavior are now centralized in-route helpers and constants, reducing branching ambiguity in the edited handlers. The dominant recommendation remains to keep additional contract tightening inside this same module to avoid widening blast radius.

## How to Read This Report
- **Scope**: only files changed between the branch and base ref under `src/app/routes/todos.py` and `tests/test_todos.py`.
- **C4 levels**: `Component` = route module and test module (no service/container boundaries changed), `Code` = handler/helper-level details.
- **Principles**: `SDP` (Stable Dependencies Principle), `SAP` (Stable Abstractions Principle), `ADP` (Acyclic Dependencies Principle).
- **Connascence**: only cross-module static naming/typing references were touched; no dynamic connascence (`CoE`, `CoTm`, `CoV`, `CoI`) was introduced.

## 2) Metrics Dashboard
| Package | Notes |
|---|---|
| `src.app.routes` (component) | No new outbound/import edges added in the delta; module boundary remains unchanged |
| `tests` (component) | Scope-expanded assertions only; no app-surface coupling added |

## 3) Findings

### Findings by severity
No findings above INFO were identified in the reviewed delta.

- **INFO / none**: Scope remained unchanged at the route/test component level, and no architectural rule violations were detected.

## 4) Dependency Graph (condensed)
The relevant dependency path remains a linear boundary from existing Flask/FastAPI route logic to models/utilities/templates:
`routes/todos.py` -> `database`, `utils`, `templates`, `models`

No new edges were introduced, and no cycles were added or exposed by this change.

## 5) Proposed Fitness Functions

| Name | What it checks | Threshold | Why |
|---|---|---|---|
| `todo-route-field-contract` | In route tests, verify `update_todo` rejects malformed `due_date` and accepts dialog contract format `YYYY-MM-DD` | Add/keep regression tests covering both cases | Prevents silent field-loss and format drift |
| `route-response-contract` | Quick-add and update responses must include expected metadata attributes used by OOB/rehydration path | Preserve existing assertions on `data-todo-priority` / `data-todo-due-date` | Guards against metadata contract regressions that break dialog reopen flow |

## 6) Recommendation Summary
No architecture-level remediation is required for this plan delta. Continue monitoring for any future changes that introduce additional responsibilities into `todos.py` (e.g., parsing/validation policy, formatting policy, and persistence logic migration into separate services) if the route grows beyond current scope.
