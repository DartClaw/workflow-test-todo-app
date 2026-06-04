"""Regression coverage for BUG-002 (due date persistence from edit dialog)."""

from datetime import datetime


class TestBug002DueDates:
    """Tests for editing a Todo's Due Date via the edit dialog payload."""

    def test_due_date_set_from_edit_dialog_and_reopens(self, authenticated_client, test_todo):
        """First due date set in the edit dialog persists and reopens."""
        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Test Todo",
                "note": "A test note",
                "due_date": "2025-12-31",
                "priority": "medium",
            },
        )
        assert response.status_code == 200
        row_html = response.text
        assert 'data-todo-due-date="2025-12-31"' in row_html

        reopen = authenticated_client.get(f"/api/todos/{test_todo.id}")
        assert reopen.status_code == 200
        assert 'data-todo-due-date="2025-12-31"' in reopen.text

    def test_due_date_replaced_when_changing_calendar_day(self, authenticated_client, test_todo, db_session):
        """Existing due date can be replaced with a different calendar day."""
        test_todo.due_date = datetime(2025, 12, 31)
        db_session.commit()

        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Test Todo",
                "note": "A test note",
                "due_date": "2026-01-15",
                "priority": "medium",
            },
        )
        assert response.status_code == 200
        assert 'data-todo-due-date="2026-01-15"' in response.text
        assert 'data-todo-due-date="2025-12-31"' not in response.text

        reopen = authenticated_client.get(f"/api/todos/{test_todo.id}")
        assert reopen.status_code == 200
        assert 'data-todo-due-date="2026-01-15"' in reopen.text

    def test_due_date_can_be_cleared(self, authenticated_client, test_todo, db_session):
        """Clearing due date in edit dialog removes stored due date."""
        test_todo.due_date = datetime(2025, 12, 31)
        db_session.commit()

        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Test Todo",
                "note": "A test note",
                "due_date": "",
                "priority": "medium",
            },
        )
        assert response.status_code == 200
        assert 'data-todo-due-date=""' in response.text
        assert '2025-12-31' not in response.text

        reopen = authenticated_client.get(f"/api/todos/{test_todo.id}")
        assert reopen.status_code == 200
        assert 'data-todo-due-date=""' in reopen.text
