"""Verify project setup is correct.

Run with: python scripts/test_setup.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_imports():
    """Verify all core modules can be imported."""
    print("Checking imports...")
    try:
        from app.config import get_settings
        from app.database import Base, get_db
        from app.main import app
        from app.models.base import TenantModel, TimestampMixin
        from app.core.security import create_access_token, get_password_hash

        print("  All imports successful")
        return True
    except ImportError as e:
        print(f"  Import error: {e}")
        return False


def check_settings():
    """Verify settings load correctly."""
    print("Checking settings...")
    try:
        from app.config import get_settings

        settings = get_settings()
        print(f"  App name: {settings.app_name}")
        print(f"  Version: {settings.app_version}")
        print(f"  Debug: {settings.debug}")
        return True
    except Exception as e:
        print(f"  Settings error: {e}")
        return False


def check_database():
    """Verify database connection."""
    print("Checking database connection...")
    try:
        from sqlalchemy import text
        from app.database import SessionLocal

        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        print(f"  Database connected: {result.scalar() == 1}")
        db.close()
        return True
    except Exception as e:
        print(f"  Database error: {e}")
        print("  (This is expected if PostgreSQL is not running)")
        return False


def main():
    """Run all setup verification checks."""
    print("=" * 50)
    print("Wafaa Platform - Setup Verification")
    print("=" * 50)

    results = []
    results.append(("Imports", check_imports()))
    results.append(("Settings", check_settings()))
    results.append(("Database", check_database()))

    print("\n" + "=" * 50)
    print("Results:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    all_passed = all(r[1] for r in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
