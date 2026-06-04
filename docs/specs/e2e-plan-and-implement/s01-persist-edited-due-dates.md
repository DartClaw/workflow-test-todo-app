# Feature Implementation Specification

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S01`

## Feature Overview and Goal

**Intent**: Preserve due dates entered in the existing edit dialog so users can save and reopen the same Todo without losing the date they just set.

**Expected Outcomes**:

- [OC01] Saving `#edit-todo-dialog` with a `YYYY-MM-DD` due date persists that date on the Todo and returns a row whose visible due date and `data-todo-due-date` reflect the stored value immediately.
- [OC02] Reopening the same Todo through the existing edit flow shows the stored due date again, and submitting an empty due date clears that state without stale values reappearing.


## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S01 story entry"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> "scope": "Persist due dates entered through the edit dialog so saving and reopening the same todo shows the stored date. Includes aligning the edit submission path with the dialog's date-only input and adding regression coverage for save-and-reopen behavior. Excludes due-today or overdue styling changes and excludes expanding due dates to time-of-day support.",
>
> "notes": "The edit dialog submits a date-only value; keep ownership to the due-date edit persistence surface plus direct regression coverage."

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> | BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |


## Deeper Context

- `CLAUDE.md#architecture` – HTMX fragment-return patterns, dialog/edit route conventions, and why this story should stay on server-rendered partial seams.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical definition of `Due Date` and the repo's preferred Todo terminology.


## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02] Edited todo saves a date-only due date and republishes it in the returned row**
  - **Given** an authenticated user opens an existing `Todo` in `#edit-todo-dialog`
  - **When** the form submits `PUT /api/todos/{id}` with `due_date=2025-12-31`
  - **Then** the persisted `Todo.due_date` becomes December 31, 2025 and the returned `#todo-{id}` HTML contains `data-todo-due-date="2025-12-31"` plus visible `Dec 31, 2025`

- [ ] **S02 [OC02] [TI02] Reopening the saved todo pre-fills the edit dialog with the stored date**
  - **Given** the rendered `.todo-item` for that `Todo` includes `data-todo-due-date="2025-12-31"`
  - **When** the user activates `.edit-todo-btn` and `openEditTodoDialog(...)`
  - **Then** `#edit-todo-due-date` opens with value `2025-12-31`

- [ ] **S03 [OC02] [TI01,TI02,TI03] Clearing an edited due date removes it from persistence and reopen state**
  - **Given** a `Todo` already stores `2025-12-31`
  - **When** the edit dialog submits `due_date` as an empty string
  - **Then** `Todo.due_date` becomes `None`, the returned `#todo-{id}` row omits the due-date badge and sets `data-todo-due-date=""`, and reopening leaves `#edit-todo-due-date` blank


## Structural Criteria

- [ ] The edit-todo due-date contract stays `YYYY-MM-DD` across `src/app/templates/app.html#edit-todo-dialog`, `src/app/routes/todos.py#update_todo`, `src/app/templates/partials/todo_item.html`, and `src/app/static/js/app.js#openEditTodoDialog`.
- [ ] Regression coverage in `tests/test_todos.py#TestTodos.test_update_todo` fails if date-only edit submissions are silently ignored and proves both persist and clear behavior using `tests/conftest.py#test_todo`.


## Scope & Boundaries

### Work Areas

- `src/app/routes/todos.py#update_todo` – the edit submission seam that currently swallows date-only parse failures.
- `src/app/routes/todos.py#update_todo` – the edit submission seam that must persist the browser date input's existing `YYYY-MM-DD` payload and empty-string clear path.
- `src/app/utils.py#format_date_input` – canonical helper if the server-side persistence seam needs normalization to stay aligned with the existing HTML date-input contract.
- `tests/test_todos.py#TestTodos.test_update_todo` and `tests/conftest.py#test_todo` – direct regression seam and fixture for edited Todo persistence.

### What We're NOT Doing

- Overdue or due-today styling changes – those belong to `BUG-004` and are explicitly excluded by the S01 plan scope.
- Time-of-day or `datetime-local` support – the story is bound to the existing date-only dialog contract.
- Malformed free-form `due_date` payload handling – S01 defines only the browser's existing `YYYY-MM-DD` submit path and empty-string clearing behavior.
- Quick-add/default-priority creation behavior – that seam is owned by S02 and must remain merge-safe.
- Authentication, session, or storage-model changes – unrelated to the defect and explicitly out of scope for this thin story.


## Architecture Decision

