"""Regression coverage for quick-add priority defaults and dialog hydration."""

import pytest

from app.database import Todo


class TestQuickAddPriority:
    """Tests for BUG-003 and S02 quick-add default priority behavior."""

    def _post_quick_add_todo(self, client, list_id: str, title: str):
        return client.post(
            "/api/todos",
            data={
                "list_id": list_id,
                "title": title,
            },
        )

    def _fetch_todo_by_title(self, db_session, list_id: str, title: str) -> Todo:
        todo = db_session.query(Todo).filter(Todo.list_id == list_id, Todo.title == title).first()
        assert todo is not None
        return todo

    def _assert_edit_payload_priority(self, response, todo: Todo, title: str, priority: str):
        assert response.status_code == 200
        assert f"data-todo-priority=\"{priority}\"".encode() in response.content
        assert (
            f"openEditTodoDialog('{todo.id}', '{title}', '', '', '{priority}')".encode()
            in response.content
        )

    def test_quick_add_todo_defaults_to_low_priority_and_renders_low(self, authenticated_client, test_list, db_session):
        """S02 + OC01: quick-add with no priority stores and renders low."""
        title = "Quick-add low todo"
        response = self._post_quick_add_todo(authenticated_client, test_list.id, title)
        assert response.status_code == 200
        assert b"data-todo-priority=\"low\"" in response.content
        assert b"priority-low" in response.content
        assert b"Low" in response.content

        todo = self._fetch_todo_by_title(db_session, test_list.id, title)
        assert todo.priority == "low"

    def test_quick_add_todo_reopens_low_in_edit_payload(self, authenticated_client, test_list, db_session):
        """S02 + TI02: quick-added todo keeps low through full hydration path."""
        title = "Quick-add reopen todo"
        assert self._post_quick_add_todo(authenticated_client, test_list.id, title).status_code == 200

        todo = self._fetch_todo_by_title(db_session, test_list.id, title)
        response = authenticated_client.get(f"/api/todos/{todo.id}")
        self._assert_edit_payload_priority(response, todo, title, "low")

    @pytest.mark.parametrize(
        "priority,expected_label",
        [("medium", "Medium"), ("high", "High")],
    )
    def test_existing_non_low_priority_todos_reopen_with_priority(
        self,
        authenticated_client,
        db_session,
        test_list,
        priority,
        expected_label,
    ):
        """S03 + TI03: explicit non-low priority is preserved when reopened."""
        title = f"Explicit {priority} todo"
        explicit_priority_todo = Todo(
            list_id=test_list.id,
            title=title,
            priority=priority,
            position=1,
        )
        db_session.add(explicit_priority_todo)
        db_session.commit()

        response = authenticated_client.get(f"/api/todos/{explicit_priority_todo.id}")
        self._assert_edit_payload_priority(response, explicit_priority_todo, title, priority)
        assert expected_label.encode() in response.content

    def test_quick_add_stays_low_after_reload_search_path(self, authenticated_client, test_list, db_session):
        """S04 + OC01/OC02: quick-add stays low across a list reload query."""
        title = "Quick-add reload todo"
        assert (
            self._post_quick_add_todo(authenticated_client, test_list.id, title).status_code
            == 200
        )

        reload_response = authenticated_client.get(f"/api/todos/search?list_id={test_list.id}&q=")
        assert reload_response.status_code == 200
        assert b"data-todo-priority=\"low\"" in reload_response.content
        assert b"Low" in reload_response.content

        todo = self._fetch_todo_by_title(db_session, test_list.id, title)

        detail_response = authenticated_client.get(f"/api/todos/{todo.id}")
        self._assert_edit_payload_priority(detail_response, todo, title, "low")
