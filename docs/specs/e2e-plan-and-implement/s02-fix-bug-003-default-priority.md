# Fix BUG-003 — default priority for quick-add todos

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S02

## Feature Overview and Goal

**Intent**: Close BUG-003 — todos created through quick-add have no default priority. Quick-add must assign the same default priority the full add form uses, and the list must render it.

## Acceptance Scenarios

- A todo created via quick-add is assigned the default priority.
- The rendered list shows the priority for a quick-added todo.

## Implementation Plan

- In src/app/routes/todos.py, set the default priority when a quick-add todo is created.
- In src/app/templates/partials/todo_list_content.html, render the todo priority so the default is visible.

## Implementation Observations

- The requested list rendering is already provided by the shared `partials/todo_item.html`,
  which is included by the list content flow and renders the priority badge. Duplicating that
  markup in `todo_list_content.html` would render the priority twice, so the implementation
  keeps the existing rendering path and adds a regression assertion for its response.
- The source FIS has no task IDs, `Proof` targets, `Verify` lines, tagged outcomes, or final
  validation checklist. Execution therefore used the existing quick-add test as the scoped
  regression proof and recorded this authoring gap for re-spec.
- Scoped proof `uv run pytest tests/test_todos.py::TestTodos::test_create_todo -q` passed after
  the fix: 1 passed. The full suite passed 57 tests and has one unrelated failure in
  `TestTodos.test_update_todo` because its `2025-12-31` input is not accepted by the existing
  `YYYY-MM-DDTHH:MM` parser; Routing: NOTICED BUT NOT TOUCHING, external S01 context.
- Independent reviewer subagent was unavailable in this runtime. A self-review of the diff found
  no additional issues; the scoped route, regression assertion, and existing shared rendering
  path are directly connected to the two acceptance scenarios.
