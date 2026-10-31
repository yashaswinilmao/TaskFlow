import pytest
from app import create_app, db, User, Task

@pytest.fixture()
def client(tmp_path):
    database = tmp_path / "test.db"
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}",
        "WTF_CSRF_ENABLED": False,
    })
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()

def register(client, username="tester", password="secret123"):
    return client.post("/register", data={"username": username, "password": password}, follow_redirects=True)

def test_register_and_dashboard(client):
    response = register(client)
    assert response.status_code == 200
    assert b"Your tasks" in response.data

def test_create_and_complete_task(client):
    register(client)
    response = client.post("/tasks", data={
        "title": "Finish assignment", "description": "Write tests",
        "priority": "High", "due_date": ""
    }, follow_redirects=True)
    assert b"Finish assignment" in response.data
    with client.application.app_context():
        task = Task.query.filter_by(title="Finish assignment").first()
        assert task is not None
        task_id = task.id
    response = client.post(f"/tasks/{task_id}/toggle", follow_redirects=True)
    assert response.status_code == 200
    with client.application.app_context():
        assert db.session.get(Task, task_id).completed is True

def test_user_cannot_access_another_users_task(client):
    register(client, "firstuser")
    client.post("/tasks", data={"title": "Private task"}, follow_redirects=True)
    with client.application.app_context():
        task_id = Task.query.first().id
    client.post("/logout")
    register(client, "seconduser")
    response = client.post(f"/tasks/{task_id}/delete")
    assert response.status_code == 404
