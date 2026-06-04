"""Regression tests for quick-add default priority behavior."""

import re

from app.database import Todo


def test_quick_add_persists_low_priority(authenticated_client, test_list, db_session):
    response = authenticated_client.post(
        "/api/todos",
        data={
            "list_id": test_list.id,
            "title": "Priority by default",
        },
    )
    assert response.status_code == 200

    created = db_session.query(Todo).filter(Todo.title == "Priority by default").first()
    assert created is not None
    assert created.priority == "low"

    payload = response.content.decode()
    assert 'data-todo-priority="low"' in payload
    assert "priority-low" in payload
    assert re.search(
        rf"openEditTodoDialog\('{created.id}', 'Priority by default', '', '[^']*', 'low'\)",
        payload,
    )


def test_ti02_quick_add_edit_payload_uses_persisted_priority(authenticated_client, test_list, db_session):
    response = authenticated_client.post(
        "/api/todos",
        data={
            "list_id": test_list.id,
            "title": "Needs edit payload",
        },
    )
    assert response.status_code == 200

    created = db_session.query(Todo).filter(Todo.title == "Needs edit payload").first()
    assert created is not None
    assert created.priority == "low"

    payload = response.content.decode()
    assert 'id="todo-' in payload
    assert f"data-todo-priority=\"{created.priority}\"" in payload
    assert f"openEditTodoDialog('{created.id}'" in payload


def test_ti03_quick_add_rejects_empty_title_stays_partial(authenticated_client, test_list, db_session):
    response = authenticated_client.post(
        "/api/todos",
        data={
            "list_id": test_list.id,
            "title": "   ",
        },
    )
    assert response.status_code == 200
    assert "Title is required" in response.text

    list_todos = db_session.query(Todo).filter(Todo.list_id == test_list.id).count()
    assert list_todos == 0
