def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_work_order_lifecycle(client):
    created = client.post(
        "/work-orders",
        json={"title": "Inspect compressor", "priority": "high", "assignee": "Kamal"},
    )
    assert created.status_code == 201
    work_order = created.json()
    assert work_order["status"] == "open"
    assert work_order["updated_at"]

    item_id = work_order["id"]
    updated = client.patch(f"/work-orders/{item_id}", json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    filtered = client.get("/work-orders?status=done")
    assert filtered.status_code == 200
    assert filtered.headers["X-Total-Count"] == "1"
    assert any(item["id"] == item_id for item in filtered.json())

    deleted = client.delete(f"/work-orders/{item_id}")
    assert deleted.status_code == 204
    assert client.get(f"/work-orders/{item_id}").status_code == 404


def test_validation_rejects_short_title(client):
    response = client.post("/work-orders", json={"title": "x"})
    assert response.status_code == 422


def test_pagination_and_sorting(client):
    for title in ["Charlie", "Alpha", "Bravo"]:
        response = client.post("/work-orders", json={"title": title})
        assert response.status_code == 201

    first_page = client.get("/work-orders?sort_by=title&sort_order=asc&limit=2&offset=0")
    assert first_page.status_code == 200
    assert first_page.headers["X-Total-Count"] == "3"
    assert [item["title"] for item in first_page.json()] == ["Alpha", "Bravo"]

    second_page = client.get("/work-orders?sort_by=title&sort_order=asc&limit=2&offset=2")
    assert [item["title"] for item in second_page.json()] == ["Charlie"]


def test_filter_by_assignee(client):
    client.post("/work-orders", json={"title": "Pump inspection", "assignee": "Dana"})
    client.post("/work-orders", json={"title": "Valve inspection", "assignee": "Kamal"})

    response = client.get("/work-orders?assignee=Kamal")
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "1"
    assert [item["assignee"] for item in response.json()] == ["Kamal"]


def test_invalid_pagination_is_rejected(client):
    assert client.get("/work-orders?limit=0").status_code == 422
    assert client.get("/work-orders?limit=101").status_code == 422
    assert client.get("/work-orders?offset=-1").status_code == 422
