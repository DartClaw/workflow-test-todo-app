# Persist Edited Due Dates

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S01`

## Feature Overview and Goal

**Intent**: Preserve user trust in the todo edit flow by making a due date entered in the existing edit dialog survive save and reappear when that same Todo is reopened.

**Expected Outcomes**:

- [OC01] A due date submitted from the existing edit dialog persists on the Todo instead of being dropped by a format mismatch.
- [OC02] The returned todo partial rehydrates the stored due date so reopening the same Todo shows the saved date in the edit dialog.
- [OC03] Clearing the optional due date field still removes the stored Due Date without changing unrelated todo behavior.


## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 40fd4632ddf74f8e5af76ebb530f47363eb8ce99 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 40fd4632ddf74f8e5af76ebb530f47363eb8ce99 -->
> | BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |


## Deeper Context

- `src/app/utils.py#format_date_input` – Existing `YYYY-MM-DD` formatter; treat it as the contract reference before widening BUG-002 into shared formatting work.
- `src/app/templates/partials/todo_item.html` – Existing row contract carrying `data-todo-due-date`; verify it remains correct after the route fix before claiming a template edit is necessary.
- `tests/test_todos.py#TestTodos.test_update_todo` – Existing route-test style to mirror in a dedicated BUG-002 regression module without reusing the shared file.


## Acceptance Scenarios

- [ ] **S01 [OC01,OC02] [TI01,TI02] Saved due date survives the existing edit flow**
  - **Given** an authenticated user opens the existing edit dialog for a Todo with no Due Date
  - **When** the user submits the dialog with `due_date=2025-12-31`
  - **Then** the Todo stores that Due Date and the returned todo partial exposes `data-todo-due-date="2025-12-31"` so reopening the same Todo shows `2025-12-31` in the date field

- [ ] **S02 [OC01,OC02] [TI01,TI02] Editing other fields does not blank an already stored due date**
  - **Given** an authenticated user has a Todo whose stored Due Date is `2025-12-31`
  - **When** the user reopens the existing edit dialog, changes title or note, and saves while leaving the due date field unchanged
  - **Then** the Todo keeps the same Due Date instead of losing it to a parse mismatch, and the refreshed row still reopens with `2025-12-31` populated

- [ ] **S03 [OC03] [TI01,TI02] Clearing the optional due date still removes it**
  - **Given** an authenticated user opens the existing edit dialog for a Todo with a stored Due Date
  - **When** the user clears the date field and saves
  - **Then** the Todo stores no Due Date and reopening the same Todo shows an empty date field


## Structural Criteria

- [ ] The edit-flow fix remains isolated to BUG-002 surfaces and does not change quick-add Priority defaults, overdue styling, or unrelated date normalization.
- [ ] The existing `data-todo-due-date="YYYY-MM-DD"` row contract is treated as verify-only unless a failing proof shows the current template output is wrong.
- [ ] Regression coverage lives in a dedicated BUG-002 test file and proves persistence, dialog rehydration, and the explicit clear-date path.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#update_todo` – edit-save Due Date parsing and clear behavior
- `tests/test_bug_002_due_date_persistence.py` – dedicated BUG-002 regression proof
- Returned todo-row HTML after edit saves – verify-only surface for `data-todo-due-date="YYYY-MM-DD"` rehydration

### What We're NOT Doing
- Quick-add default Priority behavior from `BUG-003` -- owned by `S02`, and the PRD requires independent thin stories.
- Overdue versus due-today styling from `BUG-004` -- separate defect with different date semantics and proof.
- Broad Due Date normalization across create, search, or display flows -- outside the isolated BUG-002 edit-flow contract.
- Dialog UX or JavaScript refactors unrelated to Due Date persistence -- avoid widening the file-ownership surface and risking merge conflict with sibling work.


## Architecture Decision

