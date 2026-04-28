# Feature Implementation Specification: S01 - BUG-002 Persist Edit-Dialog Due Date

**Plan**: `docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md`
**Story-ID**: `S01`

## Feature Overview and Goal
Restore trustworthy Due Date persistence for the existing edit dialog so a saved date survives the HTMX rerender and is still present when the Todo is reopened for editing.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_

## Required Context

### From `docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md` - "S01: BUG-002 Persist Edit-Dialog Due Date"
<!-- source: docs/specs/bug-002-bug-003-todo-metadata-fixes/plan.md#s01-bug-002-persist-edit-dialog-due-date -->
<!-- extracted: 2026-04-28 -->
> **Scope**: Restore the existing edit dialog's Due Date persistence path from form submit through stored `Todo.due_date`, row rerender, and dialog reopen. Include explicit clear behavior and visible invalid-input handling for unparseable date payloads. Exclude UI redesign, datetime support, and unrelated overdue/due-today styling fixes.
>
> **Acceptance Criteria**:
> - [ ] Saving an existing Todo with a valid date-only Due Date from the edit dialog persists that date on the record.
> - [ ] After a successful save, the returned todo row shows the saved Due Date and reopening the edit dialog prepopulates the same `YYYY-MM-DD` value.
> - [ ] Clearing an existing Due Date and saving removes the stored value and reopens the dialog with a blank Due Date field.
> - [ ] An unparseable Due Date payload returns the standard HTML error partial and leaves the previously stored Due Date unchanged.

### From `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md` - "FR1: Persist Due Dates From the Edit Dialog"
<!-- source: docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#fr1-persist-due-dates-from-the-edit-dialog -->
<!-- extracted: d3138c5964bb6e0d2a4c6903d5495f1e2fee21d6 -->
> **Acceptance Criteria**:
> - [ ] When a user saves an existing todo with a valid date chosen in the edit dialog, the todo record persists that date.
> - [ ] After a successful save, the returned todo row shows the saved due date in the existing due-date display area.
> - [ ] Reopening the edit dialog for that todo shows the same saved date already populated.
> - [ ] If the user clears the due date and saves, the due date is removed and the reopened dialog remains blank.
>
> **Error Handling**:
> - If the due-date value cannot be interpreted, the system must not silently drop or ignore the user change while presenting a successful save.
> - The user must receive visible error feedback in the standard HTML error pattern, and the existing stored todo state must remain unchanged.

### From `AGENTS.md` - "Project-Specific Guidelines"
<!-- source: AGENTS.md#project-specific-guidelines -->
<!-- extracted: d3138c5964bb6e0d2a4c6903d5495f1e2fee21d6 -->
> - **HTMX-first.** Every route that renders should return an HTML partial - see `## Architecture -> The stack` above. Do not introduce JSON endpoints unless explicitly asked.
> - **Do not "fix" the intentionally simple auth.** Plain-text passwords and in-memory `sessions` dict are deliberate educational choices. See `src/app/core/deps.py` and the README.
> - **Pydantic models in `src/app/models/` are _not_ wired into routes.** Validation is ad-hoc in the handlers - do not assume models run.

## Deeper Context

- `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#user-flows` - End-to-end save, clear, and invalid-payload flows that this spec must preserve.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` - Canonical Todo and Due Date terminology for naming and acceptance text.
- `AGENTS.md#the-stack--and-why-it-matters-for-edits` - HTMX fragment rules, HTML error handling, and the server-rendered row/OOB swap model for Todo updates.

## Success Criteria (Must Be TRUE)

- [ ] `PUT /api/todos/{todo_id}` accepts the existing edit dialog's `YYYY-MM-DD` Due Date payload, persists it on `Todo.due_date`, and returns a rerendered row whose visible date and `data-todo-due-date` both reflect the saved value.
- [ ] Clearing the edit dialog Due Date submits an explicit clear action that removes the stored value and reopens the dialog with an empty Due Date field.
- [ ] An unparseable Due Date payload returns the standard HTML error partial instead of a success row swap, and the previously stored Due Date remains unchanged in the database.
- [ ] The fix preserves the current HTMX edit flow, title validation, ownership checks, and Priority persistence behavior.

### Health Metrics (Must NOT Regress)
- [ ] Existing todo update, auth, and ownership tests continue to pass.
- [ ] The edit flow remains a lightweight HTMX request with no full-page reload or JSON error contract.
- [ ] Due Date display and dialog prefill keep using the existing `format_date()` / `format_date_input()` rendering contract.

## Scenarios

### Save a valid Due Date from the edit dialog
- **Given** an authenticated user opens an existing Todo whose edit form posts to `PUT /api/todos/{todo_id}`
- **When** the user submits `due_date=2025-12-31` from the current `type="date"` edit control
- **Then** the response rerenders the todo row with `Dec 31, 2025` visible and `data-todo-due-date="2025-12-31"`, and reopening the dialog prepopulates `2025-12-31`

### Clear an existing Due Date
- **Given** a Todo already has a stored Due Date and the edit dialog is open
- **When** the user clears the Due Date field and saves
- **Then** `Todo.due_date` becomes empty/null, the rerendered row stops showing a Due Date badge, and reopening the dialog leaves the field blank

### Reject an unsupported Due Date payload
- **Given** a Todo already has a stored Due Date
- **When** the update route receives an unsupported payload such as `due_date=2025/12/31`
- **Then** the response uses the standard HTML error partial, the stored Due Date is unchanged, and the route does not silently report a successful save

