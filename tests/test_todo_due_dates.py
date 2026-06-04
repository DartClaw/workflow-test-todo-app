"""BUG-002 due-date regression coverage for edit flow persistence."""

import re
from datetime import date, datetime


class TestTodoDueDates:
    """Tests for due-date persistence and reopen payloads."""

    def _extract_due_date_payload(self, response_text: str) -> str:
        """Extract data-todo-due-date from the todo row partial."""
        match = re.search(r'data-todo-due-date="([^"]*)"', response_text)
        assert match is not None
        return match.group(1)

    def _extract_due_date_onclick(self, response_text: str) -> str:
        """Extract the edit dialog prefill due-date argument from the button."""
        match = re.search(
            r"openEditTodoDialog\('[^']*', '[^']*', '[^']*', '([^']*)', '[^']*'\)",
            response_text,
        )
        assert match is not None
        return match.group(1)

    def _edit_todo(
        self,
        client,
        todo,
        due_date: str | None = None,
        include_due_date: bool = True,
    ):
        data = {
            "title": todo.title,
            "note": todo.note,
            "priority": "medium",
        }
        if include_due_date:
            data["due_date"] = due_date or ""
        return client.put(f"/api/todos/{todo.id}", data=data)

    def test_edit_todo_sets_due_date_with_valid_yyyy_mm_dd(
        self, authenticated_client, test_todo, db_session
    ):
        response = self._edit_todo(
            authenticated_client, test_todo, due_date="2025-12-31"
        )
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.due_date is not None
        assert test_todo.due_date.date() == date(2025, 12, 31)

        body = response.text
        assert f'id="todo-{test_todo.id}"' in body
        assert f'hx-target="#todo-{test_todo.id}"' in body
        assert 'data-todo-due-date="2025-12-31"' in body
        assert "Dec 31, 2025" in body

    def test_edit_todo_reopens_with_saved_due_date_payload(
        self, authenticated_client, test_todo, db_session
    ):
        response = self._edit_todo(
            authenticated_client, test_todo, due_date="2025-12-31"
        )
        assert response.status_code == 200

        body = response.text
        assert self._extract_due_date_payload(body) == "2025-12-31"
        assert self._extract_due_date_onclick(body) == "2025-12-31"

    def test_edit_todo_clears_due_date_when_empty(self, authenticated_client, test_todo, db_session):
        test_todo.due_date = datetime(2025, 12, 31)
        db_session.commit()

        response = self._edit_todo(authenticated_client, test_todo, due_date="")
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.due_date is None

        body = response.text
        assert 'data-todo-due-date=""' in body
        assert 'class="todo-due-date' not in body

    def test_edit_todo_omits_due_date_preserves_existing_value(self, authenticated_client, test_todo, db_session):
        test_todo.due_date = datetime(2025, 12, 31)
        db_session.commit()

        response = self._edit_todo(authenticated_client, test_todo, include_due_date=False)
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.due_date is not None
        assert test_todo.due_date.date() == date(2025, 12, 31)

        body = response.text
        assert self._extract_due_date_payload(body) == "2025-12-31"
        assert self._extract_due_date_onclick(body) == "2025-12-31"

    def test_edit_todo_preserves_malformed_due_date(self, authenticated_client, test_todo, db_session):
        test_todo.due_date = datetime(2025, 12, 31)
        db_session.commit()

        response = self._edit_todo(authenticated_client, test_todo, due_date="2025/12/31")
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.due_date is not None
        assert test_todo.due_date.date() == date(2025, 12, 31)

        body = response.text
        assert self._extract_due_date_payload(body) == "2025-12-31"
        assert self._extract_due_date_onclick(body) == "2025-12-31"
