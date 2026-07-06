# BUG-001 – Sidebar incomplete-count updates after todo deletion

## Feature Overview and Goal

**Intent**: Keep the sidebar's incomplete-count trustworthy during todo deletion so users see list state update immediately without relying on a full page reload.

**Expected Outcomes**:

- [OC01] Deleting an incomplete `Todo` updates the matching `TodoList` sidebar badge immediately in the same HTMX interaction.
- [OC02] Successful delete responses follow the existing OOB swap contract already used by completion toggles, keeping server-rendered UI state authoritative.
- [OC03] Delete authorization and not-found behavior stay unchanged while the sidebar count fix is added.


## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `AGENTS.md` – "The stack – and why it matters for edits"
<!-- source: AGENTS.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.
> - Redirects for HTMX requests use the `HX-Redirect` response header (not a 302), because HTMX swaps fragments — a normal redirect would replace the fragment, not the page. See the 401 handler in `src/app/main.py` and the post-login flow in `src/app/routes/auth.py` for the pattern.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.


## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts` – Canonical terms for `Partial`, `OOB Swap`, and `Error Partial`; use these terms consistently in the spec and tests.
- `docs/STACK.md#frameworks--libraries` – Confirms the FastAPI + Jinja2 + HTMX stack baseline for HTML-fragment route behavior and test expectations.


## Acceptance Scenarios

- [ ] **S01 [OC01,OC02] [TI01,TI02] Incomplete todo deletion decrements the sidebar badge without a reload**
  - **Given** a `TodoList` with two incomplete `Todo` items and the sidebar badge rendered as `id="list-{list_id}-count"` with value `2`
  - **When** the user deletes one of those incomplete todos through `DELETE /api/todos/{todo_id}`
  - **Then** the response returns `200`, includes `hx-swap-oob="true"`, and returns `<span id="list-{list_id}-count">1</span>` so the sidebar badge updates in the same HTMX interaction

- [ ] **S02 [OC01,OC02] [TI01,TI02] Completed todo deletion preserves the incomplete-count contract**
  - **Given** a `TodoList` with one incomplete `Todo`, one completed `Todo`, and the sidebar badge value `1`
  - **When** the user deletes the completed todo
  - **Then** the response still includes `hx-swap-oob="true"` and returns `<span id="list-{list_id}-count">1</span>`, proving successful delete responses keep a uniform OOB swap contract even when the numeric count does not change

- [ ] **S03 [OC03] [TI03] Missing or unauthorized deletes do not widen the success contract**
  - **Given** a delete request for a missing todo or a todo outside the current user's ownership
  - **When** `DELETE /api/todos/{todo_id}` is submitted
  - **Then** the route keeps returning `404` or `403` respectively, no todo owned by the requester is removed, and no success-only OOB count fragment is emitted


## Structural Criteria

- [ ] The sidebar badge target remains the existing `list-{list_id}-count` contract shared with `partials/todo_list_item.html`.
- [ ] Delete count updates use the same incomplete-count rule as the rest of the todo routes, excluding completed todos from the badge total.
- [ ] Existing toggle-count regression coverage remains valid while delete-path regression coverage is added.


## Scope & Boundaries

### Work Areas
- `src/app/routes/todos.py#delete_todo` success response contract
- `src/app/routes/todos.py#_get_list_todo_count` incomplete-count source of truth
- `src/app/templates/partials/todo_deleted_oob.html` delete OOB fragment
- `tests/test_todos.py` route-level delete regression coverage
- `tests/test_integration.py` HTMX response integration coverage

### What We're NOT Doing
- Changing the sidebar badge markup contract in `partials/todo_list_item.html` – the fix must target the existing `list-{list_id}-count` surface
- Introducing JSON delete responses or client-side recounting – the app is HTMX-first and server-rendered
- Altering delete authorization or missing-todo status handling – BUG-001 is about stale success-state UI only
- Broadening into other known defects such as due-date persistence or priority defaults – those are separately tracked as `BUG-002` and `BUG-003`


## Architecture Decision

**Approach**: Keep `delete_todo` on the existing HTMX fragment contract by returning an HTML partial that emits the sidebar badge OOB swap using the same incomplete-count calculation already used by `toggle_todo`.
**Why this over alternatives**: It matches the documented OOB idiom, preserves server-side UI authority, and fixes the bug without adding client-side state logic or new response formats.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. **Leave empty** when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor or url                               | why needed (intent)
file   | src/app/routes/todos.py#toggle_todo             | OOB response pattern – count is recalculated server-side and returned in the success fragment
file   | src/app/routes/todos.py#delete_todo             | Delete route contract – keep 403/404 behavior while changing only the success payload
file   | src/app/routes/todos.py#_get_list_todo_count    | Incomplete-count rule – only todos with is_completed == False contribute
file   | src/app/templates/partials/todo_item_with_oob.html:1-4 | Existing sidebar OOB markup contract used by toggle responses
file   | src/app/templates/partials/todo_deleted_oob.html:1-2   | Delete-specific OOB partial already present in the repo
file   | tests/conftest.py#authenticated_client          | Authenticated in-memory test harness for route coverage
```


## Constraints & Gotchas

- **Constraint**: Successful HTMX delete responses must remain HTML fragments, not bare `Response(status_code=200)` values or JSON payloads – Workaround: render the delete OOB partial on success
- **Avoid**: Duplicating incomplete-count logic in the client or in tests – Instead: use `src/app/routes/todos.py#_get_list_todo_count` as the server-side source of truth
- **Critical**: Deleting a completed todo should still emit the success OOB fragment even when the returned count value is unchanged – Must handle by: keeping the OOB contract uniform across successful delete cases


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful todo deletes return the existing sidebar OOB update contract
  - Follow `src/app/routes/todos.py#toggle_todo` for success-payload shape and use `src/app/templates/partials/todo_deleted_oob.html:1-2` from `src/app/routes/todos.py#delete_todo`; keep the current `403` and `404` branches unchanged
  - **Verify**: `DELETE /api/todos/{todo_id}` for one of two incomplete todos returns `200`, includes `hx-swap-oob="true"`, and returns `<span id="list-{list_id}-count">1</span>`

- [ ] **TI02** Delete responses preserve the sidebar's incomplete-count semantics across todo states
  - Reuse `src/app/routes/todos.py#_get_list_todo_count` so the value returned to `list-{list_id}-count` excludes completed todos and reflects committed database state after deletion
  - **Verify**: deleting a completed todo from a list with one incomplete todo returns `hx-swap-oob="true"` and `<span id="list-{list_id}-count">1</span>` while the deleted row no longer exists in the database

- [ ] **TI03** Regression tests prove delete fixes without weakening existing count-update behavior
  - Extend `tests/test_todos.py` and `tests/test_integration.py` using `tests/conftest.py#authenticated_client`; cover incomplete-delete decrement, completed-delete no-change, and `403`/`404` delete responses that do not emit a success OOB fragment
  - **Verify**: automated tests assert successful deletes include `hx-swap-oob="true"` with the `list-{list_id}-count` target, failed deletes omit that fragment, and the existing toggle-count OOB assertions still pass

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

Discovered Requirements entries use this shape:

- **Title**: short imperative phrase
- **Description**: 1-2 sentences on the discovered requirement
- **Rationale**: why it was missed in original spec
- **Interpretation** (AUTO_MODE only): the conservative interpretation chosen and why
- **Traced from**: task ID where the discovery occurred
- **Date**: YYYY-MM-DD

_No observations recorded yet._
