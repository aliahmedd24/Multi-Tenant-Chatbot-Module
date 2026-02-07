"""Session management service.

Handles conversation sessions with Redis caching.
"""

import json
from datetime import timedelta
from typing import Optional
from uuid import UUID

import structlog
import redis.asyncio as redis

from app.core.config import settings


logger = structlog.get_logger()


class SessionManager:
    """Manages conversation sessions with caching.

    Uses Redis for session storage with configurable TTL.

    Usage:
        session_mgr = SessionManager()
        await session_mgr.save_context(conv_id, context)
        context = await session_mgr.get_context(conv_id)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        session_ttl: int = 3600,  # 1 hour default
    ):
        """Initialize session manager.

        Args:
            redis_url: Redis connection URL.
            session_ttl: Session TTL in seconds.
        """
        self.redis_url = redis_url or settings.redis_url
        self.session_ttl = session_ttl
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _context_key(self, conversation_id: UUID) -> str:
        """Generate Redis key for conversation context."""
        return f"session:ctx:{conversation_id}"

    def _history_key(self, conversation_id: UUID) -> str:
        """Generate Redis key for conversation history."""
        return f"session:history:{conversation_id}"

    async def save_context(
        self,
        conversation_id: UUID,
        context: dict,
    ) -> None:
        """Save conversation context.

        Args:
            conversation_id: Conversation UUID.
            context: Context dictionary to save.
        """
        r = await self._get_redis()
        key = self._context_key(conversation_id)
        await r.setex(key, self.session_ttl, json.dumps(context))
        logger.debug("session_context_saved", conversation_id=str(conversation_id))

    async def get_context(
        self,
        conversation_id: UUID,
    ) -> Optional[dict]:
        """Get conversation context.

        Args:
            conversation_id: Conversation UUID.

        Returns:
            Context dictionary or None if not found.
        """
        r = await self._get_redis()
        key = self._context_key(conversation_id)
        data = await r.get(key)

        if data:
            logger.debug("session_context_found", conversation_id=str(conversation_id))
            return json.loads(data)

        logger.debug("session_context_miss", conversation_id=str(conversation_id))
        return None

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        max_history: int = 20,
    ) -> None:
        """Add a message to conversation history.

        Args:
            conversation_id: Conversation UUID.
            role: Message role (user/assistant).
            content: Message content.
            max_history: Maximum messages to keep.
        """
        r = await self._get_redis()
        key = self._history_key(conversation_id)

        message = json.dumps({"role": role, "content": content})
        await r.rpush(key, message)

        # Trim to max history
        await r.ltrim(key, -max_history, -1)
        await r.expire(key, self.session_ttl)

    async def get_history(
        self,
        conversation_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """Get conversation history.

        Args:
            conversation_id: Conversation UUID.
            limit: Maximum messages to return.

        Returns:
            List of message dictionaries.
        """
        r = await self._get_redis()
        key = self._history_key(conversation_id)
        messages = await r.lrange(key, -limit, -1)

        return [json.loads(m) for m in messages]

    async def clear_session(self, conversation_id: UUID) -> None:
        """Clear all session data for a conversation.

        Args:
            conversation_id: Conversation UUID.
        """
        r = await self._get_redis()
        await r.delete(
            self._context_key(conversation_id),
            self._history_key(conversation_id),
        )
        logger.info("session_cleared", conversation_id=str(conversation_id))

    async def extend_session(self, conversation_id: UUID) -> None:
        """Extend session TTL.

        Args:
            conversation_id: Conversation UUID.
        """
        r = await self._get_redis()
        await r.expire(self._context_key(conversation_id), self.session_ttl)
        await r.expire(self._history_key(conversation_id), self.session_ttl)
