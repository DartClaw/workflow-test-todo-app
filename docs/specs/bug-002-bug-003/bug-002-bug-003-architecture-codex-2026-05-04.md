# Architecture Review: `bug-002-bug-003`

## Executive Summary
The reviewed delta under `docs/specs/bug-002-bug-003/plan.md` is structurally small and localized to a single route module plus its regression tests. I found no architectural violations introduced by the two stories (`S01`, `S02`) when compared to the existing codebase structure, and the changes did not add new coupling across architectural boundaries. Severity distribution is 0 findings across CRITICAL/HIGH/MEDIUM/LOW/INFO for this scope. The most valuable recommendation is to keep the newly added due-date validation and default-priority behavior in `src/app/routes/todos.py` (the current boundary where request contracts are translated into model state), with test coverage in `tests/test_todos.py` as the regression gate.

## How to Read This Report
- `Ca` = number of internal packages/modules that depend on the module.
- `Ce` = number of internal packages/modules the module depends on.
- `I` = instability (`Ce / (Ca + Ce)`), where `0.0` is stable and `1.0` is unstable.
- `A` = abstractness (`0.0` fully concrete).
- `D` = distance from the main sequence (`|A + I - 1|`), with lower values preferred.
- `C4 Level` = **Component** (internal module/API boundary) in this review.
- `ADP` = Acyclic Dependencies Principle.
- `SDP` = Stable Dependencies Principle.
- `SAP` = Stable Abstractions Principle.
- `Connascence` terms: `CoN` means coupling by shared name, `CoM` by shared meaning, and the dynamic forms (`CoE`, `CoTm`, `CoV`, `CoI`) are treated as higher-risk when they cross module boundaries.

## Scope
- Scope path: `docs/specs/bug-002-bug-003/plan.md`
- Reviewed deltas (plan and implementation): `src/app/routes/todos.py`, `tests/test_todos.py`.
- Skipped unchanged packages and modules outside `S01`/`S02` diff surface.

## Metrics Dashboard
| Module | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `src.app.routes.todos` | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Web adapter boundary; depends on `app.core.deps`, `app.database`, `app.utils`; no new inbound dependencies added by the patch |
| `tests.test_todos` | 0 | 1 | 1.00 | 0.00 | 0.00 | OK | Regression layer only; no structural coupling added to product runtime graph |

## Findings
No new findings were identified at the scope of this patch.

## Dependency Graph (condensed)
- `app.main` -> `app.routes.todos`
- `app.main` -> `app.routes.todo_lists`
- `app.main` -> `app.routes.pages`
- `app.main` -> `app.routes.auth`
- `app.routes.todos` -> `app.core.deps`
- `app.routes.todos` -> `app.database`
- `app.routes.todos` -> `app.utils`
- `tests.test_todos` -> `app.database`

No cycles introduced in this scope, and no new package-level dependencies were added.

## Decomposition Recommendations
No decomposition, merge, or abstraction extraction recommendation is warranted for this patch set.

## Proposed Fitness Functions
1. **Name**: Route Dependency Drift Check
   - **What it checks**: `app.routes.todos` should not introduce new non-framework imports outside `app.core`, `app.database`, and `app.utils` without explicit review.
   - **Threshold**: No new non-test internal imports outside this allowlist in this module without adding a review finding.
   - **Governance tier**: 1
   - **Detection idea**: lightweight AST/grep check over `src/app/routes/*.py` in CI.
   - **Remediation target**: preserves the route-to-core/db boundary and prevents accidental cross-layer drift.

2. **Name**: Due-Date Contract Guard
   - **What it checks**: update handler must explicitly reject unsupported due-date formats and return `partials/error.html` without mutating todo state.
   - **Threshold**: every due-date update path has explicit parse/reject branches covered by tests.
   - **Governance tier**: 1
   - **Detection idea**: add a focused route-level test marker or property check in `tests/test_todos.py` asserting response type/data stability on invalid input.
   - **Remediation target**: prevents silent data drift from partial parsing failures.
