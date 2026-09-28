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

- Quick-add returns `partials/todo_item_with_oob.html`, which includes `partials/todo_item.html`; that shared partial already renders the priority badge and is also used by `todo_list_content.html`. The implementation therefore sets the missing persisted default and adds a regression assertion for the rendered `Low` label without duplicating template markup.
- The full suite has one unrelated pre-existing failure in `TestTodos.test_update_todo`: due-date persistence is the scope of S01/BUG-002. S02's focused proof passes; the baseline failure is external context and non-blocking for this story.
