"""Shared test fixtures for the Wafaa backend test suite."""

import os
import uuid

# Force mock vector store and LLM/embedding so tests don't call Pinecone/OpenAI
os.environ["VECTOR_DB_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import _token_blacklist
from app.core.security import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models.tenant import Tenant, SubscriptionTier
from app.models.user import User, UserRole
from app.services.vector_store import _mock_store

# Use SQLite in-memory for tests (no PostgreSQL dependency)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign key enforcement for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    _token_blacklist.clear()
    _mock_store.clear()


@pytest.fixture
def db():
    """Provide a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """Provide a test HTTP client with overridden DB dependency."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tenant & User fixtures
# ---------------------------------------------------------------------------

TENANT_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
USER_A_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_B_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

TEST_PASSWORD = "testpass123"


@pytest.fixture
def tenant_a(db) -> Tenant:
    """Create and return Tenant A."""
    t = Tenant(
        id=TENANT_A_ID,
        name="Tenant A",
        slug="tenant-a",
        is_active=True,
        subscription_tier=SubscriptionTier.basic,
        settings={},
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def tenant_b(db) -> Tenant:
    """Create and return Tenant B."""
    t = Tenant(
        id=TENANT_B_ID,
        name="Tenant B",
        slug="tenant-b",
        is_active=True,
        subscription_tier=SubscriptionTier.free,
        settings={},
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def user_a(db, tenant_a) -> User:
    """Create an owner user for Tenant A."""
    u = User(
        id=USER_A_ID,
        tenant_id=tenant_a.id,
        email="admin_a@example.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        full_name="Admin A",
        role=UserRole.owner,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def user_b(db, tenant_b) -> User:
    """Create an owner user for Tenant B."""
    u = User(
        id=USER_B_ID,
        tenant_id=tenant_b.id,
        email="admin_b@example.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        full_name="Admin B",
        role=UserRole.owner,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def token_a(user_a) -> str:
    """Return a valid access token for user A."""
    return create_access_token(
        data={"sub": str(user_a.id), "tenant_id": str(user_a.tenant_id)}
    )


@pytest.fixture
def token_b(user_b) -> str:
    """Return a valid access token for user B."""
    return create_access_token(
        data={"sub": str(user_b.id), "tenant_id": str(user_b.tenant_id)}
    )


@pytest.fixture
def auth_headers_a(token_a) -> dict:
    """Authorization headers for Tenant A owner."""
    return {"Authorization": f"Bearer {token_a}"}


@pytest.fixture
def auth_headers_b(token_b) -> dict:
    """Authorization headers for Tenant B owner."""
    return {"Authorization": f"Bearer {token_b}"}
