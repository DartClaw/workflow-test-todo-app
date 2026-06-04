# Default Quick-Add Priority

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S02`

## Feature Overview and Goal

**Intent**: Ensure the quick-add todo flow persists the documented default priority so newly created todos behave consistently the moment they render and when the edit dialog is reopened later.

**Expected Outcomes**:

- [OC01] A todo created through the quick-add form without any explicit priority is stored with the canonical `low` priority.
- [OC02] The freshly rendered todo row exposes the stored `low` priority consistently in both its visible badge/styling and its edit-dialog hydration data.
- [OC03] BUG-003 stays fixed through regression coverage focused on quick-add creation and reopened edit-dialog behavior, without widening into BUG-002 or unrelated todo-default work.

## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 40fd4632ddf74f8e5af76ebb530f47363eb8ce99 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 40fd4632ddf74f8e5af76ebb530f47363eb8ce99 -->
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |

### From `docs/specs/e2e-plan-and-implement/plan.json` – "sharedDecisions"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: 2026-06-04 -->
> S01 owns only edit-save due-date persistence plus dedicated BUG-002 regression proof, while S02 owns only quick-add default-priority persistence plus dedicated BUG-003 regression proof. Existing row-template and dialog consumers are verify-only unless a story first proves they are broken.


## Deeper Context

- `CLAUDE.md#the-stack-and-why-it-matters-for-edits` – HTMX routes must keep returning HTML partials and OOB swaps; read before changing the quick-add response contract.
- `docs/STACK.md#frameworks-libraries` – Confirms FastAPI + Jinja2 + HTMX as the baseline for server-rendered todo creation and regression tests.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical terms for `Todo`, `TodoList`, and `Priority`; use these exact names in tasks, tests, and implementation notes.
- `src/app/templates/partials/todo_item.html` – Existing row contract for visible Priority and `data-todo-priority`; verify it consumes the stored default before claiming a template edit is necessary.
- `src/app/static/js/app.js#openEditTodoDialog` and `src/app/templates/app.html#edit-todo-dialog` – Existing dialog-hydration consumers; treat them as verify-only surfaces unless stored `low` still fails to prefill the selector.


## Acceptance Scenarios

- [x] **S01 [OC01,OC02] [TI01,TI02] Quick-add renders a new todo with the documented default priority**
  - **Given** an authenticated user is viewing a `TodoList` and submits the quick-add form with only `list_id` and `title`
  - **When** `POST /api/todos` creates the new `Todo`
  - **Then** the appended todo row shows the `Low` priority badge, applies the `priority-low` styling/data contract, and still includes the list-count OOB swap used by the quick-add response

- [x] **S02 [OC02] [TI02] Reopening the edit dialog shows the stored default priority instead of a blank selector**
  - **Given** a `Todo` was created through quick-add without any explicit priority input
  - **When** the user opens the edit dialog from that todo row
  - **Then** the dialog's Priority select is pre-populated to `low`, not left empty, because the existing row and dialog consumers receive the stored priority unchanged

- [x] **S03 [OC01,OC03] [TI01,TI02] Quick-add omission of priority remains a supported input shape**
  - **Given** the quick-add form continues to submit only `list_id` and `title`
  - **When** the create route persists a new `Todo` and the list is fetched again later
  - **Then** the stored `Todo.priority` remains `low` rather than `NULL` or empty, so later renders keep the same priority contract without adding a new quick-add priority field


## Structural Criteria

- [x] The quick-add create flow continues to return the existing HTML partial response shape (`partials/todo_item_with_oob.html`) while applying the priority default.
- [x] Regression coverage lives in a dedicated BUG-003 test file and proves both persistence and edit-dialog hydration without editing S01-owned surfaces.
- [x] Existing row and dialog consumers are verify-only unless proof shows the stored `low` value is still insufficient to hydrate the selector.


## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo` – persistence boundary for the default Priority when quick-add omits the field
- `tests/test_bug_003_quick_add_priority.py` – dedicated BUG-003 regression proof
- Quick-add response markup and reopened-dialog hydration contract – verify-only surfaces for visible `Low` priority, `data-todo-priority="low"`, and the existing OOB swap

