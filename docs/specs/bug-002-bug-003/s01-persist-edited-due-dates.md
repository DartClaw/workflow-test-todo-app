# Feature Implementation Specification: Persist Edited Due Dates

**Plan**: `docs/specs/bug-002-bug-003/plan.md`
**Story-ID**: `S01`

## Feature Overview and Goal
Restore reliable due-date persistence for the existing authenticated todo edit flow. A user who saves, clears, or later reopens a due date should see behavior that matches the current date control and rendered row state every time.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` - "FR1: Persist Edited Due Dates"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates -->
<!-- extracted: a7fb3dcc22a983e20856b0d7f4e829b8845ca96a -->
> - [ ] When a user saves a valid due date from the existing edit dialog, the todo row re-renders with that due date visible.
> - [ ] When the same todo is reopened in the edit dialog after save, the due date control shows the previously saved value.
> - [ ] Editing a todo without changing its already saved due date does not clear that due date.
> - [ ] Saving a blank due date intentionally clears the due date.

### From `docs/specs/bug-002-bug-003/prd.md` - "Validation"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates -->
<!-- extracted: a7fb3dcc22a983e20856b0d7f4e829b8845ca96a -->
> - The system accepts only due-date values supported by the current edit control.
> - Blank due date input is treated as an intentional clear action.
> - Invalid due-date input must not produce a silent success that leaves the user believing a new value was saved when it was not.

### From `AGENTS.md` - "The stack - and why it matters for edits"
<!-- source: AGENTS.md#the-stack-and-why-it-matters-for-edits -->
<!-- extracted: a7fb3dcc22a983e20856b0d7f4e829b8845ca96a -->
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.


## Deeper Context

- `docs/PRODUCT-BACKLOG.md#known-defects` - original `BUG-002` wording and severity.
- `AGENTS.md#tests` - authenticated route test harness and fixture patterns.
- `AGENTS.md#project-specific-guidelines` - HTMX-first and auth-preservation rules that bound this fix.


## Success Criteria (Must Be TRUE)
- [ ] Saving a valid date from the existing edit dialog stores it, re-renders the todo row with the visible date, and preserves `data-todo-due-date="YYYY-MM-DD"` for reopen.
- [ ] Reopening a todo after a saved due date shows the same date already populated, and later edits to other fields do not clear the stored due date.
- [ ] Submitting a blank due date clears the stored value, while submitting an invalid due-date value does not return a misleading success row update.

### Health Metrics (Must NOT Regress)
- [ ] Existing authenticated todo route tests remain green after the fix.
- [ ] The route still responds with HTML partials for both success and validation failure paths.
- [ ] Existing title, note, priority, auth, and ownership behavior in `update_todo(...)` remains unchanged outside the due-date contract.


## Scenarios

### Save and reopen a valid due date
- **Given** an authenticated user has an existing todo with no due date
- **When** the user submits the current edit dialog with `due_date=2025-12-31`
- **Then** the returned todo row displays `Dec 31, 2025`, stores `data-todo-due-date="2025-12-31"`, and reopening the dialog shows `2025-12-31` already populated

### Preserve an unchanged saved due date during later edits
- **Given** an authenticated user has a todo whose due date is already `2025-12-31`
- **When** the user later updates the title or note without changing the due-date field value
- **Then** the todo keeps the same stored due date and the returned row still serializes `2025-12-31`

### Intentionally clear a saved due date
- **Given** an authenticated user has a todo whose due date is already set
- **When** the user submits the edit dialog with the due-date field blank
- **Then** the stored due date becomes empty, the returned row omits the visible due-date badge, and reopening the dialog shows a blank due-date control

### Reject an invalid due-date submission without false success
- **Given** an authenticated user has a todo whose due date is currently `2025-12-31`
- **When** the user submits a due-date value outside the dialog's supported format
- **Then** the response uses the existing HTML error pattern and the stored due date remains `2025-12-31`


## Scope & Boundaries

### In Scope
- Restore date persistence for the existing todo edit flow from submission through rendered-row reopen state.
- Preserve the current clear-date behavior as an explicit blank submission rather than an accidental parse failure.
- Add regression coverage for valid save, reopen, clear, and invalid-input handling.

### What We're NOT Doing
- Redesigning the edit dialog or switching away from the current `type="date"` control - the PRD explicitly keeps the current UX.
- Introducing time-of-day support or new due-date storage semantics - the current defect scope is date-only persistence.
- Changing unrelated todo metadata flows such as priority badges or OOB incomplete-count behavior - those belong to other backlog items.
- Modifying authentication, ownership, or session behavior - this story is limited to todo editing behavior.


