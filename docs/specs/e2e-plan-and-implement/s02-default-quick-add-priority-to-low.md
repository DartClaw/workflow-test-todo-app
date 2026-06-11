# Default quick-add priority to low

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Ensure title-only quick-add todos are born with the documented low priority so persisted state, rendered UI, and the edit dialog all agree from the first save.

**Expected Outcomes**:

- [OC01] A todo created through the quick-add form persists `priority == "low"` without requiring any follow-up edit.
- [OC02] The quick-add response row and later re-renders both expose the low priority through the existing badge, CSS class, and edit-dialog seed data.
- [OC03] Regression coverage proves the fix without widening into S01’s due-date persistence bug or changing existing quick-add validation behavior.

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
> | BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S02 scope and shared decision"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 83a3c8554e943222396cb245036c9d158acbab53 -->
> Todos created from the quick-add form start with the documented low priority so the created record and rendered todo row both show a valid priority immediately. This story includes defaulting creation-time state for quick-add flows and proving the visible result through regression coverage. It excludes edit-dialog due-date persistence, priority redesign, and changes to other todo creation flows beyond what is required to make quick-add correct.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S02 isolation and creation-time defaulting"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: 83a3c8554e943222396cb245036c9d158acbab53 -->
> Keep each story isolated to its own files; they must merge without conflict.
>
> S02 must ensure quick-add todos are stored and rendered with low priority from the moment they are created, avoiding UI-only fixes that leave persisted state inconsistent.

## Deeper Context

- `docs/STACK.md#frameworks-libraries` – confirms the FastAPI + Jinja2 + HTMX fragment pattern and pytest/httpx test baseline this story must follow.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical `Todo`, `TodoList`, and `Priority` terminology for the spec and tests.
- `src/app/database.py#Todo` – model definition where a creation-time default can be set without colliding with S01’s route work.
- `src/app/routes/todos.py#create_todo` – the current app’s only user-facing Todo creation seam; S02 must stay behaviorally limited to this quick-add flow even if the default is set one layer lower for isolation.
- `src/app/templates/partials/todo_item.html` – row contract for CSS class, badge text, and `data-todo-priority`.
- `src/app/static/js/app.js#openEditTodoDialog` – existing edit-dialog seed path that consumes row priority with no fallback.
- `src/app/models/todo.py#TodoCreate` – existing application-level precedent that the documented default priority is `low`.

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Title-only quick-add creates a low-priority todo immediately**
  - **Given** an authenticated user has a `TodoList` selected and uses the existing quick-add form, which submits only `list_id` and `title`
  - **When** the user posts a new todo title to `POST /api/todos`
  - **Then** the created `Todo` is persisted with `priority == "low"` and the returned HTML row shows the low-priority presentation expected by the current UI contract

- [x] **S02 [OC02] [TI02] Edit dialog opens with low selected for a quick-added todo**
  - **Given** a todo was created through the quick-add path without any explicit priority input
  - **When** the user activates that row’s edit action
  - **Then** the row’s existing dialog seed data provides `low` to the edit dialog and the priority selector is not blank

- [x] **S03 [OC01,OC02,OC03] [TI01,TI03] Reloading the list preserves the low-priority rendering**
  - **Given** a quick-added todo has already been committed to the database
  - **When** the user revisits the list or reloads the page and the todo is rendered again from persisted state
  - **Then** the todo row still renders with the low-priority badge and low-priority dialog seed data, proving the fix is stored state rather than a transient UI fallback

- [x] **S04 [OC03] [TI03] Blank-title quick-add still fails without creating a todo**
  - **Given** the quick-add form submits a blank or whitespace-only title
  - **When** `POST /api/todos` rejects the request
  - **Then** the route still returns the error partial and no new `Todo` is created with an inferred priority

## Structural Criteria

- [x] Quick-add keeps its existing ownership check, title validation, position calculation, and `partials/todo_item_with_oob.html` response contract while gaining a creation-time default priority.
- [x] The fix makes low priority true in persisted quick-add records; the template and dialog continue consuming stored `todo.priority` instead of introducing UI-only fallback logic.
- [x] S02 stays isolated from S01’s due-date persistence surface by owning the model-backed default and its dedicated regression coverage instead of editing S01-owned route logic.

## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo`
- Quick-add persisted-priority contract as consumed by the existing row and reopen flow
- `tests/test_todo_quick_add_priority.py`

### What We're NOT Doing
- Edit-dialog due-date parsing or save behavior – owned by S01 / BUG-002.
- Priority UX redesign or new priority options – BUG-003 only asks for the documented default to work.
- Backfilling already-persisted todos with `NULL` priority – this story is scoped to quick-add creation-time correctness.
- Broad changes to other todo creation/edit flows – excluded unless strictly required to make the quick-add path correct and merge-safe.
- UI-only fallback that masks missing stored priority – rejected because the plan requires the default to be true at creation time.