### Preserve unrelated metadata updates while fixing Due Date persistence
- **Given** the user submits a valid title, note, Due Date, and Priority through the same edit dialog
- **When** the request succeeds
- **Then** the Due Date fix does not break existing title trimming, note persistence, or explicit Priority updates

## Scope & Boundaries

### In Scope
- Align the update route with the edit dialog's existing date-only payload contract.
- Preserve clear-field behavior for `due_date=""` and rerender/reopen consistency after a successful save.
- Surface invalid Due Date submissions with the existing HTML error partial pattern and keep stored state unchanged.
- Add route-level regression coverage for valid save, clear, reopen, and invalid-input behavior.

### What We're NOT Doing
- Adding time-of-day or datetime-local editing support - the PRD limits this fix to the current date-only dialog.
- Redesigning the edit dialog, row layout, or Due Date styling rules - BUG-004 covers separate styling defects.
- Refactoring the route layer to use Pydantic request models - current route validation stays ad hoc in this story.
- Changing authentication, session storage, or authorization behavior - the educational auth model is intentionally out of scope.

## Architecture Decision

**We will**: parse `due_date` in `update_todo()` using the same date-only `YYYY-MM-DD` contract already emitted by the edit dialog and surfaced by `format_date_input()`, and return the existing HTML error partial on parse failure - this fixes the persistence bug at the route boundary without changing UI controls or introducing JSON-specific validation semantics.

## Technical Overview

### UI/UX Design (if applicable)
The edit dialog remains unchanged: users still edit Due Date in the current `sl-input type="date"` control, save through the same HTMX form, and see the todo row rerender in place.

### Data Models (if applicable)
`Todo.due_date` remains an optional SQLAlchemy `DateTime`. This story only changes how the update route interprets incoming date-only strings and clear actions before persisting that field.

### Integration Points (if applicable)
The feature crosses the edit dialog form in `app.html`, the `openEditTodoDialog()` prefill path in `app.js`, the update route in `routes/todos.py`, and the row-render helpers in `todo_item.html` / `utils.py`.

## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:169-240               | Existing update route, validation branches, and current due-date parse path
file   | src/app/templates/app.html:121-156           | Edit dialog form contract and date input shape
file   | src/app/static/js/app.js:111-125             | Dialog prefill and HTMX target wiring
file   | src/app/templates/partials/todo_item.html:1-40 | Row render and reopen dataset expectations
file   | src/app/utils.py:35-41                       | Canonical `YYYY-MM-DD` output for dialog reopen
file   | tests/test_todos.py:44-62                    | Existing update regression test to extend
file   | tests/test_models.py:144-147                 | Clear-due-date parsing precedent
```

## Constraints & Gotchas
- **Constraint**: `type="date"` emits date-only values, while the current route parser expects a datetime-local format - Workaround: align parsing to `YYYY-MM-DD` in the route and keep clear handling explicit.
- **Avoid**: silently swallowing `ValueError` and returning the success row - Instead: return `partials/error.html` and preserve the pre-existing stored Due Date.
- **Critical**: routes do not use `TodoUpdate` automatically - Must handle by: copying the relevant route-level validation behavior rather than assuming model validators execute.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo update accepts the edit dialog's date-only Due Date payload and round-trips it back into the rerendered row
  - Follow `src/app/routes/todos.py:169-240` for the update path and `src/app/utils.py:35-41` for the output contract already consumed by `src/app/templates/partials/todo_item.html:1-40`.
  - **Verify**: `PUT /api/todos/{id}` with `due_date=2025-12-31` persists the date, returns HTML containing `Dec 31, 2025`, and includes `data-todo-due-date="2025-12-31"`

- [ ] **TI02** Invalid Due Date submissions fail visibly and preserve the previous stored Due Date
  - Reuse the existing HTML error-partial pattern already used for title validation in `src/app/routes/todos.py:200-213`; do not widen the response contract beyond HTMX HTML fragments.
  - **Verify**: submitting `due_date=2025/12/31` returns the error partial with a visible message and a DB refresh shows the previous Due Date is unchanged

- [ ] **TI03** Regression tests prove save, clear, reopen, and invalid-input behavior for the edit path
  - Extend `tests/test_todos.py:44-62` using the shared authenticated fixtures from `tests/conftest.py:71-113`; include one clear-path assertion and one invalid-format assertion.
  - **Verify**: targeted pytest for the new BUG-002 coverage fails before the fix and passes after, including explicit checks for clear behavior and invalid-payload rejection

### Testing Strategy

- [TI01] Scenario: Save a valid Due Date from the edit dialog -> add a route test that asserts persisted DB state plus returned row HTML/date dataset
- [TI01,TI03] Scenario: Clear an existing Due Date -> add a route test that starts with a stored Due Date and proves the saved row and reopen state are blank
- [TI02,TI03] Scenario: Reject an unsupported Due Date payload -> add a route test that asserts error partial output and unchanged DB state
- [TI01,TI03] Scenario: Preserve unrelated metadata updates while fixing Due Date persistence -> keep or extend the existing update test to prove title/note/Priority still persist

### Validation

- Run targeted todo route tests for BUG-002 coverage after implementation.
- Manually inspect the rerendered todo row markup in test assertions for both the visible formatted date and the `data-todo-due-date` reopen contract.

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
