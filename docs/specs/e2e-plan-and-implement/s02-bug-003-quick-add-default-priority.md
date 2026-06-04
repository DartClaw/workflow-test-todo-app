# BUG-003 quick-add default priority

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S02`

## Feature Overview and Goal

**Intent**: Ensure the quick-add flow assigns the documented default Priority so a newly created Todo renders consistently and the first edit dialog open reflects a valid selection without extra client-side repair logic.

**Expected Outcomes**

- [OC01] A Todo created from the quick-add form without an explicit `priority` is stored and rendered as `low`.
- [OC02] The created Todo row remains the source of truth for the first edit-dialog open, so opening the dialog after quick-add shows `low` selected without a client-side fallback.
- [OC03] The quick-add fix preserves the existing HTMX partial and validation contract, including the list count OOB swap and title rejection behavior.

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "sharedDecisions"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> To satisfy the PRD's conflict-free merge constraint, S01 owns the due-date edit/update path while S02 owns the model-level default-priority source of truth and separate regression coverage, even where a smaller shared-file edit would be possible.
>
> Both stories keep the current server-rendered partial flow intact and avoid dialog JavaScript or template edits unless a server-side fix cannot satisfy the defect.

### From `CLAUDE.md` – "The stack — and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: eb3d1b4426d29cc3bbea2ffefc2a39c5f99f0a87 -->
> HTMX + FastAPI + Jinja2 + Shoelace. Routes return HTML fragments, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM.
>
> Out-of-Band (OOB) swaps are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers.

## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical `Todo` and `Priority` terminology; use `low | medium | high` exactly.
- `CLAUDE.md#cross-cutting-conventions` – Existing route-level ownership checks, ad-hoc validation, and non-JSON error partial conventions.
- `docs/STACK.md#frameworks--libraries` – Confirms the FastAPI + Jinja2 + HTMX baseline the fix must stay within.

## Acceptance Scenarios

- [x] **S01 [OC01] [TI01,TI03] Quick-add creates a low-priority Todo when the form omits priority**
  - **Given** an authenticated user submits the quick-add form with only `list_id` and `title`
  - **When** `POST /api/todos` creates the Todo
  - **Then** the stored Todo has `priority == "low"` and the returned `partials/todo_item_with_oob.html` payload renders the new row with `data-todo-priority="low"` and the low-priority styling hook

- [x] **S02 [OC02] [TI01,TI02,TI03] The first edit dialog open reflects the created Todo's default priority**
  - **Given** a Todo was created through quick-add without an explicit priority
  - **When** the user opens the edit dialog from the rendered Todo row
  - **Then** the dialog's priority selector resolves to `low` from the row payload instead of showing an empty selection

- [x] **S03 [OC03] [TI01,TI03] Quick-add validation failures still return the existing error partial**
  - **Given** an authenticated user submits the quick-add form with an empty `title`
  - **When** `POST /api/todos` rejects the request
  - **Then** the response remains the existing HTML error partial and no fallback low-priority Todo is created

## Structural Criteria

- [x] The model-level `Todo.priority` definition is the only source of the initial default Priority for BUG-003; the fix does not introduce a second quick-add-only default in shared route, dialog, or client code.
- [x] The create response continues to use the existing `partials/todo_item_with_oob.html` contract so the new row render and list-count OOB swap still happen in one response.
- [x] Regression coverage for BUG-003 stays on a story-owned quick-add/default-priority surface and does not widen into S01 due-date scenarios or broader todo-editor cleanup.

## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo.priority` – model-level source of truth for the default `low` Priority used by quick-add creation
- Quick-add create-response contract – preserve the existing `todo_item_with_oob.html` row payload and count OOB swap while the model default flows through unchanged route behavior
- `tests/test_todo_priority_defaults.py` – story-owned regression coverage for default-priority persistence, row payload proof, and title-validation preservation

### What We're NOT Doing
- Due-date parsing or persistence fixes – owned by `S01` and explicitly excluded by the story scope
- General edit-dialog cleanup in `src/app/templates/app.html` or `src/app/static/js/app.js` – out of scope unless a server-side fix cannot satisfy BUG-003
- New JSON endpoints or alternate response formats – the app remains HTMX-first with HTML partial responses
- Priority model expansion beyond `low | medium | high` – the bug is about the missing default, not new priority semantics

## Architecture Decision

**Approach**: Define `low` at the `Todo.priority` model boundary so quick-add creation inherits a persisted default without editing the shared due-date route surface or adding dialog fallbacks.
**Why this over alternatives**: A quick-add route patch would still overlap the shared route module, and a dialog-only fallback would hide the defect in one surface while leaving storage and row metadata inconsistent.

## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                          | why needed (intent)
file   | src/app/database.py#Todo.priority           | Model-level source of truth for the default `low` Priority
file   | src/app/routes/todos.py#create_todo         | Quick-add creation path – keep validation, ownership, position, and partial response shape intact while the model default flows through
file   | src/app/templates/partials/todo_item.html  | Rendered Todo row contract – badge, class, data attribute, and edit-dialog payload all derive from todo.priority
file   | src/app/static/js/app.js#openEditTodoDialog | Dialog population path – verify the server-rendered row still drives selector state
file   | tests/test_todo_priority_defaults.py        | Story-owned regression surface for BUG-003 without sharing S01 tests
```

## Constraints & Gotchas

- **Critical**: The quick-add form never posts `priority` – Must handle by: assigning the default before `todo_item_with_oob.html` renders so the persisted row, badge, and dialog payload agree.
- **Constraint**: S02 owns the model-level default-priority source of truth and separate regression coverage – Workaround: keep changes on `src/app/database.py#Todo.priority` plus story-owned tests unless a browser-observable proof truly requires a narrow integration assertion.
- **Avoid**: Fixing BUG-003 by hard-coding a dialog fallback in `app.html` or `app.js` – Instead: make the stored `Todo.priority` correct so the existing row-to-dialog flow remains authoritative.

## Implementation Plan

### Implementation Tasks

- [x] **TI01** Todo creation has one persisted default Priority when quick-add omits `priority`
  - Follow `src/app/database.py#Todo.priority`; define `low` at the model boundary so `src/app/routes/todos.py#create_todo` can keep its current validation, ownership, position, and `partials/todo_item_with_oob.html` response flow
  - **Verify**: `uv run pytest tests/test_todo_priority_defaults.py -k "quick_add_persists_low"` proves `POST /api/todos` without a `priority` creates a Todo with `priority == "low"`

- [x] **TI02** The rendered quick-add row remains the edit dialog's priority source of truth
  - Use `src/app/templates/partials/todo_item.html` and `src/app/static/js/app.js#openEditTodoDialog` as the contract boundary; do not add a second quick-add-only default path if TI01 can make the stored row correct
  - **Verify**: a quick-add proof asserts the create response contains `data-todo-priority="low"` and `priority-low`, and browser validation shows opening the new row's edit dialog sets `#edit-todo-priority` to `low`

- [x] **TI03** BUG-003 regression coverage proves creation-time defaulting without widening into S01
  - Add `tests/test_todo_priority_defaults.py` as the story-owned regression surface; prove the initial quick-add path resolves to `low`, the row payload carries that value, and empty-title quick-add still returns the existing error partial
  - **Verify**: `uv run pytest tests/test_todo_priority_defaults.py` passes with assertions for `priority == "low"`, `data-todo-priority="low"`, `priority-low`, and the existing error partial on empty title

### Testing Strategy


### Validation


### Execution Contract


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
