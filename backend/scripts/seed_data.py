"""Seed initial data for development and testing.

Creates 3 test tenant accounts with admin users for local development.
Run with: python scripts/seed_data.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.core.security import get_password_hash
from app.database import SessionLocal, engine, Base
from app.models.tenant import Tenant, SubscriptionTier
from app.models.user import User, UserRole

settings = get_settings()

SEED_TENANTS = [
    {
        "name": "Bite & Brew Restaurant",
        "slug": "bite-and-brew",
        "subscription_tier": SubscriptionTier.premium,
        "settings": {"industry": "restaurant", "timezone": "Asia/Riyadh"},
    },
    {
        "name": "StyleHub Retail",
        "slug": "stylehub",
        "subscription_tier": SubscriptionTier.basic,
        "settings": {"industry": "retail", "timezone": "Asia/Dubai"},
    },
    {
        "name": "Oasis Hotel Group",
        "slug": "oasis-hotel",
        "subscription_tier": SubscriptionTier.free,
        "settings": {"industry": "hospitality", "timezone": "Asia/Riyadh"},
    },
]

DEFAULT_PASSWORD = "changeme123"


def seed_tenants():
    """Create test tenants and admin users."""
    print("Seeding database...")
    print(f"Database URL: {settings.database_url}")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for tenant_data in SEED_TENANTS:
            # Skip if already exists
            existing = db.query(Tenant).filter(Tenant.slug == tenant_data["slug"]).first()
            if existing:
                print(f"  Tenant '{tenant_data['slug']}' already exists, skipping.")
                continue

            tenant = Tenant(
                name=tenant_data["name"],
                slug=tenant_data["slug"],
                is_active=True,
                subscription_tier=tenant_data["subscription_tier"],
                settings=tenant_data["settings"],
            )
            db.add(tenant)
            db.flush()

            # Create owner admin for each tenant
            email = f"admin@{tenant_data['slug']}.example.com"
            admin = User(
                tenant_id=tenant.id,
                email=email,
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                full_name=f"{tenant_data['name']} Admin",
                role=UserRole.owner,
                is_active=True,
            )
            db.add(admin)
            print(f"  Created tenant '{tenant.name}' with admin {email}")

        db.commit()
        print(f"\nSeed complete! Default password: {DEFAULT_PASSWORD}")
        print("Change passwords before using in any shared environment.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_tenants()
