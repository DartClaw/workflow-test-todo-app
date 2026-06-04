# Persist Edit-Dialog Due Dates

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Ensure Due Dates entered through the Edit Todo dialog survive save and reopen so users can trust the existing date-only edit flow.

**Expected Outcomes**:

- [OC01] A Todo with no Due Date can receive one through the Edit Todo dialog, and the saved date shows up immediately in the returned row and on the next dialog open.
- [OC02] A Todo with an existing Due Date can be changed to a different calendar date through the Edit Todo dialog without reverting to the old value or an empty field.
- [OC03] Clearing the Due Date field in the Edit Todo dialog still removes the stored Due Date and round-trips back as empty.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 4ff97922533e1c690a677b4b0ffd6209a4670d58 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 4ff97922533e1c690a677b4b0ffd6209a4670d58 -->
> | BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | - | Open |

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Story S01"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 4ff97922533e1c690a677b4b0ffd6209a4670d58 -->
> "name": "Persist edit-dialog due dates",
> "scope": "Make due dates entered through the Edit Todo dialog persist after save and round-trip back into the same dialog using the existing date-only contract. Include saving a first due date, changing an existing due date, and preserving the current clear-date behavior; exclude priority defaults, overdue styling, and broader timezone semantics.",
> "notes": "Own the due-date parsing contract end-to-end, move BUG-002 assertions into `tests/test_bug_002_due_dates.py`, and keep the change out of S02-owned priority-default surfaces."

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Shared Decisions"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: 4ff97922533e1c690a677b4b0ffd6209a4670d58 -->
> "title": "Enforce story isolation through file ownership",
> "description": "S01 stays in the due-date update path and owns `tests/test_bug_002_due_dates.py`, while S02 solves priority defaults through model/render behavior and owns `tests/test_bug_003_priority_defaults.py`; each story moves or retires its bug-specific assertions from `tests/test_todos.py` before claiming isolated green validation."

## Deeper Context

- `docs/STACK.md#frameworks--libraries` – FastAPI + Jinja2 + HTMX fragment-returning stack and pytest baseline; keep route responses and regression tests aligned with that contract.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical `Todo` and `Due Date` terminology; use these exact terms in scenarios, tasks, and tests.
- `src/app/templates/app.html:121-157` – Edit Todo dialog contract; the date input already submits `YYYY-MM-DD`.
- `src/app/templates/partials/todo_item.html:1-47` – Returned row fragment exposes `data-todo-due-date`; verify the saved value round-trips through that surface without taking ownership of the file.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02] First due dates survive save and reopen**
  - **Given** a Todo with no Due Date is open in the Edit Todo dialog
  - **When** the user enters `2025-12-31` in the Due Date field and saves
  - **Then** the returned todo row exposes `data-todo-due-date="2025-12-31"` and reopening the same dialog shows `2025-12-31` in the Due Date field

- [ ] **S02 [OC02] [TI01,TI02] Existing due dates can be replaced with a different calendar day**
  - **Given** a Todo already stores Due Date `2025-12-31`
  - **When** the user changes the Due Date to `2026-01-15` and saves from the Edit Todo dialog
  - **Then** the stored Due Date is replaced with `2026-01-15` and reopening the dialog shows `2026-01-15`, not the previous date or an empty field

- [ ] **S03 [OC03] [TI01,TI02] Clearing a due date still removes it**
  - **Given** a Todo already stores Due Date `2025-12-31`
  - **When** the user clears the Due Date field and saves
  - **Then** the todo row no longer renders due-date metadata and reopening the dialog shows an empty Due Date field

## Structural Criteria

- [ ] The edit-todo flow remains aligned with the existing `type="date"` and `format_date_input()` `YYYY-MM-DD` contract end-to-end.
- [ ] The todo update route continues to return the existing `partials/todo_item.html` fragment so HTMX replacement and dialog reopen state stay in sync.
- [ ] Focused regression coverage exists for first-set, replace-existing, and clear-date flows in an S01-owned test file, not in S02-owned priority-default coverage.

## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#update_todo` – Due Date parse, clear, and save behavior for edit-dialog submissions
- `tests/test_bug_002_due_dates.py` – focused regression coverage for first-set, replace-existing, and clear-date paths

