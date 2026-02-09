"""Tests for tenant management endpoints."""

from app.models.user import User


# ---------------------------------------------------------------------------
# GET /api/v1/tenants/me
# ---------------------------------------------------------------------------


def test_get_current_tenant(client, auth_headers_a, tenant_a):
    """Authenticated user can retrieve their tenant."""
    response = client.get("/api/v1/tenants/me", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tenant A"
    assert data["slug"] == "tenant-a"
    assert data["is_active"] is True


# ---------------------------------------------------------------------------
# PATCH /api/v1/tenants/me
# ---------------------------------------------------------------------------


def test_update_tenant_name(client, auth_headers_a, tenant_a):
    """Owner can update tenant name."""
    response = client.patch(
        "/api/v1/tenants/me",
        headers=auth_headers_a,
        json={"name": "Updated Tenant A"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Tenant A"


def test_update_tenant_settings(client, auth_headers_a, tenant_a):
    """Owner can update tenant settings JSON."""
    response = client.patch(
        "/api/v1/tenants/me",
        headers=auth_headers_a,
        json={"settings": {"welcome_message": "Hello!"}},
    )
    assert response.status_code == 200
    assert response.json()["settings"]["welcome_message"] == "Hello!"


def test_update_tenant_viewer_forbidden(client, db, tenant_a, user_a):
    """Viewer cannot update tenant."""
    from app.core.security import create_access_token
    from app.models.user import UserRole

    user_a.role = UserRole.viewer
    db.commit()

    token = create_access_token(
        data={"sub": str(user_a.id), "tenant_id": str(user_a.tenant_id)}
    )
    response = client.patch(
        "/api/v1/tenants/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Hacked"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/tenants/me/admins
# ---------------------------------------------------------------------------


def test_list_admins(client, auth_headers_a, user_a):
    """Owner can list admins for their tenant."""
    response = client.get("/api/v1/tenants/me/admins", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "admin_a@example.com"
    # Password hash must never be exposed
    assert "password_hash" not in data[0]


# ---------------------------------------------------------------------------
# POST /api/v1/tenants/me/admins
# ---------------------------------------------------------------------------


def test_create_admin(client, auth_headers_a, user_a, db):
    """Owner can create a new admin user."""
    response = client.post(
        "/api/v1/tenants/me/admins",
        headers=auth_headers_a,
        json={
            "email": "new_admin@example.com",
            "password": "securepass123",
            "full_name": "New Admin",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_admin@example.com"
    assert data["role"] == "admin"
    assert data["tenant_id"] == str(user_a.tenant_id)

    # Verify created in DB with correct tenant
    new_user = db.query(User).filter(User.email == "new_admin@example.com").first()
    assert new_user is not None
    assert new_user.tenant_id == user_a.tenant_id


def test_create_admin_duplicate_email(client, auth_headers_a, user_a):
    """Cannot create admin with existing email."""
    response = client.post(
        "/api/v1/tenants/me/admins",
        headers=auth_headers_a,
        json={
            "email": "admin_a@example.com",
            "password": "securepass123",
            "full_name": "Duplicate",
            "role": "viewer",
        },
    )
    assert response.status_code == 409


def test_create_admin_viewer_forbidden(client, db, tenant_a, user_a):
    """Viewer cannot create admins."""
    from app.core.security import create_access_token
    from app.models.user import UserRole

    user_a.role = UserRole.viewer
    db.commit()

    token = create_access_token(
        data={"sub": str(user_a.id), "tenant_id": str(user_a.tenant_id)}
    )
    response = client.post(
        "/api/v1/tenants/me/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "hack@example.com",
            "password": "password123",
            "full_name": "Hacker",
            "role": "admin",
        },
    )
    assert response.status_code == 403


def test_create_admin_short_password(client, auth_headers_a, user_a):
    """Password shorter than 8 chars is rejected by schema validation."""
    response = client.post(
        "/api/v1/tenants/me/admins",
        headers=auth_headers_a,
        json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short Pass",
            "role": "viewer",
        },
    )
    assert response.status_code == 422
