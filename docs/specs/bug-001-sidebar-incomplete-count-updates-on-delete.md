# BUG-001 – Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal

**Intent**: Keep TodoList sidebar state consistent with server truth when a Todo is deleted, without requiring a full page reload.

**Expected Outcomes** (2-4 user- or business-observable success conditions, each `[OC<NN>]`-tagged; scenarios anchor to these via `[OC<NN>]`):

- [OC01] Deleting an incomplete Todo immediately refreshes that TodoList's sidebar incomplete count in the same HTMX response.
- [OC02] Deleting a completed Todo leaves the sidebar incomplete count unchanged while still removing the Todo row.
- [OC03] Failed delete requests preserve current response semantics and do not emit a misleading sidebar count refresh.

## Required Context

> Load-bearing upstream spans inlined verbatim from PRD, plan, ADRs, or guidelines. **Omit this entire section** when there are no upstream sources to inline.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `AGENTS.md` – "The stack — and why it matters for edits"
<!-- source: AGENTS.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

## Deeper Context

> Anchored pointers for supplementary context; read on demand. **Omit this entire section** when no supplementary pointers exist.

- `AGENTS.md#visual-validation-workflow` – Required in-browser verification for interactions that update both the row and sidebar count.
- `docs/STACK.md#frameworks--libraries` – HTMX + FastAPI + Jinja baseline for server-rendered HTML fragment responses.
- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical meanings of `Partial` and `OOB Swap`.

## Acceptance Scenarios

- [ ] **S01 [OC01,OC03] [TI01,TI02,TI03] Deleting an incomplete Todo refreshes the sidebar count immediately**
  - **Given** an authenticated user is viewing a TodoList with two incomplete Todos and the sidebar badge shows `2`
  - **When** the user confirms deletion of one incomplete Todo from the current list
  - **Then** that Todo row is removed and the same server response refreshes `#list-<list_id>-count` to `1` without a full page reload

- [ ] **S02 [OC02] [TI01,TI02,TI03] Deleting a completed Todo does not decrement the incomplete badge**
  - **Given** an authenticated user is viewing a TodoList with one incomplete Todo, one completed Todo, and the sidebar badge shows `1`
  - **When** the user confirms deletion of the completed Todo
  - **Then** the completed Todo row is removed and the out-of-band sidebar badge still renders `1`

- [ ] **S03 [OC03] [TI01,TI03] Missing or unauthorized deletes do not desynchronize the sidebar**
  - **Given** the client issues a delete request for a Todo that does not exist or is not owned by the authenticated user
  - **When** the delete route handles the request
  - **Then** the route preserves its current `404` or `403` response semantics and does not return a sidebar count fragment that could desynchronize the visible badge

## Structural Criteria

> Non-behavioral proof requirements: invariants, regression guards, and structural checks that hold true when done. Each criterion is proved by a task Verify line, not a scenario.

- [ ] Sidebar count refreshes continue to target the existing `id="list-<list_id>-count"` DOM contract defined in `partials/todo_list_item.html`.
- [ ] The delete flow stays HTMX-first and server-rendered; no JSON response shape or browser-side recount logic is introduced.
- [ ] Regression coverage in `tests/test_todos.py` proves both incomplete and completed delete behavior against response content and persisted database state.

## Scope & Boundaries

### Work Areas
_Inventory of components, files, or surfaces being changed (3-7 bullets). Each Work Area must map to at least one task or scenario – a Work Area with no implementing task is a forward-coverage gap._
- `src/app/routes/todos.py` delete route success path and shared incomplete-count helper usage
- `src/app/templates/partials/todo_deleted_oob.html` or equivalent delete-response partial used by the HTMX delete flow
- `src/app/templates/partials/todo_list_item.html` sidebar badge DOM target contract
- `src/app/static/js/app.js` existing `htmx.ajax(... swap: 'delete')` delete interaction contract
- `tests/test_todos.py` delete-route regression coverage for OOB count refresh behavior

### What We're NOT Doing
_Keep this to 3-5 explicit non-goals or deferrals._
- Changing create or toggle count-refresh behavior -- those paths already work and serve as the reference contract
- Reworking the delete confirmation dialog or broader client-side delete UX -- BUG-001 is a server-response/state-sync defect
- Introducing JSON endpoints or client-side count recomputation -- that conflicts with the codebase's HTMX-first server-rendered pattern
- Altering Todo ordering, list loading, or other TodoList aggregates beyond the delete-path incomplete count refresh -- no broader defect is in scope

