# Feature Implementation Specification: Apply Quick-Add Default Priority

**Plan**: [`docs/specs/bug-002-bug-003/plan.md`](./plan.md)
**Story-ID**: S02

## Feature Overview and Goal
Make quick-add todo creation persist the documented default Priority of `low` so new Todos render and reopen from a valid metadata state without changing any explicit priority choices made later in the edit flow.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` – "FR2: Apply Quick-Add Default Priority"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr2-apply-quick-add-default-priority -->
<!-- extracted: 7b0b211 -->
> When a user creates a todo through quick add, the new todo must start with the product's default priority so the edit dialog and rendered item always reflect a valid priority state.
>
> For this release, the default value is `low`.

### From `docs/specs/bug-002-bug-003/plan.md` – "S02: Apply Quick-Add Default Priority"
<!-- source: docs/specs/bug-002-bug-003/plan.md#s02-apply-quick-add-default-priority -->
<!-- extracted: 2026-05-03 -->
> Ensure the quick-add todo creation path persists `low` as the default Priority at creation time so the rendered Todo row and edit dialog always start from a valid value. Include regression coverage for create and reopen flows. Exclude any change to explicit priority selection in the edit dialog or new defaulting rules beyond quick add.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "Todo Domain"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#todo-domain -->
<!-- extracted: 7b0b211 -->
> | Term       | Definition                                                            | Avoid (synonyms)          | Bounded Context |
> |------------|-----------------------------------------------------------------------|---------------------------|-----------------|
> | Todo       | A single task inside a TodoList                                       | task, item, entry         | Todo            |
> | Priority   | Importance level of a todo: `low` \| `medium` \| `high`               | severity, urgency         | Todo            |


## Deeper Context

- `docs/PRODUCT-BACKLOG.md#known-defects` – original BUG-003 statement and severity.
- `docs/specs/bug-002-bug-003/prd.md#validation` – allowed priority values and default-value requirement.
- `docs/specs/bug-002-bug-003/plan.md#phase-1-metadata-corrections` – story sequencing and non-overlap boundaries inside the bundle.


## Success Criteria (Must Be TRUE)
- [ ] A Todo created through the quick-add route persists with `priority="low"` immediately.
- [ ] The returned create partial renders the expected low-priority row metadata and badge, so reopening the edit dialog starts with `low` selected.
- [ ] A later explicit priority update through the existing edit flow still overrides the quick-add default normally.

### Health Metrics (Must NOT Regress)
- [ ] Existing quick-add title validation and ownership checks remain unchanged.
- [ ] Existing out-of-band incomplete-count update behavior remains intact for quick-add creation.
- [ ] Existing todo create and update route tests continue to pass after the defaulting change.


## Scenarios

### Quick Add Starts at Low Priority
- **Given** an authenticated user is viewing a TodoList
- **When** the user quick-adds a new Todo with only a title
- **Then** the Todo persists with `priority="low"` and the returned row partial exposes low-priority display and reopen metadata

### Reopen a Quick-Added Todo
- **Given** a Todo was created through quick add
- **When** the user opens that Todo in the edit dialog without changing priority first
- **Then** the dialog loads with `low` selected from the rendered row metadata

### Explicit Priority Override Still Wins
- **Given** a Todo was created through quick add with the default priority
- **When** the user later saves the Todo with `priority=high`
- **Then** the Todo persists `high` and the next reopen path shows `high`, not the original default

### Quick Add Keeps Existing Response Shape
- **Given** a valid quick-add request
- **When** the route creates the Todo
- **Then** the response still returns the standard todo row with the sidebar incomplete-count OOB update


## Scope & Boundaries

### In Scope
- Set the quick-add creation path's Priority explicitly to `low`.
- Preserve rendered row metadata and badge output for newly created Todos.
- Add regression coverage for quick-add create plus later reopen/update behavior.

### What We're NOT Doing
- Changing the edit dialog's explicit priority selection behavior – that remains the existing update-route contract.
- Introducing configurable defaults or per-list defaults – PRD scope fixes only the current quick-add regression.
- Changing other Todo creation paths beyond the quick-add route – keep the change surgical.


## Architecture Decision

