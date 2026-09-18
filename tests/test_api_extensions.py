import pytest
from fastapi.testclient import TestClient
from app.main import app, MAX_PHOTO_SIZE
from app.services import collaboration as collab


def test_photo_interpret_empty_file_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/photo/interpret",
            files={"file": ("empty.png", b"", "image/png")}
        )
        assert response.status_code == 400
        assert "vacío" in response.json()["detail"]


def test_photo_interpret_oversized_file_rejected(monkeypatch):
    monkeypatch.setattr("app.main.MAX_PHOTO_SIZE", 1024)  # Temporarily set to 1KB
    with TestClient(app) as client:
        response = client.post(
            "/api/photo/interpret",
            files={"file": ("large.png", b"x" * 2048, "image/png")}
        )
        assert response.status_code == 413
        assert "excede el límite" in response.json()["detail"]


def test_collaboration_rate_limiting(monkeypatch):
    collab._rate_limits.clear()
    d = {'name': 'Test', 'classes': [], 'relationships': []}
    with TestClient(app) as client:
        # Rapidly fire requests to trigger rate limit
        hit_429 = False
        for _ in range(35):
            res = client.post("/api/collaboration/projects", json={"diagram": d})
            if res.status_code == 429:
                hit_429 = True
                break
        assert hit_429, "Expected 429 Too Many Requests after threshold"
    collab._rate_limits.clear()


def test_unified_projects_includes_collab_rooms(tmp_path, monkeypatch):
    test_db = tmp_path / "test_collab.sqlite3"
    custom_store = collab.Store(test_db)
    d = {'name': 'CollabRoomTest', 'classes': [{'id': 'c1', 'name': 'Item', 'attributes': [], 'position': {'x': 0, 'y': 0}}], 'relationships': []}
    created = custom_store.create(d)
    room_id = created['projectId']

    monkeypatch.setattr(collab, 'store', custom_store)

    with TestClient(app) as client:
        # Retrieve collaborative project via main API
        res = client.get(f"/api/projects/{room_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == room_id
        assert data["name"] == "CollabRoomTest"
        assert data.get("isCollaborative") is True
