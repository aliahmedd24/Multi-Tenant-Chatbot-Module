"""Message processing worker tasks.

Celery tasks for processing inbound messages and generating RAG responses.
"""

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.message import Message, MessageDirection, MessageStatus
from app.services.intent_classifier import classify_intent
from app.services.rag_engine import RAGEngine
from app.services.sentiment_analyzer import analyze_sentiment

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_inbound_message(self, message_id: str):
    """Process an inbound message and generate a RAG response.

    This task:
    1. Loads the message and conversation
    2. Retrieves the channel configuration
    3. Calls the RAG engine to generate a response
    4. Sends the response via the appropriate channel API
    5. Creates an outbound message record

    Args:
        message_id: UUID string of the inbound message to process
    """
    db: Session = SessionLocal()

    try:
        # Load the inbound message
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            logger.error(f"Message not found: {message_id}")
            return

        # Load conversation and channel
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == message.conversation_id)
            .first()
        )
        if not conversation:
            logger.error(f"Conversation not found for message: {message_id}")
            return

        channel = (
            db.query(Channel)
            .filter(Channel.id == conversation.channel_id)
            .first()
        )
        if not channel:
            logger.error(f"Channel not found for conversation: {conversation.id}")
            return

        # Analyze inbound message sentiment and intent
        sentiment_result = analyze_sentiment(message.content)
        message.sentiment = sentiment_result["sentiment"]
        message.sentiment_score = sentiment_result["score"]
        message.intent = classify_intent(message.content)

        # Generate RAG response
        tenant_id = str(message.tenant_id)
        rag_engine = RAGEngine()
        rag_result = rag_engine.query(
            query=message.content,
            tenant_id=tenant_id,
        )

        response_text = rag_result["response"]

        # Send response via channel API
        external_message_id = None
        try:
            if channel.channel_type == "whatsapp":
                from app.services.whatsapp import WhatsAppClient
                import asyncio

                client = WhatsAppClient(
                    phone_number_id=channel.phone_number_id,
                    access_token=channel.access_token,
                )
                # Run async in sync context
                result = asyncio.get_event_loop().run_until_complete(
                    client.send_text_message(
                        to=conversation.customer_identifier,
                        message=response_text,
                    )
                )
                external_message_id = result.get("messages", [{}])[0].get("id")

            elif channel.channel_type == "instagram":
                from app.services.instagram import InstagramClient
                import asyncio

                client = InstagramClient(
                    page_id=channel.instagram_page_id,
                    access_token=channel.access_token,
                )
                result = asyncio.get_event_loop().run_until_complete(
                    client.send_text_message(
                        recipient_id=conversation.customer_identifier,
                        message=response_text,
                    )
                )
                external_message_id = result.get("message_id")

            status = MessageStatus.sent.value
        except Exception as send_error:
            logger.error(f"Failed to send message: {send_error}")
            status = MessageStatus.failed.value
            response_text = f"[Failed to send: {send_error}]"

        # Create outbound message record with response time
        response_time = (datetime.utcnow() - message.created_at).total_seconds()
        outbound_message = Message(
            tenant_id=message.tenant_id,
            conversation_id=conversation.id,
            direction=MessageDirection.outbound.value,
            content=response_text,
            external_id=external_message_id,
            status=status,
            response_time_seconds=response_time,
        )
        db.add(outbound_message)

        # Update conversation
        conversation.last_message_at = datetime.utcnow()

        db.commit()
        logger.info(f"Processed message {message_id}, response sent with status {status}")

    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}")
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task
def update_message_status(message_id: str, status: str, external_id: str = None):
    """Update message delivery status from webhook callback.

    Args:
        message_id: Internal message UUID
        status: New status (sent, delivered, read, failed)
        external_id: Optional external platform message ID
    """
    db: Session = SessionLocal()

    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if message:
            message.status = status
            if external_id:
                message.external_id = external_id
            db.commit()
            logger.info(f"Updated message {message_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating message status: {e}")
        db.rollback()
    finally:
        db.close()
