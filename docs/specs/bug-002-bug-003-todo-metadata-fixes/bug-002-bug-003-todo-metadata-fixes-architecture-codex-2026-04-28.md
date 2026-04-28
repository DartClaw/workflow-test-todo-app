# Architecture Review Report — BUG-002/BUG-003 Plan

Scope: Changes introduced for `docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md` on the current branch, with focus on touched files in `src/app/routes/todos.py`, `tests/test_todos.py`, and the todo-row/edit-dialog contract in `src/app/templates/partials/todo_item.html` + `src/app/static/js/app.js`.

## Executive Summary
The review area is a narrow backend route+template contract slice in a small monolith-style FastAPI app. No medium-or-higher architectural violations were found in the edited scope. The change set aligns with existing HTMX-first behavior: metadata now persists in `Todo` at create/update boundaries and flows through existing partial render paths. The most important follow-up is to reduce duplicated metadata constants across layers, which is a low-severity maintainability risk.

## How to Read This Report
- **C4**: Context, Container, Component, Code.
- **`Ca`**: incoming references to a package; **`Ce`**: outgoing dependencies; **`I`**: instability (`Ce/(Ca+Ce)`); **`A`**: abstractness (here mostly low in handlers).
- **`D`**: distance from the main sequence (`|A + I - 1|`), with values near 1 suggesting drift.
- **ADP / SDP / SAP**: Acyclic, Stable Dependencies, Stable Abstractions principles (Martin). No explicit violations were detected in the scoped modules.
- **Connascence shorthand**: `CoP` (position), `CoN` (name), `CoD` (direction), `CoS` (scale). Dynamic connascence terms (`CoV`, `CoI`, etc.) are not present across module boundaries here.

## Metrics Dashboard (Scoped)

| Package | Ca | Ce | I | A | D | Zone | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `app.routes` (observed through `todos.py`) | 2 | 5 | 0.71 | 0.00 | 0.29 | OK/Pain boundary | Focused, concrete boundary near storage/input layer |
| `app.core` (dependency target) | 1 | 1 | 0.50 | 0.00 | 0.50 | Warning | Shared session/auth helper accessed by routes |
| `app.database` (dependency target) | 1 | 0 | 0.00 | 0.00 | 1.00 | Observed sink | ORM data contracts are concrete by design |

Graph-level metrics (estimated from scoped graph): no cycles; CCD/ACD/NCCD calculations not meaningful for a 3-node partial scope.

## Findings

### ARCH-001: Metadata contract defaults are defined in multiple layers

**Severity**: LOW
**Dimension**: modularity
**C4 Level**: Code
**Category**: Convention

**Evidence**: The same conceptual default (`low`) appears in route-level constants (`src/app/routes/todos.py:20`) and model-level validation defaults (`src/app/models/todo.py:9`). Quick-add and update fallback behavior also relies on route-local coercion (`_coerce_priority`) in `todos.py:31` and client-facing badges/tests in `tests/test_todos.py:15` and `todo_item.html` (`data-todo-priority`).

**Impact**: Future domain changes (for example, adding/removing priority values or changing default ordering) can drift across handler, schema, and UI assertion layers without compiler feedback.

**Recommendation**: Extract domain constants (`TODO_PRIORITIES`, `TODO_DEFAULT_PRIORITY`, `TODO_DUE_DATE_FORMAT`) into a small domain constants module (for example `app/domain/todo.py`) and import from route, model, and templates/tests.

**Fitness Function**: Create a pre-commit or CI check that asserts constants are imported from a single domain source (e.g., static grep that fails when `"low"` appears as a priority literal in route and model code paths outside tests).

**Fix Prompt**: Move priority and date contract literals to one shared module, then replace hard-coded values in `routes/todos.py`, `models/todo.py`, and related tests with imports from that module.

## Dependency Graph Description
`main.py` includes route modules and wires `app.routes.todos` handlers; `app.routes.todos` depends on `app.database` entities + `app.core.deps` auth and `app.utils`; template and JS consumers depend on data attributes emitted by todo rows. `app.core` and `app.database` are mostly sinks in this boundary.

## Decomposition Recommendations
No package split/merge action is justified for this scope. The observed coupling is intentional for a small educational monolith.

## Proposed Fitness Functions
- **FF-001: Route-Template Contract Drift Check** (`tests`/`CI`): validate row attributes used by edit-dialog prefill (`data-todo-due-date`, `data-todo-priority`) remain present and stable after route/template changes.
- **FF-002: Domain Contract Single Source Check** (`static-analysis`): enforce that new priority/date literals are imported from a centralized domain module for non-test code paths.
- **FF-003: Error-Path Visibility Check** (`tests`): include a regression assertion that invalid due-date payloads return `partials/error.html` and do not mutate existing `Todo.due_date`.
