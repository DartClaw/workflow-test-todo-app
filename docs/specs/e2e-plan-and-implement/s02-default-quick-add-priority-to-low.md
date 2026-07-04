# Default Quick-Add Priority to Low

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Restore the documented `low` Priority default for quick-add Todos without colliding with the separate edit/update-route story.

**Expected Outcomes**:

- [OC01] Todos created through the quick-add form persist with `priority == "low"` when no Priority field is submitted.
- [OC02] The Todo returned after quick-add carries enough Priority data for the edit dialog to open with the `Low` selector value populated.
- [OC03] Existing quick-add validation, ordering, ownership, and HTMX partial/OOB behavior remain unchanged.

## Required Context

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S02 Story Brief"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> Ensure todos created through the quick-add flow always persist with the documented low priority so reopening the edit dialog shows a populated selector, while keeping the fix off the todo edit/update route and in a dedicated BUG-003 regression file. Excludes due-date parsing, visual priority styling, and broader todo-edit behavior.
>
> Restore the default through a non-route persistence seam so the story stays merge-safe with S01.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Applicable Shared Decisions"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> S01 owns the todo edit/update route surface; S02 must avoid `src/app/routes/todos.py` and restore the default priority through a different persistence seam so the stories do not collide.
>
> Each story gets its own focused regression test file so parallel execution does not force both stories into the same test module.
>
> Both fixes preserve the existing HTML-partial and ad-hoc route-validation architecture; no story introduces JSON responses, Pydantic wiring, or auth changes.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Applicable Binding Constraints"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open

### From `CLAUDE.md` – "Architecture"
<!-- source: CLAUDE.md#architecture -->
<!-- extracted: da59638f8a099350cb05d3f23216400eada2bc83 -->
> HTMX + FastAPI + Jinja2 + Shoelace. Routes return HTML fragments, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM.
>
> Pydantic models in `src/app/models/` are not wired into routes. Validation is ad-hoc in the handlers — do not assume they run.
>
> HTMX-first. Every route that renders should return an HTML partial. Do not introduce JSON endpoints unless explicitly asked.

## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical terms: Todo, TodoList, Priority, Due Date.
- `docs/STACK.md#frameworks--libraries` – FastAPI/Jinja2/SQLAlchemy/pytest baseline for implementation and regression tests.
- `CLAUDE.md#tests` – Test fixtures and `authenticated_client` usage for authenticated route tests.

## Acceptance Scenarios

- [ ] **S01 [OC01,OC02] [TI01,TI02] Quick-add Todo persists the documented low Priority**
  - **Given** an authenticated User with an existing TodoList
  - **When** the User submits the quick-add form to `POST /api/todos` with only `list_id` and `title`
  - **Then** the persisted Todo has `priority == "low"` and the returned Todo partial includes `data-todo-priority="low"`

- [ ] **S02 [OC02] [TI01,TI02] Quick-add Todo opens the edit dialog with Low selected**
  - **Given** a Todo created through the quick-add flow without a submitted Priority field
  - **When** the rendered Todo row calls `openEditTodoDialog(..., priority)` from its edit button
  - **Then** the priority argument is `low`, so `#edit-todo-priority` receives the `low` value instead of an empty value

- [ ] **S03 [OC03] [TI01,TI02] Quick-add behavior outside Priority remains unchanged**
  - **Given** the quick-add route receives a valid title for an owned TodoList
  - **When** the Todo is created
  - **Then** the title is trimmed, the Todo is appended at the next `position`, completion defaults to incomplete, and the response still renders `partials/todo_item_with_oob.html`

- [ ] **S04 [OC03] [TI02] Invalid quick-add requests still fail through existing HTML error behavior**
  - **Given** an authenticated User submits the quick-add form with a blank title
  - **When** `POST /api/todos` handles the request
  - **Then** the response remains the existing HTML Error Partial containing `Title is required` and no Todo is created

## Structural Criteria

- [ ] `src/app/routes/todos.py` remains untouched by this story.
- [ ] No JSON endpoint, Pydantic route wiring, or auth/session behavior is introduced.
- [ ] BUG-003 regression coverage lives in a dedicated test file, not a shared BUG-002 file or broad route-test rewrite.
- [ ] S02 validation uses dedicated BUG-003 coverage plus targeted quick-add route checks; the full `tests/test_todos.py` file remains bundle-level validation after both stories land.

## Scope & Boundaries

### Work Areas

- `src/app/database.py#Todo` Priority persistence default.
- `tests/test_bug_003_quick_add_priority.py` dedicated BUG-003 regression coverage.
- Existing quick-add route behavior observed through `POST /api/todos` without modifying the route.
- Existing Todo partial/edit-dialog data path observed through rendered HTML attributes and dialog argument data.

