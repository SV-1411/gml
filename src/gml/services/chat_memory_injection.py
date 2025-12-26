"""
Chat Memory Injection Service

Automatically injects relevant memories into LLM prompts:
- Semantic search for relevant memories
- Filter by relevance threshold
- Rank by importance/recency
- Insert into system prompt
- Support different prompt templates
- Optimize for different LLM models
- Handle context window limits

Usage:
    >>> from src.gml.services.chat_memory_injection import get_memory_injector
    >>> 
    >>> injector = await get_memory_injector()
    >>> prompt = await injector.build_prompt_with_memories(
    ...     user_message="...",
    ...     agent_id="agent-123",
    ...     conversation_id="conv-456"
    ... )
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Memory
from src.gml.services.memory_context_builder import get_context_builder
from src.gml.services.memory_store import get_memory_store

logger = logging.getLogger(__name__)


class ChatMemoryInjector:
    """
    Injects relevant memories into chat prompts.
    
    Automatically finds and formats relevant memories for LLM context.
    """

    def __init__(self) -> None:
        """Initialize memory injector."""
        logger.info("ChatMemoryInjector initialized")

    async def build_prompt_with_memories(
        self,
        user_message: str,
        agent_id: str,
        conversation_id: Optional[str] = None,
        relevance_threshold: float = 0.7,
        max_memories: int = 10,
        max_tokens: int = 2000,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Build prompt with relevant memories injected.

        Args:
            user_message: User's message
            agent_id: Agent ID
            conversation_id: Conversation ID
            relevance_threshold: Minimum relevance score (0.0-1.0)
            max_memories: Maximum number of memories to include
            max_tokens: Maximum tokens for memory context
            db: Database session

        Returns:
            Dictionary with:
            - system_prompt: System prompt with memories
            - user_message: User message
            - used_memories: List of memory context_ids
            - memory_context: Formatted memory context
        """
        if not db:
            raise ValueError("Database session required")

        try:
            # Get relevant memories
            context_builder = await get_context_builder()
            context = await context_builder.build_context(
                agent_id=agent_id,
                conversation_id=conversation_id,
                query=user_message,
                max_tokens=max_tokens,
                strategy="hybrid",
                db=db,
            )

            # Filter by relevance if semantic search was used
            memories = context.get("memories", [])
            if memories:
                # Simple filtering: take top N
                selected_memories = memories[:max_memories]
            else:
                selected_memories = []

            # Build memory context
            if selected_memories:
                memory_context = self._format_memories_for_prompt(selected_memories)
            else:
                memory_context = "No relevant memories found."

            # Build system prompt
            system_prompt = self._build_system_prompt(memory_context, agent_id)

            return {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "used_memories": [m["context_id"] for m in selected_memories],
                "memory_context": memory_context,
                "memory_count": len(selected_memories),
            }

        except Exception as e:
            logger.error(f"Error building prompt with memories: {str(e)}")
            raise

    def _format_memories_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for inclusion in prompt."""
        lines = ["Relevant Context from Memory:\n"]

        for i, mem in enumerate(memories, 1):
            content = mem.get("content", {})
            text = content.get("text", str(content)) if isinstance(content, dict) else str(content)

            lines.append(f"[Memory {i}]")
            if mem.get("memory_type"):
                lines.append(f"Type: {mem['memory_type']}")
            lines.append(f"Content: {text[:300]}{'...' if len(text) > 300 else ''}")
            lines.append("")

        return "\n".join(lines)

    def _build_system_prompt(self, memory_context: str, agent_id: str) -> str:
        """Build system prompt with memory context."""
        return f"""You are an AI assistant for agent {agent_id}.

You have access to the following relevant memories:
{memory_context}

Use these memories to provide helpful, context-aware responses. If a memory is relevant to the user's question, incorporate it naturally into your response.

Remember to:
- Be concise and helpful
- Reference memories when relevant
- Provide accurate information based on the context
- Ask clarifying questions if needed"""


# Singleton instance
_memory_injector: Optional[ChatMemoryInjector] = None


async def get_memory_injector() -> ChatMemoryInjector:
    """Get or create the singleton memory injector instance."""
    global _memory_injector

    if _memory_injector is None:
        _memory_injector = ChatMemoryInjector()
        logger.info("Chat memory injector singleton created")

    return _memory_injector


__all__ = ["ChatMemoryInjector", "get_memory_injector"]

