"""Standalone seed script for local testing with SQLite.

Creates a test tenant and admin user directly in SQLite database.
Run with: python backend/scripts/seed_local.py
"""

import sys
import os
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.database import Base
from app.models.tenant import Tenant, SubscriptionTier
from app.models.user import User, UserRole
# Import all models to ensure they're registered
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.knowledge import KnowledgeDocument

# Use SQLite for local testing
DATABASE_URL = "sqlite:///./wafaa_test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_ADMIN = {
    "email": "admin@wafaa.test",
    "password": "admin123",
    "full_name": "Wafaa Admin",
}

TEST_TENANT = {
    "name": "Wafaa Demo Restaurant",
    "slug": "wafaa-demo",
    "subscription_tier": SubscriptionTier.premium,
    "settings": {"industry": "restaurant", "timezone": "UTC"},
}


def seed_database():
    """Create test tenant and admin user."""
    print("Creating SQLite database for local testing...")
    print("Database: " + DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(User).filter(User.email == TEST_ADMIN["email"]).first()
        if existing:
            print("\n[OK] User already exists!")
            print("  Email:    " + TEST_ADMIN["email"])
            print("  Password: " + TEST_ADMIN["password"])
            return
        
        # Create tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name=TEST_TENANT["name"],
            slug=TEST_TENANT["slug"],
            is_active=True,
            subscription_tier=TEST_TENANT["subscription_tier"],
            settings=TEST_TENANT["settings"],
        )
        db.add(tenant)
        db.flush()
        
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=TEST_ADMIN["email"],
            password_hash=get_password_hash(TEST_ADMIN["password"]),
            full_name=TEST_ADMIN["full_name"],
            role=UserRole.owner,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        
        print("\n" + "=" * 50)
        print("[OK] Database seeded successfully!")
        print("=" * 50)
        print("\n  Tenant:   " + TEST_TENANT["name"])
        print("  Email:    " + TEST_ADMIN["email"])
        print("  Password: " + TEST_ADMIN["password"])
        print("\n  Database file: wafaa_test.db")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print("Error: " + str(e))
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