**We will**: default Priority in the quick-add `create_todo` route and let the existing row partial plus edit-dialog metadata surface that stored value – this fixes the scoped bug at the narrowest integration point (over adding a broader database default or frontend-only fallback that could mask missing persisted state).


## Technical Overview

### UI/UX Design (if applicable)
No UI changes are needed. The existing edit dialog already declares `value="low"` on the select in `src/app/templates/app.html:143-148`; the story ensures persisted quick-add data now matches that documented default.

### Data Models (if applicable)
`Todo.priority` already exists in `src/app/database.py:63-79`. The story changes the creation behavior only; no schema or model migration is required.

### Integration Points (if applicable)
The quick-add route must remain compatible with:
- `priority-{{ todo.priority }}` and badge rendering in `src/app/templates/partials/todo_item.html:1-32`
- `data-todo-priority` and `openEditTodoDialog(...)` arguments in `src/app/templates/partials/todo_item.html:3-7` and `:37-40`
- The create response wrapper that includes the sidebar incomplete-count OOB update


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:73-132             | Quick-add create handler and OOB response path
file   | src/app/database.py:63-79                  | Existing Todo metadata fields; confirms no schema change is needed
file   | src/app/templates/partials/todo_item.html:1-48 | Priority class, badge, and reopen metadata contract
file   | src/app/static/js/app.js:111-124           | Edit dialog rehydration path that must receive the stored priority
file   | tests/test_todos.py:13-30                  | Existing create regression test already encodes the intended default priority
file   | tests/test_todos.py:44-62                  | Existing update test to extend for later explicit-priority override proof
```


## Constraints & Gotchas
- **Constraint**: scope is quick add only – Workaround: set the default in `create_todo` rather than introducing a broad model-level behavior change.
- **Avoid**: relying on the edit dialog's client-side select default as proof – Instead: persist `low` in the database and prove the row partial carries that value.
- **Critical**: create responses also update the sidebar count OOB – Must handle by leaving the existing `todo_item_with_oob.html` response shape untouched.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Quick-add creation persists `low` as the default Priority
  - Update `src/app/routes/todos.py:115-123` so the quick-add `Todo(...)` includes the scoped default while preserving the existing list access, title validation, and position logic.
  - **Verify**: `Test: POST /api/todos with valid quick-add data creates a Todo with priority='low'`

- [ ] **TI02** Newly created row partial exposes low-priority render and reopen metadata
  - Confirm the returned row from `src/app/templates/partials/todo_item.html:1-48` carries `priority-low`, `data-todo-priority="low"`, and the low-priority badge after TI01; no template redesign should be necessary unless the stored value still fails to surface.
  - **Verify**: `Test: quick-add response HTML contains low-priority row metadata and badge content`

- [ ] **TI03** Later explicit priority updates still override the quick-add default
  - Extend route regression coverage to show a quick-added Todo can later be saved with another valid priority through `update_todo`; depends on TI01.
  - **Verify**: `Test: quick-added Todo updated to priority='high' persists high and reopens with high metadata`

- [ ] **TI04** Quick-add regression coverage proves behavior without disturbing OOB count updates
  - Build on `tests/test_todos.py:13-30` and the create response contract at `src/app/routes/todos.py:125-131`; keep proof at the authenticated route layer.
  - **Verify**: `Test: quick-add regression tests pass for default priority, row metadata, explicit override, and OOB response shape`

### Testing Strategy
- [TI01,TI04] Scenario: Quick Add Starts at Low Priority → route test creates a Todo and asserts database priority equals `low`.
- [TI02,TI04] Scenario: Reopen a Quick-Added Todo → route test asserts returned HTML includes `data-todo-priority="low"` and low-priority display markers.
- [TI03,TI04] Scenario: Explicit Priority Override Still Wins → route test creates via quick add, updates to `high`, and asserts persisted plus rendered value becomes `high`.
- [TI02,TI04] Scenario: Quick Add Keeps Existing Response Shape → route test asserts the response still contains the new todo row and the OOB count fragment.

### Validation
- Run `uv run pytest tests/test_todos.py -k "create_todo or priority"` once the implementation is complete.
- Visually verify quick-add then reopen in the authenticated app because the story depends on rendered row metadata feeding the dialog.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.


## Final Validation Checklist

- [ ] **All success criteria** met
- [ ] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements (if applicable)
