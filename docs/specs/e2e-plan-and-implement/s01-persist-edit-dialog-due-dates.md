# Persist edit-dialog due dates

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Ensure a due date chosen in the existing edit dialog survives save and reappears when the same Todo is reopened, so users can trust date edits in the current HTMX flow.

**Expected Outcomes**:

- [OC01] Saving a valid date from the existing edit dialog persists that date on the Todo.
- [OC02] Reopening the same Todo shows the saved date back in the due-date control using the existing `YYYY-MM-DD` HTML date contract.
- [OC03] Submitting the edit dialog with an empty due-date control clears an existing due date without breaking the rest of the edit flow.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 83a3c8554e943222396cb245036c9d158acbab53 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 83a3c8554e943222396cb245036c9d158acbab53 -->
> | BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S01 scope and constraints"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 83a3c8554e943222396cb245036c9d158acbab53 -->
> Todo edits persist a date chosen in the existing edit dialog, and reopening the same todo shows that saved date back in the due-date control. This story includes round-tripping valid date-only input and preserving the existing clear-date behavior. It excludes overdue styling changes, quick-add priority behavior, and any broader date-time redesign.
>
> Keep each story isolated to its own files; they must merge without conflict.

## Deeper Context

- `CLAUDE.md#the-stack--and-why-it-matters-for-edits` – HTMX routes return HTML partials, so the fix must preserve the fragment response shape.
- `src/app/templates/app.html#edit-todo-dialog` – the edit dialog uses `sl-input` with `type="date"`, which defines the submitted value shape.
- `src/app/routes/todos.py#update_todo` – current edit-todo update path, including the broken due-date parse seam.
- `src/app/templates/partials/todo_item.html` – saved due dates flow into rendered display and `data-todo-due-date` for dialog reopen.
- `src/app/static/js/app.js#openEditTodoDialog` – dialog reopen path copies row metadata back into `#edit-todo-due-date`.
- `src/app/utils.py#format_date_input` – canonical date-only formatter already used for HTML date inputs.
- `src/app/models/todo.py#TodoUpdate.parse_due_date` – existing date-only parsing precedent inside the repo.

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Saving a date in the edit dialog persists and round-trips back into the same control**
  - **Given** an authenticated user opens the existing edit dialog for a Todo with no due date
  - **When** they submit the dialog with `due_date=2025-12-31`
  - **Then** the Todo persists that date, the returned Todo row carries `data-todo-due-date="2025-12-31"`, and reopening the same Todo shows `2025-12-31` in the due-date control

- [x] **S02 [OC01,OC02] [TI01,TI02] Editing an existing due date replaces it with the newly chosen date**
  - **Given** a Todo already has a saved due date
  - **When** the user saves the edit dialog with a different valid date and other in-scope field edits
  - **Then** the Todo stores the new chosen date rather than the old date or an empty value, and the reopened dialog reflects the new date

- [x] **S03 [OC03] [TI03] Clearing the due-date control removes an existing due date**
  - **Given** a Todo already has a saved due date
  - **When** the user submits the edit dialog with an empty due-date control
  - **Then** the Todo no longer renders a due-date badge and reopening the dialog shows an empty due-date control

## Structural Criteria

- [x] The edit-todo route keeps its existing ownership checks, title validation, priority handling, and HTML partial response shape while fixing only the due-date persistence seam.
- [x] The due-date round-trip uses the existing date-only contract end to end (`type="date"` input, stored Todo value, `format_date_input`, row metadata, dialog reopen) without widening into datetime-local or timezone redesign.
- [x] Regression coverage proves both set-date and clear-date behavior with exact `YYYY-MM-DD` assertions so silent date-loss regressions fail tests.

## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#update_todo`
- Todo row due-date metadata contract consumed by the existing reopen flow
- `tests/test_todo_due_date_persistence.py`

### What We're NOT Doing
- Overdue or due-today styling changes – those belong to BUG-004 and are a separate behavior surface.
- Quick-add default priority behavior – that is explicitly owned by S02 in this plan.
- A broader date-time or timezone redesign – S01 must preserve the existing date-only HTML control contract.
- Refactoring route handlers to wire in `TodoUpdate` Pydantic validation globally – that is a larger architectural change than this thin bug fix.
- New user-facing error UX for malformed date payloads – the scoped fix is to make the current valid date-control path deterministic.

## Architecture Decision

**Approach**: Align the edit-todo update seam with the repo’s existing date-only contract so the persisted Todo value, returned row metadata, and dialog reopen path all honor the same `YYYY-MM-DD` shape.
**Why this over alternatives**: It fixes BUG-002 at the single broken seam and respects the plan constraint to keep S01 isolated from broader date handling and S02 priority work.

## Technical Overview

