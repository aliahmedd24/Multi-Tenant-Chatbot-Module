"""Webhook endpoints for channel integrations."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.multi_tenant import TenantContext
from app.models.client import Client
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.channels.whatsapp import WhatsAppAdapter
from app.services.channels.instagram import InstagramAdapter
from app.services.orchestrator.chat_orchestrator import ChatOrchestrator


router = APIRouter()


async def get_client_by_slug(slug: str, db: AsyncSession) -> Client:
    """Get client by slug.

    Args:
        slug: Client slug.
        db: Database session.

    Returns:
        Client.

    Raises:
        HTTPException: If client not found or inactive.
    """
    result = await db.execute(select(Client).where(Client.slug == slug))
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

    TenantContext.set_tenant(client.id)
    return client


# WhatsApp Webhook Verification
@router.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request) -> int:
    """Verify WhatsApp webhook (Meta verification challenge).

    Args:
        request: Incoming request.

    Returns:
        Challenge value if verification succeeds.
    """
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.meta_verify_token:
        return int(challenge or 0)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed",
    )


# WhatsApp Webhook Handler
@router.post("/whatsapp/{client_slug}")
async def whatsapp_webhook(
    client_slug: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Handle incoming WhatsApp messages.

    Args:
        client_slug: Client slug.
        request: Incoming webhook request.
        db: Database session.

    Returns:
        Status response.
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Verify signature
    adapter = WhatsAppAdapter()
    if not adapter.verify_webhook(body, signature, settings.meta_app_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature",
        )

    # Get client
    client = await get_client_by_slug(client_slug, db)

    # Parse payload
    payload = await request.json()
    message_data = await adapter.parse_webhook(payload)

    if not message_data:
        # Not a message event (could be status update, etc.)
        return {"status": "ok"}

    # Get or create conversation
    sender_id = message_data["sender_id"]
    result = await db.execute(
        select(Conversation).where(
            Conversation.client_id == client.id,
            Conversation.sender_id == sender_id,
            Conversation.channel == "whatsapp",
            Conversation.is_active == True,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            client_id=client.id,
            sender_id=sender_id,
            channel="whatsapp",
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # Process with orchestrator
    orchestrator = ChatOrchestrator()
    try:
        response_data = await orchestrator.process_message(
            message=message_data["message"],
            sender_id=sender_id,
            channel="whatsapp",
            client_id=client.id,
            client_name=client.name,
            conversation_id=conversation.id,
            response_tone=client.response_tone,
            max_tokens=client.max_tokens,
        )
    finally:
        await orchestrator.close()

    # Save messages
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=message_data["message"],
        metadata=message_data.get("metadata"),
    )
    db.add(user_msg)

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_data["response"],
    )
    db.add(assistant_msg)
    await db.commit()

    # Send response via WhatsApp
    # Get channel config for this client
    channel_config = next(
        (c for c in client.channel_configs if c.channel == "whatsapp" and c.is_active),
        None,
    )

    if channel_config:
        await adapter.send_message(
            to=sender_id,
            message=response_data["response"],
            config=channel_config.config,
        )

    return {"status": "ok"}


# Instagram Webhook Verification
@router.get("/instagram")
async def verify_instagram_webhook(request: Request) -> int:
    """Verify Instagram webhook.

    Args:
        request: Incoming request.

    Returns:
        Challenge value.
    """
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.meta_verify_token:
        return int(challenge or 0)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed",
    )


# Instagram Webhook Handler
@router.post("/instagram/{client_slug}")
async def instagram_webhook(
    client_slug: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Handle incoming Instagram messages.

    Args:
        client_slug: Client slug.
        request: Incoming webhook request.
        db: Database session.

    Returns:
        Status response.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    adapter = InstagramAdapter()
    if not adapter.verify_webhook(body, signature, settings.meta_app_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature",
        )

    client = await get_client_by_slug(client_slug, db)
    payload = await request.json()
    message_data = await adapter.parse_webhook(payload)

    if not message_data:
        return {"status": "ok"}

    sender_id = message_data["sender_id"]

    # Get or create conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.client_id == client.id,
            Conversation.sender_id == sender_id,
            Conversation.channel == "instagram",
            Conversation.is_active == True,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            client_id=client.id,
            sender_id=sender_id,
            channel="instagram",
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # Process message
    orchestrator = ChatOrchestrator()
    try:
        response_data = await orchestrator.process_message(
            message=message_data["message"],
            sender_id=sender_id,
            channel="instagram",
            client_id=client.id,
            client_name=client.name,
            conversation_id=conversation.id,
        )
    finally:
        await orchestrator.close()

    # Save messages
    db.add(Message(conversation_id=conversation.id, role="user", content=message_data["message"]))
    db.add(Message(conversation_id=conversation.id, role="assistant", content=response_data["response"]))
    await db.commit()

    # Send response
    channel_config = next(
        (c for c in client.channel_configs if c.channel == "instagram" and c.is_active),
        None,
    )

    if channel_config:
        await adapter.send_message(
            to=sender_id,
            message=response_data["response"],
            config=channel_config.config,
        )

    return {"status": "ok"}
