
"""Shared pytest fixtures for API and Safety & Emergency tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.services.notification_service import MockNotificationService


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database schema for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    MockNotificationService.clear_history()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provide a test client using the isolated test database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def registered_device(client):
    """Register a device for tests that need an existing device."""
    payload = {
        "device_id": "TEST_STICK_001",
        "battery": 90,
        "latitude": 15.8497,
        "longitude": 74.4977,
        "status": "safe",
    }

    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 200, response.text

    return payload["device_id"]
