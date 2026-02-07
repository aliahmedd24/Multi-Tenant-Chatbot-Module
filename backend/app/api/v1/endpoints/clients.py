"""Client management endpoints."""

import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.multi_tenant import TenantContext
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.api.v1.endpoints.auth import get_current_user, get_current_superuser
from app.services.ai.vector_store import VectorStore


router = APIRouter()


def generate_slug(name: str) -> str:
    """Generate URL-safe slug from name.

    Args:
        name: Business name.

    Returns:
        URL-safe slug.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug[:100]


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
) -> Client:
    """Create a new client/tenant.

    Args:
        client_data: Client creation data.
        db: Database session.
        current_user: Authenticated superuser.

    Returns:
        Created client.
    """
    # Generate unique slug
    base_slug = generate_slug(client_data.name)
    slug = base_slug

    # Check for slug collision
    counter = 1
    while True:
        result = await db.execute(select(Client).where(Client.slug == slug))
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create client
    client = Client(
        name=client_data.name,
        slug=slug,
        email=client_data.email,
        subscription_tier=client_data.subscription_tier,
        description=client_data.description,
        settings=client_data.settings.model_dump() if client_data.settings else {},
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    # Create vector namespace for the client
    await VectorStore.create_namespace(str(client.id))

    return client


@router.get("/", response_model=list[ClientResponse])
async def list_clients(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
    skip: int = 0,
    limit: int = 100,
) -> list[Client]:
    """List all clients.

    Args:
        db: Database session.
        current_user: Authenticated superuser.
        skip: Pagination offset.
        limit: Maximum results.

    Returns:
        List of clients.
    """
    result = await db.execute(select(Client).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Client:
    """Get client by ID.

    Args:
        client_id: Client UUID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Client.
    """
    # Check access
    if not current_user.is_superuser and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Client:
    """Update a client.

    Args:
        client_id: Client UUID.
        client_data: Update data.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Updated client.
    """
    # Check access
    if not current_user.is_superuser and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Update fields
    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "settings" and value:
            client.settings = value.model_dump() if hasattr(value, "model_dump") else value
        else:
            setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
) -> None:
    """Delete a client.

    Args:
        client_id: Client UUID.
        db: Database session.
        current_user: Authenticated superuser.
    """
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    await db.delete(client)
    await db.commit()
