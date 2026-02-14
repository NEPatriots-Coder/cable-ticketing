import pytest

import app as app_module

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "MongoClient", mongomock.MongoClient)
    flask_app = app_module.create_app()

    import app.routes as routes

    monkeypatch.setattr(routes, "notify_ticket_created", lambda ticket: None)
    monkeypatch.setattr(routes, "notify_status_change", lambda ticket, status: None)

    with flask_app.test_client() as test_client:
        yield test_client


def _create_user(client, username, email, role="user"):
    response = client.post(
        "/api/register",
        json={
            "username": username,
            "email": email,
            "phone": "555-000-0000",
            "password": "password123",
            "role": role,
        },
    )
    assert response.status_code in [200, 201]
    return response.get_json()["user"]


def _create_ticket(client, creator_id, assignee_id):
    response = client.post(
        "/api/tickets",
        json={
            "created_by_id": creator_id,
            "assigned_to_id": assignee_id,
            "items": [
                {"cable_type": "Cat6", "cable_length": "100m", "quantity": "1"},
            ],
            "notes": "test ticket",
        },
    )
    assert response.status_code == 201
    return response.get_json()["ticket"]


def test_soft_delete_and_visibility(client):
    creator = _create_user(client, "creator1", "creator1@example.com")
    assignee = _create_user(client, "assignee1", "assignee1@example.com")
    ticket = _create_ticket(client, creator["id"], assignee["id"])

    missing_actor = client.delete(f"/api/tickets/{ticket['id']}", json={})
    assert missing_actor.status_code == 400

    archived = client.delete(
        f"/api/tickets/{ticket['id']}",
        json={"user_id": creator["id"]},
    )
    assert archived.status_code == 200
    assert archived.get_json()["status"] == "deleted"

    listed = client.get("/api/tickets")
    assert listed.status_code == 200
    assert listed.get_json() == []

    listed_all = client.get("/api/tickets?include_deleted=true")
    assert listed_all.status_code == 200
    assert len(listed_all.get_json()) == 1
    assert listed_all.get_json()[0]["status"] == "deleted"
    assert listed_all.get_json()[0]["deleted_at"] is not None
    assert listed_all.get_json()[0]["deleted_by_id"] == creator["id"]

    second_archive = client.delete(
        f"/api/tickets/{ticket['id']}",
        json={"user_id": creator["id"]},
    )
    assert second_archive.status_code == 410

    get_deleted_default = client.get(f"/api/tickets/{ticket['id']}")
    assert get_deleted_default.status_code == 410

    get_deleted_included = client.get(f"/api/tickets/{ticket['id']}?include_deleted=true")
    assert get_deleted_included.status_code == 200
    assert get_deleted_included.get_json()["status"] == "deleted"

    stats = client.get("/api/dashboard/stats")
    assert stats.status_code == 200
    stats_payload = stats.get_json()
    assert stats_payload["archived"] == 1
    assert stats_payload["total_tickets"] == 0


def test_deleted_tickets_block_actions(client):
    creator = _create_user(client, "creator2", "creator2@example.com")
    assignee = _create_user(client, "assignee2", "assignee2@example.com")
    ticket = _create_ticket(client, creator["id"], assignee["id"])

    db = app_module.get_db()
    doc = db.tickets.find_one({"id": ticket["id"]})
    token = doc["approval_token"]

    client.delete(f"/api/tickets/{ticket['id']}", json={"user_id": creator["id"]})

    patch_deleted = client.patch(f"/api/tickets/{ticket['id']}", json={"status": "approved"})
    assert patch_deleted.status_code == 410

    approve_deleted = client.get(f"/api/tickets/{ticket['id']}/approve/{token}")
    assert approve_deleted.status_code == 410

    reject_deleted = client.post(
        f"/api/tickets/{ticket['id']}/reject/{token}",
        json={"reason": "not needed"},
    )
    assert reject_deleted.status_code == 410


