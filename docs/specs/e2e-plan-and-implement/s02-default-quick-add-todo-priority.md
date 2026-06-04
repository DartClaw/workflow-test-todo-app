# Default Quick-Add Todo Priority

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Ensure quick-add todos behave like documented low-priority todos from first render onward, including legacy rows that currently surface a blank priority selector in the edit dialog.

**Expected Outcomes**:

- [OC01] Todos created through the existing quick-add form persist with priority `low` even though the client submits only `list_id` and `title`.
- [OC02] Todos whose stored priority is missing expose one normalized Low priority value everywhere the edit flow reads it, instead of exposing an empty selector.
- [OC03] Todos that already have explicit `medium` or `high` priority values continue to round-trip unchanged; the fallback applies only to missing priority data.

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
> | BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | - | Open |

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Story S02"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: 4ff97922533e1c690a677b4b0ffd6209a4670d58 -->
> "name": "Default quick-add todo priority",
> "scope": "Ensure todos created through the quick-add form always carry the documented default priority and that editing a priorityless todo shows Low instead of an empty selector. Include compatibility for existing null-priority rows and the rendered fragment state used by the edit dialog; exclude changes to manual priority editing, due-date handling, or visual priority styling beyond reflecting the normalized value.",
> "notes": "Maintain merge-safe isolation from S01 by solving quick-add defaults outside the due-date update path and moving BUG-003 assertions into `tests/test_bug_003_priority_defaults.py`."

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Shared Decisions"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: 4ff97922533e1c690a677b4b0ffd6209a4670d58 -->
> "title": "Enforce story isolation through file ownership",
> "description": "S01 stays in the due-date update path and owns `tests/test_bug_002_due_dates.py`, while S02 solves priority defaults through model/render behavior and owns `tests/test_bug_003_priority_defaults.py`; each story moves or retires its bug-specific assertions from `tests/test_todos.py` before claiming isolated green validation."

## Deeper Context

- `docs/STACK.md#frameworks--libraries` – FastAPI + Jinja2 + HTMX fragment-returning stack and pytest baseline; keep fragment responses and route tests aligned with that contract.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical `Todo` and `Priority` terminology; use these exact terms in scenarios, tasks, and tests.
- `src/app/templates/partials/todo_item_with_oob.html` – Quick-add response wrapper; preserve its out-of-band incomplete-count update while normalizing the new Todo's priority state.

## Acceptance Scenarios

- [x] **S01 [OC01] [TI01,TI02] Quick-added todo appears as Low immediately after creation**
  - **Given** an authenticated user is viewing a `TodoList` that uses the existing quick-add form
  - **When** the user submits `POST /api/todos` with only `list_id` and `title`
  - **Then** the new `Todo` is stored with priority `low`, the appended fragment renders `priority-low` and a `Low` badge, and reopening Edit Todo shows Low preselected

- [x] **S02 [OC02] [TI02] Legacy missing-priority todo no longer opens with a blank selector**
  - **Given** an existing `Todo` row has no stored priority
  - **When** its `todo_item` fragment is rendered and the user opens Edit Todo from that row
  - **Then** the rendered fragment exposes the same normalized Low value in its CSS class, badge text, `data-todo-priority`, and inline `openEditTodoDialog(..., priority)` argument, and the dialog shows Low instead of an empty selection

- [x] **S03 [OC03] [TI02] Explicit priorities survive the fallback path unchanged**
  - **Given** an existing `Todo` already has priority `medium` or `high`
  - **When** its row is rendered and reopened in the edit dialog
  - **Then** the existing priority remains unchanged in the badge text, CSS class, metadata, and selected option rather than being coerced to Low

- [x] **S04 [OC01] [TI01] Missing quick-add priority input is accepted without a client contract change**
  - **Given** the quick-add form continues to submit only `list_id` and `title`
  - **When** the create flow builds and saves the new `Todo` without a submitted `priority` field
  - **Then** the request succeeds without a validation error and the returned HTMX fragment still includes the existing out-of-band incomplete-count update

## Structural Criteria

- [x] Quick-add defaulting is enforced without changing the client-side quick-add contract, and the `todo_item_with_oob` response shape remains intact.
- [x] The rendered todo-item priority contract is total: CSS class token, badge text, `data-todo-priority`, the inline `openEditTodoDialog(..., priority)` argument, and the edit-dialog priority input never surface a blank value for a missing stored priority.
- [x] Focused regression coverage exists in an S02-owned test file for quick-add default persistence, legacy null-priority fallback behavior, and preservation of explicit non-low priorities.

## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo` – persisted Priority default for quick-add-created rows
- `src/app/templates/partials/todo_item.html:1-47` – row fragment surfaces that expose Priority to CSS, badge text, metadata, and the inline `openEditTodoDialog(..., priority)` argument
- `tests/test_bug_003_priority_defaults.py` – focused regression coverage for create and render Priority behavior

