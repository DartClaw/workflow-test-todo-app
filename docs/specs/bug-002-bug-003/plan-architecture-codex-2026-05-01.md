# Architecture Review: Implementation Plan `docs/specs/bug-002-bug-003/plan.md`

**Scope**: Branch delta versus `main`, limited to files changed by this plan (`src/app/routes/todos.py`, `tests/test_todos.py`, and `docs/specs/bug-002-bug-003/*`).
**Date**: 2026-05-01

## Executive Summary
The reviewed scope remains architecture-safe for this phase and is confined to the existing `app.routes.todos` interaction slice and its test surface. No package-level structural violations (cycles, unstable dependencies, or module sprawl) were introduced by this branch. The highest-risk issue is coupling of several new assertions to specific HTML tokens, which is a maintainability concern rather than a structural failure of the runtime system. Recommendation focus: keep semantic assertions stable while preserving the HTMX partial contract.

## How to Read This Report
- **C4 levels** used: Context, Container, Component, Code.
- **Connascence** shorthand: only static `CoN` is discussed; dynamic forms (`CoE`, `CoTm`, `CoV`, `CoI`) are not introduced.
- **Metrics**: This review is scoped to a low-level slice (`app.routes.todos` + tests); we did not recompute full-repo package metrics.

## Metrics Dashboard (Scoped Slice)

| Module / Unit | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.routes.todos` | ~1 | ~3 | ~0.75 | N/A | N/A | OK | Focused handler module; no new outward dependency spikes observed in this slice. |
| `app` test surface (`tests/test_todos.py`) | N/A | N/A | N/A | N/A | N/A | N/A | Tightens regression coverage for modified handlers; no architecture boundary changes. |

## Findings

### ARCH-001: Test assertions are tightly coupled to specific response fragment tokens

**Severity**: LOW
**Dimension**: testability
**C4 Level**: Component
**Category**: Convention

**Evidence**: New checks in `tests/test_todos.py` assert string tokens from rendered fragments (`priority-low`, `data-todo-priority`, `todo-item`, `openEditTodoDialog`) at `tests/test_todos.py:33-35` and `tests/test_todos.py:111-112`.

**Connascence**: CoN (naming) — Strength: 2, Degree: 2, Locality: 1

**Impact**: Template markup refactors can fail tests even if handler behavior is correct, increasing maintenance friction around UI component boundaries.

**Recommendation**: Introduce stable, semantically stable test markers (or test key response fragments via data attributes) to decouple tests from incidental class/id strings while retaining coverage.

**Fitness Function**: Add one test convention check in PR review: any route-response assertions must target declared stable markers (`data-*` contract attributes) rather than mutable class or JS symbol names.

**Fix Prompt**: In `tests/test_todos.py`, replace raw substring assertions for class/function names with assertions over stable contract attributes in the same row partial and keep the HTMX response contract assertions limited to guaranteed fields.

## Dependency Graph

No new package boundaries were added. The runtime dependency path for the changed module remains:
- `app.main` -> `app.routes.todos` (single consumer)
- `app.routes.todos` -> `app.core.deps`, `app.database`, `app.utils`, `fastapi`, `sqlalchemy`

## Decomposition Recommendations

No decomposition action is warranted for this scope. The single shared module (`app.routes.todos`) is expected for this phase and is still a coherent ownership boundary for Todo CRUD + edit semantics.

## Proposed Fitness Functions

1. **Template-Contract Stability
   - What to check:** Add/maintain a low-cardinality set of explicit `data-*` markers in partials used by route tests.
   - **Threshold:** No new test should match transient class names only.
   - **Goverance level:** 4
   - **Tooling:** `pytest` + regression test review (manual checklist) for touched routes.
   - **Findings addressed:** ARCH-001

