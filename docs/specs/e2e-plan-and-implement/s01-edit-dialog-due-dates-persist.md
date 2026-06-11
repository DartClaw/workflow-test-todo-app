# Edit dialog due dates persist

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Ensure a Due Date entered through the existing edit todo dialog survives the save round-trip so users can rely on date-based planning without silent data loss.

**Expected Outcomes**:

- [OC01] Saving a due date from the edit todo dialog persists a non-empty `Todo.due_date` and the rendered todo row exposes the same date when reopened.
- [OC02] Clearing the due date from the same dialog removes the stored value cleanly instead of resurrecting stale data.
- [OC03] Malformed due-date payloads fail explicitly instead of being swallowed and leaving users with an apparently successful save.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: cc6e316 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: cc6e316 -->
> | BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |

## Deeper Context

- `CLAUDE.md#the-stack-and-why-it-matters-for-edits` – Todo routes return HTML fragments and use `partials/error.html` for validation failures.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical use of `Todo`, `Due Date`, and `Priority`.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI03] Edit-dialog date saves and reopens with the same value**
  - **Given** an authenticated user editing an existing `Todo` with no `due_date`
  - **When** the edit dialog submits `due_date=2025-12-31` with a valid title and priority
  - **Then** the saved row renders the due-date metadata for Dec 31, 2025 and reopening the dialog shows `2025-12-31`

- [ ] **S02 [OC02] [TI01,TI03] Clearing the dialog date removes the stored due date**
  - **Given** an existing `Todo` whose `due_date` is already set
  - **When** the edit dialog submits the same todo with an empty `due_date`
  - **Then** the stored `Todo.due_date` becomes empty and the reopened dialog keeps the field blank

- [ ] **S03 [OC03] [TI02,TI03] Malformed due-date payloads fail explicitly**
  - **Given** an existing `Todo` whose `due_date` is already set
  - **When** the update route receives an unsupported `due_date` payload such as `not-a-date`
  - **Then** the response is the standard error partial and the stored `due_date` remains unchanged

## Structural Criteria

- [ ] The edit todo route continues returning HTML partials and `partials/error.html` rather than JSON validation errors.
- [ ] The due-date round-trip stays aligned with the app's existing `YYYY-MM-DD` input/output contract used by `format_date_input`.
- [ ] Existing title, priority, and authorization behavior on `/api/todos/{todo_id}` remains unchanged.

## Scope & Boundaries

### Work Areas
- `/api/todos/{todo_id}` edit/update validation and due-date parsing
- Todo row due-date metadata used to repopulate the edit dialog
- Route-level regression tests for save, clear, and malformed edit submissions

### What We're NOT Doing
- Quick-add default priority behavior -- handled by S02 to preserve merge-safe isolation
- Overdue and due-today styling fixes -- tracked separately as BUG-004
- Changing `Todo.due_date` storage type or timezone semantics -- unnecessary for this defect fix
- Adding a new JSON validation API for todos -- the app stays HTMX-first with HTML partial responses

## Architecture Decision

**Approach**: Treat the edit dialog's `type="date"` payload as the supported contract for `update_todo`, and reject malformed values with the existing HTML error-partial pattern.
**Why this over alternatives**: It fixes the user-visible regression inside the update path and removes the silent-swallow behavior without broadening into unrelated create-flow changes.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor | why needed (intent)
file   | src/app/routes/todos.py#update_todo | Existing edit todo validation and HTML-partial response flow
file   | src/app/utils.py#format_date_input | Current due-date input/output contract for dialog round-trips
file   | src/app/templates/partials/todo_item.html | Due-date data attributes and rendered metadata used by the dialog
file   | tests/test_todos.py#TestTodos.test_update_todo | Route-level regression style for todo updates
```

## Constraints & Gotchas

- **Constraint**: `Todo.due_date` is stored as a naive `DateTime` -- Workaround: normalize the edit-dialog date-only input into the existing storage shape instead of changing the model.
- **Avoid**: silently swallowing unsupported date formats -- Instead: return the standard error partial and preserve the previously stored value.
- **Critical**: todo routes are HTMX fragment endpoints -- Must handle malformed input with `partials/error.html`, not a JSON envelope or redirect.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Edit todo saves the date format emitted by the current dialog and preserves it for reopen
  - Follow `src/app/routes/todos.py#update_todo` and `src/app/utils.py#format_date_input`; the supported edit-path contract is `YYYY-MM-DD`, and clearing the field must still remove the stored value
  - **Verify**: `Test: PUT /api/todos/{id}` with `due_date=2025-12-31` persists a non-null `Todo.due_date` and the response HTML contains `data-todo-due-date="2025-12-31"`

- [ ] **TI02** Malformed edit-dialog due-date payloads fail visibly instead of disappearing
  - Reuse the existing `partials/error.html` validation flow in `src/app/routes/todos.py#update_todo`; rejected payloads must not mutate the persisted `due_date`
  - **Verify**: `Test: PUT /api/todos/{id}` with `due_date=not-a-date` returns the error partial and reloading the same todo shows the original `due_date`

- [ ] **TI03** Todo update regression coverage proves set, clear, and malformed-date behavior at the route boundary
  - Extend the route tests around `tests/test_todos.py#TestTodos.test_update_todo`; keep proof at the save/render round-trip where the defect appears, not only in a helper-level parser check
  - **Verify**: `uv run pytest tests/test_todos.py -k "update_todo or due_date"` passes with coverage for set, clear, and malformed edit submissions

### Testing Strategy

### Validation

### Execution Contract

## Final Validation Checklist

## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

_No observations recorded yet._
