"""BUG-003 regression coverage for quick-add default priority."""

import re

from app.database import Todo


def create_quick_todo(client, list_id, title):
    return client.post(
        "/api/todos",
        data={
            "list_id": list_id,
            "title": title,
        },
    )


class TestBug003QuickAddPriority:
    """Tests for bug fix coverage around quick-add default priority."""

    def test_s01_quick_add_persist_default_priority_when_omitted(self, authenticated_client, test_list, db_session):
        """S01 [OC01] [TI01]

        Quick-add submits no priority, so the create-default boundary must persist low.
        """
        response = create_quick_todo(authenticated_client, test_list.id, "Bug 003 low default")
        assert response.status_code == 200

        created = (
            db_session.query(Todo)
            .filter(Todo.list_id == test_list.id, Todo.title == "Bug 003 low default")
            .first()
        )
        assert created is not None
        assert created.priority == "low"

    def test_s02_quick_add_render_row_and_dialog_reopen_as_low(self, authenticated_client, test_list):
        """S02 [OC02] [TI01,TI02]

        The quick-add response and dialog consumer path should expose low as active priority.
        """
        response = create_quick_todo(authenticated_client, test_list.id, "Bug 003 reopen low")
        assert response.status_code == 200

        content = response.content.decode()
        assert 'data-todo-priority="low"' in content
        assert "priority-low" in content
        assert re.search(r"<sl-badge[^>]*>\s*Low\s*</sl-badge>", content)
        assert re.search(r"openEditTodoDialog\([^\n]+, 'low'\)", content)

    def test_s03_explicit_priority_updates_remain_unchanged(self, authenticated_client, test_todo, db_session):
        """S03 [OC03] [TI03]

        BUG-003 should not alter explicit priority updates on the edit/update path.
        """
        response = authenticated_client.put(
            f"/api/todos/{test_todo.id}",
            data={
                "title": "Test Todo",
                "note": test_todo.note,
                "due_date": "",
                "priority": "high",
            },
        )
        assert response.status_code == 200

        db_session.refresh(test_todo)
        assert test_todo.priority == "high"

    def test_s04_quick_add_form_remains_title_only(self, authenticated_client, test_list):
        """S04 [OC02,OC03] [TI02]

        Keeping the quick-add UI title-only confirms defaulting happens in create/default logic.
        """
        list_page = authenticated_client.get(f"/app/lists/{test_list.id}")
        assert list_page.status_code == 200

        list_content = list_page.content.decode()
        quick_add_form_start = list_content.index('<form class="quick-add-form"')
        quick_add_form_end = list_content.index("</form>", quick_add_form_start)
        quick_add_form = list_content[quick_add_form_start:quick_add_form_end]

        assert 'name="title"' in quick_add_form
        assert 'name="list_id"' in quick_add_form
        assert 'name="priority"' not in quick_add_form
