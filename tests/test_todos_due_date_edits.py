"""Regression tests for todo due-date edit behavior."""

from datetime import date, datetime

def _set_due_date(db_session, test_todo, value):
    test_todo.due_date = value
    db_session.add(test_todo)
    db_session.commit()
    db_session.refresh(test_todo)


def test_update_todo_persists_valid_due_date_and_roundtrip(
    authenticated_client, test_todo, db_session
):
    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Updated Title",
            "note": "Updated note",
            "due_date": "2025-12-31",
            "priority": "high",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date="2025-12-31"' in response.content

    db_session.refresh(test_todo)
    assert test_todo.title == "Updated Title"
    assert test_todo.note == "Updated note"
    assert test_todo.due_date == datetime(2025, 12, 31)
    assert test_todo.priority == "high"


def test_update_todo_clears_due_date_when_blank(authenticated_client, test_todo, db_session):
    _set_due_date(db_session, test_todo, datetime(2025, 12, 31))

    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "With cleared due date",
            "note": "",
            "due_date": "",
            "priority": "low",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date=""' in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is None


def test_update_todo_preserves_due_date_on_invalid_input(authenticated_client, test_todo, db_session):
    _set_due_date(db_session, test_todo, date(2025, 12, 31))

    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Updated Title",
            "note": "Still valid",
            "due_date": "not-a-date",
            "priority": "medium",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date="2025-12-31"' in response.content

    db_session.refresh(test_todo)
    assert test_todo.title == "Updated Title"
    assert test_todo.note == "Still valid"
    assert test_todo.due_date == date(2025, 12, 31)
    assert test_todo.priority == "medium"
