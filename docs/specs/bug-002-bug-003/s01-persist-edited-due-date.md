# Feature Implementation Specification: Persist Edited Due Date

**Plan**: [`docs/specs/bug-002-bug-003/plan.md`](./plan.md)
**Story-ID**: S01

## Feature Overview and Goal
Make the existing todo edit flow persist a due date exactly as submitted by the current date-only dialog, and make invalid due-date submissions fail visibly instead of looking successful while dropping metadata.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` – "FR1: Persist Edited Due Date"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-date -->
<!-- extracted: 7b0b211 -->
> When a user saves a todo from the edit dialog with a due date, the todo must retain that date and present it again when the same dialog is reopened later.
>
> The save flow must not silently report success while discarding a user-entered due date.

### From `docs/specs/bug-002-bug-003/plan.md` – "S01: Persist Edited Due Date"
<!-- source: docs/specs/bug-002-bug-003/plan.md#s01-persist-edited-due-date -->
<!-- extracted: 2026-05-03 -->
> Fix the authenticated todo edit-save path so a due date submitted from the existing edit dialog persists and comes back when the same Todo is rendered or reopened. Include visible rejection for malformed due-date input on this route, and keep the existing HTML partial response model intact. Exclude broader date classification work such as overdue and due-today styling.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "Todo Domain"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#todo-domain -->
<!-- extracted: 7b0b211 -->
> | Term       | Definition                                                            | Avoid (synonyms)          | Bounded Context |
> |------------|-----------------------------------------------------------------------|---------------------------|-----------------|
> | Todo       | A single task inside a TodoList                                       | task, item, entry         | Todo            |
> | Due Date   | Date a todo is expected to be completed (stored naive)                | deadline, target date     | Todo            |


## Deeper Context

- `docs/PRODUCT-BACKLOG.md#known-defects` – original BUG-002 defect statement and severity.
- `docs/specs/bug-002-bug-003/prd.md#edge-cases` – clear-date and malformed-input expectations.
- `docs/specs/bug-002-bug-003/plan.md#phase-1-metadata-corrections` – story acceptance criteria and execution sequencing inside the plan bundle.


## Success Criteria (Must Be TRUE)
- [ ] A valid due date submitted from the existing edit dialog persists on the Todo and reappears in the rendered row metadata used to reopen the dialog.
- [ ] Clearing the due date through the same edit flow removes the stored value and reopens with an empty due-date field.
- [ ] A malformed due-date submission on the update route returns the standard HTML error partial and does not report an apparent success.

### Health Metrics (Must NOT Regress)
- [ ] Existing todo update behavior for title, note, and priority remains intact for valid submissions.
- [ ] Existing ownership checks and 404/403 HTML error flows remain unchanged.
- [ ] Existing todo route tests outside the due-date regression surface continue to pass.


## Scenarios

### Save and Reopen Due Date
- **Given** an authenticated user owns a Todo with no due date
- **When** the user submits the edit dialog with `due_date=2025-12-31` plus valid title and note values
- **Then** the Todo stores that date and the returned row partial contains reopen metadata that resolves back to `2025-12-31`

### Clear an Existing Due Date
- **Given** an authenticated user owns a Todo that already has a due date
- **When** the user submits the edit dialog with an empty `due_date`
- **Then** the Todo saves with no due date and the returned row partial exposes an empty reopen value

### Reject a Malformed Due Date
- **Given** an authenticated user owns a Todo
- **When** the user submits the edit route with a malformed `due_date` value that does not match the dialog contract
- **Then** the response is `partials/error.html` with a visible validation message and the Todo keeps its prior stored due date

### Preserve Other Edits With a Valid Due Date
- **Given** an authenticated user edits title, note, priority, and due date in one save
- **When** the submission contains a valid date from the current dialog control
- **Then** all valid field changes persist together in the same update


## Scope & Boundaries

### In Scope
- Align the update route's due-date parsing and validation with the existing edit dialog contract.
- Preserve row partial metadata so reopening the dialog reflects the stored due date accurately.
- Add regression coverage for valid save, clear, and malformed-input paths on the authenticated todo update flow.

### What We're NOT Doing
- Overdue or due-today styling fixes – tracked separately as BUG-004.
- Edit dialog redesign or new date controls – the current `type="date"` control stays authoritative for this story.
- New JSON error responses or redirect behavior – the route must stay in the existing HTML partial model.


## Architecture Decision

