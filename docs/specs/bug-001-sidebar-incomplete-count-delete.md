# BUG-001 Sidebar Incomplete Count Updates After Todo Delete

## Feature Overview and Goal

Fix the `BUG-001` delete regression so removing a `Todo` updates the sidebar incomplete-count immediately, without waiting for a full page reload. The change must follow the app's established HTMX OOB swap pattern used by `toggle_todo()`.

> **Technical Research**: [.technical-research.md](./.technical-research.md) _(codebase patterns, architecture analysis, API research)_

## Required Context

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |

### From `CLAUDE.md` – "The stack — and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> **HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:
>
> - Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
> - Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.
> - Redirects for HTMX requests use the `HX-Redirect` response header (not a 302), because HTMX swaps fragments – a normal redirect would replace the fragment, not the page. See the 401 handler in `src/app/main.py` and the post-login flow in `src/app/routes/auth.py` for the pattern.
> - **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### From `docs/UBIQUITOUS_LANGUAGE.md` – "UI / HTMX Concepts"
<!-- source: docs/UBIQUITOUS_LANGUAGE.md#ui--htmx-concepts -->
<!-- extracted: 5cc022878c28af49d723f55ca70343f0b979ec0d -->
> | OOB Swap | Out-of-Band HTMX swap – updates a region outside the main target in one response | side-update, secondary update | Web |

## Deeper Context

- `CLAUDE.md#visual-validation-workflow` – project-specific expectation for verifying multi-region HTMX updates after UI changes.
- `CLAUDE.md#tests` – testing fixture model for authenticated route coverage and in-memory DB isolation.

## Success Criteria (Must Be TRUE)

- [ ] Deleting an incomplete `Todo` returns HTML that updates the matching sidebar incomplete-count via `hx-swap-oob`, and the rendered count reflects the post-delete database state immediately.
- [ ] Deleting a completed `Todo` still returns the sidebar count OOB fragment, but the rendered incomplete-count value remains unchanged.
- [ ] Existing delete semantics remain intact: the `Todo` is removed from persistence, and missing or unauthorized delete attempts do not emit a misleading success OOB count update.

### Health Metrics (Must NOT Regress)

- [ ] `uv run pytest tests/test_todos.py tests/test_integration.py` passes after the change.
- [ ] The existing sidebar count target contract (`id="list-<list_id>-count"`) remains unchanged.
- [ ] No broader sidebar rerender or client-side count bookkeeping is introduced.

## Scenarios

### Delete Incomplete Todo Refreshes Sidebar Count

- **Given** an authenticated user viewing a `TodoList` whose sidebar badge shows one incomplete `Todo`
- **When** the user deletes that incomplete `Todo`
- **Then** the delete response includes an `hx-swap-oob` fragment targeting `list-<list_id>-count`, and the fragment renders `0`

### Delete Completed Todo Preserves Incomplete Count

- **Given** an authenticated user viewing a `TodoList` with one incomplete `Todo` and one completed `Todo`
- **When** the user deletes the completed `Todo`
- **Then** the delete response still includes the `list-<list_id>-count` OOB fragment, and the rendered count remains `1`

### Delete Failure Does Not Fabricate Sidebar Update

- **Given** a delete request for a missing `Todo` or a `Todo` owned by another user
- **When** the server rejects the delete request
- **Then** the response remains a failure response, and it does not include `hx-swap-oob` count markup that would imply a successful sidebar refresh

## Scope & Boundaries

### In Scope

- Return the sidebar incomplete-count OOB fragment from the successful todo delete flow.
- Reuse the existing sidebar count target and count-calculation pattern already used for `Todo` completion toggles.
- Add regression coverage for delete responses affecting incomplete-count behavior.

### What We're NOT Doing

- Changing how the client removes the deleted todo row – BUG-001 is only about the missing sidebar count refresh.
- Rebuilding delete flows around JSON or custom JavaScript state – the project is HTMX-first and already has a server-rendered OOB pattern.
- Refactoring unrelated authorization or error-partial behavior in delete routes – that is separate from this defect's scope.
- Changing `TodoList` count rendering IDs or sidebar markup structure – downstream HTMX targets depend on the existing `list-<list_id>-count` contract.

