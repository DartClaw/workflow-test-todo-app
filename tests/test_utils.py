"""Unit tests for app.utils helper functions."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.utils import is_due_today, is_overdue


def _make_todo(due_date=None, is_completed=False):
    class _Todo:
        pass

    t = _Todo()
    t.due_date = due_date
    t.is_completed = is_completed
    return t


TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)


class TestIsOverdue:
    def test_past_date_incomplete(self):
        assert is_overdue(_make_todo(due_date=YESTERDAY)) is True

    def test_today_not_overdue(self):
        assert is_overdue(_make_todo(due_date=TODAY)) is False

    def test_future_not_overdue(self):
        assert is_overdue(_make_todo(due_date=TOMORROW)) is False

    def test_no_due_date(self):
        assert is_overdue(_make_todo()) is False

    def test_completed_past_date(self):
        assert is_overdue(_make_todo(due_date=YESTERDAY, is_completed=True)) is False


class TestIsDueToday:
    def test_due_today_incomplete(self):
        assert is_due_today(_make_todo(due_date=TODAY)) is True

    def test_past_date(self):
        assert is_due_today(_make_todo(due_date=YESTERDAY)) is False

    def test_future_date(self):
        assert is_due_today(_make_todo(due_date=TOMORROW)) is False

    def test_no_due_date(self):
        assert is_due_today(_make_todo()) is False

    def test_completed_due_today(self):
        assert is_due_today(_make_todo(due_date=TODAY, is_completed=True)) is False