**We will**: accept the edit dialog's existing date-only payload on `update_todo`, normalize it into the stored `Todo.due_date`, and return `partials/error.html` for malformed values – this matches the live UI contract and preserves the current HTMX fragment workflow (over inventing a new datetime-local contract or silently coercing bad input).


## Technical Overview

### UI/UX Design (if applicable)
No UI redesign. The current edit dialog in `src/app/templates/app.html:121-157` remains the source of truth, including the date-only input and the existing save interaction.

### Data Models (if applicable)
`Todo.due_date` remains the existing optional `DateTime` column in `src/app/database.py:63-79`. No schema work is required; only the route contract and regression coverage change.

### Integration Points (if applicable)
The route update must stay compatible with:
- `openEditTodoDialog(...)` in `src/app/static/js/app.js:111-124`
- `data-todo-due-date` and `format_date_input(todo.due_date)` in `src/app/templates/partials/todo_item.html:1-48`


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:169-250            | Existing authenticated todo update handler and HTML error-return pattern
file   | src/app/templates/app.html:121-157         | Edit dialog field contract; due_date input is date-only
file   | src/app/static/js/app.js:111-124           | Reopen path that writes saved due-date metadata back into the dialog
file   | src/app/templates/partials/todo_item.html:1-48 | Row metadata contract used for reopen and display
file   | tests/test_todos.py:44-62                  | Existing todo update regression test to extend
file   | tests/conftest.py:71-113                  | Authenticated fixtures and seeded Todo pattern for route tests
```


## Constraints & Gotchas
- **Constraint**: `sl-input type="date"` posts a date-only value – Workaround: treat `YYYY-MM-DD` as the accepted route contract and reject other malformed inputs visibly.
- **Avoid**: silently swallowing `ValueError` during due-date parsing – Instead: return `partials/error.html` and leave stored state unchanged.
- **Critical**: the returned row partial feeds later dialog reopen state – Must handle by preserving accurate `data-todo-due-date` output after save and clear flows.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo update route accepts the current edit-dialog due-date format and persists it correctly
  - Update the due-date branch in `src/app/routes/todos.py:215-236` to align with the date-only dialog contract from `src/app/templates/app.html:138-145`; keep the rest of the update handler behavior unchanged.
  - **Verify**: `Test: PUT /api/todos/{id} with due_date=2025-12-31 returns 200 and stores a due date whose row partial reopens as 2025-12-31`

- [ ] **TI02** Malformed due-date submissions fail visibly instead of reporting false success
  - Reuse the existing HTML error partial pattern already used in todo validation failures in `src/app/routes/todos.py:200-213`; depends on TI01's finalized accepted input contract.
  - **Verify**: `Test: PUT /api/todos/{id} with malformed due_date returns an error partial and preserves the prior stored due date`

- [ ] **TI03** Clearing a due date removes both stored and rendered reopen metadata
  - Preserve the existing empty-input clear semantics while confirming the row partial emitted by `src/app/templates/partials/todo_item.html:1-48` no longer carries a stale due date; depends on TI01.
  - **Verify**: `Test: PUT /api/todos/{id} with due_date='' clears the database value and the returned row partial exposes an empty due-date reopen value`

- [ ] **TI04** Regression coverage proves due-date save, clear, and invalid-input behavior without breaking other field updates
  - Extend `tests/test_todos.py:44-62` with focused route tests rather than browser-only proof; keep title, note, and priority assertions in at least one valid update path.
  - **Verify**: `Test: targeted todo update regression tests pass for valid save, clear, malformed input, and combined field update scenarios`

### Testing Strategy
- [TI01,TI04] Scenario: Save and Reopen Due Date → route test updates a Todo with `due_date=2025-12-31`, asserts persisted value, and asserts returned HTML contains the reopen value.
- [TI03,TI04] Scenario: Clear an Existing Due Date → route test seeds a due date, clears it, and asserts database plus HTML metadata are empty.
- [TI02,TI04] Scenario: Reject a Malformed Due Date → route test submits malformed input, asserts error partial content, and asserts stored due date is unchanged.
- [TI01,TI04] Scenario: Preserve Other Edits With a Valid Due Date → route test updates title, note, priority, and due date together and asserts all persist.

### Validation
- Run `uv run pytest tests/test_todos.py -k "update_todo or due_date"` once the implementation is complete.
- Visually verify the authenticated edit dialog save and reopen flow in the browser because the story changes dialog-backed metadata.

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
