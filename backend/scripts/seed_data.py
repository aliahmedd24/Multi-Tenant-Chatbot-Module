"""Seed initial data for development and testing.

Creates test tenant accounts for local development.
Run with: python scripts/seed_data.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import SessionLocal, engine, Base

settings = get_settings()


def seed_tenants():
    """Create test tenant accounts.

    Full tenant model will be implemented in Phase 1.
    This script will be updated as models are added.
    """
    print("Seeding database...")
    print(f"Database URL: {settings.database_url}")

    # Create all tables (Phase 0: just ensures connection works)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Phase 0: Verify database connectivity
        from sqlalchemy import text

        result = db.execute(text("SELECT 1"))
        print(f"Database connection verified: {result.scalar()}")

        print("\nSeed data will be expanded in Phase 1 with:")
        print("  - 3 test tenants (restaurant, retail, hospitality)")
        print("  - Admin users for each tenant")
        print("  - Sample configuration data")

        print("\nSeed complete!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_tenants()