## Architecture Decision

**Approach**: Set the default on `src/app/database.py#Todo` so the current quick-add flow persists `low` priority before render, while keeping the existing row template and dialog seed path reading that stored value.
**Why this over alternatives**: In the current app the quick-add route is the only user-facing Todo creation flow, so a model-backed default stays behaviorally aligned with the PRD while keeping S02 out of `src/app/routes/todos.py` and preserving merge-safe isolation from S01.

## Technical Overview

The quick-add form posts only `list_id` and `title` into `create_todo`, and the current app exposes no other user-facing Todo creation path. The route then returns `partials/todo_item_with_oob.html`, which includes `todo_item.html`. That row serializes `todo.priority` into a CSS class, badge text, and `data-todo-priority`, and `openEditTodoDialog()` uses that value directly to seed the edit dialog. Because the quick-add path refreshes the created model before rendering, a model-level default is enough to make the stored state and all current UI consumers agree without widening the behavior beyond the app’s present quick-add surface.

## Code Patterns & External References

```text
# type | path#anchor                                 | why needed (intent)
file   | src/app/database.py#Todo                    | Creation-time default seam that avoids S01’s route file
file   | src/app/routes/todos.py#create_todo         | Quick-add integration seam; preserve access checks, validation, ordering, and fragment response
file   | src/app/templates/partials/todo_item.html   | Row contract for CSS class, badge text, and `data-todo-priority`
file   | src/app/static/js/app.js#openEditTodoDialog | Existing edit-dialog seed path that consumes row priority with no fallback
file   | src/app/models/todo.py#TodoCreate           | Existing in-repo precedent that low is the documented default priority
file   | tests/test_todo_quick_add_priority.py       | S02-owned regression surface for persisted default-priority behavior
```

## Constraints & Gotchas

- **Constraint**: Quick-add is an HTMX HTML-fragment route – preserve `partials/error.html` on validation failure and `partials/todo_item_with_oob.html` on success.
- **Avoid**: Solving BUG-003 only in the template or dialog – Instead: make `Todo.priority` correct when the record is created.
- **Critical**: Story isolation is load-bearing – Must handle by keeping S02 on the model-backed default and dedicated regression-proof surfaces, not S01’s due-date edit path or route logic.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick-add created todos inherit low priority from the persisted model default
  - Follow `src/app/database.py#Todo` and the existing `src/app/models/todo.py#TodoCreate` default semantics so title-only quick-add records are stored with `priority == "low"` before render.
  - **Verify**: `uv run pytest tests/test_todo_quick_add_priority.py -k persisted_default -vv` proves title-only quick-add stores `created.priority == "low"`.

- [x] **TI02** Existing quick-add response and reopen flow expose the stored low priority without UI fallback
  - Keep `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js#openEditTodoDialog` as read-set context only: row class, badge text, and `data-todo-priority` must continue to derive from persisted `todo.priority` without this story taking ownership of those files.
  - **Verify**: focused route coverage proves the success HTML for `POST /api/todos` contains `priority-low`, `data-todo-priority="low"`, and `Low`.

- [x] **TI03** Dedicated regression coverage proves revisit behavior and preserves current quick-add safeguards
  - Keep BUG-003 proof in `tests/test_todo_quick_add_priority.py`, including a follow-up render path and the existing blank-title rejection behavior, so S02 stays merge-safe beside S01.
  - **Verify**: `uv run pytest tests/test_todo_quick_add_priority.py -vv` proves low-priority persistence on revisit and no regression to blank-title rejection.

### Testing Strategy

- Route tests should assert both persisted database state and returned HTML-fragment content because BUG-003 breaks at the boundary between persistence and server-rendered UI.
- Keep the regression proof in an S02-owned test file so the plan’s no-conflict rule remains true during execution.

### Validation

### Execution Contract

- Do not widen the write set into S01-owned due-date persistence or unrelated edit-save behavior. If the smallest apparent fix requires that, stop and re-plan instead of silently broadening S02.

## Final Validation Checklist

- [x] The only behavior change is that quick-add created todos now persist and render with low priority immediately.
- [x] No UI-only fallback was introduced for missing priority values.
- [x] S02 remains merge-safe with S01 by avoiding due-date persistence surfaces.

## Implementation Observations

#### NOTICED BUT NOT TOUCHING
- `tests/test_todos.py::TestTodos::test_update_todo` currently fails in this worktree because `due_date` update parsing stores `None` for date-only input; this failure is unrelated to S02 and remains pre-existing.
