"""Tests for quick-add default priority behavior."""

import re

from app.database import TODO_DEFAULT_PRIORITY, Todo


class TestQuickAddPriority:
    """Regression coverage for S02 (BUG-003)."""

    low_priority_badge_re = re.compile(r"sl-badge[^>]*>\s*Low\s*</sl-badge>")

    def _assert_low_priority_rendered(self, html: str, include_oob: bool = False) -> None:
        assert f'data-todo-priority="{TODO_DEFAULT_PRIORITY}"' in html
        assert f"priority-{TODO_DEFAULT_PRIORITY}" in html
        assert self.low_priority_badge_re.search(html)
        if include_oob:
            assert "hx-swap-oob=\"true\"" in html

    def test_quick_add_without_priority_defaults_to_low(self, authenticated_client, test_list, db_session):
        """Submitting a quick-add with only title sets low priority and renders low state."""
        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": "Bug-003 Quick Add",
            },
        )
        assert response.status_code == 200

        created = db_session.query(Todo).filter(
            Todo.title == "Bug-003 Quick Add",
            Todo.list_id == test_list.id,
        ).first()
        assert created is not None
        assert created.priority == TODO_DEFAULT_PRIORITY

        self._assert_low_priority_rendered(response.text, include_oob=True)
        assert f"openEditTodoDialog('{created.id}', 'Bug-003 Quick Add', '', '', '{TODO_DEFAULT_PRIORITY}')" in response.text

    def test_reload_shows_low_priority_for_quick_add(self, authenticated_client, test_list, db_session):
        """Re-rendering the list preserves low-priority quick-add state."""
        quick = Todo(
            list_id=test_list.id,
            title="Persisted Quick Add",
            position=0,
            priority="low",
        )
        db_session.add(quick)
        db_session.commit()

        response = authenticated_client.get(f"/app/lists/{test_list.id}")
        assert response.status_code == 200
        self._assert_low_priority_rendered(response.text)

    def test_quick_add_blank_title_uses_error_partial_without_insert(self, authenticated_client, test_list, db_session):
        """Blank title quick-add still returns the error partial and inserts nothing."""
        before = (
            db_session.query(Todo)
            .filter(Todo.list_id == test_list.id)
            .count()
        )

        response = authenticated_client.post(
            "/api/todos",
            data={
                "list_id": test_list.id,
                "title": "   ",
            },
        )
        assert response.status_code == 200
        assert b"Title is required" in response.content

        after = (
            db_session.query(Todo)
            .filter(Todo.list_id == test_list.id)
            .count()
        )
        assert after == before
