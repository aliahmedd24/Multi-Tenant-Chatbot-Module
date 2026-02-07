"""Chat endpoints."""

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.multi_tenant import TenantContext
from app.models.client import Client
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ChatRequest, ChatResponse, ConversationResponse
from app.api.v1.endpoints.auth import get_current_user
from app.services.orchestrator.chat_orchestrator import ChatOrchestrator


router = APIRouter()


async def get_client_or_404(client_id: UUID, db: AsyncSession) -> Client:
    """Get client by ID or raise 404.

    Args:
        client_id: Client UUID.
        db: Database session.

    Returns:
        Client.

    Raises:
        HTTPException: If client not found.
    """
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client is inactive",
        )

    TenantContext.set_tenant(client_id)
    return client


@router.post("/", response_model=ChatResponse)
async def send_message(
    client_id: UUID,
    chat_request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    """Send a chat message and get AI response.

    Args:
        client_id: Client UUID.
        chat_request: Chat request with message.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        AI response with conversation ID.
    """
    client = await get_client_or_404(client_id, db)

    # Verify access
    if not current_user.is_superuser and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get or create conversation
    conversation = None
    if chat_request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == chat_request.conversation_id,
                Conversation.client_id == client_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        # Create new conversation
        conversation = Conversation(
            client_id=client_id,
            sender_id=chat_request.sender_id,
            channel=chat_request.channel,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # Process message with orchestrator
    orchestrator = ChatOrchestrator()
    try:
        result = await orchestrator.process_message(
            message=chat_request.message,
            sender_id=chat_request.sender_id,
            channel=chat_request.channel,
            client_id=client_id,
            client_name=client.name,
            conversation_id=conversation.id,
            response_tone=client.response_tone,
            max_tokens=client.max_tokens,
        )
    finally:
        await orchestrator.close()

    # Save messages to database
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.message,
    )
    db.add(user_message)

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["response"],
        metadata={"intent": result.get("intent")},
    )
    db.add(assistant_message)
    await db.commit()

    return ChatResponse(
        message=result["response"],
        conversation_id=conversation.id,
        metadata=result.get("metadata"),
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
) -> list[Conversation]:
    """List conversations for a client.

    Args:
        client_id: Client UUID.
        db: Database session.
        current_user: Authenticated user.
        skip: Pagination offset.
        limit: Maximum results.

    Returns:
        List of conversations.
    """
    await get_client_or_404(client_id, db)

    if not current_user.is_superuser and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(
        select(Conversation)
        .where(Conversation.client_id == client_id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(result.scalars().all())


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    client_id: UUID,
    conversation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Conversation:
    """Get a conversation with messages.

    Args:
        client_id: Client UUID.
        conversation_id: Conversation UUID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Conversation with messages.
    """
    await get_client_or_404(client_id, db)

    if not current_user.is_superuser and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.client_id == client_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation
