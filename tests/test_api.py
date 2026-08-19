from pathlib import Path

from fastapi.testclient import TestClient

DB = Path("fieldops.db")
if DB.exists():
    DB.unlink()

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_work_order_lifecycle():
    created = client.post("/work-orders", json={"title": "Inspect compressor", "priority": "high", "assignee": "Kamal"})
    assert created.status_code == 201
    work_order = created.json()
    assert work_order["status"] == "open"
    item_id = work_order["id"]
    updated = client.patch(f"/work-orders/{item_id}", json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    filtered = client.get("/work-orders?status=done")
    assert filtered.status_code == 200
    assert any(item["id"] == item_id for item in filtered.json())
    deleted = client.delete(f"/work-orders/{item_id}")
    assert deleted.status_code == 204
    assert client.get(f"/work-orders/{item_id}").status_code == 404


def test_validation_rejects_short_title():
    response = client.post("/work-orders", json={"title": "x"})
    assert response.status_code == 422
