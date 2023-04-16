import json
import pytest

from sql_app.models import Task, Tag
from api.handlers import add_tag
from fastapi import HTTPException


async def test_create_user(client, get_task_from_database):
    # Create a test task
    task_data = {
        "user_id": 1,
        "title": "Test task",
    }
    response = client.post("/task/create", data=json.dumps(task_data))
    assert response.status_code == 200
    data_from_resp = response.json()
    assert data_from_resp.get('user_id') is not None
    assert data_from_resp.get('user_id') == task_data["user_id"]
    assert data_from_resp.get('title') == task_data["title"]

    # Verify the task was saved to the database
    task = await get_task_from_database(data_from_resp["user_id"])
    assert task is not None
    assert len(task) == 1
    task_from_db = dict(task[0])
    assert task_from_db['user_id'] == task_data["user_id"]
    assert task_from_db['title'] == task_data["title"]


async def test_delete_task_success(client, create_task_in_database, get_task_from_database):
    # Create a new task in the database to delete
    task_data = {
        'id': 1,
        'user_id': 123321,
        'task': 'Помыть посуду'
    }
    await create_task_in_database(**task_data)
    tasks_from_db = await get_task_from_database(task_data["user_id"])
    # Send a request to delete the task
    response = client.delete(
        f"/task/delete_task/?task_id={tasks_from_db[0]['id']}",
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}


async def test_get_all_tasks(client, create_task_in_database):
    # Create some tasks for the user
    task_data = {
        'id': 1,
        'user_id': 123321,
        'task': 'Помыть посуду'
    }
    task_data_2 = {
        'id': 2,
        'user_id': 123321,
        'task': 'Помыть кошку'
    }
    await create_task_in_database(**task_data)
    await create_task_in_database(**task_data_2)

    # Test getting all tasks without a tag filter
    response = client.get(f"task/get_all_tasks?user_id={task_data['user_id']}")
    assert response.status_code == 200
    data = response.json()

    assert data[0]['user_id'] == task_data["user_id"]
    assert data[0]['title'] == task_data["task"]
    assert data[1]['title'] == task_data_2["task"]


async def test_add_tag(async_session_test):
    # Create a sample task and tag
    task = Task(id=1, user_id=132, title="Test Task")
    tag = Tag(id=1, user_id=132, tag="Test Tag")
    async with async_session_test() as session:
        async with session.begin():
            session.add(task)
            session.add(tag)
        await session.commit()


    # Test add_tag function
    updated_task = await add_tag(task_id=1, tag_name="Test Tag", user_id=132, db=async_session_test)

    # Check if the tag was added to the task
    assert len(updated_task.tags) == 1
    assert updated_task.tags[0].tag == "Test Tag"

    # Test nonexistent task
    with pytest.raises(HTTPException) as exc_info:
        await add_tag(task_id=999, tag_name="Test Tag", user_id=None, db=async_session_test)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Task not found"
