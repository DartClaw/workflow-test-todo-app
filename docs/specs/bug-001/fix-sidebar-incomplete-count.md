# Fix sidebar incomplete-count on todo deletion

## Feature Overview and Goal

**Intent**: Close BUG-001 — the sidebar incomplete-count is not updated when a todo is deleted; the delete response must refresh the same count via the existing HTMX out-of-band swap pattern.

## Acceptance Scenarios

- When a todo is deleted, the sidebar incomplete-count decreases via an out-of-band swap, mirroring how toggle_todo updates it.

## Implementation Plan

- Update the delete_todo handler to return the same out-of-band count fragment that toggle_todo returns.

## Implementation Observations

### Run: 2026-08-28T06:11:59Z – observations

#### NOTICED BUT NOT TOUCHING

- `tests/test_todos.py::TestTodos::test_create_todo` fails because the created Todo priority is `None` instead of `low`; unrelated to BUG-001.
- `tests/test_todos.py::TestTodos::test_update_todo` fails because the submitted date format is not parsed; unrelated to BUG-001.
