"""Admin endpoints for system management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_superuser


router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
) -> dict:
    """Get system-wide statistics.

    Args:
        db: Database session.
        current_user: Authenticated superuser.

    Returns:
        System statistics.
    """
    # Count clients
    client_result = await db.execute(select(func.count()).select_from(Client))
    client_count = client_result.scalar() or 0

    # Count active clients
    active_clients_result = await db.execute(
        select(func.count()).select_from(Client).where(Client.is_active == True)
    )
    active_client_count = active_clients_result.scalar() or 0

    # Count conversations
    conv_result = await db.execute(select(func.count()).select_from(Conversation))
    conversation_count = conv_result.scalar() or 0

    # Count messages
    msg_result = await db.execute(select(func.count()).select_from(Message))
    message_count = msg_result.scalar() or 0

    # Count knowledge documents
    doc_result = await db.execute(select(func.count()).select_from(KnowledgeDocument))
    document_count = doc_result.scalar() or 0

    # Count users
    user_result = await db.execute(select(func.count()).select_from(User))
    user_count = user_result.scalar() or 0

    return {
        "clients": {
            "total": client_count,
            "active": active_client_count,
        },
        "conversations": conversation_count,
        "messages": message_count,
        "knowledge_documents": document_count,
        "users": user_count,
    }


@router.get("/clients/{client_id}/stats")
async def get_client_stats(
    client_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
) -> dict:
    """Get statistics for a specific client.

    Args:
        client_id: Client UUID.
        db: Database session.
        current_user: Authenticated superuser.

    Returns:
        Client statistics.
    """
    from uuid import UUID

    try:
        uuid_client_id = UUID(client_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID format",
        )

    # Verify client exists
    result = await db.execute(select(Client).where(Client.id == uuid_client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Count conversations
    conv_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.client_id == uuid_client_id)
    )
    conversation_count = conv_result.scalar() or 0

    # Count messages via join
    msg_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .join(Conversation)
        .where(Conversation.client_id == uuid_client_id)
    )
    message_count = msg_result.scalar() or 0

    # Count knowledge documents
    doc_result = await db.execute(
        select(func.count())
        .select_from(KnowledgeDocument)
        .where(KnowledgeDocument.client_id == uuid_client_id)
    )
    document_count = doc_result.scalar() or 0

    # Sum chunks
    chunk_result = await db.execute(
        select(func.sum(KnowledgeDocument.chunk_count))
        .where(KnowledgeDocument.client_id == uuid_client_id)
    )
    chunk_count = chunk_result.scalar() or 0

    return {
        "client_id": str(uuid_client_id),
        "client_name": client.name,
        "is_active": client.is_active,
        "subscription_tier": client.subscription_tier,
        "conversations": conversation_count,
        "messages": message_count,
        "knowledge_documents": document_count,
        "knowledge_chunks": chunk_count,
    }
