"""Regression tests for BUG-003: quick-add defaults to low priority."""

import re

from app.database import Todo


TODO_ID_RE = re.compile(r'id="todo-([a-z0-9-]+)"')


def extract_todo_id_from_row_html(body: str) -> str:
    match = TODO_ID_RE.search(body)
    assert match is not None
    return match.group(1)


def create_quick_add_todo(client, list_id: str, title: str):
    response = client.post(
        "/api/todos",
        data={
            "list_id": list_id,
            "title": title,
        },
    )
    assert response.status_code == 200
    return response, extract_todo_id_from_row_html(response.text)


class TestBug003QuickAddPriority:
    """Tests for quick-add todo priority default and hydration behavior."""

    def test_quick_add_todos_default_to_low_and_preserve_markup_contract(
        self, authenticated_client, test_list, db_session
    ):
        response, todo_id = create_quick_add_todo(
            authenticated_client, test_list.id, "Low Priority Todo"
        )

        body = response.text

        # Quick-add should still return the OOB list-count swap contract.
        assert f'id="list-{test_list.id}-count"' in body
        assert 'hx-swap-oob="true"' in body

        # Visual priority contract should be rendered as low.
        assert f'id="todo-{todo_id}"' in body
        assert "priority-low" in body
        assert 'data-todo-priority="low"' in body
        assert "Low" in body

        todo = db_session.query(Todo).filter_by(id=todo_id).first()
        assert todo is not None
        assert todo.priority == "low"

    def test_quick_add_todo_hydrates_edit_priority_from_stored_value(
        self, authenticated_client, test_list, db_session
    ):
        create_response, todo_id = create_quick_add_todo(
            authenticated_client,
            test_list.id,
            "Edit Dialog Priority Todo",
        )

        todo = db_session.query(Todo).filter_by(id=todo_id).first()
        assert todo is not None
        assert todo.priority == "low"

        row_response = authenticated_client.get(f"/api/todos/{todo.id}")
        assert row_response.status_code == 200

        row_html = row_response.text
        assert 'data-todo-priority="low"' in row_html
        assert f'openEditTodoDialog(\'{todo.id}\'' in row_html
        assert f"'{todo.id}'," in row_html
        assert "'low')" in row_html
