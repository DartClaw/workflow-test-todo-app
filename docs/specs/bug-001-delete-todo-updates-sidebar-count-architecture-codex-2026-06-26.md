# Architecture Review – bug-001-delete-todo-updates-sidebar-count

Scope: `src/app/routes/todos.py`, `src/app/templates/partials/todo_deleted_oob.html`, `src/app/templates/partials/todo_list_item.html`, `src/app/static/js/app.js`, `tests/test_todos.py`, `tests/test_integration.py`

## Decision Trace
Written by review mode under tier-2 spec-directory match (`docs/specs/...`).

## Executive Summary
1. Scope was limited to the current BUG-001 spec surface and its caller-facing HTMX contract.
2. No architectural findings were identified in the changed path; delete count refresh is implemented via the same OOB pattern already used by toggle.
3. Primary recommendation remains unchanged: keep server-authoritative count recomputation in the delete success response and avoid client-side count guessing.
4. No additional decomposition or governance changes are warranted by this change.

## How to Read This Report
- Severity only reflects this review pass: `INFO | LOW | MEDIUM | HIGH | CRITICAL`.
- Findings are omitted when no evidence-backed issue is present.
- The reviewed boundary is HTMX row-delete + sidebar count OOB behavior; unrelated packages (auth, persistence model evolution, session architecture) were intentionally out of scope.

## Findings
No findings.

## Architecture Assessment by Dimension
- **Coupling**: Existing boundary between `delete_todo` success response and HTMX delete client contract is explicit and stable (`swap: 'delete'` + OOB fragment).
- **Consistency**: OOB success response keeps `id="list-<list_id>-count"` contract unchanged, preserving current DOM target assumptions.
- **Test alignment**: Integration and route tests cover success count updates and failure-path non-inclusion, matching OC01-OC03, OC04 acceptance intent.
- **Failure handling**: Status-only 403/404 paths are intentionally kept, consistent with spec scope.

## Proposed Fitness Functions
- No new fitness functions required for this scope; existing test coverage in `tests/test_todos.py` and `tests/test_integration.py` already enforces the required OOB success/failure contract.
