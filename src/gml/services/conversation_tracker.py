"""
Conversation Tracking Service

Tracks chat conversations using Supabase.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)


class ConversationTracker:
    """Tracks chat conversations and messages using Supabase."""

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
        db: Optional[SupabaseDB] = None,
    ) -> dict:
        """Store a chat message."""
        if not db:
            raise ValueError("Database session required")

        try:
            now = datetime.now(timezone.utc).isoformat()
            messages = await db.insert("messages", {
                "id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": {"text": content},
                "used_memories": used_memories or [],
                "metadata": metadata or {},
                "created_at": now,
            })

            logger.debug(f"Stored message for conversation {conversation_id}")
            return messages[0] if messages else {}

        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
        db: Optional[SupabaseDB] = None,
    ) -> List[dict]:
        """Get conversation history."""
        if not db:
            raise ValueError("Database session required")

        try:
            messages = await db.select(
                "messages",
                filters={"conversation_id": conversation_id},
                order="created_at asc",
                limit=limit,
            )
            return messages

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    async def generate_summary(
        self,
        conversation_id: str,
        db: Optional[SupabaseDB] = None,
    ) -> str:
        """Generate conversation summary."""
        if not db:
            raise ValueError("Database session required")

        try:
            messages = await self.get_conversation_history(conversation_id, limit=100, db=db)

            if not messages:
                return "No messages in conversation."

            # Simple summary - count and roles
            user_msgs = [m for m in messages if m.get("role") == "user"]
            assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

            summary = f"Conversation with {len(user_msgs)} user messages and {len(assistant_msgs)} assistant responses."

            # Add first user message as context
            if user_msgs:
                first_content = user_msgs[0].get("content", {})
                if isinstance(first_content, dict):
                    first_text = first_content.get("text", "")[:100]
                else:
                    first_text = str(first_content)[:100]
                summary += f" Started with: '{first_text}...'"

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Failed to generate summary."

    async def create_memory_from_chat(
        self,
        conversation_id: str,
        content: str,
        agent_id: str,
        memory_type: str = "episodic",
        db: Optional[SupabaseDB] = None,
    ) -> dict:
        """Create a memory from chat content."""
        if not db:
            raise ValueError("Database session required")

        try:
            context_id = f"ctx-{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc).isoformat()

            memories = await db.insert("memories", {
                "context_id": context_id,
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "content": {"text": content},
                "memory_type": memory_type,
                "visibility": "private",
                "version": 1,
                "created_at": now,
                "updated_at": now,
            })

            logger.info(f"Created memory {context_id} from chat")
            return memories[0] if memories else {}

        except Exception as e:
            logger.error(f"Error creating memory from chat: {str(e)}")
            raise


# Singleton instance
_tracker: Optional[ConversationTracker] = None


async def get_conversation_tracker() -> ConversationTracker:
    """Get or create conversation tracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = ConversationTracker()
    return _tracker


__all__ = ["ConversationTracker", "get_conversation_tracker"]
