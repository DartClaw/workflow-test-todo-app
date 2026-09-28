# Fix sidebar incomplete-count on todo deletion

## Feature Overview and Goal

**Intent**: Close BUG-001 — the sidebar incomplete-count is not updated when a todo is deleted; the delete response must refresh the same count via the existing HTMX out-of-band swap pattern.

## Acceptance Scenarios

- When a todo is deleted, the sidebar incomplete-count decreases via an out-of-band swap, mirroring how toggle_todo updates it.

## Implementation Plan

- Update the delete_todo handler to return the same out-of-band count fragment that toggle_todo returns.

## Implementation Observations

- The repository contains no adjacent `plan.json`, and this FIS has no `**Plan**:` or `**Story-ID**:` provenance headers; execution proceeded from the explicit FIS intent and the existing delete-specific OOB partial.
- Added a regression test covering the deleted todo's list count response. The focused proof passes: `uv run pytest tests/test_todos.py::TestTodos::test_delete_todo_updates_incomplete_count_oob -q` -> exit=0, 1 passed.
- Full-suite baseline has two unrelated failures: `TestTodos.test_create_todo` (BUG-003 default priority) and `TestTodos.test_update_todo` (BUG-002 due-date parsing). Routing: NOTICED BUT NOT TOUCHING.