### What We're NOT Doing
- Priority default behavior or null-priority fallback – owned by S02 per the plan's file-ownership split
- Overdue or "due today" styling semantics – tracked separately by BUG-004 and unrelated to Due Date persistence
- Timezone normalization or datetime-input UX changes – this story preserves the existing date-only contract rather than redefining date semantics
- Malformed non-`YYYY-MM-DD` payload handling beyond the existing dialog contract – this story restores the supported date-input path and does not redefine unsupported manual payload behavior
- New JSON endpoints or client-side state management – the app remains HTMX-first with server-rendered partial responses

## Architecture Decision

**Approach**: Keep the fix in the server-side edit-todo persistence path so `PUT /api/todos/{todo_id}` accepts the existing `YYYY-MM-DD` value emitted by the dialog and helper formatting contract.
**Why this over alternatives**: The defect is a format mismatch in the update path; changing dialog structure, JS defaults, or priority behavior would widen scope into S02-owned surfaces without addressing the root cause.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor or url                              | why needed (intent)
file   | src/app/routes/todos.py#update_todo            | Current edit route – keep ownership in the Due Date save branch
file   | src/app/utils.py#format_date_input             | Existing HTML date-input contract – round-trip persisted values as YYYY-MM-DD
file   | src/app/templates/app.html:121-157             | Edit dialog contract – preserve the current `type="date"` submission shape
file   | src/app/templates/partials/todo_item.html:1-47 | Returned fragment shape – verify `data-todo-due-date` reflects the saved value
file   | tests/conftest.py#test_todo                    | Base fixture shape for a Todo that starts without a Due Date
```

## Constraints & Gotchas

- **Constraint**: The Edit Todo dialog already submits a date-only value via `type="date"` and `format_date_input()` – Workaround: keep server parsing aligned to `YYYY-MM-DD` rather than requiring a time component.
- **Avoid**: Fixing BUG-002 by mutating priority-default behavior or dialog default selection – Instead: confine this story to Due Date persistence and leave priority normalization to S02.
- **Critical**: Todo edits return HTML fragments, not JSON – Must handle by preserving the `partials/todo_item.html` response shape that HTMX swaps back into the DOM.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo edit saves accept the existing `YYYY-MM-DD` Due Date payload
  - Keep ownership in `src/app/routes/todos.py#update_todo`; reuse the current blank-input clear branch and preserve title, note, and priority validation behavior while removing the time-component requirement from Due Date persistence. This story restores the supported dialog payload and leaves unsupported malformed payload semantics unchanged.
  - **Verify**: `Test: PUT /api/todos/{id}` with `due_date=2025-12-31` persists a non-null Due Date whose `format_date_input()` value is `2025-12-31`, and the response still renders the todo row fragment rather than `partials/error.html`.

- [ ] **TI02** Todo edit regression coverage proves first-set, replace-existing, and clear-date paths
  - Create `tests/test_bug_002_due_dates.py` using `tests/conftest.py#test_todo`; move or retire BUG-002 assertions from `tests/test_todos.py`, then assert the exact saved calendar date for a first save, a replacement save, and a clear-to-empty save without importing S02-owned priority behavior into the same file.
  - **Verify**: `Test: uv run pytest tests/test_bug_002_due_dates.py -q` passes with one case starting from no Due Date, one replacing an existing Due Date, and one clearing back to None.

### Testing Strategy

### Validation

- Confirm in the browser that saving `2025-12-31`, then `2026-01-15`, then clearing the field on the same demo Todo produces matching `data-todo-due-date` values and dialog state each time.

### Execution Contract

- Story-local validation is not complete until BUG-002 assertions have been extracted from `tests/test_todos.py` into `tests/test_bug_002_due_dates.py` or explicitly retired there, so S01 can run green without inheriting BUG-003 failures.
- If the proposed fix appears to require changes in S02-owned priority-default surfaces such as `src/app/database.py#Todo` or `src/app/templates/partials/todo_item.html`, stop and split the work back at the plan level instead of broadening S01.

## Final Validation Checklist

## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

Discovered Requirements entries use this shape:

- **Title**: short imperative phrase
- **Description**: 1-2 sentences on the discovered requirement
- **Rationale**: why it was missed in original spec
- **Interpretation** (AUTO_MODE only): the conservative interpretation chosen and why
- **Traced from**: task ID where the discovery occurred
- **Date**: YYYY-MM-DD

_No observations recorded yet._