## Architecture Decision

**Approach**: Keep delete aligned with create and toggle by returning an HTMX out-of-band sidebar count refresh sourced from `src/app/routes/todos.py#_get_list_todo_count` in the successful delete response.
**Why this over alternatives**: It preserves the existing server-rendered contract, reuses one incomplete-count source of truth, and avoids duplicating count logic in browser code.

## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. **Leave empty** when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                                     | why needed (intent)
file   | src/app/routes/todos.py#_get_list_todo_count           | Canonical incomplete-count query for TodoList sidebar badges
file   | src/app/routes/todos.py#toggle_todo                    | Existing mutation response that updates both the Todo row and sidebar count
file   | src/app/templates/partials/todo_item_with_oob.html     | Composite partial pattern for primary swap + `hx-swap-oob` badge update
file   | src/app/templates/partials/todo_list_item.html         | Authoritative sidebar badge DOM target id contract
file   | src/app/static/js/app.js#confirmDeleteTodo             | Current HTMX delete request contract: target Todo row, `swap: 'delete'`
file   | tests/test_todos.py#TestTodos.test_toggle_todo_complete | Existing test neighborhood for Todo mutation response coverage
```

## Constraints & Gotchas

_A bullet belongs here only if it is cross-cutting (applies to ≥2 tasks) or names a non-obvious framework-level trap. Task-local concerns live in task descriptions._

- **Constraint**: Todo deletes are dispatched with `htmx.ajax('DELETE', ...)` targeting `#todo-<id>` and `swap: 'delete'` -- Workaround: sidebar updates must ride on `hx-swap-oob` content because the primary target is removed by the existing client flow.
- **Avoid**: recomputing counts in JavaScript or hand-maintaining badge text in the browser -- Instead: use the server-side incomplete-count query already shared by create and toggle.
- **Critical**: the sidebar badge contract is the exact `id="list-<list_id>-count"` anchor in `partials/todo_list_item.html` -- Must handle by: keeping any delete-response OOB fragment aligned with that id format.

## Implementation Plan

### Implementation Tasks

_Format: outcome + context line (constraints, `file#symbol` pattern reference) + behavioral Verify. Task titles describe state-of-the-world outcomes – avoid implementation verbs like `Replace`, `Refactor`, `Update`, `Modify`, `Add to`._

- [ ] **TI01** Successful Todo deletes return the current sidebar incomplete count for the owning TodoList
  - Follow `src/app/routes/todos.py#toggle_todo` and `src/app/routes/todos.py#_get_list_todo_count`; the successful path in `delete_todo` must preserve current `404` and `403` behavior while including the post-delete incomplete count for the deleted Todo's `TodoList`
  - **Verify**: `Test: DELETE /api/todos/{todo_id} for an incomplete Todo returns 200, the response body contains 'id="list-<list_id>-count"' and 'hx-swap-oob="true"', the rendered count is decremented, and the Todo no longer exists in the database`

- [ ] **TI02** Delete-response OOB markup matches the existing sidebar badge contract
  - Follow `src/app/templates/partials/todo_item_with_oob.html` and `src/app/templates/partials/todo_list_item.html`; reuse or align any delete-specific partial so the delete response targets the existing sidebar badge anchor without introducing a second contract
  - **Verify**: `Test: the successful delete response contains exactly one out-of-band badge fragment with 'id="list-<list_id>-count"' and 'hx-swap-oob="true"' while the client still removes '#todo-<todo_id>' via the current HTMX 'delete' swap`

- [ ] **TI03** Regression coverage distinguishes incomplete and completed Todo deletes
  - Extend `tests/test_todos.py` next to existing toggle and delete coverage; include one case for deleting an incomplete Todo and one for deleting a completed Todo so the badge delta is asserted, not inferred
  - **Verify**: `uv run pytest tests/test_todos.py -k "delete_todo" passes, and the delete-path assertions fail if the response omits the OOB fragment or decrements the badge for a completed Todo`

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. **Leave empty** when this is sufficient; fill only when the test approach is non-obvious – level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. **Leave empty** when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.

- Run the app, delete one incomplete Todo and one completed Todo in the browser, and confirm the Todo row disappears while the sidebar badge changes only for the incomplete delete without a full page reload.

### Execution Contract
> Generic exec-spec discipline – task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy – is enforced by exec-spec. **Leave empty** when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. **Leave empty** when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


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
