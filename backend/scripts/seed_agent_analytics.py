"""Seed sample conversations with sentiment/intent/response_time data.

Populates realistic agent analytics data for dashboard testing.
Run with: python scripts/seed_agent_analytics.py
"""

import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.tenant import Tenant
from app.models.channel import Channel
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageDirection, MessageStatus
from app.services.sentiment_analyzer import analyze_sentiment
from app.services.intent_classifier import classify_intent

# Sample customer messages with natural variety
SAMPLE_MESSAGES = [
    # Positive
    "Thank you so much! That was really helpful.",
    "Great service, I love it!",
    "This is exactly what I needed, appreciate it!",
    "Wow, that was fast! Amazing support.",
    "You guys are the best, keep it up!",
    # Negative
    "This is terrible, I've been waiting forever.",
    "I'm very disappointed with the service.",
    "Worst experience I've ever had.",
    "This is unacceptable, I want a refund.",
    # Neutral / Questions
    "What are your business hours?",
    "Can you tell me about your menu?",
    "Hello, I have a question.",
    "Hi there!",
    "I'd like to place an order.",
    "Where is my delivery?",
    "Do you have vegetarian options?",
    "What's the price for the family meal?",
    "How long does delivery take?",
    "I want to give some feedback about my last visit.",
    "Can I track my order?",
]

BOT_RESPONSES = [
    "I'd be happy to help you with that! Let me look into it.",
    "Thank you for reaching out. Here's what I found for you.",
    "Great question! Our business hours are 9 AM to 10 PM daily.",
    "I understand your concern. Let me connect you with our team.",
    "Yes, we have several vegetarian options available on our menu.",
    "Your order is being prepared and should arrive within 30 minutes.",
    "I appreciate your feedback! We're always looking to improve.",
    "Let me check that for you right away.",
]


def seed_agent_data():
    """Create sample conversations with analyzed messages."""
    db = SessionLocal()

    try:
        tenant = db.query(Tenant).first()
        if not tenant:
            print("No tenant found. Run seed_data.py first.")
            sys.exit(1)

        print(f"Seeding agent analytics data for: {tenant.name}")

        # Check if channel exists, create if not
        channel = (
            db.query(Channel)
            .filter(Channel.tenant_id == tenant.id)
            .first()
        )
        if not channel:
            channel = Channel(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name="WhatsApp Main",
                channel_type="whatsapp",
                is_active=True,
                phone_number_id="1234567890",
            )
            db.add(channel)
            db.flush()
            print("  Created channel: WhatsApp Main")

        # Create conversations spread over the last 30 days
        num_conversations = 15
        statuses = [
            ConversationStatus.closed.value,
            ConversationStatus.closed.value,
            ConversationStatus.closed.value,
            ConversationStatus.active.value,
            ConversationStatus.handoff.value,
        ]

        total_messages = 0

        for i in range(num_conversations):
            days_ago = random.randint(0, 29)
            conv_time = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            status = random.choice(statuses)

            conv = Conversation(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                channel_id=channel.id,
                customer_identifier=f"+96655{random.randint(1000000, 9999999)}",
                customer_name=f"Customer {i + 1}",
                status=status,
                last_message_at=conv_time,
            )
            db.add(conv)
            db.flush()

            # Each conversation has 2-8 message exchanges
            num_exchanges = random.randint(2, 8)
            msg_time = conv_time

            for j in range(num_exchanges):
                # Inbound message (customer)
                content = random.choice(SAMPLE_MESSAGES)
                sentiment_result = analyze_sentiment(content)
                intent = classify_intent(content)

                inbound = Message(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    conversation_id=conv.id,
                    direction=MessageDirection.inbound.value,
                    content=content,
                    status=MessageStatus.delivered.value,
                    sentiment=sentiment_result["sentiment"],
                    sentiment_score=sentiment_result["score"],
                    intent=intent,
                )
                # Manually set created_at for spread
                db.add(inbound)
                db.flush()
                inbound.created_at = msg_time
                total_messages += 1

                # Outbound response (bot)
                response_delay = random.uniform(0.8, 6.0)  # seconds
                msg_time = msg_time + timedelta(seconds=response_delay + random.randint(1, 5))

                outbound = Message(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    conversation_id=conv.id,
                    direction=MessageDirection.outbound.value,
                    content=random.choice(BOT_RESPONSES),
                    status=MessageStatus.sent.value,
                    response_time_seconds=round(response_delay, 2),
                )
                db.add(outbound)
                db.flush()
                outbound.created_at = msg_time
                total_messages += 1

                msg_time = msg_time + timedelta(minutes=random.randint(1, 30))

            # Update conversation last_message_at
            conv.last_message_at = msg_time

        db.commit()

        print(f"\n  Created {num_conversations} conversations")
        print(f"  Created {total_messages} messages (with sentiment, intent, response time)")
        print(f"\n  Refresh the Agent Analytics page to see the data!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_agent_data()