## Architecture Decision

**We will**: align todo due-date persistence to the existing date-only dialog contract and return an HTML validation error for unsupported date input instead of silently ignoring the submission.
**Rationale**: the current UI already emits and rehydrates `YYYY-MM-DD` values, so the least risky fix is to make server parsing and row serialization honor that contract consistently.
**Alternatives considered**:
1. **Keep the current parse fallback and accept silent mismatch** - rejected: it preserves the bug and violates the PRD's trust requirement.
2. **Change the UI to `datetime-local` to match the current parser** - rejected: it expands scope and changes user-facing behavior the PRD explicitly keeps in place.


## Technical Overview

### UI/UX Design
The existing edit dialog remains the only entry point. The user flow is save in the dialog, see the row re-render with the visible date, and reopen the same dialog with the same date still present.

### Data Models
`Todo.due_date` remains an optional field. This story only tightens how the existing date-only value is accepted, cleared, and reflected back into row and dialog state.

### Integration Points
The flow crosses the update route, row partial, and dialog hydration path. All success and failure responses remain HTML partials inside the current HTMX interaction model.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:169-247         | Existing todo update validation and partial-response pattern
file   | src/app/utils.py:24-31                  | Canonical date-input serialization helper already used in row rendering
file   | src/app/templates/partials/todo_item.html:1-40 | Row dataset and visible due-date rendering contract
file   | src/app/static/js/app.js:111-124        | Dialog hydration path that must receive the stored date unchanged
file   | tests/test_todos.py:44-62               | Current update test pattern to extend for due-date regressions
```


## Constraints & Gotchas
- **Constraint**: Route responses must stay HTML partials - Workaround: reuse `partials/error.html` for invalid date submissions instead of inventing JSON errors.
- **Avoid**: Parsing due dates with a format the dialog never emits - Instead: treat `format_date_input(...)` and `type="date"` as the round-trip contract.
- **Critical**: A failed parse must not look like a successful save - Must handle by: returning the existing HTML validation pattern and leaving stored state unchanged.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo updates accept and persist the existing date-only due-date value
  - Follow the validation and partial-response pattern in `src/app/routes/todos.py:169-247`; align parsing with the date-only values already produced by `format_date_input(...)` in `src/app/utils.py:24-31`.
  - **Verify**: `uv run pytest tests/test_todos.py -k "update_todo and due_date"` proves a PUT with `due_date=2025-12-31` stores the date and re-renders the row with `data-todo-due-date="2025-12-31"`

- [ ] **TI02** Reopened edit dialogs and later non-date edits preserve the stored due date
  - Follow the row-to-dialog hydration contract in `src/app/templates/partials/todo_item.html:1-40` and `src/app/static/js/app.js:111-124`; this task depends on TI01's persisted date format.
  - **Verify**: `uv run pytest tests/test_todos.py -k "reopen or preserve_due_date"` proves the returned row carries the same `data-todo-due-date` after save and after a later title-or-note-only edit

- [ ] **TI03** Blank and invalid due-date submissions follow explicit clear-or-error behavior
  - Reuse the existing HTML error partial pattern already used for title validation in `src/app/routes/todos.py:200-213`; this task depends on TI01's date-only contract.
  - **Verify**: `uv run pytest tests/test_todos.py -k "clear_due_date or invalid_due_date"` proves blank input clears the date while an unsupported value returns the HTML error path and leaves the prior stored date unchanged

### Testing Strategy
- [TI01] Scenario: save and reopen a valid due date -> add a route test that asserts persisted database state plus returned HTML includes `Dec 31, 2025` and `data-todo-due-date="2025-12-31"`
- [TI02] Scenario: preserve an unchanged saved due date during later edits -> add a second update test that edits non-date fields and confirms the prior due date remains serialized
- [TI03] Scenario: intentionally clear a saved due date -> add a test that submits blank `due_date` and confirms the row and database clear state
- [TI03] Scenario: reject an invalid due-date submission without false success -> add a test that submits an unsupported value and asserts HTML error response plus unchanged stored date

### Validation
- Run `uv run pytest tests/test_todos.py -k "due_date or update_todo"` after implementation.

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
- [ ] **UI verified** to match requirements


## Implementation Observations

_No observations recorded yet._
