"""
Conversation Tracking Service

Tracks chat conversations:
- Store chat messages in database
- Link to agent and memories
- Track which memories were used
- Generate conversation summaries
- Create actionable memory items from chats
- Support conversation threading

Usage:
    >>> from src.gml.services.conversation_tracker import get_conversation_tracker
    >>> 
    >>> tracker = await get_conversation_tracker()
    >>> message = await tracker.store_message(
    ...     agent_id="agent-123",
    ...     conversation_id="conv-456",
    ...     role="user",
    ...     content="Hello"
    ... )
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import ChatMessage, Message, Memory

logger = logging.getLogger(__name__)


class ConversationTracker:
    """
    Tracks chat conversations and messages.
    
    Stores messages, links to memories, and generates summaries.
    """

    def __init__(self) -> None:
        """Initialize conversation tracker."""
        logger.info("ConversationTracker initialized")

    async def store_message(
        self,
        agent_id: str,
        conversation_id: str,
        role: str,
        content: str,
        used_memories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
    ) -> ChatMessage:
        """
        Store a chat message.

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            used_memories: List of memory context_ids used
            metadata: Additional metadata
            db: Database session

        Returns:
            Stored ChatMessage object
        """
        if not db:
            raise ValueError("Database session required")

        try:
            message = ChatMessage(
                agent_id=agent_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                used_memories=used_memories or [],
                message_metadata=metadata or {},
                created_at=datetime.now(timezone.utc),
            )

            db.add(message)
            await db.commit()
            await db.refresh(message)

            logger.debug(f"Stored message {message.id} for conversation {conversation_id}")
            return message

        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing message: {str(e)}")
            raise

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
        db: Optional[AsyncSession] = None,
    ) -> List[ChatMessage]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages
            db: Database session

        Returns:
            List of ChatMessage objects
        """
        if not db:
            raise ValueError("Database session required")

        try:
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.asc())
                .limit(limit)
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    async def generate_summary(
        self,
        conversation_id: str,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Generate conversation summary.

        Args:
            conversation_id: Conversation ID
            db: Database session

        Returns:
            Summary string
        """
        if not db:
            raise ValueError("Database session required")

        try:
            messages = await self.get_conversation_history(conversation_id, limit=100, db=db)
            
            if not messages:
                return "No conversation history."

            # Simple summary: count messages and extract key points
            user_count = sum(1 for m in messages if m.role == "user")
            assistant_count = sum(1 for m in messages if m.role == "assistant")
            
            summary_parts = [
                f"Conversation summary: {len(messages)} messages",
                f"User messages: {user_count}, Assistant messages: {assistant_count}",
            ]

            # Extract first and last user messages
            user_messages = [m for m in messages if m.role == "user"]
            if user_messages:
                summary_parts.append(f"Started with: {user_messages[0].content[:100]}...")
                if len(user_messages) > 1:
                    summary_parts.append(f"Latest: {user_messages[-1].content[:100]}...")

            return ". ".join(summary_parts) + "."

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Error generating summary."

    async def create_memory_from_chat(
        self,
        conversation_id: str,
        content: str,
        agent_id: str,
        memory_type: str = "episodic",
        db: Optional[AsyncSession] = None,
    ) -> Memory:
        """
        Create a memory from chat content.

        Args:
            conversation_id: Conversation ID
            content: Memory content
            agent_id: Agent ID
            memory_type: Memory type
            db: Database session

        Returns:
            Created Memory object
        """
        if not db:
            raise ValueError("Database session required")

        try:
            import uuid
            context_id = f"ctx-{uuid.uuid4().hex[:12]}"

            memory = Memory(
                context_id=context_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                content={"text": content},
                memory_type=memory_type,
                visibility="all",
                version=1,
                created_at=datetime.now(timezone.utc),
            )

            db.add(memory)
            await db.commit()
            await db.refresh(memory)

            logger.info(f"Created memory {context_id} from chat")
            return memory

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating memory from chat: {str(e)}")
            raise


# Singleton instance
_conversation_tracker: Optional[ConversationTracker] = None


async def get_conversation_tracker() -> ConversationTracker:
    """Get or create the singleton conversation tracker instance."""
    global _conversation_tracker

    if _conversation_tracker is None:
        _conversation_tracker = ConversationTracker()
        logger.info("Conversation tracker singleton created")

    return _conversation_tracker


__all__ = ["ConversationTracker", "get_conversation_tracker"]

