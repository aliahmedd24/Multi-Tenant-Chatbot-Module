"""Add agent analytics columns to messages table.

Revision ID: 003_agent_analytics
Revises: 002_channels
Create Date: 2026-02-11

Adds columns:
- sentiment (String) - sentiment label for inbound messages
- sentiment_score (Float) - continuous sentiment score
- intent (String) - intent classification for inbound messages
- response_time_seconds (Float) - response time for outbound messages
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003_agent_analytics"
down_revision = "002_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("sentiment", sa.String(20), nullable=True))
    op.add_column("messages", sa.Column("sentiment_score", sa.Float(), nullable=True))
    op.add_column("messages", sa.Column("intent", sa.String(50), nullable=True))
    op.add_column("messages", sa.Column("response_time_seconds", sa.Float(), nullable=True))
    op.create_index("ix_messages_sentiment", "messages", ["sentiment"])


def downgrade() -> None:
    op.drop_index("ix_messages_sentiment", table_name="messages")
    op.drop_column("messages", "response_time_seconds")
    op.drop_column("messages", "intent")
    op.drop_column("messages", "sentiment_score")
    op.drop_column("messages", "sentiment")