### What We're NOT Doing
- Due Date parsing, persistence, or edit-dialog date formatting surfaces – those belong to S01 and must stay isolated
- A data migration or bulk backfill for existing `NULL` priorities – this story restores correct behavior at create/render time instead of rewriting stored rows
- A new quick-add Priority picker or broader quick-add UX change – the quick-add form stays title-only
- Any redesign of Priority colors, badge variants, or styling rules beyond reflecting the normalized value – visual semantics stay as they are today
- Changes to manual Priority editing behavior for valid explicit values – only missing-priority fallback behavior is in scope

## Architecture Decision

**Approach**: Default Priority at the ORM model boundary and normalize missing Priority at the server-rendered todo-item boundary so both new and legacy rows surface `low` without changing the quick-add form or the S01-owned Due Date path.
**Why this over alternatives**: It fixes the first-write defect and the first-read legacy symptom with a narrow runtime footprint, avoids a migration, and preserves the S01/S02 ownership split.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor or url                              | why needed (intent)
file   | src/app/database.py#Todo                       | Stored Priority contract – set the low default where quick-add-created rows originate
file   | src/app/templates/partials/todo_item.html:1-47 | Render boundary that feeds CSS class, badge text, metadata, and edit-dialog state
file   | src/app/templates/partials/todo_item_with_oob.html | Quick-add response wrapper whose sidebar count OOB swap must remain intact
file   | src/app/static/js/app.js#openEditTodoDialog    | Existing dialog consumer of rendered Priority state – verify the normalized value reaches the selector without changing JS behavior
file   | tests/conftest.py#test_todo                    | Fixture pattern for Todos with explicit non-low Priority values
```

## Constraints & Gotchas

- **Constraint**: The quick-add path is intentionally title-only from the client side – Workaround: assign the documented `low` default at the model boundary rather than expanding the form contract.
- **Avoid**: Blanket fallback logic that overwrites valid explicit Priorities – Instead: preserve stored `low|medium|high` values exactly and apply fallback only when Priority is missing.
- **Critical**: S01 owns Due Date persistence and date-input behavior – Must handle by keeping S02 out of `src/app/routes/todos.py#update_todo`, `src/app/templates/app.html`, and `src/app/utils.py#format_date_input`.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick-add-created Todos always persist with the documented Low Priority
  - Set the stored default in `src/app/database.py#Todo` so creating `Todo(...)` without a submitted Priority still saves `low`; preserve the quick-add request contract and the `partials/todo_item_with_oob.html` response wrapper.
  - **Verify**: `Test: POST /api/todos` with only `list_id` and `title` creates a `Todo` whose `priority == "low"` and returns HTML containing `priority-low`, `data-todo-priority="low"`, `Low`, and `hx-swap-oob="true"`.

- [x] **TI02** Todo-item rendering always provides a usable Priority value to the edit flow
  - Follow `src/app/templates/partials/todo_item.html:1-47`; keep Due Date behavior untouched while ensuring missing stored Priority data renders as one normalized Low value everywhere the fragment exposes Priority, including the inline `openEditTodoDialog(..., priority)` argument, without coercing explicit `medium` or `high` values.
  - **Verify**: `Test: rendering a Todo with missing Priority yields priority-low, data-todo-priority="low", a Low badge, and an inline openEditTodoDialog argument containing "low", while a Todo seeded with priority="high" still yields priority-high, data-todo-priority="high", High, and an inline argument containing "high".`

- [x] **TI03** Priority default regressions are pinned in an S02-owned test file
  - Create `tests/test_bug_003_priority_defaults.py` with focused create/render cases; move or retire BUG-003 assertions from `tests/test_todos.py`, keep S01-owned Due Date persistence assertions out of the file, and include a case that proves opening Edit Todo from a legacy missing-Priority row selects Low rather than blank.
  - **Verify**: `Test: uv run pytest tests/test_bug_003_priority_defaults.py -q` passes with coverage for quick-add default persistence, legacy missing-Priority render fallback, and preservation of explicit non-low values.

### Testing Strategy

### Validation

- Confirm in the browser that a newly quick-added Todo displays the `Low` badge immediately and that reopening Edit Todo for both the new Todo and a seeded legacy missing-Priority Todo shows Low selected rather than a blank control.

### Execution Contract

- Story-local validation is not complete until BUG-003 assertions have been extracted from `tests/test_todos.py` into `tests/test_bug_003_priority_defaults.py` or explicitly retired there, so S02 can run green without inheriting BUG-002 failures.
- If the proposed fix appears to require changes in S01-owned Due Date surfaces such as `src/app/routes/todos.py#update_todo`, `src/app/templates/app.html`, or `src/app/utils.py#format_date_input`, stop and split the work back at the plan level instead of broadening S02.

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
