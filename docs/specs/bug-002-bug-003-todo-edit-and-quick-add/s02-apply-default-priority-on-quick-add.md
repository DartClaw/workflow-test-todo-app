**Plan**: `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/plan.md`
**Story-ID**: `S02`

## Feature Overview and Goal
Fix the quick-add flow so title-only todo creation persists the documented default Priority `low` immediately, and every downstream render or reopen path reflects that stored state.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `prd.md` – "FR2: Apply Default Priority on Quick Add"
<!-- source: docs/specs/bug-002-bug-003-todo-edit-and-quick-add/prd.md#fr2-apply-default-priority-on-quick-add -->
<!-- extracted: a84dcbdef89045430448b34c530c667b1d85840a -->
> **Description**: The quick-add todo flow must create todos with the same default priority the product already presents in the full edit experience.
>
> **Acceptance Criteria**:
> - [ ] When a user creates a todo through quick add with only a title, the stored todo priority is `low`.
> - [ ] The newly rendered todo row exposes priority data consistent with a `low` priority todo.
> - [ ] When the user opens the edit dialog for a quick-added todo, the priority selector shows `low` selected.
> - [ ] Existing quick-add behavior for title validation, list ownership, insertion order, and OOB count updates remains unchanged.

### From `plan.md` – "S02: Apply Default Priority on Quick Add"
<!-- source: docs/specs/bug-002-bug-003-todo-edit-and-quick-add/plan.md#story-s02 -->
<!-- extracted: a84dcbdef89045430448b34c530c667b1d85840a -->
> **Scope**: Fix the quick-add todo creation flow so title-only submissions persist `low` as the default Priority immediately and every downstream render path reflects that stored value. Include route-level regression coverage for created records and edit-dialog reopen state. Exclude due-date parsing changes, new quick-add fields, and any change to the priority taxonomy.
>
> **Acceptance Criteria**:
> - [ ] Creating a Todo through quick add with only a title stores Priority `low` on the created record.
> - [ ] The rendered todo row exposes priority data and visual state consistent with a `low` priority Todo immediately after creation.
> - [ ] Reopening a quick-added Todo in the edit dialog shows `low` selected until the user changes it.
> - [ ] Existing quick-add validation, Position ordering, ownership checks, and incomplete-count OOB behavior remain unchanged.
> - [ ] Route-level regression tests prove the default-priority behavior without depending on S01's due-date fix.


## Deeper Context

- `prd.md#user-flows` – quick-add create, row append, and edit-dialog reopen expectations.
- `../../PRODUCT-BACKLOG.md#known-defects` – original BUG-003 wording and severity.
- `../../UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical `Priority` term and allowed values.


## Success Criteria (Must Be TRUE)
- [ ] A `POST /api/todos` quick-add submission with only `list_id` and `title` stores `Todo.priority == "low"` on the new record.
- [ ] The returned quick-add partial immediately renders row state consistent with a low-priority Todo, including row data attributes and badge output used by later interactions.
- [ ] Reopening a quick-added Todo through the existing row-to-dialog preload path shows `low` selected in the edit dialog without any fallback-only browser behavior.
- [ ] Title validation, list ownership checks, append ordering, and OOB incomplete-count updates stay unchanged.

### Health Metrics (Must NOT Regress)
- [ ] Existing create-todo coverage remains green and grows stronger rather than moving to a new API shape.
- [ ] The quick-add route still returns `partials/todo_item_with_oob.html` and preserves the OOB incomplete-count contract.
- [ ] No due-date parsing changes land as part of this story.


## Scenarios

### Quick Add Stores Default Priority
- **Given** an authenticated user is viewing a `TodoList`
- **When** the user submits quick add with only `title=New Todo`
- **Then** the created `Todo` stores `priority="low"` and the returned row partial reflects low-priority state

### Reopen Quick-Added Todo In Edit Dialog
- **Given** a Todo was created through quick add without any explicit priority field
- **When** the user opens the edit dialog from the rendered row
- **Then** the row's preload data drives the dialog to show `low` selected

### Quick Add Validation Still Rejects Empty Titles
- **Given** the user submits quick add with a blank title
- **When** the route validates the request
- **Then** it returns the standard HTML error partial and creates no Todo record


## Scope & Boundaries

### In Scope
- Set the quick-add creation default for `Todo.priority` inside the existing create route.
- Preserve the row partial and dialog preload path so stored `low` state is visible immediately and on reopen.
- Add route-level regression tests for created records, rendered response content, and unchanged validation behavior.

### What We're NOT Doing
- Changing the `low` / `medium` / `high` taxonomy – the PRD treats the default as clarified, not configurable.
- Adding a priority field to the quick-add form – this defect only concerns implicit default assignment.
- Introducing a database schema default or migration – the fix should stay inside the existing educational app's application-layer create flow.
- Changing due-date handling – that belongs to S01.


## Architecture Decision

**We will**: assign the default Priority in `create_todo(...)` where quick-add records are created – this makes the stored state authoritative for row rendering and edit-dialog reopen behavior (over relying on template-only defaults or later edit-time normalization)


## Technical Overview

### UI/UX Design (if applicable)
The quick-add form stays title-only. The visible change is consistency: the created row and reopened dialog both behave as though the default priority had always been present.

### Data Models (if applicable)
`Todo.priority` remains the persisted field and must contain `low`, `medium`, or `high`. This story defines the create-path default when no explicit priority input exists.

### Integration Points (if applicable)
This story joins the quick-add route, the persisted `Todo.priority` field, the row partial's `data-todo-priority` attribute, and the `openEditTodoDialog(...)` preload logic that fills the edit dialog selector.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:73-132          | Quick-add creation flow, validation, ordering, and OOB response pattern
file   | src/app/database.py:73-84               | `Todo.priority` field definition and lack of DB default
file   | src/app/templates/partials/todo_item.html:1-32 | Row class, badge, and `data-todo-priority` render contract
file   | src/app/templates/app.html:142-148      | Edit dialog priority selector default and option values
file   | src/app/static/js/app.js:111-124        | Dialog preload path reading row data into the selector
file   | tests/test_todos.py:13-30               | Existing create-todo regression pattern asserting `low`
```


