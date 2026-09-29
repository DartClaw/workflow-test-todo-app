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

- The update handler already read the submitted field, but parsed it as a datetime (`%Y-%m-%dT%H:%M`) while the HTML date input submits a date (`%Y-%m-%d`). The fix aligns parsing with the existing input and template formatting; the dialog prefill was already wired through `todo_item.html` data attributes and `app.js`.
