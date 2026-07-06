# BUG-001 – Fix Sidebar Incomplete Count

## Feature Overview and Goal

**Intent**: Restore immediate sidebar feedback after Todo deletion so the active TodoList's incomplete-count stays trustworthy without a full page reload.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo updates the active TodoList sidebar incomplete-count immediately on the same interaction.
- [OC02] The sidebar incomplete-count continues to represent only incomplete Todos, so deleting a completed Todo does not decrement it.
- [OC03] Existing Todo interactions stay coherent: delete still removes the row, toggle still updates the count, and rejected deletes do not emit a misleading success-state count update.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-ID  | Description | Severity | Stories | Status |
> |---------|-------------|----------|---------|--------|
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – "The stack – and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical definitions for Partial and OOB Swap used in this FIS.
- `docs/STACK.md#frameworks--libraries` – FastAPI, Jinja2, HTMX, and SQLite baseline this fix must stay within.
- `CLAUDE.md#visual-validation-workflow` – Browser validation steps for multi-region updates after HTMX interactions.


## Acceptance Scenarios

- [ ] **S01 [OC01,OC03] [TI01] Deleting an incomplete Todo refreshes the sidebar count immediately**
  - **Given** an authenticated User viewing a TodoList whose sidebar badge `#list-{list_id}-count` shows `2` for two incomplete Todos
  - **When** the user confirms delete for one of those incomplete Todos and `DELETE /api/todos/{todo_id}` succeeds
  - **Then** `#todo-{todo_id}` is removed and the response updates `#list-{list_id}-count` to `1` via `hx-swap-oob` without a full page reload

- [ ] **S02 [OC02,OC03] [TI01,TI02] Deleting a completed Todo keeps the incomplete-count unchanged**
  - **Given** a TodoList with one incomplete Todo, one completed Todo, and sidebar badge `#list-{list_id}-count` showing `1`
  - **When** the completed Todo is deleted
  - **Then** `#todo-{todo_id}` is removed and the OOB update keeps `#list-{list_id}-count` at `1`

- [ ] **S03 [OC03] [TI02] Toggle-driven count updates still work after the delete fix**
  - **Given** an incomplete Todo in the active TodoList and sidebar badge `#list-{list_id}-count` showing `1`
  - **When** the user toggles that Todo complete through `PATCH /api/todos/{todo_id}/toggle`
  - **Then** the Todo row re-renders and the response still updates `#list-{list_id}-count` to `0` via the existing OOB pattern

- [ ] **S04 [OC03] [TI01] Rejected deletes do not emit a fake success-state count update**
  - **Given** a User submits `DELETE /api/todos/{todo_id}` for a missing Todo or a Todo owned by another User
  - **When** the request is rejected
  - **Then** the response stays `404` or `403` and does not emit a success-state `#list-{list_id}-count` OOB fragment


## Structural Criteria

- [ ] Successful delete responses target the existing sidebar badge `id="list-{list_id}-count"` rather than introducing a second count selector.
- [ ] Delete-side count recomputation reflects persisted `Todo.is_completed == False` state after the delete commit, not a client-side guess.
- [ ] Automated coverage includes explicit assertions for delete-path `hx-swap-oob` output and for the pre-existing toggle count update path.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py` delete success path and incomplete-count recomputation
- `src/app/templates/partials/todo_deleted_oob.html` and the sidebar badge contract in `src/app/templates/partials/todo_list_item.html`
- Delete and toggle regression coverage in `tests/test_todos.py` and `tests/test_integration.py`

### What We're NOT Doing
- Reworking general sidebar rendering or TodoList CRUD responses – BUG-001 is scoped to single-Todo delete behavior.
- Replacing the existing `htmx.ajax(..., swap: 'delete')` client flow in `src/app/static/js/app.js` – row removal already works and should remain the mechanism.
- Changing create or toggle behavior beyond keeping their count-update contract intact under regression coverage.
- Introducing JSON endpoints, websocket syncing, or full-page refresh fallbacks – the established HTMX/OOB pattern already matches the defect.


## Architecture Decision

**Approach**: Successful `DELETE /api/todos/{todo_id}` responses return an HTML partial containing the updated sidebar count as an OOB Swap, computed after deletion with the same incomplete-count semantics already used by toggle and create.
**Why this over alternatives**: It matches the repo's HTMX-first server-rendered interaction model, reuses existing count-target conventions, and avoids extra client-side state logic or a full sidebar rerender.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. **Leave empty** when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                                        | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo                       | Working OOB response pattern for Todo row + sidebar badge updates
file   | src/app/routes/todos.py#_get_list_todo_count              | Canonical incomplete-count query used by Todo routes
file   | src/app/templates/partials/todo_item_with_oob.html        | Existing composite OOB markup shape
file   | src/app/templates/partials/todo_deleted_oob.html          | Delete-specific OOB fragment scaffold already present in the repo
file   | src/app/templates/partials/todo_list_item.html            | Sidebar badge id contract and incomplete-count rendering target
file   | src/app/static/js/app.js#confirmDeleteTodo                | Existing delete interaction contract uses `htmx.ajax(..., swap: 'delete')`
file   | tests/test_integration.py#test_todo_completion_updates_count | Existing integration proof for toggle-driven OOB count updates
```


## Constraints & Gotchas

- **Constraint**: Delete row removal is already owned by `src/app/static/js/app.js#confirmDeleteTodo` with `swap: 'delete'` – Workaround: the server success response should add only the sidebar badge OOB fragment, not a replacement row.
- **Avoid**: Returning a bare `200` or a full sidebar rerender for single-Todo deletes – Instead: reuse the existing `id="list-{list_id}-count"` target with `hx-swap-oob`.
- **Critical**: Sidebar badges count only incomplete Todos – Must handle by recomputing from persisted `Todo.is_completed == False` state after the delete commit.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful Todo delete responses carry the updated sidebar incomplete-count for the owning TodoList
  - Follow `src/app/routes/todos.py#toggle_todo`, reuse `src/app/routes/todos.py#_get_list_todo_count`, and return `src/app/templates/partials/todo_deleted_oob.html` on `200` only after `db.commit()`
  - **Verify**: `Test: deleting an incomplete Todo removes it from the DB and returns 200 content containing "hx-swap-oob" and 'id="list-{list_id}-count"' with the decremented count`

- [ ] **TI02** Delete-side OOB markup and sidebar badge targeting stay aligned on incomplete-only semantics
  - Keep `src/app/templates/partials/todo_deleted_oob.html` and `src/app/templates/partials/todo_list_item.html` on the same `list-{{ ... }}-count` contract; the returned count must still represent only `Todo.is_completed == False`
  - **Verify**: `Test: deleting a completed Todo returns an OOB fragment that leaves the visible count unchanged, and toggling an incomplete Todo complete still drives 'id="list-{list_id}-count"' to 0`

- [ ] **TI03** Automated coverage proves delete count refresh and rejected deletes stay free of misleading OOB success markup
  - Extend `tests/test_todos.py#test_delete_todo` and `tests/test_integration.py#test_todo_completion_updates_count`; add explicit assertions for delete success OOB output plus rejected `403` and `404` delete responses
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count or toggle"` passes with assertions covering success OOB output and rejected-delete no-OOB cases

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. **Leave empty** when this is sufficient; fill only when the test approach is non-obvious – level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.

### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. **Leave empty** when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.

### Execution Contract
> Generic exec-spec discipline – task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy – is enforced by exec-spec. **Leave empty** when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. **Leave empty** when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

_No observations recorded yet._
