# Architecture Review Report: e2e-plan-and-implement (S01/S02)

## Executive Summary
This review covers only the branch changes introduced for plan `docs/specs/e2e-plan-and-implement/plan.json` and the two owned story implementations (S01 and S02). The code changes remain within the existing boundary structure: `src/app/routes/todos.py`, `src/app/database.py`, and focused test modules. No `HIGH` or `MEDIUM` architectural findings were validated. The most important result is that the merge-safe ownership split (due-date edit persistence vs quick-add default priority ownership) is preserved in implementation. The highest-impact guidance is to keep the default-priority decision adjacent to the persistence seam (model) while continuing to enforce dialog/row behavior through shared integration seams, as already done.

## How to Read This Report

- **Scope**: changed files vs base for this branch only, excluding untouched packages.
- **Metric legend**: `Ca` = inbound module/package dependents, `Ce` = outbound module/package dependencies, `I = Ce / (Ca + Ce)`, `A` = abstract types ratio (all 0 for concrete modules here), `D = |A + I - 1|`.
- **C4 levels used**: Context (system-level), Container (deployment/runtime), Component (intra-app module/package), Code (file/function).
- **Architecture principles**: ADP (acyclic deps), SDP (stable→unstable direction), SAP (stable packages should be abstract), plus connascence taxonomy where dynamic crossing is highest risk.
- **Report note**: resolved via review-location tier 2 (spec-directory match).

## Metrics Dashboard

| Package/Component | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.routes.todos` | 1 | 3 | 0.75 | 0.00 | 0.25 | Useful unstable leaf | `main.py` routes via `include_router`; depends on deps/model/templates. |
| `app.database` | 11 | 0 | 0.00 | 0.00 | 1.00 | Zone of pain-adjacent | Shared persistence anchor reused by runtime and tests. |
| `tests` (focused: `test_todos.py`, `test_quick_add_priority.py`) | 0 | 1 | 1.00 | 0.00 | 1.00 | Uselessness-adjacent | Outgoing dependency to persistence model, no reverse dependencies in-tree. |

Graph-level metrics were computed only for the review slice and counted against import edges discoverable in the current tree (`src/app` + `tests`).

## Findings

No findings meet validated severity thresholds in the reviewed scope.

## Dependency Graph (condensed)

`tests` → (`app.database`) → (`app.routes`)

- No dependency cycles in the reviewed graph.
- `app.routes.todos` does not import from tests (no back-edge from runtime to test code).
- Both story seams (`update_todo` and model defaulting) stay within the same directed runtime direction and do not cross into additional runtime packages.

## Decomposition Recommendations

No decomposition changes are warranted for this scope.

## Proposed Fitness Functions

1. **Merge-Split Ownership Guard (Project-level)**
   - **What it checks**: changed files for plan-owned stories must remain within declared ownership seams in `plan.json` (e.g., S01 edits only due-date edit persistence path, S02 owns quick-add creation default). 
   - **Threshold**: zero files outside `src/app/routes/todos.py`, `src/app/database.py`, `tests/test_todos.py`, `tests/test_quick_add_priority.py` for this plan unless status changes are approved by a re-plan.
   - **Governance level**: 3
   - **Why**: preserves merge safety and avoids cross-seam coupling regressions.

2. **Priority-Default Regression Gate**
   - **What it checks**: quick-add path tests must explicitly assert persisted default priority remains visible through a render/hydration cycle.
   - **Threshold**: test coverage for low/explicit non-low persistence and reopen behavior remains green.
   - **Governance level**: 1
   - **Why**: ensures S02 remains implemented at the persistence seam and does not regress into client-only masking.