## Constraints & Gotchas
- **Constraint**: `Todo.priority` has no database default – Workaround: assign `low` explicitly in the quick-add route.
- **Avoid**: Relying on the edit dialog's initial `value="low"` as proof of persisted state – Instead: verify the stored record and row data attribute both carry `low`.
- **Critical**: Quick add returns an OOB response used for both the row append and incomplete-count refresh – Must handle by: preserving `partials/todo_item_with_oob.html` and not widening the route contract.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Title-only quick-add submissions persist `priority="low"` on the new `Todo`
  - Follow the existing create flow at `src/app/routes/todos.py:73-132`; keep access checks, title validation, and position assignment unchanged while setting the create-time priority default
  - **Verify**: `uv run pytest tests/test_todos.py -k "test_create_todo"` passes with assertions that the created Todo stores priority == "low"`

- [ ] **TI02** The returned quick-add row partial exposes low-priority render state immediately after creation
  - Use the row contract at `src/app/templates/partials/todo_item.html:1-32`; this task depends on TI01 producing authoritative stored priority so the badge, CSS class, and `data-todo-priority` all reflect `low`
  - **Verify**: `uv run pytest tests/test_todos.py -k "quick_add_priority_render"` passes with response assertions for `priority-low`, `data-todo-priority="low"`, and visible `Low` badge content`

- [ ] **TI03** Reopening a quick-added Todo shows `low` selected in the edit dialog preload path
  - Reuse the selector contract in `src/app/templates/app.html:142-148` and the JS preload path in `src/app/static/js/app.js:111-118`; no new client-side fallback should be needed once stored state is correct
  - **Verify**: `uv run pytest tests/test_todos.py -k "quick_add_priority_reopen"` passes with response assertions that the created row carries the exact preload data value consumed by the dialog`

- [ ] **TI04** Quick-add validation and OOB behavior remain unchanged while stronger regression coverage lands
  - Keep the empty-title error path and `partials/todo_item_with_oob.html` response shape from `src/app/routes/todos.py:92-132`; this task depends on TI01-TI03 not widening the route contract
  - **Verify**: `uv run pytest tests/test_todos.py -k "create_todo_empty_title or quick_add_oob"` passes with assertions that blank titles still fail and successful quick add still includes the OOB count update markup`

### Testing Strategy
- [TI01] Scenario: Quick Add Stores Default Priority → route test posts title-only quick add and asserts stored priority `low`
- [TI02] Scenario: Quick Add Stores Default Priority → response-content assertions prove the returned row reflects low-priority state immediately
- [TI03] Scenario: Reopen Quick-Added Todo In Edit Dialog → response-content assertions prove the row carries `data-todo-priority="low"` for dialog preload
- [TI04] Scenario: Quick Add Validation Still Rejects Empty Titles → route test confirms error-partial behavior and no created record on blank title

### Validation
- Verify the successful quick-add response still contains the OOB count-update markup in addition to the created row.

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
