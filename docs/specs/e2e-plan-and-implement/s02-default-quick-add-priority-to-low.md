# Default quick-add priority to low

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S02`

## Feature Overview and Goal

**Intent**: Ensure the title-only quick-add flow creates a fully-populated Todo so users immediately see the documented default priority and do not encounter an empty edit-dialog selector on the next interaction.

**Expected Outcomes**:

- [OC01] Todos created from the quick-add form persist with `low` priority when no priority input is supplied.
- [OC02] The quick-add HTML fragment immediately exposes `low` priority in the rendered row state used for badges, styling, and edit-dialog hydration.
- [OC03] The BUG-003 fix preserves the existing quick-add validation and HTMX/OOB response contract.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 8c4b71ffe6c3cf2887422be2781f616bd0916ba7 -->
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default.

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 8c4b71ffe6c3cf2887422be2781f616bd0916ba7 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S02 scope and isolation note"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 8c4b71ffe6c3cf2887422be2781f616bd0916ba7 -->
> "scope": "Ensure Todos created from the quick-add form always start with the documented `low` priority so the rendered row and subsequent edit dialog show a populated priority value immediately. Includes create-time defaulting and regression coverage for quick-add output; excludes edit-dialog due-date parsing and broader priority UX changes.",
>
> "notes": "Keep verification out of S01's test file and prefer create-time defaulting on S02-owned surfaces so both stories remain merge-safe under the PRD constraint."

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Quick-add POST with only title returns a low-priority row**
  - **Given** an authenticated user viewing a TodoList with the quick-add form
  - **When** they submit `/api/todos` with `list_id` and `title` only
  - **Then** the new Todo is stored with `priority == "low"` and the returned fragment renders `priority-low`, `data-todo-priority="low"`, and a visible `Low` priority badge

- [x] **S02 [OC02] [TI02] Edit dialog opens from the new row with `low` already populated**
  - **Given** a Todo just created through quick-add and rendered via the returned row fragment
  - **When** the user activates the row's Edit action
  - **Then** the priority passed into `openEditTodoDialog(...)` is `low`, so the edit dialog selector is populated instead of blank

- [x] **S03 [OC01,OC02] [TI01,TI02] Reloading the list preserves the same low-priority state**
  - **Given** a Todo created from quick-add without any explicit priority input
  - **When** the user reloads or revisits the list that contains that Todo
  - **Then** the Todo renders again with `data-todo-priority="low"` and a `Low` badge, proving the value was persisted and not supplied only by a client-side fallback

- [x] **S04 [OC03] [TI02,TI03] Blank-title rejection still returns the existing error partial**
  - **Given** the quick-add form is submitted with a whitespace-only `title`
  - **When** `/api/todos` rejects the request
  - **Then** the response still follows the existing error-partial path and no Todo is inserted as a side effect of the BUG-003 fix

## Structural Criteria

- [x] The quick-add entrypoint remains a title-only contract for BUG-003; no new priority field is required from the form or POST body.
- [x] Quick-add success responses still include the existing `hx-swap-oob="true"` sidebar count update while adding populated priority state to the returned row.
- [x] S02 keeps ownership off S01's due-date update and regression surfaces by proving the fix through create-time defaulting plus a dedicated S02 regression file.

## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo` – omitted-priority create path for persisted Todo records
- Quick-add rendered-row priority contract – badges, `priority-low`, and `data-todo-priority="low"` must reflect the stored default without taking ownership of S01's update surfaces
- Existing title-only quick-add flow – preserve the current HTMX/OOB response contract while letting the persisted default flow through unchanged UI surfaces
- `tests/test_todo_quick_add_priority.py` – S02-owned regression coverage kept separate from the regression file chosen for S01's due-date work

### What We're NOT Doing
- Edit-dialog due-date parsing or persistence changes – S01 owns BUG-002 and its update-path regression surface
- Quick-add UI enhancements such as exposing a priority selector in the form – BUG-003 only requires the documented default when priority is omitted
- Pydantic request-model adoption for todo routes – the plan requires staying within the current handler/creation flow
- Overdue or due-today styling fixes – that is BUG-004, not part of this story

## Architecture Decision

**Approach**: Default omitted quick-add priority at the Todo creation boundary so the persisted record, returned HTMX row, and later edit-dialog hydration all agree on `low` without widening the quick-add form contract.
**Why this over alternatives**: It fixes BUG-003 on an S02-owned surface, avoids the S01 edit/update due-date path, and satisfies the PRD's file-isolation constraint better than another `src/app/routes/todos.py` edit.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor or url                         | why needed (intent)
file   | src/app/database.py#Todo                  | Create-time default boundary for omitted priority
file   | src/app/routes/todos.py#create_todo       | Quick-add route stays title-only and returns the success fragment
file   | src/app/templates/partials/todo_item.html:1-40 | Row attributes, badge text, and edit-action payload must all reflect the stored priority
file   | src/app/templates/partials/todo_item_with_oob.html:1-3 | Preserve the sidebar count OOB swap on successful quick-add
file   | src/app/static/js/app.js:111-119          | Edit dialog reads the rendered priority argument; empty here reproduces BUG-003
file   | tests/test_todos.py#TestTodos.test_create_todo | Existing authenticated quick-add route-test pattern to mirror in an S02-owned test module
```

## Constraints & Gotchas

- **Constraint**: Quick-add routes return HTML fragments, not JSON – Workaround: verify the success path through rendered fragment content, not only DB state
- **Avoid**: Treating the edit dialog's `sl-select` default as the fix – Instead: make the Todo row itself carry `low`, because the dialog is hydrated from rendered row state
- **Critical**: S02 must stay isolated from S01's due-date work – Must handle by: keeping the BUG-003 regression file separate from the file chosen for S01's due-date coverage and avoiding ownership of S01's update or due-date persistence surfaces

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Omitted-priority quick-add inserts persist as `low`
  - Own the create-time defaulting surface at `src/app/database.py#Todo`; preserve `src/app/routes/todos.py#create_todo` as a title-only entrypoint and do not widen into `src/app/routes/todos.py#update_todo`
  - **Verify**: A regression test posts `/api/todos` with only `list_id` and `title`, then asserts the inserted `Todo.priority` is exactly `low`

- [x] **TI02** Existing quick-add row rendering exposes `low` everywhere the UI reads priority
  - Follow `src/app/templates/partials/todo_item.html:1-40`, `src/app/templates/partials/todo_item_with_oob.html:1-3`, and `src/app/static/js/app.js:111-119` as read-set references; prove the persisted default flows through the existing fragment instead of taking ownership of S01's update surfaces
  - **Verify**: The quick-add response HTML contains `priority-low`, `data-todo-priority="low"`, `Low`, and `hx-swap-oob="true"`

- [x] **TI03** S02 regression coverage proves BUG-003 without entering S01's test surface
  - Add a dedicated test module such as `tests/test_todo_quick_add_priority.py`; cover quick-add success, reload persistence, and blank-title rejection there rather than in the file chosen for S01's due-date regression coverage
  - **Verify**: `uv run pytest tests/test_todo_quick_add_priority.py` passes and all BUG-003 assertions live in that dedicated file instead of S01's due-date regression file

### Testing Strategy

### Validation

### Execution Contract

## Final Validation Checklist

## Implementation Observations
#### NOTICED BUT NOT TOUCHING
- `tests/test_todos.py::TestTodos::test_update_todo` currently fails because `/api/todos/{todo_id}` parses `due_date` with `"%Y-%m-%dT%H:%M"` while the test posts `"2025-12-31"`, which is pre-existing and unrelated to S02 default-priority scope.
