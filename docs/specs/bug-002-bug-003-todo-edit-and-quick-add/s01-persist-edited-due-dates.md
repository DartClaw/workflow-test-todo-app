**Plan**: `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/plan.md`
**Story-ID**: `S01`

## Feature Overview and Goal
Fix the todo edit flow so a due date saved from the existing date-only dialog control persists on the `Todo`, renders back onto the row, and repopulates when the user reopens the edit dialog.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `prd.md` – "FR1: Persist Edited Due Dates"
<!-- source: docs/specs/bug-002-bug-003-todo-edit-and-quick-add/prd.md#fr1-persist-edited-due-dates -->
<!-- extracted: a84dcbdef89045430448b34c530c667b1d85840a -->
> **Description**: The existing todo edit flow must accept the date value emitted by the current due-date input and persist that value on save without silent loss.
>
> **Acceptance Criteria**:
> - [ ] When a user saves a valid due date from the edit dialog, the todo record stores a due date value.
> - [ ] After saving, the todo row renders the saved due date in its normal display region.
> - [ ] When the user reopens the edit dialog for that same todo, the due-date input is prefilled with the saved value.
> - [ ] If the user clears the due-date input and saves, the todo no longer has a due date.
> - [ ] If the submitted due-date value is invalid for the supported input format, the system must not silently convert it into a different date.

### From `plan.md` – "S01: Persist Edited Due Dates"
<!-- source: docs/specs/bug-002-bug-003-todo-edit-and-quick-add/plan.md#story-s01 -->
<!-- extracted: a84dcbdef89045430448b34c530c667b1d85840a -->
> **Scope**: Fix the existing todo edit flow so a valid date emitted by the current `type="date"` control persists through save, renders back on the todo row, and is shown again when the user reopens the edit dialog. Include route-level regression coverage for valid-save, clear-date, and malformed-date handling. Exclude quick-add priority behavior, time-of-day support, and edit-dialog redesign.
>
> **Acceptance Criteria**:
> - [ ] Saving a valid due date from the edit dialog stores a due date on the Todo record and the updated todo row renders that saved date.
> - [ ] Reopening the edit dialog for the same Todo shows the previously saved date in the due-date input.
> - [ ] Saving the edit dialog with a blank due-date field clears the stored due date and the todo row no longer renders due-date text.
> - [ ] Malformed due-date input does not silently become a different persisted date and does not change unrelated todo fields or authorization behavior.
> - [ ] Route-level regression tests cover the supported date-only format and the clear-date path without regressing existing todo update assertions.


## Deeper Context

- `prd.md#user-flows` – user-visible flows for save, reopen, clear, and malformed edit input.
- `../../STATE.md#current-phase` – confirms this work sits in active defect triage with no predecessor story dependency.
- `../../PRODUCT-BACKLOG.md#known-defects` – original BUG-002 wording and severity.


## Success Criteria (Must Be TRUE)
- [ ] A `PUT /api/todos/{todo_id}` submission with a valid `YYYY-MM-DD` due date persists that date onto `Todo.due_date` and the returned row partial shows the saved due date.
- [ ] Reopening the same Todo through the existing row-to-dialog preload path shows the exact saved date in the due-date input without manual normalization in the browser.
- [ ] Submitting an empty due-date field clears `Todo.due_date` and removes due-date display from the refreshed row partial.
- [ ] Malformed due-date input does not silently persist a wrong date and instead follows the existing HTML error-partial contract for invalid form input.

### Health Metrics (Must NOT Regress)
- [ ] Existing todo update assertions for title, note, and priority remain green.
- [ ] The edit flow still returns HTML partials and targets the existing row swap contract.
- [ ] No quick-add priority behavior or OOB count behavior changes as part of this story.


## Scenarios

### Save And Reopen A Due Date
- **Given** an authenticated user has a `Todo` in a `TodoList`
- **When** the user submits `PUT /api/todos/{todo_id}` with `due_date=2025-12-31` from the existing edit dialog flow
- **Then** the stored `Todo.due_date` represents `2025-12-31`, the returned row partial renders that date, and reopening the dialog preloads `2025-12-31`

### Clear An Existing Due Date
- **Given** a `Todo` already has a stored due date
- **When** the user submits the edit form with `due_date=` and otherwise valid fields
- **Then** the stored `Todo.due_date` becomes `None` and the refreshed row plus reopened dialog both show no due date

### Reject Malformed Due-Date Input
- **Given** a `Todo` already has a known due date
- **When** the user submits the edit form with a malformed `due_date` value outside the supported date-control format
- **Then** the route returns the standard HTML error partial and the previously stored due date is not replaced with a different value


## Scope & Boundaries

### In Scope
- Align the edit-route due-date parsing and persistence behavior with the existing `type="date"` control.
- Preserve the row-to-dialog preload path that uses `format_date_input(...)` plus `openEditTodoDialog(...)`.
- Add route-level regression tests for save, reopen, clear, and malformed-date handling.

