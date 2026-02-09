"""Tests for authentication endpoints."""

from datetime import datetime, timedelta

from jose import jwt

from app.config import get_settings
from app.core.security import create_refresh_token

settings = get_settings()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------


def test_login_success(client, user_a):
    """Valid credentials return access and refresh tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin_a@example.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify the access token contains correct claims
    payload = jwt.decode(
        data["access_token"], settings.secret_key, algorithms=[settings.algorithm]
    )
    assert payload["sub"] == str(user_a.id)
    assert payload["tenant_id"] == str(user_a.tenant_id)
    assert payload["type"] == "access"


def test_login_wrong_password(client, user_a):
    """Wrong password returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin_a@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_email(client, user_a):
    """Unknown email returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "testpass123"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client, db, user_a):
    """Inactive user cannot log in."""
    user_a.is_active = False
    db.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin_a@example.com", "password": "testpass123"},
    )
    assert response.status_code == 403


def test_login_inactive_tenant(client, db, tenant_a, user_a):
    """User from inactive tenant cannot log in."""
    tenant_a.is_active = False
    db.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin_a@example.com", "password": "testpass123"},
    )
    assert response.status_code == 403


def test_login_updates_last_login(client, db, user_a):
    """Successful login updates last_login timestamp."""
    assert user_a.last_login is None
    client.post(
        "/api/v1/auth/login",
        json={"email": "admin_a@example.com", "password": "testpass123"},
    )
    db.refresh(user_a)
    assert user_a.last_login is not None


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------


def test_refresh_success(client, user_a):
    """Valid refresh token returns new token pair."""
    refresh = create_refresh_token(
        data={"sub": str(user_a.id), "tenant_id": str(user_a.tenant_id)}
    )
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_with_access_token_fails(client, token_a):
    """Using an access token as a refresh token is rejected."""
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": token_a}
    )
    assert response.status_code == 401


def test_refresh_with_invalid_token(client, user_a):
    """Garbage token is rejected."""
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not.a.token"}
    )
    assert response.status_code == 401


def test_refresh_with_expired_token(client, user_a):
    """Expired refresh token is rejected."""
    expired = jwt.encode(
        {
            "sub": str(user_a.id),
            "tenant_id": str(user_a.tenant_id),
            "exp": datetime.utcnow() - timedelta(seconds=1),
            "type": "refresh",
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": expired}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout
# ---------------------------------------------------------------------------


def test_logout_invalidates_token(client, auth_headers_a):
    """After logout the same token is rejected."""
    # Verify token works before logout
    response = client.get("/api/v1/tenants/me", headers=auth_headers_a)
    assert response.status_code == 200

    # Logout
    response = client.post("/api/v1/auth/logout", headers=auth_headers_a)
    assert response.status_code == 204

    # Same token should now fail
    response = client.get("/api/v1/tenants/me", headers=auth_headers_a)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoint without token
# ---------------------------------------------------------------------------


def test_protected_endpoint_no_token(client, tenant_a):
    """Accessing a protected endpoint without a token returns 401."""
    response = client.get("/api/v1/tenants/me")
    assert response.status_code == 401
