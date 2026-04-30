# Feature Implementation Specification: S01 Persist due-date edits


## Feature Overview and Goal
Preserve Due Date changes made through the Todo edit dialog so a saved date survives save-and-reopen, intentional clearing still works, and invalid date input never silently corrupts existing metadata.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` – "FR1: Persist Todo Due Date Updates"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr1-persist-todo-due-date-updates -->
<!-- extracted: 7023cec2a64bab1642a6dd7e08e95b322ae864fe -->
> **Description**: The todo edit workflow must preserve valid due-date updates entered through the current edit dialog and must reflect the saved value consistently in both the rendered todo row and the dialog when reopened.
>
> **Acceptance Criteria**:
> - [ ] When a user saves a todo with a valid due date from the edit dialog, the stored todo record retains that due date.
> - [ ] When the same todo is reopened in the edit dialog after a successful save, the due-date field is pre-populated with the saved value.
> - [ ] Clearing the due-date field intentionally removes the due date from the todo.
> - [ ] If the submitted due-date value is invalid or unsupported, the system does not silently replace an existing due date with an unintended value.
>
> **Validation**:
> - Accept the date format emitted by the current due-date input control.
> - Preserve existing title validation and existing optional-field behavior.
> - Treat an intentionally blank due-date submission as a request to clear the due date.
>
> **Error Handling**:
> - Invalid due-date input must not create silent data loss.
> - If the due-date value cannot be accepted, the response must preserve user trust by leaving previously saved due-date data unchanged or by surfacing a normal error partial rather than pretending the save succeeded with altered data.

### From `docs/specs/bug-002-bug-003/plan.md` – "S01: Persist due-date edits"
<!-- source: docs/specs/bug-002-bug-003/plan.md#p-s01-persist-due-date-edits -->
<!-- extracted: 7023cec2a64bab1642a6dd7e08e95b322ae864fe -->
> **Scope**: Correct the todo edit-save-reopen flow so date-only values emitted by the current dialog persist in storage and round-trip back into the dialog. Include regression coverage for valid save, intentional clear, and invalid-input protection. Exclude overdue styling semantics, broader datetime normalization, and any UI redesign.
>
> **Acceptance Criteria**:
> - [ ] Saving a todo from the edit dialog with a valid `YYYY-MM-DD` due date persists that value on the Todo record.
> - [ ] Reopening the same todo after a successful save shows the saved due date populated in the edit dialog and row metadata.
> - [ ] Submitting an intentionally blank due-date value clears an existing due date.
> - [ ] Submitting an invalid or unsupported due-date value does not silently overwrite an existing saved due date.
>
> **Key Scenarios**:
> - Happy: edit an existing Todo, save `2025-12-31`, reopen it, and see `2025-12-31` still populated.
> - Edge: clear a previously saved Due Date and confirm reopen shows the field blank.
> - Error: submit an invalid due-date string against a Todo that already has a Due Date and confirm the existing value survives.


## Deeper Context

- `docs/specs/bug-002-bug-003/prd.md#edge-cases` – date-clear and invalid-input expectations that should be mirrored in regression tests.
- `docs/specs/bug-002-bug-003/prd.md#user-flows` – the save, reopen, and clear flows this fix must preserve.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical use of `Todo` and `Due Date`.


## Success Criteria (Must Be TRUE)
- [ ] `PUT /api/todos/{todo_id}` accepts the date-only string emitted by the current edit dialog and persists it on the Todo record.
- [ ] After a successful update, the returned todo fragment carries the saved Due Date in both visible metadata and the `format_date_input(todo.due_date)` reopen payload.
- [ ] An intentionally blank `due_date` submission clears the stored Due Date.
- [ ] An invalid or unsupported `due_date` submission against a Todo with an existing Due Date leaves the stored value unchanged.

### Health Metrics (Must NOT Regress)
- [ ] Existing authenticated todo CRUD coverage continues to pass.
- [ ] The edit flow still returns HTML fragments and does not introduce a full-page reload or JSON branch.
- [ ] Existing title, note, and Priority update behavior remains unchanged.


## Scenarios

### Save a valid Due Date and reopen
- **Given** an authenticated user has a `Todo` without a Due Date
- **When** the user submits `PUT /api/todos/{todo_id}` with `due_date=2025-12-31`
- **Then** the stored `Todo.due_date` becomes December 31, 2025 and the returned todo fragment contains `data-todo-due-date="2025-12-31"`

### Clear an existing Due Date intentionally
- **Given** an authenticated user has a `Todo` whose `due_date` is already set
- **When** the user submits the edit form with `due_date` blank
- **Then** the stored `Todo.due_date` becomes `None` and the returned fragment no longer carries a populated due-date payload

