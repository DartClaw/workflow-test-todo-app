**Plan**: `docs/specs/bug-002-bug-003/plan.md`
**Story-ID**: `S02`

## Feature Overview and Goal
Make quick-add Todo creation assign the documented default Priority of `low` at create time so newly created rows and later edit-dialog opens always start from a valid state. The fix must preserve the existing title-only quick-add contract and its HTMX partial response.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` – "FR2: Apply Default Priority on Quick Add"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr2-apply-default-priority-on-quick-add -->
<!-- extracted: 2026-05-04 -->
> When a user creates a todo through quick add with only a title, the todo is stored with priority `low`.
>
> The newly rendered todo row shows the default priority state immediately after creation.
>
> When the same quick-added todo is opened in the edit dialog, the priority selector is prefilled with `low`.
>
> Existing non-quick-add update behavior continues to allow the user to change the priority later.

### From `docs/specs/bug-002-bug-003/prd.md` – "Key Constraints, Assumptions & Dependencies"
<!-- source: docs/specs/bug-002-bug-003/prd.md#key-constraints-assumptions--dependencies -->
<!-- extracted: 2026-05-04 -->
> The app remains HTMX-first and must preserve existing HTML-fragment response behavior for create and update flows.
>
> The documented default priority remains `low`, matching current product copy and existing test expectations.
>
> Final acceptance depends on automated tests covering both flows and confirming no regression in existing todo create/update behavior.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "Todo Domain"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#todo-domain -->
<!-- extracted: 2026-05-04 -->
> Priority | Importance level of a todo: `low` | `medium` | `high`


## Deeper Context

- `docs/specs/bug-002-bug-003/plan.md#phase-breakdown` – story-level scope, acceptance criteria, and constraints for S02.
- `docs/specs/bug-002-bug-003/prd.md#user-flows` – create, row-render, and edit-reopen behavior that this story must preserve.


## Success Criteria (Must Be TRUE)
- [x] Quick add with only `list_id` and `title` stores the new Todo with Priority `low`.
- [x] The `POST /api/todos` response still returns the existing todo-row-plus-OOB partial and the rendered row visibly reflects Priority `low`.
- [x] Opening that quick-added Todo in the existing edit dialog shows `low` in the Priority selector without relying on a client-side fallback.
- [x] Later todo updates can still change Priority away from `low` through the existing update flow.
- [x] Quick add does not silently create a Todo with missing or invalid Priority state.

### Health Metrics (Must NOT Regress)
- [x] Existing todo create tests continue to pass.
- [x] The quick-add path still requires the existing title validation and next-position behavior.
- [x] The incomplete-count OOB update remains present in the quick-add response.


## Scenarios

### Quick add stores the default Priority
- **Given** an authenticated User viewing a TodoList
- **When** the User quick-adds a Todo with only a title
- **Then** the new Todo is stored with Priority `low` and the returned row shows that Priority immediately

### Edit dialog reopens with the stored default Priority
- **Given** a Todo created through quick add
- **When** the User opens that Todo in the edit dialog
- **Then** the dialog's Priority selector is prefilled with `low` from the row dataset

### Later edits can override the default Priority
- **Given** a Todo that was created through quick add with Priority `low`
- **When** the User updates that Todo and selects `high`
- **Then** the update succeeds and later reopen-state reflects the user-selected Priority instead of forcing `low`

### Title validation still blocks invalid quick adds
- **Given** an authenticated User submits quick add with an empty title
- **When** the request is processed
- **Then** the existing visible error partial is returned and no Todo is created


## Scope & Boundaries

### In Scope
- Make create-time Priority assignment authoritative for title-only quick adds.
- Preserve row-render and edit-dialog reopen consistency for newly created Todos.
- Keep the existing quick-add OOB count update and validation behavior intact.
- Add regression coverage that proves rendered state stays aligned with DB state, building on the existing create test that already checks `priority == "low"`.

