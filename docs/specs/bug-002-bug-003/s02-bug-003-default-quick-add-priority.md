# Feature Implementation Specification: Apply default Priority on quick-add

**Plan**: [`plan.md`](./plan.md)
**Story-ID**: S02

## Feature Overview and Goal
Restore the documented default Priority for quick-add so title-only Todo creation produces a complete, editable Todo state. The fix must preserve the minimal-entry HTMX quick-add flow while ensuring reopened edit dialogs show `Low` selected.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `prd.md` – "FR2: Apply Default Priority on Quick Add"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr2-apply-default-priority-on-quick-add -->
<!-- extracted: 621e664cd1c04fe8cc22d3d2ed8dd2e9bbed9673 -->
> The quick-add workflow must create todos with the documented default priority so that all todos created through the main entry path start in a valid, editable state.
>
> When a user creates a todo through quick-add without explicitly setting priority, the new todo is stored with priority `low`.
>
> When the user opens the edit dialog for that todo, the priority selector shows `Low` selected.
>
> The fix does not require any additional input from the user during quick-add.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 621e664cd1c04fe8cc22d3d2ed8dd2e9bbed9673 -->
> BUG-003: Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default.

### From `README.md` – "Features"
<!-- source: README.md#features -->
<!-- extracted: 621e664cd1c04fe8cc22d3d2ed8dd2e9bbed9673 -->
> Todo items with title, notes, due dates, and priority levels


## Deeper Context

- `docs/specs/bug-002-bug-003/plan.md#s02-apply-default-priority-on-quick-add` – story-level scope and acceptance criteria.
- `docs/specs/bug-002-bug-003/prd.md#edge-cases` – quick-add edge cases and minimal-entry constraints.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – canonical `Todo` and `Priority` terminology.


## Success Criteria (Must Be TRUE)
- [x] Quick-add creation persists new Todos with `priority="low"` when only `list_id` and `title` are submitted.
- [x] The Todo partial rendered immediately after quick-add is consistent with `priority="low"`, including the server-rendered priority badge and dialog data attribute.
- [x] Reopening the edit dialog for a quick-added Todo shows `Low` selected without requiring any new user input during creation.
- [x] Existing Todo edit/update behavior for valid `low`, `medium`, and `high` priorities remains unchanged.

### Health Metrics (Must NOT Regress)
- [ ] Existing quick-add validation for blank or oversized titles continues to behave the same.
- [ ] Quick-add still returns the current Todo partial plus OOB count update behavior.
- [ ] The route-level Todo test suite continues to pass outside the new default-priority assertions.


## Scenarios

### Quick-add stores the default Priority
- **Given** an authenticated user is viewing a `TodoList`
- **When** the user quick-adds a Todo with only a title
- **Then** the stored `Todo.priority` is `low`

### Edit dialog reopens with Low selected
- **Given** a Todo was created through quick-add
- **When** the user opens the existing edit dialog for that Todo
- **Then** the Priority control shows `Low` selected from the stored value

### Quick-add stays minimal
- **Given** the quick-add form currently requires only `title` and `list_id`
- **When** the default-priority fix ships
- **Then** no new required field or user action is introduced in that flow

### Invalid quick-add title still fails normally
- **Given** an authenticated user submits a blank quick-add title
- **When** the request reaches `create_todo()`
- **Then** the app returns the existing HTML error partial and does not create a Todo record


## Scope & Boundaries

### In Scope
- Set the quick-add route's default stored Priority explicitly to `low`.
- Preserve rendered Todo partial behavior so the new Todo immediately reflects the stored Priority.
- Add or strengthen route-level regression coverage for quick-add persisted state and edit-dialog prepopulation signals.

### What We're NOT Doing
- Adding a Priority control to quick-add – the PRD explicitly keeps quick-add title-only.
- Changing valid Priority values or their UI labels – existing `low`/`medium`/`high` semantics stay intact.
- Refactoring the broader Todo creation architecture – this is a surgical defect fix.
- Bundling unrelated OOB-swap or Due Date fixes into this story – those belong to other backlog items or stories.


