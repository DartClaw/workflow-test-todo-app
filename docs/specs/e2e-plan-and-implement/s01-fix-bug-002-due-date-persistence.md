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

- The update handler already read the submitted `due_date` field, but parsed it as `YYYY-MM-DDTHH:MM` while the edit dialog submits the HTML date-input format `YYYY-MM-DD`. The fix aligns parsing with the existing browser control.
- The edit dialog's current-value binding was already implemented through `data-todo-due-date` in `partials/todo_item.html` and `openEditTodoDialog` in `static/js/app.js`; no additional `app.html` change was required.
- The FIS contains no declared task IDs, runnable Proof lines, or Final Validation Checklist. The regression test added for BUG-002 is the executable story proof.