**Approach**: Keep the existing `type="date"` UI contract and align `update_todo` persistence with `format_date_input(...)` so the same normalized date flows from form submit to stored Todo to returned row dataset to dialog reopen.
**Why this over alternatives**: Switching the dialog to datetime input or broadening into styling/default-priority fixes would exceed BUG-002's scope and violate the plan's merge-safe story split.


## Technical Overview

The defect lives in the edit submission seam, not in the dialog widget: `#edit-todo-dialog` already emits a date-only `due_date`. Once `src/app/routes/todos.py#update_todo` accepts that existing shape and stores a compatible value, `src/app/templates/partials/todo_item.html` can continue to normalize it through `format_date_input(todo.due_date)` for `data-todo-due-date`, and `src/app/static/js/app.js#openEditTodoDialog` can reopen the dialog without a second client-side formatting path.


## Code Patterns & External References

```text
# type | path#anchor                                   | why needed (intent)
file   | src/app/routes/todos.py#update_todo          | Edit route ownership, validation flow, and returned partial seam
file   | src/app/templates/app.html#edit-todo-dialog  | Existing `type="date"` form contract for edited due dates
file   | src/app/utils.py#format_date_input           | Canonical `YYYY-MM-DD` mapping for HTML date inputs
file   | src/app/templates/partials/todo_item.html   | Todo row dataset + display contract consumed on reopen
file   | src/app/static/js/app.js#openEditTodoDialog | Dialog hydration path from row dataset back into form fields
file   | tests/test_todos.py#TestTodos.test_update_todo | Existing route-level regression seam for edited Todo updates
```


## Constraints & Gotchas

- **Constraint**: The edit dialog already submits date-only values from `sl-input type="date"` – Workaround: keep `due_date` handling in `YYYY-MM-DD` form all the way through the returned row dataset instead of introducing a second format.
- **Avoid**: Broadening this story into generic free-form date parsing – Instead: keep the server-side handling aligned to the existing browser `YYYY-MM-DD` contract plus empty-string clearing only.
- **Critical**: S01 must stay merge-safe with S02 – Must handle by: keeping changes on edited due-date persistence surfaces only and stopping to re-plan if the fix appears to require the quick-add/default-priority seam.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Edited todo saves the dialog's `YYYY-MM-DD` due date into the persisted Todo
  - Follow the existing `src/app/templates/app.html#edit-todo-dialog` contract and `src/app/utils.py#format_date_input` as read-only references; `src/app/routes/todos.py#update_todo` must accept the existing browser date payload and persist it without changing the dialog contract.
  - **Verify**: `PUT /api/todos/{id}` with `due_date=2025-12-31` changes `Todo.due_date` to 2025-12-31 and the response HTML includes `data-todo-due-date="2025-12-31"`

- [ ] **TI02** Returned todo rows and reopened edit dialogs carry the same persisted due date end-to-end
  - Use `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js#openEditTodoDialog` as verification surfaces only; TI01's stored value must continue to flow through `format_date_input(todo.due_date)` without introducing a new client-side date transformation path or claiming ownership of those shared files.
  - **Verify**: after saving `2025-12-31`, the row shows `Dec 31, 2025`, `.todo-item` exposes `data-todo-due-date="2025-12-31"`, and reopening sets `#edit-todo-due-date` to `2025-12-31`

- [ ] **TI03** Edited due-date regression coverage proves persist and clear behavior on the existing fixture
  - Extend `tests/test_todos.py#TestTodos.test_update_todo` or adjacent route-level coverage; reuse `tests/conftest.py#test_todo` and keep the assertions on edited due-date persistence rather than S02's quick-add default-priority behavior.
  - **Verify**: test coverage proves `due_date=2025-12-31` persists, and confirms a follow-up empty `due_date` clears the stored value and returned `data-todo-due-date=""`

### Testing Strategy

- Use route-level `TestClient` coverage plus returned HTML assertions at `PUT /api/todos/{id}` as the primary proof surface; the reopen contract is encoded in `data-todo-due-date` and consumed unchanged by `openEditTodoDialog(...)`.

### Validation

- Manual browser check with `demo@example.com` / `demo123`: edit a Todo, save `2025-12-31`, reopen the same Todo and confirm `#edit-todo-due-date` is prefilled with `2025-12-31`, then clear it and confirm the next reopen is blank.

### Execution Contract

- If satisfying BUG-002 appears to require touching quick-add creation or default-priority code, stop and re-plan instead of widening into S02's ownership seam.


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
