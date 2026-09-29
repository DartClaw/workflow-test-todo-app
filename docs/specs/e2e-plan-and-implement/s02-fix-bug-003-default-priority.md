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

- The list content template delegates todo rendering to `partials/todos_list.html`, which includes `partials/todo_item.html`; the priority badge already renders there. The implementation therefore assigns `low` in the quick-add route and extends the existing route test to assert the rendered `Low` badge.
- The existing `test_create_todo` test was the defect reproduction: it failed because the persisted priority was `None`.
- The full suite has one unrelated baseline failure in `TestTodos.test_update_todo` for BUG-002 due-date persistence; it is external context and was not changed by S02.
