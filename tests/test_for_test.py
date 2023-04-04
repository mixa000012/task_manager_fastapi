import json
import datetime

async def test_create_user(client, get_user_from_database):
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
    task = await get_user_from_database(data_from_resp["user_id"])
    assert task is not None
    assert len(task) == 1
    task_from_db = dict(task[0])
    assert task_from_db['user_id'] == task_data["user_id"]
    assert  task_from_db['title'] == task_data["title"]


