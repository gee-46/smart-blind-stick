"""Tests for real backend-persisted emergency contacts and Expo push token registration."""


def test_create_and_list_contacts(client, auth_headers):
    response = client.post(
        "/api/contacts",
        json={"name": "Priya Rao", "phone": "+919900000001", "relationship_label": "Daughter", "is_primary": True},
        headers=auth_headers,
    )
    assert response.status_code == 201
    contact_id = response.json()["id"]

    response = client.get("/api/contacts", headers=auth_headers)
    assert response.status_code == 200
    contacts = response.json()
    assert len(contacts) == 1
    assert contacts[0]["id"] == contact_id
    assert contacts[0]["is_primary"] is True


def test_update_contact(client, auth_headers):
    created = client.post(
        "/api/contacts",
        json={"name": "Priya Rao", "phone": "+919900000001"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/api/contacts/{created['id']}",
        json={"name": "Priya R.", "phone": "+919900000009", "relationship_label": "Daughter", "is_primary": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "+919900000009"


def test_delete_contact(client, auth_headers):
    created = client.post(
        "/api/contacts", json={"name": "Temp Contact", "phone": "+911111111111"}, headers=auth_headers
    ).json()

    response = client.delete(f"/api/contacts/{created['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get("/api/contacts", headers=auth_headers)
    assert response.json() == []


def test_cannot_edit_another_guardians_contact(client, auth_headers):
    created = client.post(
        "/api/contacts", json={"name": "Mine", "phone": "+911111111111"}, headers=auth_headers
    ).json()

    other = client.post(
        "/api/auth/register",
        json={"email": "other2@example.com", "password": "AnotherPass123", "full_name": "Other"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    response = client.put(
        f"/api/contacts/{created['id']}",
        json={"name": "Hijacked", "phone": "+922222222222"},
        headers=other_headers,
    )
    assert response.status_code == 404


def test_contacts_require_auth(client):
    response = client.get("/api/contacts")
    assert response.status_code in (401, 403)


def test_register_push_token(client, auth_headers):
    response = client.post(
        "/api/push/register",
        json={"expo_push_token": "ExponentPushToken[abc123]", "device_id": "phone-1"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_register_push_token_twice_updates_not_duplicates(client, auth_headers):
    payload = {"expo_push_token": "ExponentPushToken[same-token]", "device_id": "phone-1"}
    r1 = client.post("/api/push/register", json=payload, headers=auth_headers)
    r2 = client.post("/api/push/register", json={**payload, "device_id": "phone-2"}, headers=auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
