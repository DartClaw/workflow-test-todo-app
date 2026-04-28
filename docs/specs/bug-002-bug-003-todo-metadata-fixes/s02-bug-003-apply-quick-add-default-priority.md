# Feature Implementation Specification: S02 - BUG-003 Apply Quick-Add Default Priority

**Plan**: `docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md`
**Story-ID**: `S02`

## Feature Overview and Goal
Ensure the title-only quick-add flow persists the documented `low` Priority so the created row and later edit dialog reopen both reflect a consistent default metadata state.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_

## Required Context

### From `docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md` - "S02: BUG-003 Apply Quick-Add Default Priority"
<!-- source: docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md#s02-bug-003-apply-quick-add-default-priority -->
<!-- extracted: 2026-04-28 -->
> **Scope**: Ensure the quick-add create path persists `low` Priority when the user submits only a title, and prove that the returned todo row and later edit dialog reopen reflect that stored default. Preserve current title-only quick-add UX and existing explicit `medium`/`high` update behavior. Exclude new quick-add controls, schema changes unrelated to defaulting, and changes to unrelated Todo metadata flows.
>
> **Acceptance Criteria**:
> - [ ] Creating a Todo through quick-add with only a title persists `low` Priority on the new record.
> - [ ] The returned todo row renders the `low` Priority state consistently, including the row class, badge, and row dataset used for dialog reopen.
> - [ ] Opening the edit dialog for a quick-add-created Todo shows `low` as the selected Priority.
> - [ ] Existing flows that explicitly set `medium` or `high` Priority continue to preserve the user-selected value.

### From `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md` - "FR2: Apply Default Priority to Quick-Add Todos"
<!-- source: docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#fr2-apply-default-priority-to-quick-add-todos -->
<!-- extracted: d3138c5964bb6e0d2a4c6903d5495f1e2fee21d6 -->
> **Acceptance Criteria**:
> - [ ] When a user submits the quick-add form with only a title, the created todo persists with priority `low`.
> - [ ] The newly rendered todo row reflects the `low` priority state consistently with existing priority badges and styling.
> - [ ] Opening the edit dialog for a quick-add-created todo shows `low` as the selected priority.
> - [ ] Existing flows that explicitly set `medium` or `high` priority continue to preserve the user-selected value.
>
> **Validation**:
> - Quick-add continues to require only a non-empty title.
> - When priority is omitted in this flow, the system applies `low` automatically.
> - Existing priority validation remains restricted to `low`, `medium`, and `high`.

### From `AGENTS.md` - "Project-Specific Guidelines"
<!-- source: AGENTS.md#project-specific-guidelines -->
<!-- extracted: d3138c5964bb6e0d2a4c6903d5495f1e2fee21d6 -->
> - **HTMX-first.** Every route that renders should return an HTML partial - see `## Architecture -> The stack` above. Do not introduce JSON endpoints unless explicitly asked.
> - **Do not "fix" the intentionally simple auth.** Plain-text passwords and in-memory `sessions` dict are deliberate educational choices. See `src/app/core/deps.py` and the README.
> - **Pydantic models in `src/app/models/` are _not_ wired into routes.** Validation is ad-hoc in the handlers - do not assume models run.

## Deeper Context

- `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#user-flows` - Quick-add create, immediate reopen, and later explicit-priority-update flows this story must preserve.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` - Canonical Todo and Priority terms for spec wording and test names.
- `AGENTS.md#the-stack--and-why-it-matters-for-edits` - Server-rendered partial rules and why quick-add success must continue returning the row partial/OOB response shape.

## Success Criteria (Must Be TRUE)

- [ ] A title-only `POST /api/todos` quick-add persists `priority="low"` on the new `Todo` before the row partial is rendered.
- [ ] The quick-add response row exposes the stored default consistently through `priority-low`, the visible `Low` badge, and `data-todo-priority="low"` so later edit dialog reopen uses the same source of truth.
- [ ] Opening the edit dialog for a quick-add-created Todo shows `low` selected without adding new client-side fallback logic or new quick-add inputs.
- [ ] Existing explicit Priority updates to `medium` or `high` remain unchanged by the defaulting fix.

### Health Metrics (Must NOT Regress)
- [ ] Existing quick-add title validation and Todo ownership checks continue to pass.
- [ ] Quick-add remains a single lightweight HTMX POST returning the current row/OOB partial path.
- [ ] The existing edit dialog and row badge semantics continue to reflect stored Priority values consistently.

## Scenarios

### Quick-add a title-only Todo
- **Given** an authenticated user is viewing a TodoList and submits the existing quick-add form with only `list_id` and `title`
- **When** `POST /api/todos` creates the new Todo
- **Then** the database record stores `priority="low"` and the returned row HTML includes `priority-low`, `Low`, and `data-todo-priority="low"`

### Reopen a quick-added Todo for editing
- **Given** a Todo was just created through the title-only quick-add flow
- **When** the user opens the edit dialog from the rendered row
- **Then** the dialog's Priority select is prepopulated with `low` from the row dataset without extra fallback branches

### Preserve explicit later Priority changes
- **Given** a Todo was created by quick-add and therefore starts at `low`
- **When** the user later updates it through `PUT /api/todos/{todo_id}` with `priority=medium` or `priority=high`
- **Then** the explicitly chosen Priority persists normally and the row/edit dialog reflect that new value

