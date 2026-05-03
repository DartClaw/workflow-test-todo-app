# Architecture Review: bug-001-sidebar-incomplete-count-delete (scope)

## Executive Summary
- Scope of review: `docs/specs/bug-001-sidebar-incomplete-count-delete.md` and the implementation delta it drove in `src/app/routes/todos.py` + `tests/test_todos.py`.
- Overall assessment: the patch is mostly safe and aligned with the project HTMX-first pattern, with no new cycles or package-level dependency rule violations.
- Findings: 1 total, with 0 Medium-or-higher findings.
- Most impactful recommendation: simplify the new delete OOB partial path so server responses do not implicitly rely on an undefined template context.

## How to Read This Report
- **Ca** = number of in-scope packages that depend on the target package.
- **Ce** = number of in-scope outbound dependencies from the target package.
- **I** = instability, `Ce / (Ca + Ce)`.
- **A** = abstractness (`0` here because no package-level abstractions changed).
- **D** = distance from main sequence, `abs(A + I - 1)`.
- **C4 level** values used: Context, Container, Component, Code.
- **ADP/SDP/SAP** refer to Martin’s package principles.
- **OOB** = out-of-band HTMX swap.
- **Zone of Pain** = stable but concrete packages (high Ca, low A).
- **Connascence** uses static strength levels CoN→CoT→CoM→CoP→CoA and dynamic CoE/CoTm/CoV/CoI.

## Metrics Dashboard

| Package | Ca | Ce | I | A | D | Zone | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| app.routes | 1 | 3 | 0.75 | 0.00 | 0.25 | Healthy | UI/route wiring package with expected high outbound dependencies |
| app.database | 4 | 0 | 0.00 | 0.00 | 1.00 | Pain/infra-leaning | Stable persistence base package with multiple inbound references |
| app.utils | 2 | 0 | 0.00 | 0.00 | 1.00 | Healthy | Leaf helper package |
| app.core.deps | 4 | 0 | 0.00 | 0.00 | 1.00 | Healthy | Auth/session helper package used by routes |
| tests (test_todos.py) | 0 | 1 | 1.00 | 0.00 | 0.00 | Leaf test code | Tests as leaves in this delta |

## Findings

### ARCH-001: Delete OOB response path still renders a partial with undeclared row context

**Severity**: LOW
**Dimension**: coupling
**C4 Level**: Code
**Category**: Convention

**Evidence**: `delete_todo()` now returns `partials/todo_deleted_oob.html` with context `{"list_id": list_id, "count": count}` in `src/app/routes/todos.py:312-318`, while that partial includes `partials/todo_item.html` in `src/app/templates/partials/todo_deleted_oob.html:2`. The include expects `todo` fields (`todo.id`, `todo.is_completed`, etc.) that are no longer present in this response path.

**Connascence**: Cross-template context coupling (CoM) through implicit, undocumented required values, Strength: 3, Degree: 2 (list context + template contract), Locality: 1 (across file boundary) -> Severity: 6.0

**Impact**: The response currently survives by Jinja2 default undefined behavior, which is fragile. If template context strictness is tightened (a common hardening step), delete responses could regress into runtime template errors. It also couples a delete flow to a row-rendering template that is not semantically required for an OOB-only count refresh.

**Recommendation**: Per Page-Jones and Ousterhout (modular clarity), keep response surfaces explicit: return an OOB-only partial for delete (count badge only), or pass a complete `todo` context only when row markup is intentionally part of the response. This is a small structural cleanup, not a functional change, and matches the established toggle OOB pattern.

**Fitness Function**: Add a CI guard that renders `partials/todo_deleted_oob.html` with `list_id` and `count` only in a test, with a strict Jinja undefined policy, then verifies no undefined variable access and that the response includes only the expected OOB marker payload.

**Fix Prompt**: `Delete the \'{% include "partials/todo_item.html" %}\' line from src/app/templates/partials/todo_deleted_oob.html, or pass explicit todo context and assert the contract in delete handler tests.`

## Dependency Graph

Within this scope, the condensed graph is:
- `src/app/main.py` depends on `app.routes`, `app.database`, `app.utils`.
- `app.routes` depends on `app.core.deps`, `app.database`, and `app.utils`.
- `tests/test_todos.py` depends on `app.database`.
- No dependency cycles were introduced by this patch.

## Decomposition Recommendations

No decomposition action is required from this review. The current verticals remain stable, and the change is bounded to one flow.

## Proposed Fitness Functions

1. **FF-ARCH-001: Deleted OOB template context contract**
   - What it checks: each OOB partial used by mutating routes renders with a declared, non-empty required context under `StrictUndefined`.
   - Threshold: all OOB partials in route handlers pass strict render in test suite.
   - Governance level: 2 (route-handler + template boundary checks).
   - Why: prevents hidden context coupling like the delete-row fragment currently included without required context.

2. **FF-ARCH-002: Error/success response shape consistency for HTMX routes**
   - What it checks: success mutating HTMX routes that previously returned HTML fragments continue to return `hx-swap-oob` payloads where required and never include success-only fragments on error responses.
   - Threshold: no 4xx/5xx response in `src/app/routes/todos.py` includes `hx-swap-oob` marker.
   - Governance level: 1 (route contract tests).

## Decision Trace

Location resolved by `review-report-location.md` as a spec-directory match (tier 2: `docs/specs/`), because the scope is a bug-spec artifact.
