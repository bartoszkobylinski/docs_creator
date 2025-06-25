from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_list_items():
    token = client.post("/users/token", json={}).json()["access_token"]
    resp = client.post(
        "/items/", json={"name": "foo", "description": "bar"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    resp2 = client.get("/items/?skip=0&limit=5")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 5