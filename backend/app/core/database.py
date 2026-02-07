"""Database configuration and session management.

Provides async SQLAlchemy engine, session factory, and dependency injection.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.multi_tenant import TenantContext


# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with tenant context.

    Yields:
        AsyncSession: Database session with tenant context set.

    Note:
        Sets PostgreSQL session variable for RLS policies.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set tenant context for RLS
            tenant_id = TenantContext.get_tenant()
            if tenant_id:
                await session.execute(
                    f"SET app.current_tenant_id = '{tenant_id}'"  # noqa: S608
                )
            yield session
        finally:
            await session.close()


# Type alias for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
