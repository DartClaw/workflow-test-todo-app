# Feature Implementation Specification: S02 Default quick-add priority


## Feature Overview and Goal
Ensure Todos created through quick add always start with the documented `low` Priority so storage, the rendered row, and the edit dialog all agree on the same default state without widening the route surface.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` – "FR2: Apply Default Priority on Quick Add"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr2-apply-default-priority-on-quick-add -->
<!-- extracted: 7023cec2a64bab1642a6dd7e08e95b322ae864fe -->
> **Description**: The quick-add creation workflow must assign the documented default priority to new todos so that the stored record, rendered row, and edit dialog all agree on the initial priority state.
>
> **Acceptance Criteria**:
> - [ ] When a user creates a todo through quick add with only a title, the stored todo record is created with `low` priority.
> - [ ] The newly rendered todo row reflects the same default priority value used in storage.
> - [ ] When the user opens the edit dialog for a quick-added todo, the priority selector shows `Low` selected.
> - [ ] Existing edit behavior for manually changing priority after creation remains unchanged.
>
> **Validation**:
> - The quick-add flow still requires a non-empty title of 200 characters or fewer.
> - The default priority is applied automatically when the quick-add form does not provide a priority value.
>
> **Error Handling**:
> - Validation failures in quick add still return the standard HTML error partial.
> - The absence of an explicit priority in quick add is treated as normal input, not an error condition.

### From `docs/specs/bug-002-bug-003/plan.md` – "S02: Default quick-add priority"
<!-- source: docs/specs/bug-002-bug-003/plan.md#p-s02-default-quick-add-priority -->
<!-- extracted: 7023cec2a64bab1642a6dd7e08e95b322ae864fe -->
> **Scope**: Ensure quick-add Todo creation produces a stored `low` Priority even when the form submits only `list_id` and `title`, then prove the rendered row and edit dialog reflect that stored default. Include isolated regression coverage for repeated quick-add creation and later manual priority edits. Exclude any change to the available Priority values or to the edit dialog UI structure.
>
> **Acceptance Criteria**:
> - [ ] Creating a Todo through quick add with title only stores `low` as the effective Priority.
> - [ ] The newly rendered todo row reflects the same `low` Priority that was stored.
> - [ ] Opening the edit dialog for a quick-added Todo shows `Low` selected until the user changes it.
> - [ ] Later edits that change Priority to `medium` or `high` continue to persist normally.
>
> **Key Scenarios**:
> - Happy: quick-add a Todo, open edit, and see `Low` selected.
> - Edge: quick-add several Todos in succession and confirm every stored Priority is `low`.
> - Regression: change a quick-added Todo to `high`, save, reopen, and see `High` selected.


## Deeper Context

- `docs/specs/bug-002-bug-003/prd.md#edge-cases` – repeated quick-add creation and later manual Priority changes that must stay correct.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical use of `Todo` and `Priority`.
- `docs/specs/bug-002-bug-003/prd.md#constraints-assumptions` – merge-safe ownership and `low` default constraints.


## Success Criteria (Must Be TRUE)
- [x] Creating a Todo through `POST /api/todos` with only `list_id` and `title` persists `priority="low"` on the Todo record.
- [x] The quick-add response fragment renders the same `low` Priority in both the CSS class / badge state and the reopened payload `data-todo-priority="low"`.
- [x] Opening the edit dialog for a quick-added Todo selects `Low` because the persisted Priority is already `low`.
- [x] Later edit saves that change Priority to `medium` or `high` still persist and round-trip normally.

### Health Metrics (Must NOT Regress)
- [x] Existing quick-add title validation remains unchanged.
- [x] The quick-add flow still returns the OOB fragment response and updates the incomplete-count badge.
- [x] Existing todo update behavior for explicit Priority changes remains unchanged.


## Scenarios

### Quick add stores the default Priority
- **Given** an authenticated user submits quick add with only `list_id` and `title`
- **When** the Todo is created
- **Then** the stored `Todo.priority` is `low` and the returned fragment includes `data-todo-priority="low"`

### Reopen a quick-added Todo in the edit dialog
- **Given** a quick-added Todo was created with the default Priority
- **When** the user opens the edit dialog for that Todo
- **Then** the dialog uses the persisted Priority value and shows `Low` selected

### Quick add stays stable across repeated creation
- **Given** an authenticated user quick-adds several Todos in succession
- **When** each Todo is persisted
- **Then** every created Todo receives `priority="low"` without needing an explicit form field

### Later manual Priority changes still win
- **Given** a Todo was created through quick add with `priority="low"`
- **When** the user edits that Todo and saves `priority="high"`
- **Then** the stored Priority becomes `high` and the reopened fragment carries `data-todo-priority="high"`


