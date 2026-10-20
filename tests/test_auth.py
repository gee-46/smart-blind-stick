"""Tests for guardian registration, login, refresh, and /me."""


def test_register_creates_real_account_and_returns_tokens(client):
    payload = {
        "email": "newguardian@example.com",
        "password": "SuperSecret123",
        "full_name": "Ravi Kumar",
        "phone": "+919900000002",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["guardian"]["email"] == payload["email"]
    assert body["guardian"]["full_name"] == payload["full_name"]
    assert "password" not in body["guardian"]


def test_register_rejects_duplicate_email(client, guardian_tokens):
    response = client.post(
        "/api/auth/register",
        json={
            "email": guardian_tokens["guardian"]["email"],
            "password": "AnotherPass123",
            "full_name": "Someone Else",
        },
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "shortpw@example.com", "password": "short", "full_name": "X"},
    )
    assert response.status_code == 422


def test_login_with_correct_credentials(client, guardian_tokens):
    response = client.post(
        "/api/auth/login",
        json={"email": guardian_tokens["guardian"]["email"], "password": "SuperSecret123"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_fails(client, guardian_tokens):
    response = client.post(
        "/api/auth/login",
        json={"email": guardian_tokens["guardian"]["email"], "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_login_with_unknown_email_fails(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "whatever123"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code in (401, 403)


def test_me_returns_current_guardian(client, guardian_tokens, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == guardian_tokens["guardian"]["email"]


def test_me_rejects_garbage_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_refresh_returns_new_access_token(client, guardian_tokens):
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": guardian_tokens["refresh_token"]}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_rejects_access_token_used_as_refresh(client, guardian_tokens):
    """An access token must not work as a refresh token (type check)."""
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": guardian_tokens["access_token"]}
    )
    assert response.status_code == 401


def test_logout_requires_auth_and_succeeds(client, auth_headers, guardian_tokens):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 204
