**Plan**: `docs/specs/bug-002-bug-003/plan.md`
**Story-ID**: `S01`

## Feature Overview and Goal
Restore trust in Todo due-date editing by making the edit dialog's date input round-trip cleanly through save and reopen. Invalid due-date submissions must fail visibly inside the existing HTMX dialog flow instead of being ignored as if the update succeeded.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` – "FR1: Persist Edited Due Dates"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates -->
<!-- extracted: 2026-05-04 -->
> When a user saves a valid due date from the edit dialog, the todo record retains that date after save.
>
> When the same todo is reopened in the edit dialog, the due-date field is prefilled with the saved date.
>
> When the due date is intentionally cleared and saved, reopening the dialog shows the field empty.
>
> When the submitted due-date value is invalid or unsupported, the system does not silently ignore the problem; it returns a visible error response and leaves the previous saved value unchanged.

### From `docs/specs/bug-002-bug-003/prd.md` – "Constraints"
<!-- source: docs/specs/bug-002-bug-003/prd.md#constraints -->
<!-- extracted: 2026-05-04 -->
> Existing HTML-partial, HTMX-first interaction patterns must remain intact.
>
> The intentionally simple authentication and broader educational architecture are unchanged by this effort.

### From `docs/guidelines/CRITICAL-RULES-AND-GUARDRAILS.md` – "Core Behavioral Rules"
<!-- source: docs/guidelines/CRITICAL-RULES-AND-GUARDRAILS.md#core-behavioral-rules -->
<!-- extracted: 2026-05-04 -->
> Verify before claiming done. Run the actual verification command (build, tests, lint) and include key results in your response. Never state something is complete or fixed without evidence. Orchestrators: run top-level verification before claiming overall completion.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "Todo Domain"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#todo-domain -->
<!-- extracted: 2026-05-04 -->
> Due Date | Date a todo is expected to be completed (stored naive)


## Deeper Context

- `docs/specs/bug-002-bug-003/prd.md#user-flows` – defect-specific flows for save, reopen, clear, and invalid-input behavior.
- `docs/specs/bug-002-bug-003/plan.md#phase-breakdown` – story-level scope, risk note, and acceptance criteria for S01.


## Success Criteria (Must Be TRUE)
- [x] Saving a valid `YYYY-MM-DD` Due Date from the edit dialog persists that date on the Todo and returns the normal updated todo-row partial.
- [x] Reopening the same Todo after save shows the persisted Due Date in the row dataset and edit dialog without requiring any client-side correction.
- [x] Clearing the Due Date and saving persists `None`, and the reopened edit dialog shows an empty Due Date field.
- [x] Submitting an invalid or unsupported Due Date swaps the form target with `partials/error.html`, keeps the dialog open, shows the exact message `Due date must use YYYY-MM-DD format`, and does not render a success-looking todo row.
- [x] An invalid Due Date submission preserves the previously saved valid Due Date in storage.

### Health Metrics (Must NOT Regress)
- [ ] Existing todo create/update route tests continue to pass.
- [ ] HTMX fragment behavior remains unchanged: authenticated updates still return HTML partials rather than redirects or JSON.
- [ ] Priority, note, and title update behavior remain unchanged unless explicitly covered by due-date validation.


## Scenarios

### Save and reopen a valid Due Date
- **Given** an authenticated User editing an existing Todo with no Due Date
- **When** the User submits the edit dialog with `due_date=2025-12-31`
- **Then** the update succeeds, the Todo stores that date, and later reopening the Todo shows `2025-12-31` in the dialog's Due Date field

### Clear an existing Due Date
- **Given** an authenticated User editing a Todo that already has a Due Date
- **When** the User submits the edit dialog with an empty Due Date field
- **Then** the Todo no longer has a Due Date and later reopening shows the field empty

### Reject malformed Due Date input
- **Given** an authenticated User editing a Todo that already has a valid Due Date
- **When** the update request submits a malformed `due_date` value that the dialog format does not accept
- **Then** the dialog remains open, the form swap target is replaced by `partials/error.html` showing `Due date must use YYYY-MM-DD format`, and the previously saved Due Date remains unchanged in storage

### Preserve other editable fields during a valid Due Date update
- **Given** an authenticated User updates title, note, Priority, and a valid Due Date together
- **When** the update succeeds
- **Then** the Todo row reflects the saved title, note, Priority, and Due Date using the existing partial contract


## Scope & Boundaries

### In Scope
- Make the update handler accept the edit dialog's date-only Due Date format and persist it correctly.
- Reject malformed or unsupported Due Date values with the existing visible HTML error-partial pattern inside the dialog's `hx-target="this"` swap area.
- Preserve reopen-state consistency by keeping the todo row dataset aligned with stored Due Date values.
- Add regression coverage for valid save, clear, reopen-state, and invalid-input behavior.