### What We're NOT Doing

- Editing `src/app/routes/todos.py` – S01 owns the todo edit/update route surface, and the plan requires disjoint route ownership.
- Changing due-date parsing or edit-dialog save behavior – belongs to BUG-002/S01.
- Changing visual Priority styling or CSS classes – BUG-003 is about missing default persistence and selector population.
- Wiring Pydantic models into route handlers – project architecture says route validation is currently ad-hoc.
- Adding migrations or a new persistence framework – this educational SQLite app uses SQLAlchemy model definitions and `create_all` test setup.

## Architecture Decision

**Approach**: Restore `low` as the Todo persistence default at the SQLAlchemy model seam so quick-add creation receives the default without changing `src/app/routes/todos.py`.
**Why this over alternatives**: Route-level assignment would violate the plan’s disjoint-write decision; Pydantic defaults are ineffective here because route handlers do not consume those models.

## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor                               | why needed (intent)
file   | src/app/database.py#Todo                  | Persistence seam for `Todo.priority`; use the same model-level default style as other Todo fields
file   | src/app/routes/todos.py#create_todo       | Read-only reference for quick-add inputs, validation, position behavior, and returned partial contract; do not edit
file   | src/app/templates/partials/todo_item.html | Read-only reference for `data-todo-priority` and edit-button priority argument
file   | src/app/templates/app.html#edit-todo-priority | Read-only reference for the edit-dialog Priority select values
file   | src/app/static/js/app.js#openEditTodoDialog | Read-only reference for how the rendered priority argument populates the selector
file   | tests/conftest.py#authenticated_client    | Fixture pattern for authenticated route regression tests
file   | tests/test_todos.py#TestTodos.test_create_todo | Existing broad test behavior; do not rely on editing it as the dedicated BUG-003 regression
```

## Constraints & Gotchas

- **Critical**: S02 must not edit `src/app/routes/todos.py` – use a non-route persistence seam.
- **Constraint**: Pydantic `TodoCreate.priority` already defaults to `low`, but route handlers do not use that model – do not treat it as the fix.
- **Avoid**: A template-only fallback such as rendering `todo.priority or "low"` – it can hide persisted `NULL` Priority and fail the documented persistence requirement.
- **Constraint**: Keep route responses as HTML partials – no JSON response shape changes.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Todo persistence defaults missing Priority to `low`
  - Make `Todo.priority` in `src/app/database.py#Todo` default to the canonical Priority value `low`, following the existing SQLAlchemy column default style used by Todo fields such as `is_completed` and `position`.
  - **Verify**: `uv run pytest tests/test_bug_003_quick_add_priority.py::test_quick_add_without_priority_persists_low_and_renders_low_priority -q` proves a quick-add POST without `priority` persists `priority == "low"` and returns `data-todo-priority="low"`.

- [ ] **TI02** BUG-003 has isolated regression coverage for quick-add Priority and unchanged failure behavior
  - Add `tests/test_bug_003_quick_add_priority.py` using `authenticated_client`, `test_list`, and `db_session`; cover valid quick-add persistence/rendering and blank-title rejection without editing shared BUG-002 tests or `tests/test_todos.py`.
  - **Verify**: `uv run pytest tests/test_bug_003_quick_add_priority.py -q` passes and includes assertions for `priority == "low"`, `data-todo-priority="low"`, next-position preservation, incomplete default, and `Title is required` on blank title.

- [ ] **TI03** S02 remains disjoint from the todo edit/update route surface
  - Keep `src/app/routes/todos.py` as a read-only reference for this story; all implementation writes must stay outside that route file.
  - **Verify**: `git diff -- src/app/routes/todos.py` prints no diff after implementation.

- [ ] **TI04** Existing todo behavior remains green with the BUG-003 default in place
  - Run only the existing quick-add route checks after the dedicated BUG-003 test passes so S02 stays independent from the BUG-002 edit-route surface.
  - **Verify**: `uv run pytest tests/test_bug_003_quick_add_priority.py tests/test_todos.py::TestTodos::test_create_todo tests/test_todos.py::TestTodos::test_create_todo_empty_title -q` passes.

### Testing Strategy


### Validation


### Execution Contract


## Final Validation Checklist

- [ ] `uv run pytest tests/test_bug_003_quick_add_priority.py tests/test_todos.py::TestTodos::test_create_todo tests/test_todos.py::TestTodos::test_create_todo_empty_title -q` passes.
- [ ] No S02 change edits `src/app/routes/todos.py`, broadens quick-add behavior beyond the missing `low` Priority default, or masks persisted `NULL` Priority only at render time.

## Implementation Observations

_No observations recorded yet._
