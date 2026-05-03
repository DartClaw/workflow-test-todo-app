# Architecture Review: BUG-001 OOB Sidebar Count Sync on Todo Delete

## Executive Summary
Scope was limited to `docs/specs/bug-001-sidebar-incomplete-count-delete-oob.md` and its changed implementation/test surface in `src/app/routes/todos.py` and touched test files. The focused architecture is small and still follows a single `app.routes` orchestration pattern with explicit service dependencies (`app.core`, `app.database`, `app.utils`) and HTMX-partial response contracts. I found **0 findings** at the time of this review. Most recent changes increased consistency with the existing OOB pattern rather than introducing new structural coupling, cycles, or principle violations in the touched component boundary. The strongest recommendation is to formalize a lightweight regression check around HTMX OOB response contracts to guard against future drift in delete/toggle behaviors.

## How to Read This Report
- **Scope marker**: This review covers only files touched in the BUG-001 branch work and immediate intra-app dependencies used by those files.
- **C4 level**: `Context` (system), `Container` (runtime/service layer), `Component` (module/package), `Code` (file/function).
- **Package metrics**:
  - `Ca`: inbound dependency count (who depends on this package)
  - `Ce`: outbound dependency count (what this package depends on)
  - `I`: instability (`Ce/(Ca+Ce)`), `0` stable / `1` unstable
  - `A`: abstractness (abstract types / total types), `0` here means concrete
  - `D`: distance from main sequence, `|A+I-1|` where `<0.3` is healthy
- **Graph metrics**:
  - `CCD` and `ACD` are aggregate coupling measures over package reachability.
- **Principles**:
  - `ADP` = Acyclic Dependencies Principle
  - `SDP` = Stable Dependencies Principle (stable packages should not depend on volatile packages)
  - `SAP` = Stable Abstractions Principle (stable packages should be abstract)
- **Connascence shorthand** (strongest to weakest): `CoN`, `CoT`, `CoM`, `CoP`, `CoA`, `CoE`, `CoTm`, `CoV`, `CoI`.
- **Decision trace**: report location resolved via review spec-directory rule (`docs/specs/...`) because scope provided a spec artifact.

## Metrics Dashboard

| Package      | Ca | Ce | I    | A | D    | Zone         | Notes |
|--------------|----|----|------|---|------|--------------|-------|
| app.main     | 0  | 3  | 1.00 | 0 | 0.00 | OK           | Container entrypoint; routes/dependency wiring node |
| app.routes   | 1  | 3  | 0.75 | 0 | 0.25 | OK           | Route composition boundary for HTMX/HTML flow |
| app.core     | 1  | 0  | 0.00 | 0 | 1.00 | Zone of Pain (infra-like) | Stable utility/session boundary; no abstractions and no inbound beyond API layer |
| app.database  | 1  | 0  | 0.00 | 0 | 1.00 | Zone of Pain (infra) | ORM/model boundary with stable low-change role |
| app.utils    | 1  | 0  | 0.00 | 0 | 1.00 | Zone of Pain (infra-like) | Shared utility package with leaf-like behavior |

- **Graph-level metrics (primary scope DAG)**
  - `CCD`: 12
  - `ACD`: 2.40
  - `NCCD`: not computed (no Lakos-style baseline configured in this repository setup)

## Findings

No validated architecture findings.

### Summary
- `MEDIUM-or-higher`: 0
- `LOW/INFO`: 0

## Dependency Graph

Condensed package-level graph for touched scope:
- `app.main` → `app.routes`, `app.database`, `app.utils`
- `app.routes` → `app.core`, `app.database`, `app.utils`
- `app.core` → (no internal app package imports)
- `app.database` → (no internal app package imports)
- `app.utils` → (no internal app package imports)

No package cycles were observed in the touched scope.

Cross-boundary coupling observed at the touched edge set is static and explicit (function/module imports and shared IDs). No dynamic connascence (`CoE`, `CoTm`, `CoV`, `CoI`) was introduced by the bug-fix changes.

## Decomposition Recommendations

No decomposition/scope change needed for this touchpoint.

## Proposed Fitness Functions

1. **Name**: `htmx_oob_contract_smoke`
   - **Check**: For mutating HTMX endpoints in `app.routes`, assert that successful responses that are expected to update multiple UI regions include at least one `hx-swap-oob` marker and that error responses retain a deliberate HTML-partial or explicit non-partial protocol.
   - **Threshold**: 0 violations for files under `app/routes/todos.py`.
   - **Governance level**: 2 (every PR).
   - **Implementation idea**: lightweight pytest + response-body assertion on route integration tests.
   - **Targets**: stability of the BUG-001 delete/toggle OOB pattern.

2. **Name**: `fastapi_route_dependency_direction`
   - **Check**: Detect import cycles among `app` packages and assert route package import direction stays to dependency packages only (`app.routes` → `core`, `database`, `utils`).
   - **Threshold**: 0 cycles; no upward edges from dependency packages to route package.
   - **Governance level**: 1 (every commit in CI fast check).
   - **Implementation idea**: regex/AST-based import scanner in test or pre-commit hook.
   - **Targets**: ADP and accidental drift in package boundaries.

## References Reviewed

- `src/app/routes/todos.py` (scope and implementation)
- `src/app/templates/partials/todo_deleted_oob.html` (OOB contract)
- `src/app/static/js/app.js` (delete request handling and htmx swap semantics)
- `tests/test_todos.py`, `tests/test_integration.py` (regression coverage tied to delete OOB updates)
- `docs/specs/bug-001-sidebar-incomplete-count-delete-oob.md` (feature contract)
- `/Users/tobias/.agents/skills/andthen-architecture/references/mode-review.md`
- `/Users/tobias/.agents/skills/andthen-architecture/references/review-output.md`
- `/Users/tobias/.agents/skills/andthen-architecture/references/package-principles.md`
- `/Users/tobias/.agents/skills/andthen-architecture/references/architecture-calibration.md`
- `/Users/tobias/.agents/skills/andthen-architecture/references/review-calibration.md`

**Decision**: PASS for current review scope, with explicit watchpoint on OOB contract regression. The patch is architecturally aligned with existing HTMX + partial conventions.