## Scope & Boundaries

### In Scope
- Define the default Priority at a merge-safe boundary used by quick-add creation.
- Prove the quick-add fragment and edit-dialog reopen path both reflect the stored default.
- Add isolated regression coverage for default creation, repeated quick add, and later explicit Priority changes.

### What We're NOT Doing
- Changing the available Priority options or badge styling rules – the defect is missing default state, not presentation design.
- Expanding quick add to accept an explicit Priority input – the PRD keeps quick add title-only.
- Modifying the todo edit Due Date behavior – that belongs to `S01`.
- Refactoring the broader Todo creation flow beyond what is needed to guarantee `low` as the default.


## Architecture Decision

**We will**: enforce the default Priority at the `Todo` model boundary rather than inside `create_todo` – this keeps `BUG-003` merge-safe from `BUG-002`, covers all Todo creation paths that omit Priority, and preserves the existing route fragment contract.


## Technical Overview

### UI/UX Design (if applicable)
No visual redesign is planned. The edit dialog already exposes `Low`, `Medium`, and `High`, and the row fragment already uses `todo.priority` for both the badge and reopen payload.

### Data Models (if applicable)
`Todo.priority` remains a string field constrained by route-level validation on update. This story adds or relies on a default so newly created Todos never persist with an undefined Priority.

### Integration Points (if applicable)
This story connects the Todo model definition in `src/app/database.py`, the quick-add create flow in `src/app/routes/todos.py`, and the row/dialog contract in `src/app/templates/partials/todo_item.html` plus `src/app/templates/app.html`.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/database.py:72-83                 | Primary ownership for the Todo.priority default
file   | src/app/routes/todos.py:67-121            | Quick-add create flow that currently omits priority
file   | src/app/routes/todos.py:153-224           | Update path that must still allow explicit medium/high changes
file   | src/app/templates/partials/todo_item.html:1-40 | Returned fragment exposes priority badge and reopen payload
file   | src/app/templates/app.html:143-148        | Edit dialog Priority selector contract
file   | tests/conftest.py:1-93                    | Authenticated client and fixture setup
```


## Constraints & Gotchas
- **Constraint**: `BUG-003` must stay merge-safe from `BUG-002` – Workaround: keep primary write ownership in `src/app/database.py` and an isolated test module.
- **Avoid**: Fixing the bug by only setting a client-side default in the dialog – Instead: persist `low` so the row, dialog, and storage all agree.
- **Critical**: Later manual Priority edits already work through `update_todo` – Must handle by: preserving the existing update path and proving explicit `high` or `medium` still wins after creation.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick-add Todo creation persists `low` as the default Priority without requiring a form field
  - Own `src/app/database.py:72-83`; choose the model-level default so quick add and any future omitted-Priority create path share the same baseline.
  - **Verify**: `POST /api/todos` with only `list_id` and `title` creates a Todo whose stored `priority` is exactly `"low"`

- [x] **TI02** Quick-add response fragments and edit-dialog reopen payload reflect the stored default Priority
  - Depends on TI01; treat `src/app/templates/partials/todo_item.html:1-40` and `src/app/templates/app.html:143-148` as the behavioral contract to prove, not redesign.
  - **Verify**: the quick-add response contains `data-todo-priority="low"` and reopening that Todo shows `Low` selected

- [x] **TI03** Default-Priority behavior is covered in an isolated regression module without breaking later edits
  - Add a focused test file rather than editing the shared todo CRUD test file; include repeated quick-add creation and a follow-up edit that saves `priority=high`.
  - **Verify**: a regression test quick-adds a Todo, then updates it with `priority=high`, and asserts the stored value becomes `"high"`

### Testing Strategy
- [TI01] Scenario: Quick add stores the default Priority → route test asserts `Todo.priority == "low"` in storage
- [TI02] Scenario: Reopen a quick-added Todo in the edit dialog → route test asserts the response fragment carries `data-todo-priority="low"` for the dialog handoff
- [TI03] Scenario: Quick add stays stable across repeated creation → route test asserts each created Todo stores `priority="low"`
- [TI02,TI03] Scenario: Later manual Priority changes still win → route test asserts a quick-added Todo can be updated to `high` and reopens with `data-todo-priority="high"`

### Validation
- Run focused quick-add and todo update tests covering the new Priority regression module plus the existing todo CRUD suite.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.


## Final Validation Checklist

- [x] **All success criteria** met
- [x] **All tasks** fully completed, verified, and checkboxes checked
- [x] **No regressions** or breaking changes introduced
- [x] **UI verified** to match requirements (if applicable)
