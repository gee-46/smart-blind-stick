"""
Shared pytest fixtures.

Uses a separate on-disk SQLite test database (test_smart_blind_stick.db)
so tests never touch the real development database, and overrides the
`get_db` FastAPI dependency to use it.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_PATH = "test_smart_blind_stick.db"
TEST_DATABASE_URL = f"sqlite:///./{TEST_DB_PATH}"

# Ensure the app picks up the test DB URL before any app module is imported.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.database.base import Base  # noqa: E402
from app.database.database import get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create tables once for the whole test session, drop them after."""
    from app.models import device, location, event, guardian  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture()
def client():
    # Entering as a context manager runs the app's lifespan (startup/shutdown),
    # which is required so websocket_manager.main_event_loop gets captured
    # and the offline-watcher background task starts -- matching real
    # runtime behavior instead of only exercising routes in isolation.
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def registered_device(client):
    """Creates a device via the real API so tests can build on it."""
    payload = {
        "device_id": "TEST_STICK_001",
        "battery": 90,
        "latitude": 15.8497,
        "longitude": 74.4977,
        "status": "safe",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 200
    return payload["device_id"]


@pytest.fixture()
def guardian_tokens(client):
    """Registers a real guardian account via the API and returns its token pair."""
    payload = {
        "email": f"guardian-{uuid.uuid4().hex[:8]}@example.com",
        "password": "SuperSecret123",
        "full_name": "Asha Rao",
        "phone": "+919900000000",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture()
def auth_headers(guardian_tokens):
    return {"Authorization": f"Bearer {guardian_tokens['access_token']}"}


@pytest.fixture()
def paired_device(client, auth_headers, registered_device):
    """A device that has both checked in AND been paired to the test guardian."""
    response = client.post(
        "/api/guardian/devices",
        json={"device_id": registered_device, "nickname": "Test Stick"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return registered_device
