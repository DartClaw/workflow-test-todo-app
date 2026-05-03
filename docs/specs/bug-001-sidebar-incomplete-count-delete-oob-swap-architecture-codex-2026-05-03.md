# Architecture Review: BUG-001 OOB delete sidebar count

**Scope**: Branch-introduced changes scoped to `docs/specs/bug-001-sidebar-incomplete-count-delete-oob-swap.md` and affected implementation/test files.
**Date**: 2026-05-03
**Mode**: review
**Project**: Todo App (Python, HTMX + FastAPI + Jinja2)
**Decision trace**: tier 2 spec-directory match (`docs/specs`).

## Executive Summary

The review finds no structural regressions in package dependency shape from the bug-fix changes. The changed path adds one HTMX OOB response path from `delete_todo` without introducing new package dependencies, cycles, or fan-out explosions. Findings are limited to two low-risk consistency issues and one missing automated guard in the tested area. The most important action is to harden route-contract checks so OOB/fragment behavior remains intentional as this pattern expands.

- Findings count: 3 total
- Severity distribution: 0 critical, 0 high, 0 medium, 1 low, 2 info
- Most impactful recommendation: standardize route error/response contracts for todo mutation endpoints and enforce via a lightweight route-contract fitness function.

## How to Read This Report

- `Ca` is afferent coupling: number of packages that depend on this package.
- `Ce` is efferent coupling: number of packages this package depends on.
- `I` is instability (`Ce / (Ca + Ce)`), 0 stable to 1 volatile.
- `A` is abstractness (`abstract types / total types`), currently 0 in this codebase for reviewed packages.
- `D` is distance from main sequence (`|A + I - 1|`), high values mean drift.
- `CCD`, `ACD`: package reachability aggregates (`CD` = number of nodes reachable including self, `CCD` sum, `ACD` average reachability).
- `C4` levels: Context | Container | Component | Code.
- `ADP`, `SDP`, `SAP`: Martin package principles (acyclic, stable dependencies, stable-abstractions).
- `Zone of Pain`: concrete, stable package (`I≈0`, `A≈0`) with high coupling pressure.
- `Zone of Uselessness`: abstract, unstable package (`I≈1`, `A≈1`) with no dependents.
- Connascence scale used: `CoN` (name) to `CoI` (identity), static to dynamic. Dynamic types are higher risk when crossing package boundaries.

## Metrics Dashboard

Per-package metrics are computed from current import edges in `src/app` (package view):

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| app.main | 0 | 3 | 1.00 | 0.00 | 0.00 | OK | Entry package, high I expected |
| app.routes | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Stable outward dependency direction |
| app.utils | 2 | 1 | 0.33 | 0.00 | 0.67 | Watch | Low abstraction + nontrivial coupling |
| app.core | 1 | 0 | 0.00 | 0.00 | 1.00 | Watch | Stable and concrete support package |
| app.database | 3 | 0 | 0.00 | 0.00 | 1.00 | Watch | Stable storage foundation |
| app.models | 0 | 0 | 0.00 | 0.00 | 1.00 | Uselessness-adjacent (standalone) | Detached by current architecture |

Graph-level metrics:
- CD values: `app.main=5`, `app.routes=4`, `app.utils=2`, `app.core=1`, `app.database=1`, `app.models=1`
- `CCD=15`, `ACD=2.14`
- `NCCD`: not computed in this environment (Lakos/`pydeps` unavailable for this environment)

## Findings

### ARCH-001: Mixed HTML contract for 4xx responses inside todo mutation routes

**Severity**: LOW
**Dimension**: coupling
**C4 Level**: Component
**Category**: Convention

**Evidence**: `src/app/routes/todos.py` returns HTML partials on most validation and missing-authorized paths, e.g. `src/app/routes/todos.py:50-57`, `153-160`, `183-188`, while `delete_todo()` and `reorder_todo()` return bare `Response` statuses for 403/404 (`src/app/routes/todos.py:294-302`, `326-332`). The current fix preserved this behavior per spec, but the route surface is now used in mixed client pathways with HTMX-first semantics (delete handler in `static/js/app.js` uses `target`/`swap` swap modes tied to HTML fragments).

**Connascence**: CoN (name/shape of route contract) — strength 1, degree 2, locality 1 -> severity 2.0

**Impact**: Divergent route contracts increase coupling between client handlers, tests, and future middleware because error and success envelopes are not normalized. This makes failure-mode handling harder to reason about as additional todo endpoints are added.

**Recommendation**: Per Martin, keep boundary behavior consistent by documenting a route contract policy in `app.routes` and applying it uniformly: either all mutation endpoints in this package return HTML fragments (including failures) or failures are explicitly standardized with tests and comments when raw status codes are intentional.

**Fitness Function**: Level 2 structural check. Script all route files under `src/app/routes/` to assert one of two explicit response contract classes per endpoint family:
1) fragment-first JSONless HTMX routes, or 2) raw status routes only with a whitelisted exception list; fail on mixed use without comment/metadata.

