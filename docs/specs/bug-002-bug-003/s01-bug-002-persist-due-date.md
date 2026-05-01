# Feature Implementation Specification: Persist edited Due Date

**Plan**: [`plan.md`](./plan.md)
**Story-ID**: S01

## Feature Overview and Goal
Restore reliable Due Date persistence in the existing edit-todo dialog so a saved calendar date survives save-and-reopen cycles. The fix must also stop malformed due-date submissions from returning a misleading success fragment.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `prd.md` – "FR1: Persist Edited Due Dates"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates -->
<!-- extracted: 621e664cd1c04fe8cc22d3d2ed8dd2e9bbed9673 -->
> The edit-todo workflow must store a valid due date selected through the existing dialog and must round-trip that date back into the UI when the same todo is edited again.
>
> When a user saves a todo with a valid due date from the edit dialog, the todo record retains that date after the save completes.
>
> When the user reopens the edit dialog for that todo, the due-date input displays the previously saved date.
>
> Saving a todo without a due date continues to clear the due date as it does today.
>
> If due-date input is invalid for the supported edit flow, the app must not imply that the submitted date was saved successfully.

### From `AGENTS.md` – "HTMX-first"
<!-- source: AGENTS.md#project-specific-guidelines -->
<!-- extracted: 621e664cd1c04fe8cc22d3d2ed8dd2e9bbed9673 -->
> Every route that renders should return an HTML partial. Do not introduce JSON endpoints unless explicitly asked.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 621e664cd1c04fe8cc22d3d2ed8dd2e9bbed9673 -->
> BUG-002: Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches.


## Deeper Context

- `docs/specs/bug-002-bug-003/plan.md#s01-persist-edited-due-date` – story-level acceptance and key scenarios for this defect slice.
- `docs/specs/bug-002-bug-003/prd.md#user-flows` – paired happy-path, clear-path, and malformed-payload expectations.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical terms for `Todo`, `Due Date`, and `Priority`.


## Success Criteria (Must Be TRUE)
- [ ] Submitting `due_date=YYYY-MM-DD` through the existing edit-todo form stores that calendar date on the Todo and returns the normal Todo partial success response.
- [ ] Reopening the edit dialog for that Todo rehydrates the due-date control with the same `YYYY-MM-DD` value via the existing server-rendered data attributes.
- [ ] Submitting the edit-todo form with an empty due-date value clears the stored Due Date without regressing title, note, or Priority updates.
- [ ] Submitting a malformed due-date payload returns the existing HTML error pattern and leaves the previously stored Due Date unchanged.

### Health Metrics (Must NOT Regress)
- [ ] Existing Todo route tests unrelated to due-date persistence continue to pass.
- [ ] The edit-todo flow remains HTMX partial based; no new JSON responses or client-side state stores are introduced.
- [ ] Existing title, note, and Priority update behavior remains unchanged for valid edit submissions.


## Scenarios

### Save and reopen with a valid Due Date
- **Given** an authenticated user owns a `Todo` with no stored Due Date
- **When** the user submits the existing edit-todo form with `due_date=2025-12-31`
- **Then** the server stores that date on the Todo and the reopened dialog shows `2025-12-31`

### Clear an existing Due Date
- **Given** an authenticated user owns a `Todo` with a stored Due Date
- **When** the user submits the edit-todo form with the due-date field blank
- **Then** the Todo is saved with no Due Date and the reopened dialog shows no selected date

### Update title and note while keeping Due Date persistence
- **Given** an authenticated user edits a `Todo` title, note, and Due Date in one request
- **When** the form submission succeeds
- **Then** the updated title and note persist alongside the correct Due Date

### Reject a malformed Due Date payload
- **Given** an authenticated user owns a `Todo` with an existing Due Date
- **When** the server receives an unsupported `due_date` payload for the edit route
- **Then** the response uses `partials/error.html` semantics instead of the normal success partial, and the previously stored Due Date is preserved


## Scope & Boundaries

### In Scope
- Accept the date shape emitted by the existing edit dialog and persist it through `update_todo()`.
- Preserve server-rendered dialog rehydration through the existing `format_date_input()` and `data-todo-due-date` pattern.
- Add route-level regression coverage for valid save, reopen, clear, and malformed-payload behavior.

