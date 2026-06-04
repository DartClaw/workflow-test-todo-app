"""Regression tests for BUG-002 due date persistence through the edit dialog."""

from datetime import datetime


SAMPLE_DUE_DATE = "2025-12-31"


def _submit_todo_update(
    authenticated_client,
    test_todo,
    *,
    due_date,
    title=None,
    note=None,
    priority=None,
):
    payload = {
        "title": title if title is not None else test_todo.title,
        "note": note if note is not None else (test_todo.note or ""),
        "priority": priority if priority is not None else test_todo.priority,
        "due_date": due_date,
    }
    return authenticated_client.put(
        f"/api/todos/{test_todo.id}",
        data=payload,
    )


def test_update_todo_persists_date_only_due_date(
    authenticated_client, test_todo, db_session
):
    response = _submit_todo_update(
        authenticated_client,
        test_todo,
        due_date=SAMPLE_DUE_DATE,
    )
    assert response.status_code == 200
    assert f'data-todo-due-date="{SAMPLE_DUE_DATE}"'.encode() in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is not None
    assert test_todo.due_date == datetime(2025, 12, 31)


def test_update_todo_response_includes_persisted_due_date_metadata(
    authenticated_client, test_todo, db_session
):
    response = _submit_todo_update(
        authenticated_client,
        test_todo,
        due_date=SAMPLE_DUE_DATE,
    )
    assert response.status_code == 200
    assert f'data-todo-due-date="{SAMPLE_DUE_DATE}"'.encode() in response.content


def test_ti03_s03_clears_due_date_when_edit_submitted_empty(
    authenticated_client,
    test_todo,
    db_session,
):
    test_todo.due_date = datetime(2026, 1, 1)
    db_session.add(test_todo)
    db_session.commit()

    response = _submit_todo_update(
        authenticated_client,
        test_todo,
        due_date="",
    )
    assert response.status_code == 200
    assert b'data-todo-due-date=""' in response.content

    db_session.refresh(test_todo)
    assert test_todo.due_date is None


def test_update_todo_invalid_due_date_returns_error_partial(
    authenticated_client, test_todo, db_session
):
    original_title = test_todo.title
    original_note = test_todo.note
    original_priority = test_todo.priority
    original_due_date = datetime(2026, 1, 1)
    test_todo.due_date = original_due_date
    db_session.add(test_todo)
    db_session.commit()

    response = _submit_todo_update(
        authenticated_client,
        test_todo,
        title="Changed title",
        note="Changed note",
        due_date="2025/12/31",
        priority="high",
    )
    assert response.status_code == 400
    assert b"Invalid due date format" in response.content

    db_session.refresh(test_todo)
    assert test_todo.title == original_title
    assert test_todo.note == original_note
    assert test_todo.priority == original_priority
    assert test_todo.due_date == original_due_date
