from uuid import uuid4

from app.database import Todo


class TestPriorityDefaults:
    """Regression tests for BUG-003 quick-add and priority fallback behavior."""

    @staticmethod
    def assert_priority_fragment(content: str, priority: str) -> None:
        assert f"priority-{priority}" in content
        assert f'data-todo-priority="{priority}"' in content
        assert priority.capitalize() in content
        assert f"'{priority}'" in content

    def test_quick_add_todo_defaults_to_low_priority(
        self, authenticated_client, test_list, db_session
    ):
        title = f"Priority Default Todo {uuid4()}"
        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": title,
            },
        )
        assert response.status_code == 200

        created = db_session.query(Todo).filter(
            Todo.list_id == test_list.id,
            Todo.title == title,
        ).first()
        assert created is not None
        assert created.priority == "low"

        content = response.text
        self.assert_priority_fragment(content, "low")
        assert 'hx-swap-oob="true"' in content

    def test_todo_item_renders_missing_priority_as_low(
        self, authenticated_client, test_list, db_session
    ):
        legacy_todo = Todo(
            list_id=test_list.id,
            title="Legacy Priority",
            position=0,
            priority=None,
        )
        db_session.add(legacy_todo)
        db_session.commit()

        # Render with a legacy missing-priority row
        response = authenticated_client.get(
            f"/api/todos/{legacy_todo.id}"
        )
        assert response.status_code == 200

        # Ensure legacy missing values normalize to low everywhere the row exposes Priority
        content = response.text
        self.assert_priority_fragment(content, "low")
        assert "openEditTodoDialog" in content

    def test_todo_item_preserves_explicit_high_priority(
        self, authenticated_client, test_list, db_session
    ):
        explicit_todo = Todo(
            list_id=test_list.id,
            title="High Priority",
            position=1,
            priority="high",
        )
        db_session.add(explicit_todo)
        db_session.commit()

        # Render with explicit non-low priority and keep it unchanged
        response = authenticated_client.get(f"/api/todos/{explicit_todo.id}")
        assert response.status_code == 200

        content = response.text
        self.assert_priority_fragment(content, "high")
        assert "openEditTodoDialog" in content
