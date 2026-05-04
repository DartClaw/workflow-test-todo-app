# Architecture Review: bug-002-bug-003-todo-edit-and-quick-add

**Mode**: review (auto)
**Scope**: `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/plan.md` (stories S01, S02)
**Resolved location tier**: tier-2 spec-directory match (`docs/specs/bug-002-bug-003-todo-edit-and-quick-add`)

## 1. Executive Summary
The scoped review found no module-level architectural regressions introduced by S01/S02. The route layer changes remain confined to `src/app/routes/todos.py` with route-local validation and persistence behavior, and the companion tests stay in `tests/test_todos.py`.

The dependency graph for the touched layer is still acyclic, and no stability (SDP) violations or package-level principle breaches were observed for the changed paths.

No blocking findings were identified. The highest follow-up risk is not structural but behavioral coverage alignment, which should be handled in product/test governance.

Found counts: **0 findings (0 CRITICAL/HIGH/MEDIUM, 0 LOW/INFO)**.

## 2. How to Read This Report

- **Ca** = number of incoming package/module dependencies (how many local components depend on it)
- **Ce** = number of outgoing local dependencies (how many local components it depends on)
- **I** = instability (`Ce / (Ce + Ca)`, 0 = stable, 1 = unstable)
- **A** = abstractness (no meaningful abstractions detected in touched modules, so approx. 0)
- **D** = distance from main sequence (`|A + I - 1|`), higher means farther from ideal
- **C4 level**: Context (system), Container (service/runtime), Component (module), Code (file/function)
- **Principles**: ADP (Acyclic Dependencies Principle), SDP (Stable Dependencies Principle), SAP (Stable Abstractions Principle)
- **Connascence**: `CoN` name-level coupling; dynamic `CoI/CoE/CoTm/CoV` are the highest-risk forms and were not observed across package boundaries in this scope

## 3. Metrics Dashboard (scope-local)

| Package/Module | Ca | Ce | I | A | D | Zone | Notes |
|---|---:|---:|---:|---:|---:|---|---|
| `app.main` | 0 | 3 | 1.00 | 0.00 | 0.00 | OK | Leaves runtime entrypoint, orchestrates routers and startup wiring |
| `app.routes` | 1 | 3 | 0.75 | 0.00 | 0.25 | OK | Stable-ish behavior-focused layer depending on core/db/utils |
| `app.core` | 4 | 0 | 0.00 | 0.00 | 1.00 | Pain (expected for infrastructure/auth boundary) | In-memory auth/session utility, imported by route modules |
| `app.utils` | 4 | 0 | 0.00 | 0.00 | 1.00 | Pain (expected shared utility kernel) | Cross-cutting date helpers used by pages, routes, app bootstrap |
| `app.database` | 5 | 0 | 0.00 | 0.00 | 1.00 | Pain (expected persistence boundary) | ORM models and session factory are shared by routes/pages/main |

Graph-level metrics (manual pass over touched module graph):
- **CCD**: N/A (single-path, shallow DAG in scope)
- **ACD**: N/A
- **NCCD**: N/A

## 4. Findings

No architecture findings were identified in the current branch changes.

## 5. Dependency Graph (condensed DAG)

```text
app.main -> app.routes
app.main -> app.utils
app.main -> app.database
app.routes -> app.core.deps
app.routes -> app.database
app.routes -> app.utils
```

There are no cycles in the touched scope. Leaves are `app.main`-adjacent leaves for runtime entrypoint and `app.routes` as the application API surface; foundational nodes are `app.core.deps`, `app.utils`, and `app.database`.

## 6. Decomposition Recommendations

No decomposition changes are recommended from this review. The current boundary between route orchestration and lower-level auth/db/utils modules is appropriate for this educational app and aligns with the existing HTMX-first architecture.

## 7. Proposed Fitness Functions

1. **No cross-layer cycle rule**
   - Check that local import graph under `src/app/` remains acyclic (`ruff`/`pydeps` graph check or equivalent import check in CI).
   - Threshold: zero cycles on local modules under `src/app`.
   - Targets findings: architecture drift into cyclic coupling (ADP violations).

2. **Default priority contract test**
   - Add/keep a route-level assertion that quick-add and update paths converge on explicit default-priority policy.
   - Threshold: no test or route path may create a `Todo` without a defined `priority` value.
   - Targets quality risk: implicit domain defaults split across multiple handlers.

3. **Date-format boundary contract check**
   - Enforce tests asserting date-only parse/render round-trips through `type="date"` path.
   - Threshold: `src/app/routes/todos.py` quick-update and dialog preload assertions always use the same format token family.
   - Targets quality risk: hidden UI/form contract drift.

## Remediation Status

No actionable findings were identified in this architecture review. No remediation changes were required.
