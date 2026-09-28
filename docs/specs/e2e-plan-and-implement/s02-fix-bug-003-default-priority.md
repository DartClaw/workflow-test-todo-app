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

- The shared `partials/todo_item.html` already renders each todo's priority badge and is included by `todo_list_content.html`; no template change was necessary. The implementation sets quick-add priority to `low` and extends the existing route regression test to prove both persistence and rendered output.
- The supplied FIS has no task IDs or runnable Proof/Verify entries, so execution used the existing `test_create_todo` target as the regression proof and records no completed task IDs.
- Full-suite verification remains externally red because `tests/test_todos.py::TestTodos::test_update_todo` fails on the pre-existing BUG-002 due-date persistence defect; 57 other tests pass. Routing: NOTICED BUT NOT TOUCHING (S01).
