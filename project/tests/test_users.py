from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_read_user():
    # Create
    resp = client.post("/users/", json={
        "username": "bob", "email": "bob@example.com", "password": "pwd"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "bob"

    # Me
    token = client.post("/users/token", json={}).json()["access_token"]
    resp2 = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200