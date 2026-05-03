# Feature Implementation Specification: Apply Quick-Add Default Priority

**Plan**: `docs/specs/bug-002-bug-003/plan.md`
**Story-ID**: `S02`

## Feature Overview and Goal
Ensure todos created through quick-add start in the same valid priority state the product already documents in the edit dialog. The created row, reopened dialog, and later explicit edits should all agree on the stored canonical default.

> **Technical Research**: [`.technical-research.md`](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_


## Required Context

### From `docs/specs/bug-002-bug-003/prd.md` - "FR2: Apply Quick-Add Default Priority"
<!-- source: docs/specs/bug-002-bug-003/prd.md#fr2-apply-quick-add-default-priority -->
<!-- extracted: a7fb3dcc22a983e20856b0d7f4e829b8845ca96a -->
> - [ ] When a user creates a todo through quick-add with title only, the created todo is stored with the default priority.
> - [ ] Opening that todo in the existing edit dialog shows `Low` selected immediately after creation.
> - [ ] The rendered todo row displays the default priority consistently with other todos using the same priority value.
> - [ ] Users can still change the priority later through the existing edit dialog.

### From `docs/specs/bug-002-bug-003/prd.md` - "Assumptions"
<!-- source: docs/specs/bug-002-bug-003/prd.md#constraints-assumptions -->
<!-- extracted: a7fb3dcc22a983e20856b0d7f4e829b8845ca96a -->
> - `Low` is the canonical default priority for new todos created without explicit priority input.

### From `AGENTS.md` - "Project-Specific Guidelines"
<!-- source: AGENTS.md#project-specific-guidelines -->
<!-- extracted: a7fb3dcc22a983e20856b0d7f4e829b8845ca96a -->
> - **HTMX-first.** Every route that renders should return an HTML partial.
> - **Pydantic models in `src/app/models/` are _not_ wired into routes.** Validation is ad-hoc in the handlers - do not assume models run.


## Deeper Context

- `docs/PRODUCT-BACKLOG.md#known-defects` - original `BUG-003` wording and severity.
- `AGENTS.md#architecture` - todo model and route layout for current creation and edit flows.
- `AGENTS.md#tests` - test harness patterns for authenticated route assertions.


## Success Criteria (Must Be TRUE)
- [ ] Quick-add creates new todos with the canonical stored priority value `low` before the response fragment is rendered.
- [ ] The returned row and reopened edit dialog both reflect that stored default immediately through `data-todo-priority="low"`, a visible low-priority badge, and `Low` selected in the dialog.
- [ ] Users can still update the todo to another valid priority later through the existing edit flow without regressing the quick-add default behavior.

### Health Metrics (Must NOT Regress)
- [ ] Existing quick-add validation for empty or oversized titles remains unchanged.
- [ ] Existing update behavior for explicit priority changes remains green.
- [ ] Route responses stay server-rendered HTML partials with no new JSON-only path.


## Scenarios

### Quick-add creates a low-priority todo
- **Given** an authenticated user is viewing a todo list
- **When** the user submits quick-add with only a non-empty title
- **Then** the created `Todo` stores `priority="low"` and the returned row renders the same low-priority badge state as other low-priority todos

### Reopen the new todo immediately after quick-add
- **Given** a todo was just created through quick-add
- **When** the user opens that todo in the existing edit dialog
- **Then** the dialog receives `data-todo-priority="low"` from the row and shows `Low` selected without any extra user action

### Later explicit priority changes still win
- **Given** a quick-add todo currently carries the default low priority
- **When** the user later updates the todo to `high` through the existing edit dialog
- **Then** the stored priority changes to `high` and the returned row and future reopen state both reflect the explicit user choice

### Existing quick-add validation remains unchanged
- **Given** an authenticated user submits quick-add with an empty or oversized title
- **When** the create route rejects the request
- **Then** the response still uses the existing HTML error partial behavior and no todo is created


## Scope & Boundaries

### In Scope
- Initialize quick-add todos with the canonical default priority value at creation time.
- Preserve row rendering and dialog reopen behavior so they both reflect the stored default immediately after creation.
- Add regression coverage for create, reopen, and later explicit priority override flows.

### What We're NOT Doing
- Adding new priority values or changing the existing `low` / `medium` / `high` domain - the PRD keeps the current set.
- Redesigning the quick-add UI or edit dialog selector - this fix is behavioral, not UX expansion.
- Refactoring unrelated todo creation concerns such as positioning, list lookup, or OOB count updates - those flows are already working and out of scope.
- Changing auth, ownership, or session behavior - this defect is limited to todo metadata initialization.


## Architecture Decision

**We will**: establish the canonical `low` priority during quick-add creation so stored state, rendered row state, and dialog reopen state all derive from the same persisted value.
**Rationale**: the current product already documents `Low` as the default selection, and storing the value at creation time is the narrowest way to make UI and persistence agree.
**Alternatives considered**:
1. **Rely only on the dialog's UI default** - rejected: it keeps newly created rows and reopened dialogs out of sync with stored state.
2. **Broaden the fix into a priority-domain refactor** - rejected: unnecessary scope expansion for a localized backlog defect.


## Technical Overview

### UI/UX Design
The quick-add form stays title-only. The user-visible change is that the resulting row and first reopen already behave as though the default `Low` selection had been applied.

### Data Models
`Todo.priority` remains the existing `low` / `medium` / `high` string field. This story only guarantees a canonical initialization value when the quick-add route creates a new todo without explicit priority input.

### Integration Points
The fix centers on the quick-add route, then flows through the row partial and edit-dialog hydration path that already read `todo.priority`.


## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:73-132          | Current quick-add creation path and validation/OOB response pattern
file   | src/app/database.py:65-84               | Todo model shape and absence of a database-level priority default
file   | src/app/templates/partials/todo_item.html:1-32 | Row badge and dataset contract that must reflect stored priority
file   | src/app/static/js/app.js:111-124        | Dialog hydration path that reads `data-todo-priority`
file   | tests/test_todos.py:13-30,44-62         | Existing create and update test patterns to extend
```


## Constraints & Gotchas
- **Constraint**: Quick-add must stay title-only - Workaround: assign the default server-side rather than adding new form fields.
- **Avoid**: Treating the UI select default as sufficient without persisted state - Instead: make the created `Todo` carry `priority="low"` before rendering.
- **Critical**: Validation remains ad hoc in route handlers - Must handle by: preserving the existing title-validation branches and HTML error partial behavior.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Quick-add creation stores the canonical default priority for new todos
  - Follow the existing create flow in `src/app/routes/todos.py:73-132`; keep validation, position assignment, and OOB response behavior unchanged while ensuring created rows already have `priority="low"`.
  - **Verify**: `uv run pytest tests/test_todos.py -k "create_todo"` proves the created database row stores `priority == "low"` immediately after POST

- [ ] **TI02** Rendered rows and reopened dialogs reflect the stored default priority immediately
  - Follow the row dataset and dialog hydration contract in `src/app/templates/partials/todo_item.html:1-32` and `src/app/static/js/app.js:111-124`; this task depends on TI01's persisted default.
  - **Verify**: `uv run pytest tests/test_todos.py -k "quick_add_default_priority or create_todo"` proves the response HTML contains `data-todo-priority="low"` and the low-priority badge state for a quick-add todo

- [ ] **TI03** Later explicit priority changes still override the create-time default
  - Extend the existing update test pattern in `tests/test_todos.py:44-62`; this task depends on TI01 and should prove the default initialization does not interfere with later user-selected priorities.
  - **Verify**: `uv run pytest tests/test_todos.py -k "priority and update_todo"` proves a quick-add todo can later persist `priority="high"` through the existing update route

### Testing Strategy
- [TI01] Scenario: quick-add creates a low-priority todo -> extend the create-route test to assert stored `priority == "low"`
- [TI02] Scenario: reopen the new todo immediately after quick-add -> add a response-content assertion that the row carries `data-todo-priority="low"` and low-priority badge output
- [TI03] Scenario: later explicit priority changes still win -> add a create-then-update regression test that moves the same todo from low to high
- [TI01] Scenario: existing quick-add validation remains unchanged -> keep empty-title and oversized-title failure coverage green while confirming no todo is created

### Validation
- Run `uv run pytest tests/test_todos.py -k "create_todo or priority"` after implementation.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact - implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research - spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature - build/tests/lint-analysis where those checks exist and are relevant - and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion - do not batch.


## Final Validation Checklist

- [ ] **All success criteria** met
- [ ] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements


## Implementation Observations

_No observations recorded yet._