### What We're NOT Doing
- Change Due Date storage to timezone-aware values or alter broader date/time semantics – out of scope for this defect pair.
- Redesign the edit dialog UI or add new Due Date affordances – the current dialog remains the product contract.
- Introduce Pydantic-route validation for todo updates – route handlers remain the active validation layer in this project.
- Change unrelated Todo styling behavior such as overdue/due-today logic – tracked separately in `BUG-004`.


## Architecture Decision

**We will**: keep the existing `PUT /api/todos/{todo_id}` HTML-partial flow and fix the handler's Due Date parsing/validation in place – this matches the current HTMX contract and keeps the change isolated to the update path (over introducing a broader form/model rewrite).


## Technical Overview

### UI/UX Design
No new UI is introduced. The existing edit dialog remains authoritative. On malformed Due Date input, the dialog stays open while the form swap target is replaced by the existing `partials/error.html` alert, so the failure is visible without mutating the underlying todo row.

### Data Models
`Todo.due_date` remains an optional naive datetime field. The story only changes how the existing route accepts, validates, clears, and preserves that field.

### Integration Points
The update handler must remain aligned with the todo row partial, the `data-todo-due-date` attribute, and `openEditTodoDialog()` hydration so save and reopen behavior stay consistent. The invalid-input path must also stay aligned with the dialog's `hx-swap="outerHTML"` / `hx-target="this"` contract.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:169-233           | Existing update-path validation and partial-response pattern
file   | src/app/templates/app.html:122-147        | Edit dialog form contract, including the `type="date"` Due Date input
file   | src/app/templates/partials/todo_item.html:1-40 | Row dataset and reopen-state rendering for Due Date
file   | src/app/templates/partials/error.html:1-3 | Visible alert partial that will occupy the form swap target on invalid input
file   | src/app/static/js/app.js:111-121          | Dialog hydration from row data attributes
file   | src/app/utils.py:28-35                    | `format_date_input()` pattern for `YYYY-MM-DD` output
file   | tests/test_todos.py:44-62                 | Existing todo update test style to extend
```


## Constraints & Gotchas
- **Constraint**: The dialog submits date-only values – Workaround: parse only the accepted `YYYY-MM-DD` format for this route.
- **Avoid**: Silent `ValueError` fallback on invalid Due Date – Instead: return `partials/error.html` with `Due date must use YYYY-MM-DD format` and keep the previously saved value unchanged.
- **Critical**: The row dataset is the reopen source of truth – Must handle by ensuring saved/cleared Due Date values render back through `format_date_input(todo.due_date)`.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Todo updates accept the edit dialog's valid Due Date format and persist it consistently
  - Follow the existing update-path pattern at `src/app/routes/todos.py:169-233`; keep the route HTML-partial based and limit the change to Due Date parsing/clearing behavior.
  - **Verify**: `Test: PUT /api/todos/{id} with due_date=2025-12-31 returns 200, persists the Due Date, and the rendered row contains data-todo-due-date="2025-12-31"` ✅

- [x] **TI02** Invalid Due Date submissions fail visibly and preserve the prior stored value
  - Reuse the validation-failure response shape already used in `src/app/routes/todos.py`; on this path the dialog stays open and the form target is replaced by `partials/error.html` showing `Due date must use YYYY-MM-DD format`. Depends on TI01 keeping valid parsing behavior isolated from invalid-input handling.
  - **Verify**: `Test: PUT /api/todos/{id} with malformed due_date returns the error partial containing Due date must use YYYY-MM-DD format, does not render the todo row as success, and leaves the previously stored Due Date unchanged` ✅

- [x] **TI03** Regression coverage proves save, clear, reopen-state, and invalid-input behavior
  - Extend `tests/test_todos.py` using the existing route-test style; assert both DB state and rendered HTML dataset because reopen behavior is driven from the row partial.
  - **Verify**: `Test suite covers valid Due Date save, Due Date clear-to-empty, and invalid-input preservation without breaking existing todo update assertions` ✅

### Testing Strategy
- [TI01] Scenario: Save and reopen a valid Due Date → route test that updates a Todo, checks DB persistence, and asserts `data-todo-due-date="2025-12-31"` in the returned row
- [TI01,TI03] Scenario: Clear an existing Due Date → route test that starts with a saved Due Date, submits an empty field, and proves `todo.due_date is None` plus empty rendered dataset
- [TI02,TI03] Scenario: Reject malformed Due Date input → route test that preserves a previously saved Due Date and returns the error partial on malformed input
- [TI01,TI03] Scenario: Preserve other editable fields during a valid Due Date update → route test that updates title, note, and Priority alongside Due Date and proves no accidental regression

### Validation
- Verify the returned success partial still supports reopening through the existing row dataset, and verify the invalid-input path returns the alert partial inside the dialog target without changing the todo row.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details explicitly named in this FIS (format strings, file paths, and the invalid-input message `Due date must use YYYY-MM-DD format`) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.


## Final Validation Checklist

- [x] **All success criteria** met
- [x] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements (if applicable)


## Implementation Observations

_No observations recorded yet._
