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

- The edit dialog's due-date input was already populated by `openEditTodoDialog` in `src/app/static/js/app.js`, using the formatted value emitted by `src/app/templates/partials/todo_item.html`; no additional `app.html` change was necessary.
- The update endpoint received the browser's date-only value but parsed only a date-time format. It now parses `YYYY-MM-DD`, matching the `type="date"` input and preserving the existing HTML partial re-render.
- NOTICED BUT NOT TOUCHING: quick-add todos still have a missing default priority; this is BUG-003 and belongs to sibling story S02.
- ASSUMPTION: The missing `docs/TESTING-STRATEGY.md` does not block this focused regression test – the existing pytest route test conventions and `docs/KEY_DEVELOPMENT_COMMANDS.md` remain authoritative for this fixture.
