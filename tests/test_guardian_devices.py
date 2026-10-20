"""Tests for guardian <-> device pairing."""


def test_pairing_unknown_device_fails(client, auth_headers):
    response = client.post(
        "/api/guardian/devices",
        json={"device_id": "GHOST_STICK", "nickname": "Nope"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_pairing_requires_auth(client, registered_device):
    response = client.post(
        "/api/guardian/devices", json={"device_id": registered_device}
    )
    assert response.status_code in (401, 403)


def test_pair_real_device_succeeds(client, auth_headers, registered_device):
    response = client.post(
        "/api/guardian/devices",
        json={"device_id": registered_device, "nickname": "Dad's Stick"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["device_id"] == registered_device
    assert body["nickname"] == "Dad's Stick"
    assert body["online"] is True


def test_pairing_same_device_twice_conflicts(client, auth_headers, paired_device):
    response = client.post(
        "/api/guardian/devices",
        json={"device_id": paired_device},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_list_paired_devices(client, auth_headers, paired_device):
    response = client.get("/api/guardian/devices", headers=auth_headers)
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) == 1
    assert devices[0]["device_id"] == paired_device


def test_list_devices_empty_for_new_guardian(client, auth_headers):
    response = client.get("/api/guardian/devices", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_unpair_device(client, auth_headers, paired_device):
    response = client.delete(f"/api/guardian/devices/{paired_device}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get("/api/guardian/devices", headers=auth_headers)
    assert response.json() == []


def test_unpair_unknown_pairing_returns_404(client, auth_headers):
    response = client.delete("/api/guardian/devices/NEVER_PAIRED", headers=auth_headers)
    assert response.status_code == 404


def test_second_guardian_cannot_see_first_guardians_device(client, auth_headers, paired_device):
    """Ownership must be per-guardian, not global."""
    other = client.post(
        "/api/auth/register",
        json={
            "email": "other-guardian@example.com",
            "password": "AnotherPass123",
            "full_name": "Other Guardian",
        },
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    response = client.get("/api/guardian/devices", headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []
