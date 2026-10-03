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

- The list content already includes `partials/todos_list.html`, which includes the shared `partials/todo_item.html`; that shared item already renders the priority badge and `priority-*` class. The implementation therefore only needed to set `priority="low"` in quick-add creation, plus regression assertions for persistence and rendered output.
- NOTICED BUT NOT TOUCHING: the full suite has a pre-existing S01 due-date failure in `tests/test_todos.py::TestTodos::test_update_todo`; it is outside BUG-003 scope.
