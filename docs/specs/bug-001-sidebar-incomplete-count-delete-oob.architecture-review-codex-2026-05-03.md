# Architecture Review: BUG-001 sidebar incomplete-count delete OOB update

## Executive Summary
This branch change is structurally narrow and mostly additive: it updates only the todo deletion route plus regression tests and bug-spec documentation. Dependency shape for the touched runtime path remains a small acyclic flow from `app.main` → `app.routes` → `{app.core, app.database, app.utils}`. No new package-level cycles, and no package exceeds coupling thresholds that would indicate a decomposition regression. The successful delete response now mirrors the existing OOB count-update pattern used by create/toggle, which removes the prior stale-sidebar behavior while preserving HTMX swap semantics. One low-severity convention debt remains visible in this path: successful and failure delete responses still use different surface contracts (partial vs bare status response).

## How to Read This Report
- **Metrics**: `Ca` = inbound package dependents, `Ce` = outbound package dependencies, `I` = instability (`Ce / (Ca + Ce)`, 0 stable, 1 volatile), `A` = abstractness, `D` = distance from main sequence (`|A + I - 1|`), lower is healthier. Zone of Pain: low `I` + low `A` with high `D` (stable+concrete, hard to change safely); Zone of Uselessness: high `I` + high `A` with high `D` (abstract+unused).
- **Graph terms**: `CCD` = cumulative component dependency, `ACD` = average component dependency (CCD per node).
- **C4 levels** used here: `Component` = module/package slice, `Code` = file-level behavior.
- **Principles**: `C`ontext-`C`oupling principle checks use ADP (acyclic), SDP (stable dependencies direction), and SAP (stable abstractions).
- **Connascence**: `CoN`=name, `CoT`=type, `CoM`=meaning, `CoP`=position, dynamic forms include `CoE/CoTm/CoV/CoI`; any cross-package dynamic form is materially high.

## Metrics Dashboard

Scope: branch diff `5cc0228..HEAD` (runtime changes in `app.routes` + route-level tests).

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| app.routes | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Route entrypoint package for todo endpoints |
| app.main | 0 | 3 | 1.00 | 0.00 | 0.00 | OK | Container/wiring package |
| app.database | 2 | 0 | 0.00 | 0.00 | 1.00 | Pain (low-Ca) | Foundation model package |
| app.core | 1 | 0 | 0.00 | 0.00 | 1.00 | Pain (low-Ca) | Session/auth utility package |
| app.utils | 2 | 0 | 0.00 | 0.00 | 1.00 | Pain (low-Ca) | Shared format helpers |
| app.models | 0 | 0 | 0.00 | 0.00 | 1.00 | Unused by app package graph | Pydantic schema package, consumed mainly from tests |

Graph-level metrics: `CCD=13`, `ACD=2.17`, `NCCD` not computed (no Lakos-style graph tooling executed in this environment).

## Findings

### ARCH-001: Mixed response contract for delete success vs failure in todo deletion route

**Severity**: LOW
**Dimension**: testability
**C4 Level**: Code
**Category**: Convention

**Evidence**: `src/app/routes/todos.py` now returns `TemplateResponse` on success (`delete_todo`) at lines 310-315, while still returning bare `Response(status_code=404/403)` for missing/unauthorized cases (lines ~299-301). The route is mixed between HTMX-oriented partial responses and status-only responses in the same interaction.

**Connascence**: Per-file `CoN` only; no dynamic connascence detected across package boundaries.

**Impact**: The route can produce two transport contracts for the same endpoint (`DELETE /api/todos/{todo_id}`), which weakens uniform error-handling assumptions and makes future client-side/UX refactors harder to reason about at one glance.

**Recommendation**: Normalize delete responses to a single contract style where failure paths also emit explicit HTML partials, with `HX-Redirect` or an error partial per project convention, per `Predictable` behavior guidance in AGENTS and `app.main` error-handler standards.

**Fitness Function**: Add a route-contract check that flags endpoints under `app.routes` returning `Response(status_code=...)` directly when they also have successful `TemplateResponse` branches.

**Fix Prompt**: In `delete_todo`, return a partial (or explicit route error template) for 403/404 instead of status-only, while preserving 404/403 semantics for HTMX and tests.

## Dependency Graph Description
- `app.main` depends on `app.routes`, `app.database`, and `app.utils` (wiring layer).
- `app.routes` (todos/pages/lists/auth) depends on `app.core`, `app.database`, and `app.utils`.
- `app.models`, `app.core`, `app.database`, and `app.utils` are leaf-like foundations with no outbound app-internal dependencies.
- No package cycles detected in `src/app` imports.
- Leaves: `app.main`, `app.models`.
- Foundations: `app.core`, `app.database`, `app.utils`.

## Decomposition Recommendations
No decomposition action is indicated by this branch; touched logic remains within the existing route-layer boundary.

## Proposed Fitness Functions

1. **Name**: route-contract-consistency
   - **Checks**: Every route function returning partial UI success in `app.routes` must have matching failure responses that are also template-derived or explicitly documented.
   - **Threshold**: 0 mixed-success/failure response-style exceptions per HTTP route.
   - **Governance level**: 1 (local repo checks, run in CI).
   - **Implementation**: lint-like AST + AST-based unit tests using simple grep for `Response(` patterns in `@router` handlers that also call `TemplateResponse`.
   - **Addresses**: `ARCH-001`

2. **Name**: oob-delete-payload-preservation
   - **Checks**: Successful HTMX delete routes (`swap: 'delete'` interaction in frontend) must return `hx-swap-oob` or documented alternative in regression tests.
   - **Threshold**: 100% of such endpoints covered by at least one route-level test asserting OOB marker.
   - **Governance level**: 2 (pre-merge test policy + CI).
   - **Implementation**: extend route test conventions in `tests/` with marker assertions.
   - **Addresses**: `BUG-001` acceptance behavior and future accidental contract regressions.

### Decision Trace
Report location resolved via **review-report-location tier 2** (spec-directory match under `docs/specs/`).