### What We're NOT Doing
- Adding datetime or time-of-day support – the PRD scopes this to the current date-only control.
- Refactoring todo validation into Pydantic models – route-level validation is the existing project pattern.
- Changing quick-add priority behavior – that belongs to S02.
- Redesigning the edit dialog or its field layout – UI preservation is part of the defect-fix scope.


## Architecture Decision

**We will**: normalize S01 entirely inside the existing `update_todo(...)` handler and preserve the current template/JS preload contract – this fixes the bug at the source of persistence without introducing new APIs or client-side state rules (over a new JSON endpoint or broader form architecture change)


## Technical Overview

### UI/UX Design (if applicable)
The user keeps the same edit dialog and row interaction. The only behavior change is correctness: date-only input values round-trip through save, row render, and reopen without disappearing.

### Data Models (if applicable)
`Todo.due_date` remains the persisted field. The story only changes how route input maps into that field and how invalid submissions are handled.

### Integration Points (if applicable)
This story integrates the FastAPI update route, the `format_date_input(...)` helper already used in the row partial, and the JS dialog preload path that assigns `dueDate` into `#edit-todo-due-date`.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:169-240         | Existing edit/update route, ownership checks, validation flow
file   | src/app/templates/app.html:121-149      | Edit dialog field names and current `type="date"` contract
file   | src/app/templates/partials/todo_item.html:1-40 | Row render and data attributes used for reopen-state preload
file   | src/app/static/js/app.js:111-124        | `openEditTodoDialog(...)` preload behavior
file   | tests/test_todos.py:44-62               | Existing update test pattern to extend for regression coverage
file   | src/app/utils.py:35-41                  | `format_date_input(...)` helper feeding the dialog's due-date value
```


## Constraints & Gotchas
- **Constraint**: The supported input format is whatever the current date-only control emits – Workaround: parse that format explicitly and keep the route behavior aligned with the existing template contract.
- **Avoid**: Silently swallowing malformed dates and leaving stale state ambiguous – Instead: return the standard HTML error partial and preserve the previous stored value.
- **Critical**: Reopen behavior depends on row data attributes, not a second database fetch into the dialog – Must handle by: ensuring the refreshed row exposes the same persisted date the dialog expects.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** The edit route accepts the current date-only dialog value and persists it onto `Todo.due_date`
  - Follow the existing handler structure at `src/app/routes/todos.py:169-240`; keep ownership, title validation, and priority normalization intact while replacing the mismatched due-date parsing path
  - **Verify**: `uv run pytest tests/test_todos.py -k "update_todo and not other_users"` passes with assertions that a PUT carrying due_date=2025-12-31 stores that date and returns 200`

- [ ] **TI02** Clearing the due-date field removes the stored value and the returned row no longer renders due-date state
  - Reuse the existing blank-field branch in `src/app/routes/todos.py:223-230`; ensure the row partial at `src/app/templates/partials/todo_item.html:23-29` reflects the cleared state without extra client logic
  - **Verify**: `uv run pytest tests/test_todos.py -k "clear_due_date"` passes with assertions that submitting due_date='' sets Todo.due_date to None and the response content omits the due-date display`

- [ ] **TI03** Malformed due-date submissions follow the HTML error-partial contract instead of silently mutating persisted state
  - Extend the same route-level validation pattern used for empty title errors in `src/app/routes/todos.py:200-213`; keep the response in `partials/error.html` form and do not touch unrelated fields when the date is invalid
  - **Verify**: `uv run pytest tests/test_todos.py -k "invalid_due_date"` passes with assertions that malformed input returns the error partial and the previously stored due date remains unchanged`

- [ ] **TI04** Regression coverage proves the row-to-dialog reopen path uses the persisted date value end to end
  - Build on the row data contract in `src/app/templates/partials/todo_item.html:1-7` and the preload pattern in `src/app/static/js/app.js:111-118`; this task depends on TI01 and TI02 producing correct stored state
  - **Verify**: `uv run pytest tests/test_todos.py -k "reopen_due_date"` passes with response assertions that the refreshed row includes the exact `data-todo-due-date="2025-12-31"` value used by the edit dialog preload path`

### Testing Strategy
- [TI01] Scenario: Save And Reopen A Due Date → route test updates a todo with `due_date=2025-12-31` and verifies persisted storage plus rendered response content
- [TI02] Scenario: Clear An Existing Due Date → route test starts with a stored due date, submits `due_date=''`, and verifies DB state plus rendered row state
- [TI03] Scenario: Reject Malformed Due-Date Input → route test submits a malformed date string and verifies the HTML error partial plus unchanged stored due date
- [TI04] Scenario: Save And Reopen A Due Date → response-content assertion proves the row carries the exact date value that the dialog preload script consumes

### Validation
- Verify the refreshed row response contains the same date string that the dialog preload path expects, not just a database value.

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


## Implementation Observations

_No observations recorded yet._