### Keep existing quick-add validation intact
- **Given** the quick-add form is submitted with a blank or whitespace-only title
- **When** the request hits `POST /api/todos`
- **Then** the route still returns the existing HTML error partial and does not create a Todo with any Priority value

## Scope & Boundaries

### In Scope
- Apply the documented `low` Priority default at the quick-add persistence boundary.
- Prove that the created row and edit dialog reopen both reflect the stored default Priority.
- Preserve title-only quick-add UX and existing explicit `medium`/`high` update behavior.
- Add route-level regression coverage for create, render, reopen, and later explicit-priority behavior.

### What We're NOT Doing
- Adding a Priority control to the quick-add form - the PRD explicitly keeps quick-add title-only.
- Introducing database migrations or broad ORM refactors unrelated to this defaulting bug - the minimal fix belongs in the existing create path.
- Changing edit-dialog behavior beyond consuming the correctly persisted Priority - reopen should continue using row dataset values.
- Changing authentication, authorization, or unrelated Todo metadata flows - those remain governed by existing project rules.

## Architecture Decision

**We will**: set `priority="low"` inside the quick-add create route before commit and rely on the existing row-render + dialog-reopen dataset contract to carry that persisted value through the UI - this fixes the bug at the data boundary instead of hiding missing data with UI-only defaults or schema-wide changes.

## Technical Overview

### UI/UX Design (if applicable)
The user-facing quick-add flow stays the same: users still submit only a title, and the returned row continues to appear via the current HTMX partial response.

### Data Models (if applicable)
`Todo.priority` remains limited to `low`, `medium`, and `high`. This story only ensures the create path never persists a missing value when the quick-add form omits Priority.

### Integration Points (if applicable)
The story touches the quick-add create route, the rendered todo row metadata used by the edit dialog, and regression tests that prove the persisted default carries across create and later edit flows.

## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:73-132                | Existing quick-add create path and OOB response behavior
file   | src/app/database.py:73-84                    | `Todo.priority` column shape and lack of ORM/DB default
file   | src/app/models/todo.py:9-14                  | Canonical Pydantic default of `low` for Todo creation
file   | src/app/templates/partials/todo_item.html:1-40 | Row class, badge, and dataset fields that must all reflect `low`
file   | src/app/static/js/app.js:111-125             | Edit-dialog prefill path reading `data-todo-priority`
file   | tests/test_todos.py:13-30                    | Existing quick-add regression test to extend
file   | tests/test_todos.py:44-62                    | Existing explicit-priority update coverage to preserve
```

## Constraints & Gotchas

- **Constraint**: `Todo.priority` has no database default - Workaround: assign the documented default before the model is committed in `create_todo()`.
- **Avoid**: relying on the edit dialog or row renderer to hide a missing stored Priority - Instead: fix the persistence boundary so UI state stays a pure reflection of stored data.
- **Critical**: quick-add must stay title-only and HTMX-first - Must handle by: keeping the form shape unchanged and returning the same partial response path.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Title-only quick-add persists `low` Priority before the new Todo is committed
  - Follow `src/app/routes/todos.py:73-132` for the create path and align the chosen default with `src/app/models/todo.py:9-14`; do not add new quick-add form inputs.
  - **Verify**: `POST /api/todos` with only `list_id` and `title` creates a DB row with `priority == "low"`

- [ ] **TI02** The quick-add response row and reopen path both expose the stored default Priority
  - Reuse the existing row dataset and badge contract in `src/app/templates/partials/todo_item.html:1-40` together with dialog prefill in `src/app/static/js/app.js:111-125`; no client-side fallback branch should be added.
  - **Verify**: the quick-add response HTML contains `priority-low`, `Low`, and `data-todo-priority="low"`, and a reopen-oriented test can derive `low` from the rendered row metadata

- [ ] **TI03** Regression tests cover title-only create, immediate reopen evidence, and later explicit Priority updates
  - Extend `tests/test_todos.py:13-30` and preserve/update the explicit Priority assertions around `tests/test_todos.py:44-62`; keep blank-title validation behavior unchanged.
  - **Verify**: targeted pytest for the new BUG-003 coverage proves title-only quick-add stores `low`, row metadata carries `low`, and later updates to `medium`/`high` still persist

### Testing Strategy

- [TI01,TI02] Scenario: Quick-add a title-only Todo -> extend/create a route test that asserts DB state plus returned row class, badge text, and `data-todo-priority`
- [TI02,TI03] Scenario: Reopen a quick-added Todo for editing -> add an assertion that the rendered row metadata can drive a `low` preselection on reopen
- [TI03] Scenario: Preserve explicit later Priority changes -> retain or extend the existing update test to prove `medium` and `high` still persist
- [TI03] Scenario: Keep existing quick-add validation intact -> keep the blank-title error test green to prove defaulting did not widen the validation surface

### Validation

- Run targeted todo route tests for BUG-003 coverage after implementation.
- Inspect returned row HTML in assertions so the stored default is proven in both persistence and UI-reopen terms.

### Execution Contract

- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact - implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research - spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature - build/tests/lint-analysis where those checks exist and are relevant - and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion - do not batch.

## Final Validation Checklist

- [ ] **All success criteria** met
- [ ] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements (if applicable)

## Implementation Observations

_No observations recorded yet._
