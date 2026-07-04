"""Regression tests for BUG-002."""

from datetime import datetime

from app.database import User

due_date_value = "2025-12-31"


def test_edit_todo_due_date_persists_and_reopens(authenticated_client, test_todo, db_session):
    """Date changes in the edit dialog should persist and return in row data."""
    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Updated Title",
            "note": "Updated note",
            "due_date": due_date_value,
            "priority": "high",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date="2025-12-31"' in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is not None
    assert test_todo.due_date.date().isoformat() == due_date_value


def test_edit_todo_due_date_can_be_cleared(authenticated_client, test_todo, db_session):
    """Submitting a blank edit dialog due date must clear a stored Due Date."""
    test_todo.due_date = datetime(2025, 12, 31)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Still Clearing",
            "note": "Cleared date",
            "due_date": "",
            "priority": "medium",
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date=""' in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is None


def test_edit_dialog_persists_fields_and_non_owner_is_blocked(
    authenticated_client,
    test_todo,
    db_session,
    client,
):
    """Todo editing keeps title, note, and priority; non-owner updates are denied."""
    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Owner Update",
            "note": "Owner note",
            "due_date": "2025-12-31",
            "priority": "high",
        },
    )
    assert response.status_code == 200
    assert b"Owner Update" in response.content
    assert b"Owner note" in response.content

    db_session.refresh(test_todo)
    assert test_todo.title == "Owner Update"
    assert test_todo.note == "Owner note"
    assert test_todo.priority == "high"

    other_user = User(email="other@example.com", password="password")
    db_session.add(other_user)
    db_session.commit()
    from app.core.deps import create_session

    session_id = create_session(other_user.id)
    client.cookies.set("session_id", session_id)

    response = client.put(
        f"/api/todos/{test_todo.id}",
        data={"title": "Blocked", "note": "Blocked", "due_date": "2024-01-01"},
    )
    assert response.status_code == 403
    assert b"Not authorized" in response.content
