# Quick-add default priority

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Ensure todos created from the quick-add form receive the documented default priority so newly added items display and reopen consistently without expanding the quick-add UI.

**Expected Outcomes**:

- [OC01] Creating a todo from the title-only quick-add form persists priority `low` when no explicit priority is supplied.
- [OC02] A newly created quick-add todo renders and reopens with `low` as its priority state.
- [OC03] The fix lives on the create/default path and does not consume S01's edit-path ownership.


## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: de827ca -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: de827ca -->
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |

### From `docs/UBIQUITOUS_LANGUAGE.md` – "Todo Domain"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#todo-domain -->
<!-- extracted: de827ca -->
> Priority | Importance level of a todo: `low` \| `medium` \| `high` | severity, urgency | Todo |


## Deeper Context

- `src/app/templates/partials/todo_list_content.html` – Quick-add form shape; it currently submits only `list_id` and `title`.
- `CLAUDE.md#the-stack--and-why-it-matters-for-edits` – Reminder that create routes return HTML fragments and rely on server-rendered state rather than client-side JSON patching.
- `docs/STACK.md#frameworks-libraries` – SQLAlchemy model-default and FastAPI route context for the create path.


## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01] Quick-add creates a low-priority todo when no priority is supplied**
  - **Given** a user submits the quick-add form with only `list_id` and `title`
  - **When** `POST /api/todos` creates the new todo
  - **Then** the persisted todo has priority `low`

- [ ] **S02 [OC02] [TI01,TI02] Newly created quick-add todos render and reopen as low priority**
  - **Given** a todo was just created from the quick-add form
  - **When** the server returns the todo row and the user opens the edit dialog
  - **Then** the row uses the low-priority state and the dialog shows `Low` selected

- [ ] **S03 [OC03] [TI01,TI03] Defaulting stays on the create/default boundary**
  - **Given** the quick-add form remains title-only and other todo flows may still submit explicit priorities
  - **When** the BUG-003 fix lands
  - **Then** omitted create-path priorities receive `low` while explicit priority values in other flows remain untouched

- [ ] **S04 [OC02,OC03] [TI02] Quick-add UI does not grow a priority control**
  - **Given** the quick-add form is meant to stay a thin title-only entry point
  - **When** a user adds a todo and immediately edits it
  - **Then** the default priority comes from server-side create/default behavior rather than a new quick-add field


## Structural Criteria

- [ ] `Todo.priority` stays within the canonical `low | medium | high` vocabulary after defaulting is introduced.
- [ ] The quick-add response continues to support the existing row-render + OOB count behavior while exposing `data-todo-priority="low"` for dialog reopen state.
- [ ] BUG-003 regression coverage lives in a story-owned test surface so S02 can land without editing S01's due-date tests.


## Scope & Boundaries

### Work Areas
- Create/default priority behavior for new todos in `src/app/database.py`
- Quick-add response surface in `src/app/templates/partials/todo_item.html` and `src/app/templates/partials/todo_item_with_oob.html`
- Story-owned BUG-003 regression coverage under `tests/`

### What We're NOT Doing
- Edit-dialog due-date persistence or malformed date handling -- reserved for BUG-002 / S01.
- Adding a priority selector to the quick-add form -- the PRD calls for a default, not a wider entry UI.
- Reworking priority styling rules or other visual hierarchy beyond honoring the existing low-priority state.
- Changing documented priority vocabulary -- `low`, `medium`, and `high` remain the only valid values.


## Architecture Decision

**Approach**: Put the `low` default on the create/default boundary so every quick-add todo receives a canonical priority without widening the title-only quick-add form.
**Why this over alternatives**: It satisfies the documented default and keeps ownership off S01's edit-path surfaces instead of duplicating fallback logic across UI and route layers.


## Technical Overview

The quick-add form does not send a priority value today, but the rendered row and edit dialog already assume one exists. The fix should therefore establish the default before the row partial is rendered so the existing template and dialog data attributes become correct without adding a new control.


## Code Patterns & External References

```text
# type | path#anchor or url | why needed (intent)
file | src/app/database.py#Todo | Model-level priority shape and safest shared default boundary
file | src/app/routes/todos.py#create_todo | Current quick-add create flow and OOB count update path
file | src/app/templates/partials/todo_item.html:1-40 | Proof surface for rendered priority styling and dialog reopen data attributes
file | src/app/static/js/app.js#openEditTodoDialog | Existing edit-dialog consumer of row-level priority data attributes
```


## Constraints & Gotchas

- **Constraint**: The quick-add form posts only `list_id` and `title` -- Workaround: establish the default before the response row is rendered instead of adding form inputs.
- **Avoid**: Fixing BUG-003 by piggybacking on edit-dialog code or widening the quick-add UI -- Instead: keep the default at the create/default boundary.
- **Critical**: The create response already updates the sidebar count via OOB swap -- Must handle by: preserving the current `todo_item_with_oob.html` response shape.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** New quick-add todos persist with canonical low priority
  - Establish the default at `src/app/database.py#Todo` so title-only POSTs through `src/app/routes/todos.py#create_todo` inherit it without consuming the shared todo route file as story ownership.
  - **Verify**: `uv run pytest tests/test_bug_003_quick_add_priority.py -k "persist or default"` proves a title-only quick-add POST stores priority "low".

- [ ] **TI02** Quick-add rows and reopen state expose the low-priority default
  - Reuse the existing row partial and `openEditTodoDialog` consumer path so the returned HTML advertises `priority-low` styling and `data-todo-priority="low"` immediately after create.
  - **Verify**: `uv run pytest tests/test_bug_003_quick_add_priority.py -k "render or dialog"` asserts the returned HTML exposes the low-priority state and dialog value without extra user input.

- [ ] **TI03** Explicit priority handling in other flows remains unchanged
  - Protect update-path and explicit-priority behavior so the new default only fills omitted create-path values and does not reinterpret existing `medium` or `high` priorities.
  - **Verify**: `uv run pytest tests/test_todos.py::TestTodos::test_update_todo tests/test_bug_003_quick_add_priority.py` keeps explicit update behavior green alongside the BUG-003 regression checks.

### Testing Strategy

- [TI01,TI02,TI03] Add BUG-003 regression coverage in a dedicated test file so this story stays merge-safe with S01 and does not rely on shared due-date test edits.

### Validation

- Create a todo from the quick-add field in the browser, inspect the rendered badge/state, and reopen the edit dialog to confirm `Low` is selected without any extra quick-add control.

### Execution Contract

- Keep production ownership on create/default priority surfaces. Prefer the model/default boundary; if the fix starts requiring edit-path due-date handling or shared route-file ownership, stop and re-scope with S01 instead of widening this story.


## Final Validation Checklist

- [ ] Quick-add remains title-only while newly created todos render and reopen with `low` priority and no S01 surface ownership is consumed.


## Implementation Observations

_No observations recorded yet._