def test_restore_purge_and_transition_validation(client):
    creator = _create_user(client, "creator3", "creator3@example.com")
    assignee = _create_user(client, "assignee3", "assignee3@example.com")
    admin = _create_user(client, "admin1", "admin1@example.com", role="admin")
    ticket = _create_ticket(client, creator["id"], assignee["id"])

    client.delete(f"/api/tickets/{ticket['id']}", json={"user_id": creator["id"]})

    forbidden_restore = client.post(
        f"/api/tickets/{ticket['id']}/restore",
        json={"user_id": assignee["id"]},
    )
    assert forbidden_restore.status_code == 403

    restored = client.post(
        f"/api/tickets/{ticket['id']}/restore",
        json={"user_id": creator["id"]},
    )
    assert restored.status_code == 200
    assert restored.get_json()["ticket"]["status"] == "pending_approval"

    invalid_transition = client.patch(
        f"/api/tickets/{ticket['id']}",
        json={"status": "fulfilled"},
    )
    assert invalid_transition.status_code == 409

    valid_transition = client.patch(
        f"/api/tickets/{ticket['id']}",
        json={"status": "approved"},
    )
    assert valid_transition.status_code == 200
    assert valid_transition.get_json()["ticket"]["status"] == "approved"

    client.delete(f"/api/tickets/{ticket['id']}", json={"user_id": creator["id"]})

    forbidden_purge = client.delete(
        f"/api/tickets/{ticket['id']}/purge",
        json={"user_id": creator["id"]},
    )
    assert forbidden_purge.status_code == 403

    purged = client.delete(
        f"/api/tickets/{ticket['id']}/purge",
        json={"user_id": admin["id"]},
    )
    assert purged.status_code == 200

    get_after_purge = client.get(f"/api/tickets/{ticket['id']}?include_deleted=true")
    assert get_after_purge.status_code == 404


def test_cable_receiving_creates_positive_inventory(client):
    admin = _create_user(client, "admin2", "admin2@example.com", role="admin")
    user = _create_user(client, "user4", "user4@example.com")

    forbidden = client.post(
        "/api/cable-receiving",
        json={
            "user_id": user["id"],
            "vendor": "CableCo",
            "items": [{"cable_type": "Cat6", "cable_length": "100m", "quantity": 5}],
        },
    )
    assert forbidden.status_code == 403

    created = client.post(
        "/api/cable-receiving",
        json={
            "user_id": admin["id"],
            "vendor": "CableCo",
            "po_number": "PO-100",
            "items": [
                {"cable_type": "Cat6", "cable_length": "100m", "quantity": 5},
                {"cable_type": "Fiber", "cable_length": "200m", "quantity": 2},
            ],
        },
    )
    assert created.status_code == 201
    payload = created.get_json()["receipt"]
    assert payload["vendor"] == "CableCo"
    assert len(payload["items"]) == 2

    on_hand = client.get("/api/inventory/on-hand")
    assert on_hand.status_code == 200
    entries = on_hand.get_json()
    assert {"cable_type": "Cat6", "cable_length": "100m", "on_hand": 5} in entries
    assert {"cable_type": "Fiber", "cable_length": "200m", "on_hand": 2} in entries


def test_ticket_fulfillment_creates_consumption_movements(client):
    creator = _create_user(client, "creator5", "creator5@example.com")
    assignee = _create_user(client, "assignee5", "assignee5@example.com")
    admin = _create_user(client, "admin5", "admin5@example.com", role="admin")

    receipt = client.post(
        "/api/cable-receiving",
        json={
            "user_id": admin["id"],
            "items": [{"cable_type": "Cat6", "cable_length": "100m", "quantity": 10}],
        },
    )
    assert receipt.status_code == 201

    ticket = _create_ticket(client, creator["id"], assignee["id"])
    to_approved = client.patch(f"/api/tickets/{ticket['id']}", json={"status": "approved"})
    assert to_approved.status_code == 200
    to_in_progress = client.patch(f"/api/tickets/{ticket['id']}", json={"status": "in_progress"})
    assert to_in_progress.status_code == 200
    to_fulfilled = client.patch(f"/api/tickets/{ticket['id']}", json={"status": "fulfilled"})
    assert to_fulfilled.status_code == 200

    movements = client.get("/api/inventory/movements?source_type=ticket_fulfillment")
    assert movements.status_code == 200
    movement_rows = movements.get_json()
    assert len(movement_rows) == 1
    assert movement_rows[0]["movement_type"] == "consumption"
    assert movement_rows[0]["quantity_delta"] == -1

    on_hand = client.get("/api/inventory/on-hand")
    assert on_hand.status_code == 200
    assert {"cable_type": "Cat6", "cable_length": "100m", "on_hand": 9} in on_hand.get_json()
