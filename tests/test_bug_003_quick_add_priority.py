from app.database import Todo

API_TODOS_URL = "/api/todos"
QUICK_ADD_TITLE = "Quick Add Todo"
BLANK_TITLE = "   "
EXISTING_TODO_TITLE = "Existing Todo"


def test_quick_add_without_priority_persists_low_and_renders_low_priority(
    authenticated_client,
    test_list,
    db_session,
):
    """Test quick-add creates todo with low priority and renders low priority data."""
    existing = Todo(list_id=test_list.id, title=EXISTING_TODO_TITLE, position=3)
    db_session.add(existing)
    db_session.commit()

    response = authenticated_client.post(
        API_TODOS_URL,
        data={"list_id": test_list.id, "title": QUICK_ADD_TITLE},
    )
    assert response.status_code == 200
    assert b'data-todo-priority="low"' in response.content

    created = db_session.query(Todo).filter(Todo.title == QUICK_ADD_TITLE).first()
    assert created is not None
    assert created.priority == "low"
    assert created.position == existing.position + 1
    assert created.is_completed is False


def test_quick_add_rejects_empty_title_and_preserves_list_state(
    authenticated_client,
    test_list,
    db_session,
):
    """Test blank title quick-add still fails with existing HTML error behavior."""
    initial_count = db_session.query(Todo).filter(Todo.list_id == test_list.id).count()

    response = authenticated_client.post(
        API_TODOS_URL,
        data={"list_id": test_list.id, "title": BLANK_TITLE},
    )

    assert response.status_code == 200
    assert b"Title is required" in response.content

    final_count = db_session.query(Todo).filter(Todo.list_id == test_list.id).count()
    assert final_count == initial_count
