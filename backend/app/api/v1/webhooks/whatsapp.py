"""WhatsApp webhook endpoints.

These endpoints are PUBLIC (no JWT auth) but protected by signature verification.
They handle incoming messages from WhatsApp Cloud API and webhook verification.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.channel import Channel, ChannelType
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageDirection, MessageStatus
from app.services.whatsapp import (
    parse_webhook_payload,
    verify_webhook_challenge,
    verify_webhook_signature,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> Response:
    """Verify WhatsApp webhook subscription.

    This is called by Meta when you configure the webhook URL.
    Returns the challenge string if verification succeeds.
    """
    settings = get_settings()

    challenge = verify_webhook_challenge(
        mode=hub_mode or "",
        token=hub_token or "",
        challenge=hub_challenge or "",
        verify_token=settings.webhook_verify_token,
    )

    if challenge:
        logger.info("WhatsApp webhook verification successful")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("WhatsApp webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_message(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    """Receive incoming WhatsApp messages.

    This endpoint is called by WhatsApp when a user sends a message.
    The message is validated, stored, and queued for processing.
    """
    # Get raw body for signature verification
    body = await request.body()
    payload = await request.json()

    # Log webhook receipt
    logger.info(f"Received WhatsApp webhook: {len(body)} bytes")

    # Parse messages from payload
    messages = parse_webhook_payload(payload)

    if not messages:
        # May be a status update or other event, acknowledge receipt
        return {"status": "ok"}

    # Process each message
    db: Session = next(get_db())
    try:
        for msg_data in messages:
            phone_number_id = msg_data.get("phone_number_id")

            # Find the channel by phone_number_id
            channel = (
                db.query(Channel)
                .filter(
                    Channel.phone_number_id == phone_number_id,
                    Channel.channel_type == ChannelType.whatsapp.value,
                    Channel.is_active == True,
                )
                .first()
            )

            if not channel:
                logger.warning(f"No active channel for phone_number_id: {phone_number_id}")
                continue

            # Verify signature using channel's webhook secret
            if channel.webhook_secret and x_hub_signature_256:
                if not verify_webhook_signature(
                    body, x_hub_signature_256, channel.webhook_secret
                ):
                    logger.warning("Invalid webhook signature")
                    continue

            # Update channel last webhook time
            channel.last_webhook_at = datetime.utcnow()

            # Find or create conversation
            customer_phone = msg_data.get("from")
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.channel_id == channel.id,
                    Conversation.customer_identifier == customer_phone,
                    Conversation.status == ConversationStatus.active.value,
                )
                .first()
            )

            if not conversation:
                conversation = Conversation(
                    tenant_id=channel.tenant_id,
                    channel_id=channel.id,
                    customer_identifier=customer_phone,
                    status=ConversationStatus.active.value,
                    last_message_at=datetime.utcnow(),
                )
                db.add(conversation)
                db.flush()

            # Create message record
            message = Message(
                tenant_id=channel.tenant_id,
                conversation_id=conversation.id,
                direction=MessageDirection.inbound.value,
                content=msg_data.get("text", ""),
                external_id=msg_data.get("message_id"),
                status=MessageStatus.delivered.value,
            )
            db.add(message)

            # Update conversation last message time
            conversation.last_message_at = datetime.utcnow()

            db.commit()

            # Queue for RAG processing (async)
            try:
                from app.workers.message_tasks import process_inbound_message

                process_inbound_message.delay(str(message.id))
            except Exception as e:
                logger.warning(f"Failed to queue message for processing: {e}")

    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        db.rollback()
    finally:
        db.close()

    return {"status": "ok"}
