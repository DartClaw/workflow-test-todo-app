# Architecture Review Report

## Scope

- **Mode**: review
- **Target**: changes introduced on branch `40fd463..HEAD` for `docs/specs/e2e-plan-and-implement/plan.json` (stories S01 + S02)
- **Review boundary**: changed code files only: `src/app/routes/todos.py`, `src/app/database.py` (plus dedicated test files for evidence)
- **Decision trace**: resolved to tier 2 via spec-directory match `docs/specs/e2e-plan-and-implement`

## Executive Summary

This review scope is healthy and narrowly scoped: both defect-fix stories preserved boundary isolation and retained existing HTMX partial-response patterns.
Found 1 issue, all at LOW severity.
Most notable: ORM-level persistence defaults now diverge from the checked-in SQLite schema because the project has no migration path.
Most impactful recommendation: persist the `Todo.priority` default as a schema-level contract (or add startup validation/backfill), so model-level assumptions remain true across persisted data.

## How to Read This Report

- **Packages/containers reviewed**: `app.database`, `app.routes`, and the new regression tests.
- **Metric legend**:
  - `Ca`: incoming package dependencies
  - `Ce`: outgoing package dependencies
  - `I = Ce / (Ca + Ce)` (instability)
  - `A`: inferred abstractness (0 here because these are concrete modules)
  - `D = |A + I - 1|` (distance from main sequence)
- **Severity legend**: `CRITICAL | HIGH | MEDIUM | LOW | INFO`
- **C4 level legend**:
  - **Code** = file-level logic and contracts
  - **Component** = module-level boundaries in `app/`
  - **Container** = service/runtime assembly in `main.py`
  - **Context** = entire product
- **Fitness function** = an automated guard (test, lint check, startup assertion) that should prevent the same architectural drift from reappearing

## Metrics Dashboard

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.database` | 10 | 0 | 0.00 | 0.00 | 1.00 | Boundary (core storage) | Foundation module for Todo persistence; no internal code drift observed in this slice |
| `app.routes` | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Controller layer remains a leaf-like composition node in this scope |

Per-slice graph-level metrics (scope-limited), no cycles detected:
- `CCD`: 1
- `ACD`: 2.0
- `NCCD`: 0.11

## Findings

### ARCH-001: Persisted-priority default lives only at ORM object level while DB schema remains nullable

**Severity**: LOW  
**Dimension**: governance  
**C4 Level**: Component  
**Category**: Convention  

**Evidence**:  
- `src/app/database.py` changed `Todo.priority` to `Column(String(10), default="low", nullable=False)`.  
- Startup still relies on `Base.metadata.create_all` in `src/app/database.py` and `src/app/main.py`; there is no migration layer.  
- Checked-in `todo.db` is already present in the workspace and currently reports the `todos.priority` column as nullable (`PRAGMA table_info(todos)` shows `notnull = 0`), so persistence contract and ORM contract are not lockstep.
- The same issue affects the storage boundary (`app.database`) and any out-of-band writes to old rows before app restart.

**Connascence** (if applicable):  
CoN (name) – Strength: 1, Degree: 2, Locality: 3 -> Severity: 1.5  
(UI and route code now assume the same semantic meaning for “priority” as the ORM default across storage boundaries)

**Impact**:  
Contract drift risk between persisted data and application assumptions. A future DB state with `NULL` priorities can leak into class generation in `templates/partials/todo_item.html` (`priority-{{ todo.priority }}`) and edit-dialog hydration, producing inconsistent rendering even before functional failures.

**Recommendation**:  
Per DDD aggregate-boundary discipline, enforce the `priority` default and non-null contract where persistence is defined. Add either:
- a migration-style startup check that verifies schema invariants (`notnull` and allowed default), or
- a SQL-backed data remediation step at startup that normalizes legacy `NULL` priorities to `low`.

**Fitness Function**:  
Add a startup or CI test that asserts SQLite schema compatibility:
`PRAGMA table_info(todos)` must report `notnull = 1` for priority, and sample rows created/loaded across startup paths must always expose `"low" | "medium" | "high"`.

**Fix Prompt**:  
Define a single persistence boundary contract check in `src/app/main.py` (or a startup helper in `src/app/database.py`) that fails fast if `todos.priority` is nullable or if any existing row has a NULL/invalid `priority` value.

## Dependency Graph

Observed condensed edges in the reviewed slice:
- `main` -> `app.database`, `app.routes` (router aggregate), `app.utils`
- `app.routes.todos` -> `app.core.deps`, `app.database`, `app.utils`
- Tests for BUG-002/BUG-003 -> `app.database` (validation-only, no production cycle)

No dependency cycles were introduced by these changes.

## Decomposition Recommendations

No decomposition changes required in this scope.

## Proposed Fitness Functions

1. **FF-DB-PRIORITY-CONTRACT-001**
   - **What it checks**: `Todo.priority` is present and non-null in both ORM metadata and SQLite file schema.
   - **Threshold**: `notnull = 1` and no legacy row with invalid `priority`.
   - **Governance level**: 2 (CI gate + startup guard)
   - **Implementation**: SQL schema assertion in startup tests and optional runtime check in `init_db` path.
   - **Findings addressed**: ARCH-001
