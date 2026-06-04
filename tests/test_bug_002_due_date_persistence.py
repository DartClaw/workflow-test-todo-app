"""Regression coverage for BUG-002 due date persistence in edit flow."""

from datetime import datetime


DUE_DATE = "2025-12-31"
DUE_DATE_PARSED = datetime(2025, 12, 31)


def assert_response_due_date(response, expected: str) -> None:
    assert response.status_code == 200
    assert f'data-todo-due-date="{expected}"'.encode() in response.content


def assert_stored_due_date(db_session, test_todo, expected: datetime | None) -> None:
    db_session.refresh(test_todo)
    assert test_todo.due_date == expected


class TestBug002DueDatePersistence:
    """Tests for preserving and clearing due dates through edit save."""

    def test_due_date_persistence_survives_edit_save(self, authenticated_client, test_todo, db_session):
        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Updated title",
                "note": "Updated note",
                "due_date": DUE_DATE,
                "priority": "high",
            },
        )
        assert_response_due_date(response, DUE_DATE)
        assert_stored_due_date(db_session, test_todo, DUE_DATE_PARSED)

        reopen = authenticated_client.get(f"/api/todos/{test_todo.id}")
        assert_response_due_date(reopen, DUE_DATE)

    def test_due_date_rehydrates_when_unmodified_in_edit(self, authenticated_client, test_todo, db_session):
        test_todo.due_date = DUE_DATE_PARSED
        db_session.commit()
        db_session.refresh(test_todo)

        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Title with unchanged due date",
                "note": "Unchanged note",
                "due_date": DUE_DATE,
                "priority": "medium",
            },
        )
        assert_response_due_date(response, DUE_DATE)
        assert_stored_due_date(db_session, test_todo, DUE_DATE_PARSED)

        reopen = authenticated_client.get(f"/api/todos/{test_todo.id}")
        assert_response_due_date(reopen, DUE_DATE)

    def test_due_date_can_be_cleared(self, authenticated_client, test_todo, db_session):
        test_todo.due_date = datetime(2025, 12, 31)
        db_session.commit()
        db_session.refresh(test_todo)

        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Cleared due date",
                "note": "Will clear date",
                "due_date": "",
                "priority": "medium",
            },
        )
        assert_response_due_date(response, "")

        assert_stored_due_date(db_session, test_todo, None)

        reopen = authenticated_client.get(f"/api/todos/{test_todo.id}")
        assert_response_due_date(reopen, "")

    def test_invalid_due_date_is_rejected(self, authenticated_client, test_todo):
        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Invalid due date",
                "due_date": "2025-12-31T00:00",
                "priority": "low",
            },
        )
        assert response.status_code == 400
        assert b"Invalid due date format" in response.content
