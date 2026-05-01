# Architecture Review: BUG-001

Mode: `review` · Auto mode · Scope: `src/app/routes/todos.py`, `tests/test_todos.py` (current-branch changes only)

## Executive Summary
This change is narrowly scoped and preserves the app's HTMX-first partial-response architecture.
No new architectural coupling, cyclic dependency risk, or principle-level violations were introduced by the changed files.
The delete flow now aligns with existing OOB badge-update behavior while keeping failure behavior stable.
Most critical check for this review is consistency of response contracts across error paths, which remains unchanged by this patch.

## How to Read This Report
- **Code level (C4)**: the file- and route-level scope used for this review.
- **OOB swap**: HTMX out-of-band fragment update using `hx-swap-oob="true"`.
- **SDP/SAP/ADP**: package dependency principles (Stable Dependency, Stable Abstractions, Acyclic Dependencies) used for guidance.
- Severity in this report follows `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` from the review calibration references.

## Metrics Dashboard
No package dependency metrics were recomputed because the review was scoped to a two-file change set with no module graph modification.

## Findings
No architecture findings in the changed scope.

## Dependency Graph Notes
- Changed dependency edges remain internal to existing modules (`app.routes.todos` still depends on `app.database`, `app.utils`, and existing template modules as before).
- No new import, service, or storage dependency was added.
- No cycles or principle regressions (ADP/SDP/SAP) were introduced by this patch.

## Proposed Fitness Functions
1. **Template Response Contract Check for todo routes**
   - **Check**: Ensure HTML route mutations return documented partial responses and error responses stay explicit under intentional exception policies.
   - **Stack**: Manual review and targeted tests in `tests/test_todos.py`.
   - **Goal**: Prevent accidental drift toward mixed `Response` vs `TemplateResponse` contracts.

2. **OOB Count-Update Regression Guard**
   - **Check**: For any route that mutates list counts, include tests asserting both updated and unchanged badge scenarios.
   - **Stack**: Automated tests (`authenticated_client`), plus explicit `hx-swap-oob` assertions.
   - **Goal**: Avoid regressions where sidebar aggregate UI state desynchronizes from mutations.