### What We're NOT Doing
- Make the default Priority configurable – the PRD fixes it at `low`.
- Expand quick add to accept Priority or other extra fields – the form remains title-only.
- Change the update flow's Priority editing semantics beyond proving later edits still work.
- Add database migrations or broader schema refactors – the fix stays within the current educational app model.


## Architecture Decision

**We will**: assign the default Priority explicitly in `create_todo()` and verify the existing row/dialog contract reflects that stored value – this is the smallest authoritative fix and is preferable to relying on ORM defaults or client-side UI defaults alone.


## Technical Overview

### UI/UX Design
No UI redesign is needed. The created row and the existing edit dialog must simply reflect the authoritative stored Priority state immediately after quick add.

### Data Models
`Todo.priority` remains the existing string field constrained by the app's `low | medium | high` domain. This story only ensures title-only creation initializes it to `low`.

### Integration Points
The create handler must stay aligned with `partials/todo_item_with_oob.html`, `partials/todo_item.html`, and `openEditTodoDialog()` so both immediate row rendering and later reopen-state remain consistent.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:73-122            | Existing quick-add flow, title validation, next-position logic, and OOB response pattern
file   | src/app/database.py:73-84                 | Current Todo persistence model showing no `priority` default
file   | src/app/templates/partials/todo_list_content.html:47-56 | Quick-add form contract proving only `list_id` and `title` are submitted
file   | src/app/templates/partials/todo_item.html:1-40 | Visible Priority badge and edit-dialog dataset attributes
file   | src/app/static/js/app.js:111-121          | Edit dialog hydration from row data attributes
file   | tests/test_todos.py:13-31                 | Existing create-path regression style and assertions
```


## Constraints & Gotchas
- **Constraint**: Quick add submits only title and list identity – Workaround: the server must assign the default Priority before persisting and rendering the row.
- **Avoid**: Relying on the edit dialog's UI default to mask missing persisted data – Instead: prove the stored Todo and row dataset both carry `low`.
- **Critical**: The create response includes an OOB incomplete-count update – Must handle by preserving `partials/todo_item_with_oob.html` as the success response shape.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick add stores Priority `low` as part of Todo creation
  - Follow the existing create-path pattern at `src/app/routes/todos.py:73-122`; keep title validation, ownership checks, and next-position logic unchanged while making default Priority authoritative.
  - **Verify**: `Test: POST /api/todos with only list_id and title returns 200 and the created Todo in the database has priority == "low"`

- [x] **TI02** The returned quick-add row and later edit-dialog reopen-state both reflect the stored default Priority
  - Reuse the existing row partial and dialog hydration contract at `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js:111-121`; depends on TI01 storing the default value.
  - **Verify**: `Test: quick-add response contains the visible low-priority row state and a reopen-state data attribute that yields low in the edit dialog`

- [x] **TI03** Regression coverage proves quick-add defaulting without breaking create or later update behavior
  - Extend `tests/test_todos.py`; assert DB state, returned HTML, and a follow-up update path that changes Priority away from `low`.
  - **Verify**: `Test suite covers create-with-default, reopen-state consistency, and later user override while preserving existing quick-add validation and OOB behavior`

### Testing Strategy
- [TI01] Scenario: Quick add stores the default Priority → route test that creates a Todo and proves `priority == "low"` in the DB
- [TI01,TI02] Scenario: Edit dialog reopens with the stored default Priority → route test that inspects the returned row dataset or edit-open contract for `low`
- [TI03] Scenario: Later edits can override the default Priority → create-then-update route test that changes Priority to `high` and proves the later value sticks
- [TI03] Scenario: Title validation still blocks invalid quick adds → preserve or extend existing invalid-title test so the fix does not weaken validation

### Validation
- Confirm the quick-add success response still includes the OOB incomplete-count update along with the todo row.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details explicitly named in this FIS (the default Priority value `low`, response shapes, and referenced file paths) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.


## Final Validation Checklist

- [x] **All success criteria** met
- [x] **All tasks** fully completed, verified, and checkboxes checked
- [x] **No regressions** or breaking changes introduced
- [x] **UI verified** to match requirements (if applicable)


## Implementation Observations

_No observations recorded yet._
