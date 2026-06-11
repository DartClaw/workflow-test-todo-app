"""Regression tests for quick-add default priority behavior."""

from app.database import Todo


LOW_PRIORITY = "low"
LOW_PRIORITY_TOKEN = LOW_PRIORITY.encode()
LOW_PRIORITY_DATA_ATTR = f'data-todo-priority="{LOW_PRIORITY}"'


def _quick_add(authenticated_client, test_list, title: str):
    return authenticated_client.post(
        "/api/todos",
        data={
            "list_id": test_list.id,
            "title": title,
        },
    )


def _todo_count_for_list(db_session, list_id: str) -> int:
    return db_session.query(Todo).filter(Todo.list_id == list_id).count()


def _assert_low_priority_row_rendered(html: bytes) -> None:
    assert f"priority-{LOW_PRIORITY}".encode() in html
    assert LOW_PRIORITY_DATA_ATTR.encode() in html
    assert b'<sl-badge' in html
    assert b'Low' in html


def test_quick_add_persisted_default_priority_and_rendered_badge(authenticated_client, test_list, db_session):
    """S01 [TI01,TI02]."""
    response = _quick_add(authenticated_client, test_list, "Quick Added")
    assert response.status_code == 200

    created = db_session.query(Todo).filter(Todo.title == "Quick Added").first()
    assert created is not None
    assert created.priority == LOW_PRIORITY

    _assert_low_priority_row_rendered(response.content)


def test_quick_add_row_seed_data_drives_edit_dialog_priority(authenticated_client, test_list):
    """S02 [TI02]."""
    response = _quick_add(authenticated_client, test_list, "Dialog Priority")
    assert response.status_code == 200

    body = response.text
    assert LOW_PRIORITY_DATA_ATTR in body
    assert "openEditTodoDialog" in body
    assert f", '{LOW_PRIORITY}'" in body or f', "{LOW_PRIORITY}"' in body


def test_quick_added_low_priority_survives_reload(authenticated_client, test_list, db_session):
    """S03 [TI01,TI03]."""
    response = _quick_add(authenticated_client, test_list, "Reload Persist")
    assert response.status_code == 200

    created = db_session.query(Todo).filter(Todo.title == "Reload Persist").first()
    assert created is not None
    assert created.priority == LOW_PRIORITY

    response = authenticated_client.get(f"/app/lists/{test_list.id}")
    assert response.status_code == 200
    _assert_low_priority_row_rendered(response.content)


def test_quick_add_blank_title_rejected_without_todo(authenticated_client, test_list, db_session):
    """S04 [TI03]."""
    existing = _todo_count_for_list(db_session, test_list.id)

    response = _quick_add(authenticated_client, test_list, "   ")
    assert response.status_code == 200
    assert b"Title is required" in response.content

    current = _todo_count_for_list(db_session, test_list.id)
    assert current == existing