## Architecture Decision

**We will**: assign `priority="low"` inside the quick-add creation path and rely on the existing partial/template wiring to surface that stored value – this fixes the root cause at persistence time rather than masking it in the dialog UI.


## Technical Overview

### UI/UX Design
The user experience does not change visually or procedurally during quick-add. The visible improvement is that the created Todo consistently renders with the expected low-priority state and the edit dialog opens with `Low` selected.

### Data Models
`Todo.priority` remains the existing string field backed by supported literals `low`, `medium`, and `high`. This story ensures quick-add always persists one valid literal instead of leaving the field unset.

### Integration Points
The fix must stay compatible with `todo_item_with_oob.html`, `todo_item.html`, and `openEditTodoDialog()` so the stored priority flows through immediate render and later edit-dialog hydration without extra client logic.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:65-116         | Quick-add creation handler and OOB response path
file   | src/app/database.py:62-77              | `Todo` model field definitions, including missing priority default
file   | src/app/templates/partials/todo_item.html:1-33 | Priority badge and dialog data attribute are rendered from stored priority
file   | src/app/static/js/app.js:111-120       | Edit dialog hydration uses the stored priority value directly
file   | tests/test_todos.py:12-33              | Existing quick-add regression test already asserts `priority == "low"`
```


## Constraints & Gotchas
- **Constraint**: Quick-add must remain a title-only HTMX form – Workaround: set the default on the server in `create_todo()` instead of adding UI inputs.
- **Avoid**: Depending on dialog defaults to hide a missing stored value – Instead: persist `low` at creation so every later render is consistent.
- **Critical**: This story shares `src/app/routes/todos.py` and `tests/test_todos.py` with S01 – Must handle by executing in W2 after S01 and keeping edits confined to the quick-add path plus its tests.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick-add persists new Todos with explicit Priority `low`
  - Update `create_todo()` in `src/app/routes/todos.py:89-102`; keep the current title validation, ordering logic, and OOB response contract unchanged.
  - **Verify**: `Test: POST /api/todos with list_id and title only creates a Todo whose stored priority is exactly 'low'`

- [x] **TI02** The immediate Todo partial and reopened edit dialog both surface the stored low-priority value
  - Reuse the existing render/hydration path in `src/app/templates/partials/todo_item.html:1-33` and `src/app/static/js/app.js:111-120`; this task depends on TI01 storing the correct value.
  - **Verify**: `Test: the quick-add response and reopened dialog path expose priority 'low' so the edit select shows Low selected`

- [x] **TI03** Quick-add keeps its current minimal-entry and validation behavior
  - Preserve the current validation branches in `src/app/routes/todos.py:79-95`; do not add new required form inputs or alternate error contracts.
  - **Verify**: `Test: blank-title quick-add still returns the existing HTML error partial and creates no Todo record`

### Testing Strategy
- [TI01] Scenario: Quick-add stores the default Priority → keep or strengthen the existing create-route database assertion.
- [TI02] Scenario: Edit dialog reopens with Low selected → add response-content or rendered-attribute assertions proving the stored priority surfaces through the partial.
- [TI03] Scenario: Quick-add stays minimal → assert the route still accepts title-only form submission and uses the default server-side.
- [TI03] Scenario: Invalid quick-add title still fails normally → preserve the negative-path quick-add test.

### Validation
- Manual UI check after implementation: quick-add a Todo while logged in, then open the edit dialog and confirm `Low` is selected with no extra creation inputs.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.


## Final Validation Checklist

- [x] **All success criteria** met
- [x] **All tasks** fully completed, verified, and checkboxes checked
- [x] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements (if applicable)


## Implementation Observations

_No observations recorded yet._
