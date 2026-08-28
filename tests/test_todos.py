"""Tests for todo item routes."""

from datetime import date, datetime, timezone

import pytest

from app.database import Todo, TodoList, User


class TestTodos:
    """Tests for todo CRUD operations."""

    def test_create_todo(self, authenticated_client, test_list, db_session):
        """Test creating a new todo."""
        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": "New Todo",
            },
        )
        assert response.status_code == 200
        assert b"New Todo" in response.content

        # Verify in database
        created = db_session.query(Todo).filter(Todo.title == "New Todo").first()
        assert created is not None
        assert created.list_id == test_list.id
        assert created.priority == "low"
        assert created.is_completed is False

    def test_create_todo_empty_title(self, authenticated_client, test_list):
        """Test creating todo with empty title fails."""
        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": "   ",
            },
        )
        assert response.status_code == 200
        assert b"required" in response.content

    def test_update_todo(self, authenticated_client, test_todo, db_session):
        """Test updating a todo."""
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

        # Verify in database
        db_session.refresh(test_todo)
        assert test_todo.title == "Updated Title"
        assert test_todo.note == "Updated note"
        assert test_todo.due_date.year == 2025
        assert test_todo.priority == "high"

    def test_toggle_todo_complete(self, authenticated_client, test_todo, db_session):
        """Test toggling todo completion."""
        assert test_todo.is_completed is False

        # Toggle to complete
        response = authenticated_client.patch(f"/api/todos/{test_todo.id}/toggle")
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.is_completed is True
        assert test_todo.completed_at is not None

        # Toggle back to incomplete
        response = authenticated_client.patch(f"/api/todos/{test_todo.id}/toggle")
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.is_completed is False
        assert test_todo.completed_at is None

    def test_delete_todo(self, authenticated_client, test_todo, db_session):
        """Test deleting a todo."""
        todo_id = test_todo.id
        response = authenticated_client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 200

        # Verify deleted
        deleted = db_session.query(Todo).filter(Todo.id == todo_id).first()
        assert deleted is None

    def test_delete_incomplete_todo_updates_list_count(
        self, authenticated_client, test_list, test_todo, db_session
    ):
        """S01: deleting an incomplete todo returns its authoritative count OOB swap."""
        second_todo = Todo(list_id=test_list.id, title="Second Todo", position=1)
        db_session.add(second_todo)
        db_session.commit()

        response = authenticated_client.delete(f"/api/todos/{test_todo.id}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        content = response.content.decode()
        assert f'id="list-{test_list.id}-count"' in content
        assert 'hx-swap-oob="true"' in content
        assert ">1<" in content
        assert db_session.query(Todo).filter(Todo.id == test_todo.id).first() is None

    def test_delete_completed_todo_preserves_list_count(
        self, authenticated_client, test_list, test_todo, db_session
    ):
        """S02: deleting a completed todo returns the unchanged incomplete count."""
        test_todo.is_completed = True
        db_session.commit()

        response = authenticated_client.delete(f"/api/todos/{test_todo.id}")

        assert response.status_code == 200
        content = response.content.decode()
        assert f'id="list-{test_list.id}-count"' in content
        assert 'hx-swap-oob="true"' in content
        assert ">0<" in content

    def test_delete_missing_or_inaccessible_todo_has_no_count_swap(
        self, authenticated_client, test_user, db_session
    ):
        """S03: rejected deletes preserve status and do not return an OOB swap."""
        missing_response = authenticated_client.delete("/api/todos/missing-todo")
        assert missing_response.status_code == 404
        assert b"hx-swap-oob" not in missing_response.content

        other_user = User(email="other@example.com", password="otherpass")
        db_session.add(other_user)
        db_session.commit()
        other_list = TodoList(user_id=other_user.id, name="Other List", position=0)
        db_session.add(other_list)
        db_session.commit()
        other_todo = Todo(list_id=other_list.id, title="Private Todo", position=0)
        db_session.add(other_todo)
        db_session.commit()

        forbidden_response = authenticated_client.delete(f"/api/todos/{other_todo.id}")
        assert forbidden_response.status_code == 403
        assert b"hx-swap-oob" not in forbidden_response.content
        assert db_session.query(Todo).filter(Todo.id == other_todo.id).first() is not None

    def test_reorder_todo_move_up(self, authenticated_client, test_list, db_session):
        """Test reordering a todo to an earlier position."""
        # Create three todos
        todo1 = Todo(list_id=test_list.id, title="Todo 1", position=0)
        todo2 = Todo(list_id=test_list.id, title="Todo 2", position=1)
        todo3 = Todo(list_id=test_list.id, title="Todo 3", position=2)
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        # Move todo3 to position 0
        response = authenticated_client.post(
            f"/api/todos/{todo3.id}/reorder",
            data={"position": 0},
        )
        assert response.status_code == 200

        # Verify positions updated
        db_session.refresh(todo1)
        db_session.refresh(todo2)
        db_session.refresh(todo3)
        assert todo3.position == 0
        assert todo1.position == 1
        assert todo2.position == 2

    def test_reorder_todo_move_down(self, authenticated_client, test_list, db_session):
        """Test reordering a todo to a later position."""
        # Create three todos
        todo1 = Todo(list_id=test_list.id, title="Todo 1", position=0)
        todo2 = Todo(list_id=test_list.id, title="Todo 2", position=1)
        todo3 = Todo(list_id=test_list.id, title="Todo 3", position=2)
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        # Move todo1 to position 2
        response = authenticated_client.post(
            f"/api/todos/{todo1.id}/reorder",
            data={"position": 2},
        )
        assert response.status_code == 200

        # Verify positions updated
        db_session.refresh(todo1)
        db_session.refresh(todo2)
        db_session.refresh(todo3)
        assert todo2.position == 0
        assert todo3.position == 1
        assert todo1.position == 2

    def test_search_todos(self, authenticated_client, test_list, db_session):
        """Test searching todos."""
        # Create some todos
        todos = [
            Todo(list_id=test_list.id, title="Buy groceries", position=0),
            Todo(list_id=test_list.id, title="Buy milk", position=1),
            Todo(list_id=test_list.id, title="Send email", position=2),
        ]
        for todo in todos:
            db_session.add(todo)
        db_session.commit()

        # Search for "buy"
        response = authenticated_client.get(
            f"/api/todos/search?list_id={test_list.id}&q=buy"
        )
        assert response.status_code == 200
        assert b"Buy groceries" in response.content
        assert b"Buy milk" in response.content
        assert b"Send email" not in response.content

    def test_search_case_insensitive(self, authenticated_client, test_list, db_session):
        """Test search is case-insensitive."""
        todo = Todo(list_id=test_list.id, title="Buy Groceries", position=0)
        db_session.add(todo)
        db_session.commit()

        # Search with different case
        response = authenticated_client.get(
            f"/api/todos/search?list_id={test_list.id}&q=BUY"
        )
        assert response.status_code == 200
        assert b"Buy Groceries" in response.content

    def test_search_empty_query(self, authenticated_client, test_list, db_session):
        """Test search with empty query returns all todos."""
        todos = [
            Todo(list_id=test_list.id, title="Todo 1", position=0),
            Todo(list_id=test_list.id, title="Todo 2", position=1),
        ]
        for todo in todos:
            db_session.add(todo)
        db_session.commit()

        response = authenticated_client.get(
            f"/api/todos/search?list_id={test_list.id}&q="
        )
        assert response.status_code == 200
        assert b"Todo 1" in response.content
        assert b"Todo 2" in response.content


class TestTodoAccess:
    """Tests for todo access control."""

    def test_cannot_access_other_users_todo(self, client, test_todo, db_session):
        """Test users cannot access other users' todos."""
        from app.core.deps import create_session
        from app.database import User

        # Create another user
        other_user = User(email="other@example.com", password="password")
        db_session.add(other_user)
        db_session.commit()

        # Authenticate as other user
        session_id = create_session(other_user.id)
        client.cookies.set("session_id", session_id)

        # Try to access the todo
        response = client.get(f"/api/todos/{test_todo.id}")
        assert response.status_code == 403

    def test_cannot_modify_other_users_todo(self, client, test_todo, db_session):
        """Test users cannot modify other users' todos."""
        from app.core.deps import create_session
        from app.database import User

        # Create another user
        other_user = User(email="other@example.com", password="password")
        db_session.add(other_user)
        db_session.commit()

        # Authenticate as other user
        session_id = create_session(other_user.id)
        client.cookies.set("session_id", session_id)

        # Try to update the todo
        response = client.put(
            f"/api/todos/{test_todo.id}",
            data={"title": "Hacked!"},
        )
        assert response.status_code == 403
