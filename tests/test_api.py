def register(client, email="viewer@example.com", password="viewer-password", full_name="Viewer"):
    return client.post("/auth/register", json={"email": email, "password": password, "full_name": full_name})


def login_headers(client, email, password):
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_and_readiness(client):
    assert client.get("/").json()["docs"] == "/docs"
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_register_login_and_me(client):
    created = register(client, email="USER@Example.com", full_name="Test User")
    assert created.status_code == 201
    assert created.json()["email"] == "user@example.com"
    assert created.json()["role"] == "viewer"

    headers = login_headers(client, "user@example.com", "viewer-password")
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["full_name"] == "Test User"


def test_duplicate_registration_and_bad_login(client):
    assert register(client).status_code == 201
    assert register(client, email="VIEWER@example.com").status_code == 409
    bad = client.post(
        "/auth/token",
        data={"username": "viewer@example.com", "password": "wrong-password"},
    )
    assert bad.status_code == 401


def test_work_orders_require_authentication(client):
    assert client.get("/work-orders").status_code == 401
    assert client.post("/work-orders", json={"title": "Inspect pump"}).status_code == 401


def test_viewer_can_read_but_cannot_modify(client, admin_headers):
    created = client.post("/work-orders", json={"title": "Inspect pump"}, headers=admin_headers)
    assert created.status_code == 201

    assert register(client).status_code == 201
    viewer = login_headers(client, "viewer@example.com", "viewer-password")
    assert client.get("/work-orders", headers=viewer).status_code == 200
    assert client.post(
        "/work-orders", json={"title": "Unauthorized create"}, headers=viewer
    ).status_code == 403
    assert client.patch(
        f"/work-orders/{created.json()['id']}", json={"status": "done"}, headers=viewer
    ).status_code == 403
    assert client.delete(f"/work-orders/{created.json()['id']}", headers=viewer).status_code == 403


def test_admin_can_manage_roles(client, admin_headers):
    user = register(client, email="tech@example.com", password="technician-password").json()
    promoted = client.patch(
        f"/users/{user['id']}/role",
        json={"role": "technician"},
        headers=admin_headers,
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "technician"

    users = client.get("/users", headers=admin_headers)
    assert users.status_code == 200
    assert {item["email"] for item in users.json()} >= {"admin@example.com", "tech@example.com"}

    technician = login_headers(client, "tech@example.com", "technician-password")
    item = client.post("/work-orders", json={"title": "Technician task"}, headers=technician)
    assert item.status_code == 201
    assert item.json()["created_by_id"] == user["id"]
    assert client.patch(
        f"/work-orders/{item.json()['id']}", json={"status": "done"}, headers=technician
    ).status_code == 200
    assert client.delete(f"/work-orders/{item.json()['id']}", headers=technician).status_code == 403


def test_work_order_lifecycle(client, admin_headers):
    created = client.post(
        "/work-orders",
        json={"title": "Inspect compressor", "priority": "high", "assignee": "Kamal"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    work_order = created.json()
    assert work_order["status"] == "open"
    assert work_order["created_by_id"] is not None

    item_id = work_order["id"]
    updated = client.patch(
        f"/work-orders/{item_id}", json={"status": "done"}, headers=admin_headers
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    filtered = client.get("/work-orders?status=done", headers=admin_headers)
    assert filtered.status_code == 200
    assert filtered.headers["X-Total-Count"] == "1"

    assert client.delete(f"/work-orders/{item_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/work-orders/{item_id}", headers=admin_headers).status_code == 404


def test_validation_rejects_short_title(client, admin_headers):
    response = client.post("/work-orders", json={"title": "x"}, headers=admin_headers)
    assert response.status_code == 422


def test_pagination_sorting_and_filtering(client, admin_headers):
    for title, assignee in [("Charlie", "Dana"), ("Alpha", "Kamal"), ("Bravo", "Kamal")]:
        response = client.post(
            "/work-orders", json={"title": title, "assignee": assignee}, headers=admin_headers
        )
        assert response.status_code == 201

    first_page = client.get(
        "/work-orders?sort_by=title&sort_order=asc&limit=2", headers=admin_headers
    )
    assert first_page.headers["X-Total-Count"] == "3"
    assert [item["title"] for item in first_page.json()] == ["Alpha", "Bravo"]

    filtered = client.get("/work-orders?assignee=Kamal", headers=admin_headers)
    assert filtered.headers["X-Total-Count"] == "2"


def test_invalid_pagination_is_rejected(client, admin_headers):
    assert client.get("/work-orders?limit=0", headers=admin_headers).status_code == 422
    assert client.get("/work-orders?limit=101", headers=admin_headers).status_code == 422
    assert client.get("/work-orders?offset=-1", headers=admin_headers).status_code == 422


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer definitely-not-a-jwt"}
    )
    assert response.status_code == 401
