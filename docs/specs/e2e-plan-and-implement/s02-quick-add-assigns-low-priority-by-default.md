# Quick-add assigns low priority by default

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Ensure title-only quick-add creates a fully initialized `Todo` so newly added tasks immediately carry the documented default Priority without manual repair.

**Expected Outcomes**:

- [OC01] Quick-add creates todos with persisted `priority="low"` when the user supplies only `list_id` and `title`.
- [OC02] The new todo row and reopened edit dialog both expose `low` as the saved priority for quick-add-created todos.
- [OC03] Existing quick-add validation still rejects invalid submissions instead of creating partially initialized todos.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: cc6e316 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: cc6e316 -->
> | BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |

## Deeper Context

- `CLAUDE.md#the-stack-and-why-it-matters-for-edits` – Quick-add responses are HTML partials with OOB swaps, not JSON responses.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical use of `Todo` and `Priority`.

## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Title-only quick-add creates a low-priority todo**
  - **Given** an authenticated user with an open `TodoList`
  - **When** the quick-add form submits only `list_id` and `title`
  - **Then** the created `Todo` persists with `priority="low"` and the returned row exposes low-priority badge and dialog metadata

- [x] **S02 [OC02] [TI01,TI02] Reopening a quick-add-created todo preserves the low-priority selection**
  - **Given** a todo that was created through the quick-add flow
  - **When** the user opens the edit dialog for that todo
  - **Then** the dialog reads back `low` instead of an empty priority selector

- [x] **S03 [OC03] [TI03] Invalid quick-add submissions still create nothing**
  - **Given** the quick-add form submits a blank or whitespace-only title
  - **When** the create route rejects the request
  - **Then** the response stays the standard error partial and no new `Todo` is persisted

## Structural Criteria

- [x] The default priority source applies to quick-add creation without widening this story into the edit-path due-date fix.
- [x] Existing todos with explicit `medium` or `high` priorities continue rendering those values unchanged.
- [x] The quick-add route keeps its HTML partial plus OOB count-update response shape.

## Scope & Boundaries

### Work Areas
- Todo persistence default for title-only quick-add rows
- Persisted priority metadata rendered on the todo row and consumed by the edit dialog
- Route-level regression coverage for valid and invalid quick-add submissions

### What We're NOT Doing
- Edit-dialog due-date parsing and persistence -- handled by S01
- Adding a visible priority selector to the quick-add form -- not required to satisfy the documented default
- Retroactive cleanup of existing null-priority rows -- outside this thin defect fix unless implementation proves it is unavoidable
- Changing priority names, badge colors, or other presentation taxonomy -- not part of BUG-003

## Architecture Decision

**Approach**: Source the title-only quick-add default at the create/model boundary so missing priority values resolve to `low` before persistence.
**Why this over alternatives**: It matches the documented default while keeping S02 on the create/default surface instead of forcing overlap with the edit/update story.

## Technical Overview

## Code Patterns & External References

```text
# type | path#anchor | why needed (intent)
file   | src/app/routes/todos.py#create_todo | Quick-add entrypoint and OOB response flow
file   | src/app/database.py#Todo.priority | Persisted priority source for title-only todo creation
file   | src/app/templates/partials/todo_item.html | Badge and dialog metadata that prove the saved priority
file   | tests/test_todos.py#TestTodos.test_create_todo | Existing route-level quick-add regression style
```

## Constraints & Gotchas

- **Constraint**: quick-add submits only `list_id` and `title` -- Workaround: default missing priority at creation time instead of expecting an omitted form field to appear later.
- **Constraint**: this story must remain merge-safe with S01 -- Workaround: prefer a model-bound default so `update_todo` ownership stays isolated to S01.
- **Avoid**: fixing the symptom only in rendered HTML -- Instead: persist `low` on the created `Todo` so the row and reopened dialog stay aligned.
- **Critical**: the create route also updates the sidebar count through the same response -- Must preserve the existing OOB response contract.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Title-only quick-add persists `priority="low"` on every valid new todo
  - Source the default from the `Todo` creation boundary in `src/app/database.py#Todo.priority`; treat `src/app/routes/todos.py#create_todo` as the proof surface, not the preferred write surface, so S01 keeps ownership of edit-path route changes
  - **Verify**: `Test: POST /api/todos` with only `list_id` and `title` creates a `Todo` whose `priority == "low"`

- [x] **TI02** Quick-add response and reopened dialog expose the same low-priority value
  - Use `src/app/templates/partials/todo_item.html` as the proof surface; the returned row must contain the persisted low-priority badge and `data-todo-priority="low"` consumed by the edit dialog
  - **Verify**: `Test: the quick-add response HTML contains both `priority-low` and `data-todo-priority="low"` for the created todo`

- [x] **TI03** Quick-add validation behavior stays intact while defaulting applies only to valid creates
  - Keep the existing blank-title rejection in `src/app/routes/todos.py#create_todo` unchanged; this story must not create partially initialized todos on invalid input
  - **Verify**: `uv run pytest tests/test_todos.py -k "create_todo"` passes, including the blank-title rejection and the low-priority default case

### Testing Strategy

### Validation

### Execution Contract

## Final Validation Checklist

## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

_No observations recorded yet._
