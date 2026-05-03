# BUG-001 – Sidebar incomplete-count updates on todo delete

## Feature Overview and Goal
Fix the `BUG-001` regression where deleting a Todo removes the row but leaves the sidebar incomplete-count stale until a full reload. The delete flow must follow the existing HTMX OOB swap pattern already used for create and toggle so the sidebar stays consistent in the same response.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – "The stack – and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "UI / HTMX Concepts"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | OOB Swap | Out-of-Band HTMX swap – updates a region outside the main target in one response | side-update, secondary update | Web |

## Deeper Context

- `CLAUDE.md#visual-validation-workflow` – project-specific visual verification steps for HTMX interactions and OOB swaps.
- `docs/guidelines/CRITICAL-RULES-AND-GUARDRAILS.md#core-behavioral-rules` – UI changes must be verified visually and backed by actual validation.

## Success Criteria (Must Be TRUE)
- [ ] Deleting an incomplete Todo updates the sidebar incomplete-count for that TodoList in the same HTMX response, with no full page reload.
- [ ] Deleting a completed Todo leaves the sidebar incomplete-count unchanged while still removing the Todo from the UI and database.
- [ ] Todo delete authorization and not-found behavior remain unchanged: unauthorized deletes still return `403`, missing Todos still return `404`, and neither path emits a misleading count update.
- [ ] Automated tests prove the delete response contains the expected OOB swap markup and the count values are correct for incomplete and completed delete cases.

### Health Metrics (Must NOT Regress)
- [ ] Existing todo CRUD and access-control tests continue to pass.
- [ ] The existing delete confirmation dialog and HTMX `DELETE` flow remain unchanged for users.
- [ ] No new JSON endpoint, client-side counter bookkeeping, or cross-route refactor is introduced.

## Scenarios

### Delete an incomplete Todo from the current list
- **Given** an authenticated User viewing a TodoList whose sidebar badge currently shows `1` incomplete Todo
- **When** the User confirms deletion of that incomplete Todo
- **Then** the Todo is removed and the delete response includes an OOB swap that updates `#list-{list_id}-count` to `0` in the same HTMX interaction

### Delete a completed Todo
- **Given** an authenticated User viewing a TodoList that contains one completed Todo and one incomplete Todo, and the sidebar badge shows `1`
- **When** the User confirms deletion of the completed Todo
- **Then** the completed Todo is removed and the delete response updates `#list-{list_id}-count` to `1`, preserving the incomplete-count

### Delete a Todo from another user’s list
- **Given** an authenticated User targets a Todo owned by a different User
- **When** the delete request is submitted
- **Then** the route returns `403` and no OOB count fragment is emitted

### Delete a Todo that no longer exists
- **Given** an authenticated User requests deletion for a Todo id that is not present
- **When** the delete request is submitted
- **Then** the route returns `404` and no sidebar count update is produced

## Scope & Boundaries

### In Scope
- Align the Todo delete route with the existing server-rendered HTMX OOB swap pattern already used by Todo create and toggle.
- Reuse the existing sidebar count DOM contract so delete updates the correct `TodoList` badge without changing the client-side delete flow.
- Add regression coverage for delete response markup, count correctness, and preserved error behavior.

### What We're NOT Doing
- Change the delete confirmation dialog or `htmx.ajax('DELETE', ...)` target/swap configuration in `app.js` – the bug is in the server response contract, not the client trigger.
- Rework sidebar rendering or count calculation strategy across the app – this fix stays within the existing `_get_list_todo_count()` helper and OOB partial pattern.
- Refactor create/toggle/delete into a new abstraction – the defect is narrow and should be fixed surgically.
- Change auth/session behavior or convert `403` / `404` deletes into HTML error partials – current response semantics stay intact for this bug fix.

### Agent Decision Authority
- **Autonomous**: Reuse the existing delete-specific OOB partial if it cleanly satisfies the contract.
- **Escalate**: Any change that would require altering the client-side delete swap semantics, sidebar DOM ids, or broader HTMX interaction model.

## Architecture Decision

**We will**: keep todo delete on the existing HTMX `DELETE` path and return a server-rendered OOB count fragment after successful deletion, using the established sidebar count contract, over client-side counter bookkeeping or a broader response refactor.

## Technical Overview

### UI/UX Design
The visible behavior does not change except that the sidebar badge updates immediately after a Todo is deleted. The existing delete confirmation dialog, row removal animation behavior, and list navigation remain as-is.

### Data Models
No schema or model changes are needed. The count continues to mean "number of incomplete Todos in a TodoList" and must be derived from persisted Todo completion state after deletion.

### Integration Points
The delete route must stay compatible with the current HTMX call in `src/app/static/js/app.js`, which targets `#todo-{id}` with `swap: delete`. That means the success response only needs the OOB sidebar update fragment; the row deletion remains driven by the existing client-side HTMX swap behavior.

## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:33-37             | Existing helper for incomplete-count calculation
file   | src/app/routes/todos.py:125-132           | Create Todo response pattern with count + OOB partial
file   | src/app/routes/todos.py:276-283           | Toggle Todo response pattern with count + OOB partial
file   | src/app/routes/todos.py:286-306           | Delete Todo route to align with existing OOB behavior
file   | src/app/templates/partials/todo_item_with_oob.html:1-4 | Canonical Todo mutation response including sidebar OOB swap
file   | src/app/templates/partials/todo_deleted_oob.html:1-2   | Existing delete-only OOB partial suited to this fix
file   | src/app/templates/partials/todo_list_item.html:20      | Sidebar count DOM id contract the OOB swap must target
file   | src/app/static/js/app.js:166-173          | Current HTMX delete request target and swap behavior
file   | tests/test_todos.py:84-92                 | Existing delete coverage to extend
```

## Constraints & Gotchas
- **Constraint**: Todo delete currently uses HTMX `swap: delete` on `#todo-{id}` – Workaround: return only the sidebar OOB fragment on success, because the row removal is already handled by the client-side swap.
- **Avoid**: Recomputing the count before the delete is committed – Instead: delete first, commit, then derive the incomplete-count from current persisted state.
- **Critical**: The sidebar badge id is `list-{list_id}-count` – Must handle by: rendering that exact id in the OOB fragment so HTMX updates the correct TodoList badge.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful Todo deletes emit the same server-authoritative incomplete-count contract used by other Todo mutations
  - Update the successful delete path in `src/app/routes/todos.py:286-306` to recompute the incomplete-count after commit and return a rendered partial, preserving the current `403` / `404` response branches unchanged; follow the count pattern at `src/app/routes/todos.py:125-132` and `src/app/routes/todos.py:276-283`.
  - **Verify**: `uv run pytest tests/test_todos.py -k "delete_todo"` proves successful delete responses return HTTP 200 and include `hx-swap-oob="true"` with the correct `list-{list_id}-count` value while unauthorized/missing deletes still return 403/404.`

- [ ] **TI02** The delete response uses the existing sidebar OOB fragment without changing the client-side delete interaction
  - Reuse the existing partial contract at `src/app/templates/partials/todo_deleted_oob.html:1-2` or an equivalent server-rendered fragment that targets `src/app/templates/partials/todo_list_item.html:20`; do not change `src/app/static/js/app.js:166-173`.
  - **Verify**: `Response-body assertions show successful delete responses contain `<span id="list-{list_id}-count" hx-swap-oob="true">` and no JavaScript changes are required for the badge to refresh.`

- [ ] **TI03** Regression coverage proves count correctness for incomplete and completed delete cases
  - Extend `tests/test_todos.py:84-92` with delete-focused cases that distinguish incomplete from completed Todos and assert both database deletion and exact OOB count output; use authenticated fixtures from `tests/conftest.py:70-113`.
  - **Verify**: `uv run pytest tests/test_todos.py` passes with cases that fail if an incomplete delete does not decrement the count or a completed delete incorrectly changes it.`

### Testing Strategy
- [TI01, TI02] Scenario: Delete an incomplete Todo from the current list → test deletes an incomplete Todo and asserts the response body contains `hx-swap-oob="true"` plus the exact `id="list-{list_id}-count">0<` badge update.
- [TI01, TI03] Scenario: Delete a completed Todo → test deletes a completed Todo from a list that still has one incomplete Todo and asserts the response body updates the badge to `1`.
- [TI01, TI03] Scenario: Delete a Todo from another user’s list → test keeps current `403` behavior and asserts the response body does not contain `hx-swap-oob="true"`.
- [TI01, TI03] Scenario: Delete a Todo that no longer exists → test keeps current `404` behavior and asserts the response body is empty of sidebar count markup.

### Validation
- Run `uv run pytest tests/test_todos.py` for focused regression coverage.
- Run `uv run pytest` before closing implementation to confirm no broader Todo behavior regressed.
- Perform the project visual validation flow in `CLAUDE.md#visual-validation-workflow`: delete one incomplete Todo and one completed Todo in the browser and confirm the sidebar badge updates immediately without reloading.

### Execution Contract
- Implement tasks in listed order. Each **Verify** line must pass before proceeding to the next task.
- Prescriptive details (column names, format strings, file paths, error messages) are exact – implement them verbatim.
- Proactively use sub-agents for non-coding needs: documentation lookup, architectural advice, UX/UI guidance, build troubleshooting, research – spawn in background when possible and do not block progress unnecessarily.
- After all tasks: run the applicable project validation gates for the feature – build/tests/lint-analysis where those checks exist and are relevant – and keep `rg "TODO|FIXME|placeholder|not.implemented" <changed-files>` clean.
- Mark task checkboxes immediately upon completion – do not batch.

## Final Validation Checklist

- [ ] **All success criteria** met
- [ ] **All tasks** fully completed, verified, and checkboxes checked
- [ ] **No regressions** or breaking changes introduced
- [ ] **UI verified** to match requirements

## Implementation Observations

_No observations recorded yet._
