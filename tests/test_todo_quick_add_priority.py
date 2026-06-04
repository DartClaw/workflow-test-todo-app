import re
from app.database import Todo


def quick_add(client, list_id: str, title: str):
    return client.post("/api/todos", data={"list_id": list_id, "title": title})


def latest_todo(db_session, list_id: str, title: str):
    return (
        db_session.query(Todo)
        .filter(Todo.list_id == list_id, Todo.title == title)
        .order_by(Todo.created_at.desc())
        .first()
    )


class TestQuickAddPriority:
    """Tests for quick-add Priority defaults."""

    def test_quick_add_defaults_priority_to_low(self, authenticated_client, test_list, db_session):
        """Quick-add without an explicit Priority persists low as the default."""
        title = "Priority Default"
        response = quick_add(authenticated_client, test_list.id, title)
        assert response.status_code == 200

        created = latest_todo(db_session, test_list.id, title)
        assert created is not None
        assert created.priority == "low"
        assert b"data-todo-priority=\"low\"" in response.content

    def test_quick_add_response_includes_low_priority_metadata(self, authenticated_client, test_list):
        """Quick-added row metadata includes a Low priority value for reopen."""
        response = quick_add(authenticated_client, test_list.id, "Quick Priority Metadata")
        assert response.status_code == 200
        html = response.text

        assert "priority-low" in html
        assert "data-todo-priority=\"low\"" in html
        assert "<span class=\"todo-title\">Quick Priority Metadata</span>" in html
        assert "<sl-badge" in html and "Low" in html
        assert "openEditTodoDialog('" in html and "low')" in html
        assert re.search(r'<span id="list-.+-count" hx-swap-oob="true">', html)

    def test_quick_add_empty_title_prevents_creation(self, authenticated_client, test_list, db_session):
        """Quick-add continues to reject blank titles."""
        starting_count = db_session.query(Todo).count()

        response = quick_add(authenticated_client, test_list.id, "   ")
        assert response.status_code == 200
        assert b"required" in response.content

        assert db_session.query(Todo).count() == starting_count