### Reject malformed Due Date input without data loss
- **Given** an authenticated user has a `Todo` whose `due_date` is `2025-12-31`
- **When** the user submits the edit form with an invalid `due_date` string such as `not-a-date`
- **Then** the stored Due Date remains `2025-12-31` and the response does not mutate it to an unintended value

### Preserve other editable fields while fixing Due Date parsing
- **Given** an authenticated user edits a `Todo` title, note, due date, and Priority together
- **When** the update succeeds
- **Then** the title, note, Due Date, and Priority all reflect the submitted values in storage and the returned fragment


## Scope & Boundaries

### In Scope
- Correct the edit-route Due Date parsing to match the date-only UI contract.
- Preserve the row-to-dialog round trip by ensuring the returned fragment exposes the persisted date in input format.
- Add isolated regression coverage for valid save, intentional clear, and invalid-input preservation.

### What We're NOT Doing
- Changing overdue or due-today styling logic in `src/app/utils.py` – that is `BUG-004`, not this story.
- Redesigning the edit dialog markup or client-side event flow – the current UI contract already emits the right shape.
- Introducing timezone conversion or datetime-local support – the PRD scope is date-only capture.
- Changing quick-add Priority defaults – that belongs to `S02`.


## Architecture Decision

**We will**: correct Due Date handling inside the existing `update_todo` route and prove the round trip with route-level regression tests – this matches the current HTMX fragment pattern with the smallest behavioral surface.


## Technical Overview

### UI/UX Design (if applicable)
No UI redesign is expected. The existing edit dialog already emits a date-only value and the row fragment already carries the reopen payload; the fix is to make server persistence honor that contract.

### Data Models (if applicable)
`Todo.due_date` remains the existing optional `DateTime` column. This story only defines which input shapes the edit route accepts and how blank versus invalid submissions affect stored state.

### Integration Points (if applicable)
This story integrates the edit dialog form in `src/app/templates/app.html`, the `update_todo` route in `src/app/routes/todos.py`, and the reopened fragment payload in `src/app/templates/partials/todo_item.html`.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:153-224              | Existing update_todo ownership and validation flow
file   | src/app/utils.py:26-33                       | format_date_input contract used by reopen payload
file   | src/app/templates/app.html:132-149           | Edit dialog emits a date-only due_date input
file   | src/app/templates/partials/todo_item.html:1-40 | Returned fragment must carry the persisted due date back to the dialog
file   | tests/conftest.py:1-93                       | Authenticated test client and fixture patterns
```


## Constraints & Gotchas
- **Constraint**: The route must continue returning HTML fragments – Workaround: keep the existing `TemplateResponse("partials/todo_item.html", ...)` success path.
- **Avoid**: Parsing `due_date` with a datetime-local format the UI never emits – Instead: align accepted input with the date-only control and test the exact string shape.
- **Critical**: Blank `due_date` already means "clear the date" – Must handle by: preserving the blank branch explicitly while tightening only the non-blank parse path.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo edit updates accept the date-only Due Date contract without silent loss
  - Own `src/app/routes/todos.py:153-224`; keep title and Priority validation behavior unchanged while replacing the mismatched due-date parse path.
  - **Verify**: `PUT /api/todos/{todo_id}` with `due_date=2025-12-31` stores a Due Date whose reopened fragment includes `data-todo-due-date="2025-12-31"`

- [ ] **TI02** Todo edit updates still support intentional Due Date clearing
  - Depends on TI01; preserve the existing blank-input branch as the explicit clear behavior for `due_date`.
  - **Verify**: starting from a Todo with `due_date=2025-12-31`, `PUT /api/todos/{todo_id}` with blank `due_date` leaves `Todo.due_date is None`

- [ ] **TI03** Malformed Due Date submissions preserve existing data and stay covered by isolated regressions
  - Add a dedicated regression module rather than editing the shared todo test file; prove valid save, blank clear, invalid-input preservation, and reopen payload behavior.
  - **Verify**: a test submitting `due_date=not-a-date` against a Todo already set to `2025-12-31` asserts the stored value remains `2025-12-31`

### Testing Strategy
- [TI01] Scenario: Save a valid Due Date and reopen → route test asserts DB persistence and `data-todo-due-date="2025-12-31"` in the returned fragment
- [TI02] Scenario: Clear an existing Due Date intentionally → route test asserts `Todo.due_date is None` after blank submission
- [TI03] Scenario: Reject malformed Due Date input without data loss → route test asserts the existing stored date survives invalid input
- [TI01,TI03] Scenario: Preserve other editable fields while fixing Due Date parsing → route test asserts title, note, Due Date, and Priority update together without regression

### Validation
- Run focused todo route tests covering the new Due Date regression module plus the existing todo CRUD suite.

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
