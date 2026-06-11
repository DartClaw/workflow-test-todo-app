# e2e-plan-and-implement architecture review (plan scope)

## Executive Summary

Reviewed files introduced by `docs/specs/e2e-plan-and-implement/plan.json` against base ref show limited structural risk.
The update path stays inside the existing HTMX-first architecture: the edit/update and quick-add paths remain isolated and no new cross-cutting package cycles were introduced.
Findings count: 1 (LOW, 0 MEDIUM+, 0 HIGH/CRITICAL).
The only actionable issue is in the newly changed test slice: test module symbol references were added without corresponding imports, which weakens the plan’s verification layer.

## How to Read This Report

**Mode(s)**: review  
**Scope**: `src/app/routes/todos.py`, `src/app/database.py`, `tests/test_todos.py` (plan-scoped delta from base ref)  
**Primary language**: Python (FastAPI + SQLAlchemy + Jinja2)  
**C4 levels used**: Code, Component  
**Metrics**:
- `Ca` = inbound dependencies, `Ce` = outbound dependencies
- `I = Ce / (Ca + Ce)`, `A` = abstractness (not formally measured, all concrete in changed modules), `D = |A + I - 1|`
- ADP = Acyclic Dependency Principle, SDP = Stable Dependencies Principle, SAP = Stable Abstractions Principle

## Metrics Dashboard

| Package/Module | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.routes.todos` | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Routes layer depends on `app.core.deps`, `app.database`, `app.utils`; no outwardly problematic coupling. |
| `app.database` | 4 | 0 | 0.00 | 0.00 | 1.00 | Pain (watchlist) | Source of truth model package; stable-and-concrete is acceptable in this scale because it is low-churn and foundational. |
| `tests.test_todos` | 0 | 1 | 1.00 | 0.00 | 1.00 | OK | Test leaf; no production coupling concerns. |

## Dependency Graph (condensed)

- `app.main` → `app.routes.todos` (single use, leaf adapter)
- `app.main` → `app.database`
- `app.routes.todos` → `app.core.deps`
- `app.routes.todos` → `app.database`
- `app.routes.todos` → `app.utils`
- `tests.test_todos` → `app.database`
- `tests.test_todos` → `app.core.deps` (runtime import inside access-control tests)

No dependency cycles were introduced by this plan-scope delta.

## Findings by Severity

### ARCH-001: Missing standard-library imports in new due-date scenario tests

**Severity**: LOW  
**Dimension**: testability  
**C4 Level**: Code  
**Category**: Convention

**Evidence**: `tests/test_todos.py` now uses `date` and `datetime` in the new S01 regression tests (`test_update_todo_due_date_round_trip`, `test_update_todo_clear_due_date`, `test_update_todo_rejects_malformed_due_date`) but the module header imports only `pytest` and `app.database` on line 1-5. This delta is confined to touched files from this plan and leaves those new acceptance scenarios unable to execute reliably.

**Connascence**: CoN across module boundary to Python stdlib symbols – weak form, but a missing import in touched tests creates deterministic runtime faults in exercised tests.

**Impact**: Verification quality degrades because the newly added route-level scenarios for BUG-002 do not run as expected when Python executes the test module; regressions in S01 can become partially unobservable.

**Recommendation**: Re-add required imports (`from datetime import date, datetime`) next to existing top-level imports in `tests/test_todos.py`. Keep all route-level scenario data factories and assertions in one import section to avoid local-name drift.

**Fitness Function**: Add a CI guard for touched test modules: `python -m py_compile tests/test_todos.py` (or equivalent static import check) on each integration branch to prevent undefined-symbol regressions in test code.

**Fix Prompt**: In `tests/test_todos.py` line 1 block, add `from datetime import date, datetime` and re-run the touched due-date tests (`uv run pytest tests/test_todos.py -k \"due_date_round_trip or clear_due_date or rejects_malformed\"`).

## Decomposition Recommendations

- No decomposition changes recommended; story boundaries remain intentionally isolated between update-path and create-path fixes.

## Proposed Fitness Functions

1. **Touchpoint import completeness (module)**  
   - Check: `python -m py_compile <changed_files>` for changed Python files in branch scope.  
   - Threshold: no compile failures.  
   - Governance: CI gate 1.  
   - Applies to: `tests/test_todos.py` and all touched route/model modules.

2. **Plan-scoped import hygiene (module)**  
   - Check: `rg -n \"\\bdate\\b|\\bdatetime\\b\" src/app/routes/todos.py tests/test_todos.py` against import block to ensure external symbols referenced in new assertions are declared.  
   - Threshold: every reference must have an explicit module import.  
   - Governance: CI gate 2 (developer warning).  
   - Prevents a repeat of `ARCH-001`.

## Decision Trace

Report location resolved via spec-directory tier (review target doc scope): `docs/specs/e2e-plan-and-implement/`.
