"""Tests for quick-add default priority behavior."""

from app.database import Todo


class TestQuickAddPriority:
    """Tests for quick-add todo default priority behavior."""

    def test_quick_add_todo_defaults_to_low_priority(self, authenticated_client, test_list, db_session):
        """Test quick-add assigns low priority when not provided."""
        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": "Priority Default Todo",
            },
        )
        assert response.status_code == 200
        assert b'data-todo-priority="low"' in response.content

        created = db_session.query(Todo).filter(Todo.title == "Priority Default Todo").first()
        assert created is not None
        assert created.priority == "low"

    def test_quick_add_repeated_creates_always_default_low(self, authenticated_client, test_list, db_session):
        """Test repeated quick-add always persists low priority."""
        titles = ["Repeat One", "Repeat Two", "Repeat Three"]
        for title in titles:
            response = authenticated_client.post(
                "/api/todos",
                data={
                    "list_id": test_list.id,
                    "title": title,
                },
            )
            assert response.status_code == 200
            assert b'data-todo-priority="low"' in response.content

        created = (
            db_session.query(Todo)
            .filter(Todo.list_id == test_list.id, Todo.title.in_(titles))
            .all()
        )
        assert len(created) == len(titles)
        assert all(todo.priority == "low" for todo in created)

    def test_quick_added_todo_round_trips_low_then_high(self, authenticated_client, test_list, db_session):
        """Test quick-added todo opens with low and can be updated to high."""
        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": "Priority Edit Todo",
            },
        )
        assert response.status_code == 200
        assert b'data-todo-priority="low"' in response.content

        todo = db_session.query(Todo).filter(Todo.title == "Priority Edit Todo").first()
        assert todo is not None
        assert todo.priority == "low"

        reopen = authenticated_client.get(f"/api/todos/{todo.id}")
        assert reopen.status_code == 200
        assert b"openEditTodoDialog(" in reopen.content
        assert b'data-todo-priority="low"' in reopen.content

        updated = authenticated_client.put(
            f"/api/todos/{todo.id}",
            data={
                "title": "Priority Edit Todo",
                "note": "edited",
                "due_date": "",
                "priority": "high",
            },
        )
        assert updated.status_code == 200

        db_session.refresh(todo)
        assert todo.priority == "high"

        reopened = authenticated_client.get(f"/api/todos/{todo.id}")
        assert reopened.status_code == 200
        assert b'data-todo-priority="high"' in reopened.content
