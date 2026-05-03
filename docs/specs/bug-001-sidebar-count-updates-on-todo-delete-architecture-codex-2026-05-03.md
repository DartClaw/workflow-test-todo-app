# Architecture Review: bug-001-sidebar-count-updates-on-todo-delete

**Date:** 2026-05-03
**Mode:** review
**Scope:** `docs/specs/bug-001-sidebar-count-updates-on-todo-delete.md` (current-branch changes scoped to bug-001 implementation files)
**Decision trace:** tier 2 spec-directory match (co-located with the spec under `docs/specs/`).

## Executive Summary

The scoped review area has a healthy HTMX-first container shape, with clear controller→model→template flow and no new dependency cycles in the touched feature boundary. There is **1 finding (LOW)** and no Medium-or-higher architectural issue introduced by this change set. The most important gap is a **testability coupling**: two test modules assert the exact OOB HTML fragment string that the delete route now emits. The most impactful recommendation is to decouple tests from raw markup formatting so future safe template refactors do not become regression work.

## How to Read This Report

- **C4 level:** `Context` (system level), `Container` (deployable runtime building block), `Component` (module/API slice), `Code` (single function/file behavior).
- **Metrics:** `Ca` = afferent dependencies (how many internal modules depend on a component); `Ce` = efferent dependencies (how many internal modules this component depends on); `I` = instability (`Ce / (Ca + Ce)`), `A` = abstractness (`abstract_types / total_types`), `D` = distance from main sequence (`|A + I - 1|`).
- **Principles:** ADP = Acyclic Dependencies Principle, SDP = Stable Dependencies Principle, SAP = Stable Abstractions Principle (all from Martin).
- **Zones:** `Zone of Pain` = `I≈0`, `A≈0`, often concrete-but-stable with high blast radius. `Zone of Uselessness` = `I≈1`, `A≈1`, abstract-but-unused.
- **Connascence:** CoN/CoT across boundaries are expected API forms; static dynamic-cross-boundary forms are materially worse.

## Metrics Dashboard

| Component | Ca | Ce | I | A | D | Zone |
|---|---:|---:|---:|---:|---:|---|
| app.database | 5 | 0 | 0.00 | 0.00 | 1.00 | Pain |
| app.utils | 4 | 0 | 0.00 | 0.00 | 1.00 | Pain |
| app.core.deps | 4 | 0 | 0.00 | 0.00 | 1.00 | Pain |
| app.routes.todo_lists | 1 | 3 | 0.75 | 0.00 | 0.25 | Green zone |
| app.routes.pages | 1 | 3 | 0.75 | 0.00 | 0.25 | Green zone |
| app.routes.auth | 1 | 2 | 0.67 | 0.00 | 0.33 | Alert |
| app.routes.todos | 1 | 3 | 0.75 | 0.00 | 0.25 | Green zone |
| app.main | 0 | 4 | 1.00 | 0.00 | 0.00 | Green zone |

Notes:
- `app.routes.todos`, `app.routes.todo_lists`, and `app.routes.pages` share nearly identical dependencies and are high-leaf, highly volatile nodes, which is coherent for Thin HTTP-facing modules in this architecture.
- No module with `I < 0.3` has `A > 0.3`, so no SAP violation appears in the scoped graph.
- No internal dependency cycle exists in the scoped graph.
- `CCD` and `ACD` are low for this change boundary (8 nodes with shallow reachability), with no evidence of tangled reachability growth from this patch.

## Findings

### ARCH-001: Tests depend on exact OOB fragment HTML formatting for delete count updates

**Severity**: LOW  
**Dimension**: testability  
**C4 Level**: Code  
**Category**: Coupling

**Evidence**: 
- `src/app/routes/todos.py` now returns `partials/todo_deleted_oob.html` for successful DELETE operations in `delete_todo`.
- `tests/test_todos.py:95-121`, `tests/test_todos.py:142-151`, `tests/test_todos.py:163-174`, and `tests/test_integration.py:182-200` assert exact substrings such as:
  - `id="list-{list_id}-count" hx-swap-oob="true">2</span>`
  - This assertion style appears in four places and is coupled to the exact serialization order of a single `<span>`.

**Connascence**: CoN — Strength: 1, Degree: 4, Locality: 2 -> Severity: 2.0

**Impact**:
- Fragile test architecture: harmless template formatting edits (attribute order, whitespace, additional wrapper elements) can trigger false failures.
- Increases maintenance overhead without increasing behavioral coverage.
- Makes the route/template boundary harder to evolve safely because tests enforce internal representation.

**Recommendation** (Per OOP+Martin): prefer stable contracts over representation details at API boundaries. For route contracts that are HTMX fragments, test observable semantics (`hx-swap-oob` marker plus target id count) rather than exact full markup.

**Fitness Function**:
- Add/adjust two assertions so they parse response HTML and assert `(count_id == expected and hx-swap-oob present)` rather than raw full-string equality.
- Proposed helper: `assert_has_oob_count(response_text, list_id, expected_count)` in test utilities, then run this helper in both `test_todo_delete_updates_sidebar_count` and `test_todo_delete_updates_count`.

**Fix Prompt**: Replace raw-byte-string assertions on `hx-swap-oob` markup with a semantic helper that extracts by element id and checks `id` + `hx-swap-oob` + normalized count.

## Dependency Graph

Condensed DAG (scoped):
- `app.main` depends on `app.routes.todo_lists`, `app.routes.pages`, `app.routes.todos`, `app.routes.auth`, and `app.database`.
- `app.routes.*` modules all depend on `app.core.deps`, `app.database`, `app.utils`.
- `app.core.deps`, `app.database`, and `app.utils` do not depend on other internal application modules (leaf/stability foundations).
- No back-edges from foundations to volatile routes exist; no cycles were found in this scoped graph.

## Decomposition Recommendations

- No split/merge required in this scope.
- Keep count-update behavior in `app.routes.todos` and `src/app/templates/partials/todo_deleted_oob.html` to preserve HTMX pattern consistency.

## Proposed Fitness Functions

1. **F-ARCH-001 (test contract resilience):**
   - Check: delete-endpoint tests in `test_todo_delete_*` must assert only semantic markers.
   - Threshold: all tests in the spec scope use selector-based OOB assertions, not hardcoded literal HTML spans.
   - Level: 3 (repo-local testing + review policy).

2. **F-ARCH-002 (scoped OOB contract):**
   - Check: both successful delete and unauthorized/404 responses must assert OOB marker behavior explicitly (`has marker` vs `does not have marker`).
   - Threshold: both cases covered by automated route tests.
   - Level: 3.