The round-trip is already defined by the existing surfaces: `sl-input type="date"` emits a date-only string, `update_todo` persists the Todo, `todo_item.html` re-renders the row and its `data-todo-due-date`, and `openEditTodoDialog()` copies that metadata back into the same control. S01 fixes that closed loop without changing unrelated todo-edit behavior.

## Code Patterns & External References

```text
# type | path#anchor                                 | why needed (intent)
file   | src/app/routes/todos.py#update_todo         | Current broken parse seam; keep auth/title/priority behavior intact
file   | src/app/templates/app.html#edit-todo-dialog | Source of truth for the dialog's `type="date"` input contract
file   | src/app/templates/partials/todo_item.html   | Returned row must carry the saved date for display and dialog reopen
file   | src/app/static/js/app.js#openEditTodoDialog | Reopen path consumes the row metadata and repopulates the date control
file   | src/app/utils.py#format_date_input          | Existing canonical formatter for HTML date inputs
file   | src/app/models/todo.py#TodoUpdate.parse_due_date | Existing date-only parsing precedent inside the repo
file   | tests/test_todo_due_date_persistence.py     | S01-owned regression surface for set-date and clear-date round-tripping
```

## Constraints & Gotchas

- **Constraint**: The PRD requires S01 and S02 to merge without conflict – keep S01 ownership to the edit-dialog due-date path and an S01-owned regression surface; do not widen into quick-add priority behavior.
- **Avoid**: Parsing the dialog submission as a datetime-local value – Instead: honor the date-only `YYYY-MM-DD` contract already used by the dialog and `format_date_input`.
- **Critical**: The current route swallows `ValueError` and can silently lose the chosen date while the rest of the edit succeeds – Must handle by making the valid date-control path deterministic and exact-match tested.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Valid date-only submissions from the edit dialog persist on the Todo
  - Follow `src/app/routes/todos.py#update_todo` and the date-only precedent in `src/app/models/todo.py#TodoUpdate.parse_due_date`; keep ownership, title validation, and priority behavior unchanged.
  - **Verify**: `uv run pytest tests/test_todo_due_date_persistence.py -k persist -vv` proves `due_date="2025-12-31"` persists as a saved Todo due date.

- [x] **TI02** Returned Todo rows feed the saved date back into the existing reopen flow
  - Follow `src/app/templates/partials/todo_item.html`, `src/app/static/js/app.js#openEditTodoDialog`, and `src/app/utils.py#format_date_input` as read-set context; the same saved date must appear in `data-todo-due-date` and in the reopened control without claiming S02-owned surfaces.
  - **Verify**: focused route coverage proves the update response contains `data-todo-due-date="2025-12-31"` and would repopulate `#edit-todo-due-date` with `2025-12-31`.

- [x] **TI03** Empty due-date submissions clear existing saved dates through the same edit flow
  - Preserve the current clear-date behavior in `src/app/routes/todos.py#update_todo`; clearing must remove both persisted date state and rendered due-date UI without affecting the rest of the edit.
  - **Verify**: `uv run pytest tests/test_todo_due_date_persistence.py -k clear -vv` proves submitting `due_date=""` leaves `todo.due_date is None` and the returned Todo HTML exposes no saved due date.

- [x] **TI04** Regression proof fails on silent date-loss regressions
  - Keep the BUG-002 proof in the dedicated `tests/test_todo_due_date_persistence.py` surface so the story stays merge-safe beside S02.
  - **Verify**: `uv run pytest tests/test_todo_due_date_persistence.py -vv` fails if the route reverts to swallowing valid date-only submissions.

### Testing Strategy

- Keep regression proof at the todo route/partial level: assert exact persisted date state plus returned HTML metadata needed for dialog reopen, and keep the tests in an S01-owned file so the plan’s no-conflict rule remains true in execution.

### Validation

- Manually verify on `http://localhost:8000` with `demo@example.com` / `demo123` that saving `2025-12-31` in the edit dialog and reopening the same Todo shows `2025-12-31`, and that clearing the control removes it on the next reopen.

### Execution Contract

- TI01 must land before TI02 because reopen-prefill behavior depends on a correctly persisted saved value.
- Keep test ownership in `tests/test_todo_due_date_persistence.py`; do not broaden into S02’s quick-add regression surfaces.

## Final Validation Checklist

- [x] Saving `2025-12-31` in the edit dialog persists that exact date.
- [x] Reopening the same Todo shows `2025-12-31` in the due-date control.
- [x] Clearing the control removes the saved due date without changing unrelated edit behavior.

## Implementation Observations

### NOTICED BUT NOT TOUCHING
- `uv run pytest` currently reports `tests/test_todos.py::TestTodos::test_create_todo` failure because `Todo.priority` is not persisted as `"low"` for quick-add flow; this is owned by `S02` and is a known baseline issue.
