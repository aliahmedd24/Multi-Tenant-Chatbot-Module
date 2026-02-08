"""Tests for health check endpoints."""


def test_root_health_check(client):
    """Test the root /health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data


def test_api_health_check(client):
    """Test the /api/v1/health endpoint returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_db_health_check(client):
    """Test the /api/v1/health/db endpoint."""
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    # With SQLite test DB, this should return healthy
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