**Fix Prompt**: `Create a lightweight route contract lint rule in CI to block accidental introduction of mixed TODO mutation error responses, then either normalize `delete_todo()` and `reorder_todo()` to fragment responses or annotate them as intentional exceptions with a tracked ADR.

### ARCH-002: OOB-count assertion logic is brittle and duplicated across test layers

**Severity**: INFO
**Dimension**: testability
**C4 Level**: Code
**Category**: Convention

**Evidence**: `tests/test_todos.py` uses a regex parser for the OOB marker in `_extract_oob_count()` (`tests/test_todos.py:15-24`), while integration tests include a duplicate hardcoded marker assertion (`tests/test_integration.py:198-199`). Both are coupled to exact attribute order (`id=... hx-swap-oob="true"`) rather than to a semantic helper.

**Connascence**: CoM (meaning/format convention) across tests and server template output — strength 3, degree 2, locality 1 -> severity 6.0 (low due same component)

**Impact**: Any future template markup change requires edits in multiple test modules before assertions pass, increasing churn and making OOB contract drift harder to detect earlier.

**Recommendation**: Per Ousterhout (APoSD Ch. 4, depth), keep HTMX OOB contract checks in one helper fixture and share a semantic assertion helper for integration and unit routes.

**Fitness Function**: Level 1 fast check. Add a shared test utility in `tests/conftest.py` for OOB count extraction and fail PRs that duplicate direct string/regex assertions for `hx-swap-oob` markers.

**Fix Prompt**: `Refactor both OOB assertions to call tests/conftest.py::extract_oob_count_by_list_id and remove duplicated marker text construction from individual test functions.`

### ARCH-003: `app.models` is currently disconnected from route/runtime package use

**Severity**: INFO
**Dimension**: coupling
**C4 Level**: Component
**Category**: Zone analysis

**Evidence**: In the current package graph, `app.models` has `Ca=0` and `Ce=0` (`app.models` row in dashboard), while `src/app/database.py` is used directly by route handlers and pages.

**Connascence**: Not applicable (no cross-package edge)

**Impact**: This indicates the model package does not currently participate as a dependency unit; the main data contract is concentrated through `app.database` ORM classes. If `app.models` is intended as future domain layer, this is an architectural signal worth tracking to avoid speculative boundaries.

**Recommendation**: Per CUPID and DDD alignment, keep this as an explicit non-blocking observation: either wire `app.models` into a concrete consumer path or move remaining model definitions under `app.database` if the split remains unused.

**Fitness Function**: Level 3 periodic check. Add a script to flag disconnected packages (`Ca=0`, `Ce=0`) with nontrivial LOC and report as governance debt, not immediate failure.

**Fix Prompt**: `Decide ADR for app.models: either remove placeholder split (move files), or add integration path and tests showing domain use.`

## Dependency Graph Description

Condensed DAG edges are:
- `app.main` -> `app.routes`, `app.database`, `app.utils`
- `app.routes` -> `app.core`, `app.database`, `app.utils`
- `app.utils` -> `app.database`
- Leaves (I≈1): `app.main` and `app.routes` are execution-oriented leaves.
- Foundations (I≈0): `app.database` and `app.core` have only incoming edges.
- No cycle was detected in observed imports.

Per-package risk profile is healthy for this scope: no `Ce > 10`, no ADP violations, and `app.routes` now has one additional success-path partial return without adding any new package edges.

## Decomposition Recommendations

No split/merge is warranted from this scoped change. Maintain current boundaries for now.

## Proposed Fitness Functions

1) **FF-1: route-response-contract-policy**
- **What it checks**: enforce a documented contract for each route module: fragment-first routes return `TemplateResponse` consistently, unless route is in an explicit exception list.
- **Threshold**: any unapproved mixed contract is a violation.
- **Governance stack**: Level 1.
- **Implementation**: AST scan in CI over `src/app/routes/*.py`.
- **Addresses**: ARCH-001.

2) **FF-2: oob-marker-semantic-extractor**
- **What it checks**: all tests use a single helper for extracting OOB sidebar counts.
- **Threshold**: >1 duplicated marker regex/substring check for `hx-swap-oob` in test files.
- **Governance stack**: Level 1.
- **Implementation**: lightweight custom lint script in test phase.
- **Addresses**: ARCH-002.

3) **FF-3: route-module-dependency-fingerprint**
- **What it checks**: each changed route endpoint keeps its allowed dependency edges (`app.routes` must not add dependencies to high-level packages).
- **Threshold**: new edges crossing `app.routes` out of existing package whitelist are blocked.
- **Governance stack**: Level 2.
- **Implementation**: import-linter/pydeps-like scripted rule with frozen baseline + regression-only mode.
- **Addresses**: general coupling drift and ADP/SAP regressions.