### Agent Decision Authority

- **Autonomous**: Reuse the existing count helper, existing delete-specific partial, and existing test style if they satisfy the scenarios and success criteria.
- **Escalate**: Any change that would require altering delete interaction semantics beyond sidebar count refresh, such as changing HTTP failure contracts or replacing the current HTMX delete wiring.

## Architecture Decision

**We will**: return a successful delete response as a server-rendered OOB partial containing the recalculated sidebar incomplete-count, reusing the established count helper and existing delete-specific partial – instead of introducing client-side count bookkeeping or rerendering the full sidebar.

## Technical Overview

### UI/UX Design

The visible behavior change is immediate sidebar badge refresh after deleting a `Todo`. No new controls, dialogs, or layouts are introduced.

### Integration Points

The change sits entirely within the `Todo` delete route and the existing sidebar badge DOM target. Tests must prove the route returns the expected OOB fragment and that the database state and rendered count stay aligned.

## Code Patterns & External References

```text
# type | path/url | why needed
file   | src/app/routes/todos.py:33-37            | Existing incomplete-count helper to reuse
file   | src/app/routes/todos.py:243-283          | Canonical toggle response pattern with count recompute + OOB partial
file   | src/app/routes/todos.py:286-306          | Defective delete route to bring into alignment
file   | src/app/templates/partials/todo_item_with_oob.html:1-4 | Existing OOB fragment structure for count updates
file   | src/app/templates/partials/todo_deleted_oob.html:1-2   | Existing delete-specific OOB fragment to reuse
file   | src/app/templates/partials/todo_list_item.html:20      | Sidebar count DOM target contract
file   | tests/test_todos.py:84-92                | Current delete route regression coverage baseline
file   | tests/test_integration.py:163-180        | Existing OOB assertion style for count updates
```

## Constraints & Gotchas

- **Constraint**: The app is HTMX-first and server-rendered – Workaround: return an HTML partial, not JSON, from successful delete flow.
- **Avoid**: Recomputing the badge count in browser code – Instead: use the same server-side `_get_list_todo_count()` pattern already trusted for toggles.
- **Critical**: The sidebar badge target is keyed by `list-<list_id>-count` – Must handle by preserving that exact ID in the delete OOB fragment.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Successful `Todo` deletes emit the refreshed sidebar incomplete-count via OOB swap
  - Align `src/app/routes/todos.py:286-306` with the existing pattern at `src/app/routes/todos.py:243-283`; reuse `src/app/templates/partials/todo_deleted_oob.html:1-2` and preserve the `list-<list_id>-count` target from `src/app/templates/partials/todo_list_item.html:20`.
  - **Verify**: `uv run pytest tests/test_todos.py -k delete` proves deleting an incomplete todo returns `200`, removes the todo from the DB, includes `hx-swap-oob`, and renders the exact target id/value pair for the updated count.

- [ ] **TI02** Delete regression coverage proves completed-todo and failure-path behavior stays correct
  - Extend the current delete/OOB test style from `tests/test_todos.py:84-92` and `tests/test_integration.py:163-180`; this task depends on TI01's successful delete response contract.
  - **Verify**: `uv run pytest tests/test_todos.py tests/test_integration.py` proves deleting a completed todo keeps the rendered incomplete-count unchanged and missing/unauthorized delete responses do not contain `hx-swap-oob`.

### Testing Strategy

- [TI01] Scenario: Delete Incomplete Todo Refreshes Sidebar Count → add a delete-route test that asserts DB deletion plus exact OOB target markup and updated count value.
- [TI02] Scenario: Delete Completed Todo Preserves Incomplete Count → add a test with one completed and one incomplete todo, then assert the delete response still renders the sidebar badge with the unchanged incomplete count.
- [TI02] Scenario: Delete Failure Does Not Fabricate Sidebar Update → add assertions that missing or unauthorized delete responses stay non-successful and omit `hx-swap-oob`.

### Validation

- If the route change modifies rendered HTML, visually confirm the sidebar badge updates immediately after deleting both an incomplete and a completed `Todo`.

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
