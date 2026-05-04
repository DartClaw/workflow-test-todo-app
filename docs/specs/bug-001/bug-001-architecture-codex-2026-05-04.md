# Architecture Review: BUG-001 (delete todo OOB update)

**Scope:** `docs/specs/bug-001/bug-001.md` against `origin/main` base ref.  
**Review mode:** architecture review (package-level with component/code checks only in touched files).  
**Target:** source-code change set + spec documentation set in `docs/specs/bug-001/`.

## Executive Summary
The `BUG-001` patch is narrowly scoped and restores an established HTMX OOB pattern for delete without changing ownership, persistence, or routing boundaries. No new cross-module dependencies were introduced.  
Found 0 medium-or-higher findings and 2 low findings.  
Most notable risk is not a new architectural violation, but test fragility from assertions that depend on exact response HTML text, which can cause false failures during harmless template formatting changes.  
Most impactful recommendation is adding a dedicated OOB response assertion utility so route behavior is validated semantically (ID + integer count) rather than via exact byte snippets.

## How to Read This Report
- `Ca` = count of incoming package/module dependents; `Ce` = outgoing dependencies.  
- `I` = instability (`0` = stable, `1` = volatile), `A` = abstractness (`0` = concrete), `D` = distance from main-sequence (`0` best).  
- **C4**: Context, Container, Component, Code.  
- **Principles:**  
  - **ADP** (Acyclic Dependencies Principle) — avoid package cycles.  
  - **HTMX UI Contract** (project pattern) — mutations that affect multiple DOM regions should return an HTML partial with OOB targets for all affected regions.  
- **Connascence:**  
  - **CoN** (Name) = callers and callees rely on shared names/strings. Dynamic forms (CoV/CoI/CoTm/CoE) are materially riskier.

## Metrics Dashboard

| Package | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `src.app.routes.todos` | n/a | n/a | n/a | n/a | n/a | n/a | No new imports; behavior now matches existing create/toggle OOB pattern. |
| `tests.test_todos` | n/a | n/a | n/a | n/a | n/a | n/a | Expanded assertions are behaviorally aligned with changed response contract. |

## Findings

### ARCH-001: Delete endpoint still mixes response media types by status

**Severity**: LOW  
**Dimension**: modularity  
**C4 Level**: Component  
**Category**: Convention  

**Evidence**: In `src/app/routes/todos.py:286-313`, the success path now returns `TemplateResponse` with OOB HTML, while `404`/`403` still return bare `Response(status_code=...)` at lines `295-301`. This means one handler now has mixed contracts in production paths. A consumer expecting fragment swaps has no fragment payload in error conditions.

**Connascence** (if applicable): CoN — Strength: 2, Degree: 2, Locality: 2 -> Severity: 4  

**Impact**: Error behavior and success behavior are observable differently for the same route, which reduces uniformity and makes client-side behavior harder to reason about when extending delete UI handling.

**Recommendation**: Per project HTMX-first contract, normalize error paths for HTMX routes to return HTML partials (even minimal) instead of empty responses, with explicit `hx-swap`-agnostic error snippets if desired. This keeps endpoint response contracts obvious and consistent without changing business rules.

**Fitness Function**: Add a response-contract check in tests that asserts both success and failure branches return documented content type/templated body structure for HTMX routes in `src.app.routes.todos`.  

**Fix Prompt**: "Update `delete_todo` in `src/app/routes/todos.py` to return `TemplateResponse(... error partial ...)` for the `404` and `403` branches, preserving status codes but returning consistent HTML fragment responses."

### ARCH-002: Tests assert raw HTML string fragments for OOB semantics

**Severity**: LOW  
**Dimension**: testability  
**C4 Level**: Code  
**Category**: Convention  

**Evidence**: In `tests/test_todos.py:89-91` and `97-113`, tests assert `">{0}</span>"` and `">{1}</span>"` to validate count values. This creates brittle coupling between test logic and exact template whitespace/markup formatting.

**Connascence** (if applicable): CoN — Strength: 3, Degree: 1, Locality: 2 -> Severity: 6  

**Impact**: Minor refactors in `todo_deleted_oob.html` or whitespace formatting can fail tests despite semantics being correct, increasing false negatives and masking real regressions.  

**Recommendation**: Per API clarity and stability guidance, assert response semantics (presence of target id and parsable count value) via a helper parser/helper method instead of exact `<span>` string matching.

**Fitness Function**: Add a small HTML assertion helper that parses `response.content` and validates `id="list-{list_id}-count"` and extracted integer count equals expected. Require its use for all OOB UI contract tests.

**Fix Prompt**: "Create a test helper in `tests/test_todos.py` (or shared test util) that parses response HTML and verifies OOB target `id` and integer badge value."

## Dependency Graph
- `src.app.routes.todos` depends on `app.core.deps`, `app.database`, `app.utils`, and framework modules (`fastapi`, `sqlalchemy`) and is consumed by `app.main` through router inclusion.
- `tests.test_todos` depends on `app.database` and route behavior; no new dependency edges were added by this change.
- No new cycles were introduced, and no cross-cutting coupling expanded to untouched packages.

## Decomposition Recommendations
- No package split/merge is warranted. The change is behaviorally local and keeps all logic in the existing todo route module.

## Proposed Fitness Functions
1. **HTMX Route Contract Uniformity Check**
   - What it checks: each HTMX mutation endpoint in `src.app.routes.todos` returns a fragment body for both success and expected failure branches.
   - Threshold: zero mutation endpoint branches may return empty response bodies without an explicit HTML contract.
   - Governance level: 2 (code owner + review checklist).
   - Why: prevents mixed response contracts from reappearing.

2. **OOB Assertion Robustness**
   - What it checks: OOB response tests validate structure semantically (`id` + parsed integer count) rather than exact inner HTML.
   - Threshold: all `hx-swap-oob` assertions must use helper that extracts semantic fields.
   - Governance level: 2.
   - Why: lowers test fragility from template formatting changes.

## Decision Trace
Resolved output location via review-report policy tier 2 (spec-directory match): `docs/specs/bug-001/`.
