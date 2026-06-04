from datetime import datetime



def test_s01_save_and_round_trip_due_date(authenticated_client, test_todo, db_session):
    """Save a due date from the edit dialog and reopen it with the same value."""
    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": test_todo.title,
            "note": test_todo.note,
            "due_date": "2025-12-31",
            "priority": test_todo.priority,
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date="2025-12-31"' in response.content
    assert b"Dec 31, 2025" in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date == datetime(2025, 12, 31)

    reopen_response = authenticated_client.get(f"/api/todos/{test_todo.id}")
    assert reopen_response.status_code == 200
    assert b'data-todo-due-date="2025-12-31"' in reopen_response.content


def test_s02_clear_due_date_removes_row_and_dialog_state(authenticated_client, test_todo, db_session):
    """Clear due date in edit dialog payload and ensure reopen state is empty."""
    test_todo.due_date = datetime(2025, 12, 31)
    db_session.commit()
    db_session.refresh(test_todo)

    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": test_todo.title,
            "note": test_todo.note,
            "due_date": "",
            "priority": test_todo.priority,
        },
    )
    assert response.status_code == 200
    assert b'data-todo-due-date=""' in response.content
    assert b'class="todo-due-date' not in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is None

    reopen_response = authenticated_client.get(f"/api/todos/{test_todo.id}")
    assert reopen_response.status_code == 200
    assert b'data-todo-due-date=""' in reopen_response.content


def test_s03_invalid_due_date_is_rejected_and_keeps_existing_due_date(
    authenticated_client, test_todo, db_session
):
    """Malformed date payload should return the error partial and leave todo unchanged."""
    test_todo.title = "Malformed Todo"
    test_todo.note = "Malformed note"
    test_todo.priority = "medium"
    test_todo.due_date = datetime(2024, 12, 1)
    db_session.commit()
    db_session.refresh(test_todo)

    response = authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data={
            "title": "Modified title",
            "note": test_todo.note,
            "due_date": "2025/12/31",
            "priority": test_todo.priority,
        },
    )
    assert response.status_code == 200
    assert b"Invalid due date format. Use YYYY-MM-DD." in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date == datetime(2024, 12, 1)
    assert test_todo.title == "Malformed Todo"
    assert test_todo.note == "Malformed note"
    assert test_todo.priority == "medium"
