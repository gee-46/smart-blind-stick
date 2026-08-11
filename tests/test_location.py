"""Tests for the GPS/location endpoints."""


def test_get_latest_location(client, registered_device):
    response = client.get(f"/api/location/{registered_device}")
    assert response.status_code == 200
    body = response.json()
    assert body["device_id"] == registered_device
    assert isinstance(body["latitude"], float)
    assert isinstance(body["longitude"], float)


def test_location_history_accumulates(client, registered_device):
    for lat, lng in [(15.86, 74.50), (15.87, 74.51)]:
        client.post(
            "/api/device/data",
            json={
                "device_id": registered_device,
                "battery": 70,
                "latitude": lat,
                "longitude": lng,
                "status": "moving",
            },
        )

    response = client.get(f"/api/location/{registered_device}/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 3  # 1 from fixture + 2 above
    for point in history:
        assert "latitude" in point
        assert "longitude" in point
        assert "timestamp" in point


def test_location_history_limit(client, registered_device):
    response = client.get(f"/api/location/{registered_device}/history?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_location_unknown_device_returns_404(client):
    response = client.get("/api/location/DOES_NOT_EXIST")
    assert response.status_code == 404


def test_location_history_unknown_device_returns_404(client):
    response = client.get("/api/location/DOES_NOT_EXIST/history")
    assert response.status_code == 404
