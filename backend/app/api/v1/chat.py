"""Chat API endpoint for RAG-powered conversations."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.channel import Channel
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageDirection, MessageStatus
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, SourceDocument, UsageMetrics
from app.services.rag_engine import rag_query

router = APIRouter()


def _get_or_create_dashboard_channel(db: Session, tenant_id: uuid.UUID) -> Channel:
    """Get or create the in-app chat channel for this tenant."""
    channel = (
        db.query(Channel)
        .filter(
            Channel.tenant_id == tenant_id,
            Channel.channel_type == "dashboard",
        )
        .first()
    )
    if channel:
        return channel
    channel = Channel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="In-app chat",
        channel_type="dashboard",
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


def _get_or_create_chat_conversation(
    db: Session,
    channel_id: uuid.UUID,
    tenant_id: uuid.UUID,
    customer_identifier: str,
    customer_name: str | None,
) -> Conversation:
    """Get or create an active conversation for this user in the dashboard channel."""
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.channel_id == channel_id,
            Conversation.tenant_id == tenant_id,
            Conversation.customer_identifier == customer_identifier,
            Conversation.status == ConversationStatus.active.value,
        )
        .first()
    )
    if conv:
        return conv
    conv = Conversation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        channel_id=channel_id,
        customer_identifier=customer_identifier,
        customer_name=customer_name,
        status=ConversationStatus.active.value,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get a RAG-powered response.

    The response is generated using the tenant's knowledge base.
    Each exchange is stored as a conversation so it appears in Conversations and dashboard metrics.
    """
    channel = _get_or_create_dashboard_channel(db, current_user.tenant_id)
    conversation = _get_or_create_chat_conversation(
        db,
        channel.id,
        current_user.tenant_id,
        customer_identifier=current_user.email,
        customer_name=current_user.full_name,
    )

    # Inbound message (user)
    msg_in = Message(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        conversation_id=conversation.id,
        direction=MessageDirection.inbound.value,
        content=request.message,
        content_type="text",
        status=MessageStatus.delivered.value,
    )
    db.add(msg_in)
    db.commit()

    result = rag_query(
        query=request.message,
        tenant_id=current_user.tenant_id,
        db=db,
    )

    # Outbound message (assistant)
    msg_out = Message(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        conversation_id=conversation.id,
        direction=MessageDirection.outbound.value,
        content=result["response"],
        content_type="text",
        status=MessageStatus.sent.value,
    )
    db.add(msg_out)
    conversation.last_message_at = datetime.utcnow()
    db.commit()

    return ChatResponse(
        response=result["response"],
        sources=[
            SourceDocument(
                document_id=source["document_id"],
                filename=source["filename"],
                chunk_content=source["chunk_content"],
                relevance_score=source["relevance_score"],
            )
            for source in result["sources"]
        ],
        usage=UsageMetrics(
            context_chunks=result["usage"]["context_chunks"],
            prompt_tokens=result["usage"]["prompt_tokens"],
            completion_tokens=result["usage"]["completion_tokens"],
            total_tokens=result["usage"]["total_tokens"],
        ),
    )
