# Fix BUG-002 — persist edited due dates

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Close BUG-002 — a due date set in the edit dialog is lost after save. The update handler must read the submitted due-date field and persist it on the todo, and the edit dialog must pre-fill the current value.

## Acceptance Scenarios

- Editing a todo, setting a due date, and saving persists the due date so it is still present after the list re-renders.
- The edit dialog pre-populates the existing due date when reopened.

## Implementation Plan

- In src/app/routes/todos.py, read the due-date form field in the update handler and store it on the todo.
- In src/app/templates/app.html, bind the edit dialog's due-date input to the todo's current value.

## Implementation Observations

- The existing todo partial exposes `format_date_input(todo.due_date)` through the todo data attribute, and `openEditTodoDialog` assigns that value to the edit input. The prefill acceptance path therefore required no additional `app.html` change; a regression test now proves the rendered value is present.
- The update handler now parses the HTML date input format (`YYYY-MM-DD`) and persists it as the existing naive `datetime` storage type.
