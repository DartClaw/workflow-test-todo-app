# BUG-001 – Sidebar incomplete count updates on todo delete

## Feature Overview and Goal

**Intent**: Keep the sidebar's incomplete count synchronized with successful todo deletions so users can trust list state without a full page reload.

**Expected Outcomes**:

- [OC01] Deleting an incomplete Todo updates the visible list state in one HTMX round-trip, including the sidebar badge for the owning TodoList.
- [OC02] The sidebar badge continues to represent incomplete Todos only, so completed-todo deletions leave the count unchanged and deleting the last incomplete Todo renders `0`.
- [OC03] The delete flow adopts the existing OOB swap response pattern without changing current access-control or not-found behavior.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – "The stack — and why it matters for edits"
<!-- source: CLAUDE.md#architecture -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

- `CLAUDE.md#visual-validation-workflow` – When validating the fix, check both the todo row removal and the sidebar region updated by `hx-swap-oob`.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical terminology for `Partial`, `Todo`, `TodoList`, and `OOB Swap`.


## Acceptance Scenarios

- [x] **S01 [OC01] [TI01,TI03] Deleting an incomplete Todo refreshes the sidebar badge without a page reload**
  - **Given** an authenticated user is viewing a TodoList whose sidebar badge `id="list-<todo-list-id>-count"` shows `2`, and the targeted Todo is incomplete
  - **When** the user confirms deletion of that Todo
  - **Then** HTMX removes `#todo-<todo-id>` and applies an OOB swap to `#list-<todo-list-id>-count` so the badge shows `1` in the same request

- [x] **S02 [OC02] [TI02,TI03] Deleting the only remaining incomplete Todo renders a zero badge**
  - **Given** an authenticated user is viewing a TodoList with one incomplete Todo and the sidebar badge shows `1`
  - **When** the user deletes that Todo
  - **Then** the delete response updates `#list-<todo-list-id>-count` to `0` without requiring a full page reload

- [x] **S03 [OC02] [TI02,TI03] Deleting a completed Todo leaves the incomplete badge unchanged**
  - **Given** an authenticated user is viewing a TodoList with one incomplete Todo, one completed Todo, and the sidebar badge shows `1`
  - **When** the user deletes the completed Todo
  - **Then** the completed Todo is removed and the OOB swap keeps `#list-<todo-list-id>-count` at `1`

- [x] **S04 [OC03] [TI03] Missing Todo deletes keep existing failure semantics**
  - **Given** an authenticated user issues `DELETE /api/todos/<todo-id>` for a Todo ID that no longer exists
  - **When** the route handles the request
  - **Then** it returns `404` without emitting a successful delete OOB fragment


## Structural Criteria

- [x] Successful todo deletes keep server-rendered HTML as the only source of sidebar count truth; no client-side count arithmetic or JSON response is introduced.
- [x] The sidebar badge target contract remains `id="list-<todo-list-id>-count"` across list rendering and the successful delete response.
- [x] `delete_todo` continues to rely on the existing HTMX `swap: 'delete'` row-removal behavior while preserving current `403` and `404` semantics.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#delete_todo` – successful delete response contract
- `src/app/routes/todos.py#_get_list_todo_count` – canonical incomplete-count calculation reused by delete
- `src/app/templates/partials/todo_deleted_oob.html` – delete-specific OOB payload for the sidebar badge
- `src/app/static/js/app.js#confirmDeleteTodo` plus `src/app/templates/partials/todo_list_item.html` – existing target/swap and badge-id contract the response must honor
- `tests/test_todos.py` and `tests/test_integration.py#test_todo_completion_updates_count` – regression coverage for delete count synchronization

### What We're NOT Doing
- Changing the create or toggle count-refresh flows – they already demonstrate the intended OOB pattern.
- Re-rendering the full sidebar or computing counts in browser JavaScript – the server-rendered partial remains the source of truth.
- Changing delete confirmation dialog UX or the broader HTMX delete wiring beyond what is required for the count refresh.
- Altering successful delete behavior for lists, or changing `403`/`404` semantics beyond preserving current status handling.


## Architecture Decision

**Approach**: Keep successful `delete_todo` responses in the same server-rendered HTMX contract as `toggle_todo` by returning `partials/todo_deleted_oob.html` with the post-delete incomplete count from `src/app/routes/todos.py#_get_list_todo_count`.
**Why this over alternatives**: Reusing the existing OOB partial pattern preserves the client's `swap: 'delete'` row-removal behavior and avoids duplicate count logic in JavaScript or full-sidebar rerenders.


## Technical Overview


## Code Patterns & External References

```text
# type | path#anchor or url                            | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo          | Existing OOB count-update response to mirror for successful deletes
file   | src/app/routes/todos.py#_get_list_todo_count | Canonical incomplete-count helper – reuse rather than recalculate differently
file   | src/app/static/js/app.js#confirmDeleteTodo   | Delete requests already use `target: #todo-<id>` with `swap: 'delete'`
file   | src/app/templates/partials/todo_deleted_oob.html | Existing delete-only OOB fragment shape already present in the repo
file   | tests/test_integration.py#test_todo_completion_updates_count | Current regression pattern proving an OOB count swap exists
```


## Constraints & Gotchas

- **Constraint**: `confirmDeleteTodo` already calls `htmx.ajax('DELETE', ..., { target: '#todo-<id>', swap: 'delete' })` -- Workaround: successful server responses should supply only the sidebar OOB fragment, not replacement row markup.
- **Avoid**: Recomputing the sidebar badge from ad hoc route logic or browser state -- Instead: reuse `src/app/routes/todos.py#_get_list_todo_count` so create, toggle, and delete share one incomplete-count definition.
- **Critical**: Todo routes in this app return HTML fragments, not JSON -- Must handle by: keeping the successful delete path on an HTML partial response and leaving failure branches aligned with current status semantics.


## Implementation Plan

### Implementation Tasks

- [x] **TI01** Successful delete responses carry the sidebar badge's OOB refresh payload
  - Follow `src/app/routes/todos.py#toggle_todo`, `src/app/static/js/app.js#confirmDeleteTodo`, and `src/app/templates/partials/todo_deleted_oob.html`; the delete success path must preserve the row's existing `swap: 'delete'` behavior while returning the badge refresh fragment
  - **Verify**: Deleting an incomplete Todo from a list whose badge shows `2` removes `#todo-<todo-id>` and returns a response containing `hx-swap-oob`, `id="list-<todo-list-id>-count"`, and the updated badge value `1`

- [x] **TI02** Delete count semantics stay aligned with incomplete Todo membership
  - Reuse `src/app/routes/todos.py#_get_list_todo_count` for the successful delete response so completed-todo deletes and zero-count cases stay consistent with the rest of the app
  - **Verify**: Deleting a completed Todo leaves `#list-<todo-list-id>-count` unchanged, and deleting the last incomplete Todo returns the same OOB fragment with badge value `0`

- [x] **TI03** Delete regression coverage proves the OOB contract without widening endpoint behavior
  - Extend `tests/test_todos.py` and `tests/test_integration.py#test_todo_completion_updates_count` style coverage so success assertions check the OOB fragment and failure assertions keep `403`/`404` status-only behavior distinct
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py -k "delete or count"` passes with assertions that successful delete responses include `hx-swap-oob` while missing-Todo `404` responses do not

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