### What We're NOT Doing
- Due-date parsing, edit-save persistence, or dialog rehydration for dates -- owned by S01 / BUG-002 and excluded by the shared-isolation constraint
- Adding a priority input to the quick-add form -- the bug is the missing default on omitted input, not a missing UI control
- Refactoring shared todo create/update helpers or consolidating form validation -- out of scope unless a minimal correction is required to keep BUG-003 merge-safe
- Changing explicit manual priority selection behavior in the edit dialog -- this story only restores the documented default when quick-add omits priority


## Architecture Decision

**Approach**: Establish the `low` default at the Todo persistence boundary first, then prove the existing quick-add row and edit-dialog consumers use that stored value without additional UI changes.
**Why this over alternatives**: A client-only fallback would hide the bug in the dialog while leaving storage and later renders inconsistent, and widening into edit-surface changes would violate the PRD's merge-safe isolation constraint.


## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                      | why needed (intent)
file   | src/app/database.py#Todo               | Persistence-default boundary; prefer stored `low` over route or UI fallbacks
file   | src/app/routes/todos.py#create_todo    | Quick-add request/response contract that must stay HTML/OOB compatible
file   | src/app/templates/partials/todo_item.html | Contract reference for visible Priority and `data-todo-priority` in the returned row
file   | tests/test_todos.py#TestTodos.test_create_todo | Pattern to mirror in a dedicated BUG-003 regression module
```


## Constraints & Gotchas

- **Constraint**: The quick-add form posts only `list_id` and `title` -- Workaround: apply the documented default where the create path persists a `Todo`, not in a later UI-only patch.
- **Avoid**: Fixing BUG-003 only in `openEditTodoDialog()` or the edit dialog markup -- Instead: ensure the stored/rendered `Todo.priority` is already `low` so every downstream consumer agrees.
- **Critical**: S02 must remain merge-safe beside S01 -- Must handle by keeping tasks and tests confined to BUG-003 surfaces, with no bundled due-date or general cleanup work.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Quick-add created todos persist the canonical `low` priority when the request omits any priority field
  - Follow `src/app/database.py#Todo` first and preserve the existing quick-add request shape and HTML/OOB response contract in `src/app/routes/todos.py#create_todo`; do not widen into edit-surface changes unless the stored default still fails proof.
  - **Verify**: `Test: POST /api/todos` with only `list_id` and `title` stores `Todo.priority == "low"` and the response markup contains visible `Low`.

- [x] **TI02** Dedicated BUG-003 regression proof covers response markup and reopened edit-dialog hydration
  - Add `tests/test_bug_003_quick_add_priority.py` using the existing create-todo test style as a pattern; assert `data-todo-priority="low"`, `priority-low`, the existing OOB count swap, and reopened dialog hydration without editing shared JavaScript or dialog markup unless the proof shows the stored value is insufficient.
  - **Verify**: `uv run pytest tests/test_bug_003_quick_add_priority.py -q` fails when quick-add leaves `Todo.priority` null/empty and passes only when the returned row and reopened dialog both carry `low`.

### Testing Strategy
- Add BUG-003 proof in `tests/test_bug_003_quick_add_priority.py` using `authenticated_client` plus HTML assertions on the quick-add response, instead of widening the shared `tests/test_todos.py` or integration suite.
- Treat dialog hydration as a two-part proof: route-level assertions for visible `Low` priority plus `data-todo-priority="low"`, and a bounded browser smoke that opens the existing edit dialog and observes the preselected Priority.

### Validation
- Run `uv run pytest tests/test_bug_003_quick_add_priority.py -q` and `uv run pytest tests/test_todos.py -k create_todo -q`.
- Run `./run.sh`, log in with `demo@example.com` / `demo123`, quick-add a Todo with only title input, reopen it through the existing edit dialog, and confirm the Priority select is pre-populated to `low` while the list-count OOB update still occurs.

### Execution Contract
- Keep edits out of S01-owned due-date persistence surfaces and out of shared test files. If a persistence-boundary fix still fails to hydrate the existing dialog correctly, prove that with the dedicated BUG-003 tests before widening into row or dialog consumers.
- If the browser smoke fails while the returned row contract is correct, stop parallel execution and resequence before widening into shared dialog consumers.


## Final Validation Checklist
- [x] The implementation diff excludes S01-owned due-date persistence surfaces and any BUG-002 assertions.
- [x] The quick-add response still includes the list-count OOB swap while exposing visible `Low` priority and `data-todo-priority="low"`.
- [x] The bounded browser smoke confirms the reopened edit dialog preselects `low` for quick-add-created Todos.


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