### What We're NOT Doing
- Fixing overdue versus due-today styling behavior from `BUG-004` – separate defect scope.
- Redesigning the edit dialog or switching the Due Date control away from `type="date"` – outside this defect fix.
- Introducing timezone-aware Due Date semantics – the project intentionally stores Due Date naively today.
- Changing authentication, authorization, or session behavior – explicitly out of scope for this repository.


## Architecture Decision

**We will**: align `update_todo()` with the existing date-only edit dialog and convert malformed date parsing into the current HTML error-partial flow – this fixes the actual contract break without changing the HTMX interaction model (over client-side coercion or silent fallback behavior).


## Technical Overview

### UI/UX Design
The user continues to edit Todos through the existing modal dialog. No new controls or steps are added; the fix is entirely about making the existing Due Date field trustworthy.

### Data Models
`Todo.due_date` remains the existing optional SQLAlchemy `DateTime` field. This story only changes how edit-dialog submissions are interpreted and persisted so they round-trip through `format_date_input()`.

### Integration Points
The route output must stay compatible with `src/app/templates/partials/todo_item.html` and `openEditTodoDialog()` in `src/app/static/js/app.js`, both of which already pass a `YYYY-MM-DD` string around the dialog lifecycle.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:118-174         | Primary update handler and current due-date parsing bug
file   | src/app/templates/app.html:138-144      | Edit dialog Due Date and Priority controls
file   | src/app/templates/partials/todo_item.html:1-33 | Server-rendered data attributes used when reopening the dialog
file   | src/app/static/js/app.js:111-120        | Dialog hydration path for dueDate and priority values
file   | src/app/utils.py:26-33                  | `format_date_input()` contract for dialog round-tripping
file   | tests/test_todos.py:36-53               | Existing update-route regression test to extend
```


## Constraints & Gotchas
- **Constraint**: The route must keep returning HTML partials – Workaround: use `partials/error.html` for malformed-date rejection rather than throwing a JSON validation contract into the flow.
- **Avoid**: Parsing only datetime-local input – Instead: accept the date-only payload the current `type="date"` control actually submits.
- **Critical**: Silent `ValueError` fallback recreates the defect – Must handle by returning an explicit error partial and not committing a misleading success state.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Edit-todo submissions accept the current dialog's date-only payload and persist it in a form that round-trips through `format_date_input()`
  - Update the `update_todo()` Due Date branch in `src/app/routes/todos.py:155-160`; keep the existing title/note/Priority flow intact and use the current template/JS round-trip path as the contract.
  - **Verify**: `Test: PUT /api/todos/{id} with due_date=2025-12-31 stores a Due Date whose reopened dialog value is exactly 2025-12-31`

- [ ] **TI02** Blank edit-dialog submissions still clear Due Date without breaking other Todo field updates
  - Reuse the existing clear-on-empty branch in `src/app/routes/todos.py:160-162`; ensure it remains compatible with title, note, and Priority edits in the same request.
  - **Verify**: `Test: PUT /api/todos/{id} with due_date='' clears the stored Due Date while preserving the submitted title, note, and priority values`

- [ ] **TI03** Malformed Due Date payloads fail with the standard HTML error partial instead of silent success
  - Follow the repository's ad hoc validation pattern in `src/app/routes/todos.py:79-95` and the error-partial contract in `src/app/templates/partials/error.html`; this task depends on TI01 preserving the valid path.
  - **Verify**: `Test: PUT /api/todos/{id} with due_date='not-a-date' returns the error partial, does not report success content, and leaves the previous Due Date unchanged`

### Testing Strategy
- [TI01] Scenario: Save and reopen with a valid Due Date → extend the update-route test to assert persisted date and reopened-dialog value.
- [TI02] Scenario: Clear an existing Due Date → add a route test covering blank submission plus preserved title/note/Priority values.
- [TI03] Scenario: Reject a malformed Due Date payload → add a negative-path route test that proves HTML error handling and unchanged stored state.
- [TI01,TI02] Scenario: Update title and note while keeping Due Date persistence → keep assertions on existing non-date fields in the valid/clear edit tests.

### Validation
- Manual UI check after implementation: run the app, edit a Todo with a date, reopen the dialog, then clear the date and confirm both states in the authenticated UI.

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
