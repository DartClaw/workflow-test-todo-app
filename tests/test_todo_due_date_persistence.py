"""Regression tests for edit-dialog due-date persistence."""

from datetime import datetime

from app.database import Todo


def _create_todo_with_due_date(db_session, test_list, due_date):
    todo = Todo(
        list_id=test_list.id,
        title="Original",
        note="Has a due date",
        due_date=due_date,
        priority="medium",
        position=1,
    )
    db_session.add(todo)
    db_session.commit()
    return todo


def test_update_todo_persists_due_date_from_edit_dialog(authenticated_client, test_todo, db_session):
    """Updating a todo with a date-only value persists and returns reopen metadata."""
    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Test Todo",
            "note": "A test note",
            "due_date": "2025-12-31",
            "priority": "high",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date="2025-12-31"' in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is not None
    assert test_todo.due_date.date().strftime("%Y-%m-%d") == "2025-12-31"


def test_update_todo_replaces_existing_due_date(authenticated_client, test_list, db_session):
    """Editing an existing date with a different valid date replaces the persisted value."""
    todo = _create_todo_with_due_date(db_session, test_list, datetime(2025, 12, 31, 0, 0))

    response = authenticated_client.put(
        f"/api/todos/{todo.id}",
        data={
            "title": "Original",
            "note": "Has a due date",
            "due_date": "2026-01-01",
            "priority": "medium",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date="2026-01-01"' in response.content

    db_session.refresh(todo)
    assert todo.due_date is not None
    assert todo.due_date.date().strftime("%Y-%m-%d") == "2026-01-01"


def test_update_todo_clears_due_date_when_empty(authenticated_client, test_list, db_session):
    """Submitting an empty due-date value clears an existing due date."""
    todo = _create_todo_with_due_date(db_session, test_list, datetime(2026, 1, 1, 0, 0))

    response = authenticated_client.put(
        f"/api/todos/{todo.id}",
        data={
            "title": "Original",
            "note": "Has a due date",
            "due_date": "",
            "priority": "medium",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date=""' in response.content
    assert b'class="todo-due-date' not in response.content
    assert b"Jan 01, 2026" not in response.content

    db_session.refresh(todo)
    assert todo.due_date is None