**Approach**: Align the `update_todo` Due Date parser with the existing date-only contract already emitted by `format_date_input` and consumed by the edit dialog, while preserving the current `Todo.due_date` storage type and empty-field clear behavior.
**Why this over alternatives**: It fixes the broken server-client seam at the narrowest point instead of widening into datetime-local UI changes or global date cleanup that the story explicitly excludes.


## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor                                | why needed (intent)
file   | src/app/routes/todos.py#update_todo       | Existing edit-flow update seam and partial-response contract
file   | src/app/utils.py#format_date_input        | Contract reference for the accepted `YYYY-MM-DD` date-input value
file   | src/app/templates/partials/todo_item.html | Contract reference for row rehydration after the route fix
file   | tests/test_todos.py#TestTodos.test_update_todo | Pattern to mirror in a dedicated BUG-002 regression module
```


## Constraints & Gotchas

- **Constraint**: The existing edit dialog submits a date-only field and the row stores that value in both `data-todo-due-date` and the inline edit action -- Workaround: keep all BUG-002 changes aligned to the shared `YYYY-MM-DD` contract instead of introducing a second input format.
- **Avoid**: Silent parse-mismatch fallthrough in the update route -- Instead: make persistence and rehydration observable in regression tests so the swallowed-format behavior cannot return unnoticed.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Edit-dialog Due Date submissions persist using the existing date-only contract
  - Adjust `src/app/routes/todos.py#update_todo` so the route accepts the same `YYYY-MM-DD` value produced by `src/app/utils.py#format_date_input`; keep the empty-string path clearing `Todo.due_date` and keep the change confined to BUG-002 edit-flow behavior.
  - **Verify**: A todo updated through `PUT /api/todos/{todo_id}` with `due_date=2025-12-31` stores a Due Date whose formatted input value is exactly `2025-12-31`, and submitting `due_date=` still stores `None`.

- [ ] **TI02** Dedicated BUG-002 regression proof covers persistence, rehydration, and clear-date behavior
  - Add `tests/test_bug_002_due_date_persistence.py` using the existing route-test style as a pattern; assert the returned row still carries `data-todo-due-date="2025-12-31"` after save and an empty value after clear, without editing shared template or JavaScript surfaces unless the proof shows they are wrong.
  - **Verify**: `uv run pytest tests/test_bug_002_due_date_persistence.py -q` fails against the swallowed-format behavior and passes only when edited Due Dates persist, rehydrate, and clear correctly.

### Testing Strategy
- Add BUG-002 proof in `tests/test_bug_002_due_date_persistence.py` using `authenticated_client` plus direct HTML assertions on the returned todo row, instead of expanding the shared `tests/test_todos.py` surface.
- Treat dialog rehydration as a two-part proof: route-level assertions for the returned `data-todo-due-date` contract plus a bounded browser smoke that reopens the existing edit dialog and observes the populated date input.

### Validation
- Run `uv run pytest tests/test_bug_002_due_date_persistence.py -q` and `uv run pytest tests/test_todos.py -k update_todo -q`.
- Run `./run.sh`, log in with `demo@example.com` / `demo123`, save `2025-12-31` through the existing edit dialog, reopen the same Todo, and confirm the date input shows `2025-12-31`; repeat once with the field cleared and confirm the reopened input is empty.

### Execution Contract
- Keep edits out of S02-owned quick-add/default surfaces and out of shared test files. If the route-only fix appears to require template or JavaScript edits, prove the existing row contract is insufficient before widening the story.
- If the browser smoke fails while the returned row contract is correct, stop parallel execution and resequence before widening into shared dialog consumers.


## Final Validation Checklist
- [ ] The implementation diff excludes S02-owned quick-add default surfaces and any BUG-003 assertions.
- [ ] The post-save row still exposes `data-todo-due-date="YYYY-MM-DD"` for persisted dates and an empty value after clearing.
- [ ] The bounded browser smoke confirms reopened-dialog hydration for both persisted and cleared Due Date values.


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
