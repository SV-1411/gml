"""
Memory Context Builder Service

Builds context windows from memories using multiple strategies:
- Semantic search for relevant memories
- Keyword search for recent memories
- Conversation history loading
- Context ranking and prioritization
- Deduplication and size optimization

Usage:
    >>> from src.gml.services.memory_context_builder import get_context_builder
    >>> 
    >>> builder = await get_context_builder()
    >>> context = await builder.build_context(
    ...     agent_id="agent-123",
    ...     conversation_id="conv-456",
    ...     max_tokens=4000
    ... )
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Memory
from src.gml.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class MemoryContextBuilder:
    """
    Builds optimized context windows from memories for agent initialization.
    
    Combines multiple search strategies to find relevant memories and
    optimizes them to fit within token limits.
    """

    def __init__(self) -> None:
        """Initialize memory context builder."""
        self.embedding_service = None
        logger.info("MemoryContextBuilder initialized")

    async def build_context(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
        query: Optional[str] = None,
        max_tokens: int = 4000,
        strategy: str = "hybrid",
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Build optimized context window from memories.

        Args:
            agent_id: Agent ID to load memories for
            conversation_id: Optional conversation ID for filtering
            query: Optional query string for semantic search
            max_tokens: Maximum tokens for context window
            strategy: Strategy to use (semantic, keyword, hybrid, all)
            db: Database session

        Returns:
            Dictionary with:
            - memories: List of relevant memories
            - formatted_context: Formatted string for LLM
            - token_count: Estimated token count
            - sources: List of memory sources
            - metadata: Additional context metadata
        """
        if not db:
            raise ValueError("Database session required")

        try:
            memories = []
            seen_ids: Set[str] = set()

            # Load memories based on strategy
            if strategy in ["semantic", "hybrid", "all"] and query:
                semantic_memories = await self._load_semantic_memories(
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    query=query,
                    db=db,
                )
                for mem in semantic_memories:
                    if mem.context_id not in seen_ids:
                        memories.append(mem)
                        seen_ids.add(mem.context_id)

            if strategy in ["keyword", "hybrid", "all"]:
                keyword_memories = await self._load_keyword_memories(
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    query=query,
                    db=db,
                )
                for mem in keyword_memories:
                    if mem.context_id not in seen_ids:
                        memories.append(mem)
                        seen_ids.add(mem.context_id)

            if conversation_id:
                conversation_memories = await self._load_conversation_memories(
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    db=db,
                )
                for mem in conversation_memories:
                    if mem.context_id not in seen_ids:
                        memories.append(mem)
                        seen_ids.add(mem.context_id)

            # Rank and prioritize memories
            ranked_memories = await self._rank_memories(
                memories=memories,
                query=query,
                conversation_id=conversation_id,
            )

            # Optimize for token limit
            optimized_memories = self._optimize_for_tokens(
                memories=ranked_memories,
                max_tokens=max_tokens,
            )

            # Build formatted context
            formatted_context = self._format_context(optimized_memories)

            # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
            token_count = len(formatted_context) // 4

            return {
                "memories": [
                    {
                        "context_id": m.context_id,
                        "content": m.content,
                        "memory_type": m.memory_type,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in optimized_memories
                ],
                "formatted_context": formatted_context,
                "token_count": token_count,
                "sources": [m.context_id for m in optimized_memories],
                "metadata": {
                    "total_found": len(memories),
                    "selected": len(optimized_memories),
                    "strategy": strategy,
                    "max_tokens": max_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Error building context: {str(e)}", exc_info=True)
            raise

    async def _load_semantic_memories(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        query: str,
        db: AsyncSession,
    ) -> List[Memory]:
        """Load memories using semantic search."""
        try:
            # Generate query embedding
            embedding_service = await get_embedding_service()
            query_embedding = await embedding_service.generate_embedding(query)

            # Perform semantic search using memory store
            from src.gml.services.memory_store import get_memory_store
            
            memory_store = await get_memory_store()
            search_results = await memory_store.search_similar(
                query_embedding=query_embedding,
                top_k=20,
                agent_id=agent_id,
                conversation_id=conversation_id,
            )

            # Get memory objects from context_ids
            memories = []
            for context_id, score, metadata in search_results:
                result = await db.execute(
                    select(Memory).where(Memory.context_id == context_id)
                )
                memory = result.scalar_one_or_none()
                if memory:
                    memories.append(memory)

            return memories

        except Exception as e:
            logger.warning(f"Semantic search failed: {str(e)}")
            return []

    async def _load_keyword_memories(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        query: Optional[str],
        db: AsyncSession,
    ) -> List[Memory]:
        """Load memories using keyword search."""
        try:
            # Build query
            query_builder = select(Memory).where(Memory.agent_id == agent_id)

            if conversation_id:
                query_builder = query_builder.where(
                    Memory.conversation_id == conversation_id
                )

            # Order by recency
            query_builder = query_builder.order_by(Memory.created_at.desc()).limit(20)

            result = await db.execute(query_builder)
            return list(result.scalars().all())

        except Exception as e:
            logger.warning(f"Keyword search failed: {str(e)}")
            return []

    async def _load_conversation_memories(
        self,
        agent_id: str,
        conversation_id: str,
        db: AsyncSession,
    ) -> List[Memory]:
        """Load all memories from a specific conversation."""
        try:
            result = await db.execute(
                select(Memory)
                .where(
                    and_(
                        Memory.agent_id == agent_id,
                        Memory.conversation_id == conversation_id,
                    )
                )
                .order_by(Memory.created_at.asc())
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.warning(f"Conversation load failed: {str(e)}")
            return []

    async def _rank_memories(
        self,
        memories: List[Memory],
        query: Optional[str],
        conversation_id: Optional[str],
    ) -> List[Memory]:
        """
        Rank memories by relevance.

        Prioritizes:
        1. Memories from current conversation
        2. Recent memories
        3. Semantic relevance (if query provided)
        """
        # Simple ranking: prioritize conversation memories, then by recency
        def get_priority(memory: Memory) -> Tuple[int, int]:
            # Priority 0 = from conversation, 1 = others
            conv_priority = 0 if memory.conversation_id == conversation_id else 1
            # Recency (more recent = lower timestamp)
            recency = -memory.created_at.timestamp()
            return (conv_priority, recency)

        return sorted(memories, key=get_priority)

    def _optimize_for_tokens(
        self,
        memories: List[Memory],
        max_tokens: int,
    ) -> List[Memory]:
        """
        Optimize memory list to fit within token limit.

        Removes least relevant memories until within limit.
        """
        optimized = []
        current_tokens = 0

        for memory in memories:
            # Estimate tokens for this memory
            content = str(memory.content) if memory.content else ""
            mem_tokens = len(content) // 4

            if current_tokens + mem_tokens <= max_tokens:
                optimized.append(memory)
                current_tokens += mem_tokens
            else:
                # Try to fit a compressed version
                remaining = max_tokens - current_tokens
                if remaining > 100:  # Minimum useful size
                    # Could implement truncation here
                    break

        return optimized

    def _format_context(self, memories: List[Memory]) -> str:
        """
        Format memories for LLM consumption.

        Uses a simple template-based format.
        """
        if not memories:
            return "No relevant memories found."

        lines = ["Relevant Memories:\n"]

        for i, memory in enumerate(memories, 1):
            content = memory.content
            text = content.get("text", str(content)) if isinstance(content, dict) else str(content)

            lines.append(f"[Memory {i}]")
            lines.append(f"Type: {memory.memory_type}")
            lines.append(f"Date: {memory.created_at.strftime('%Y-%m-%d %H:%M')}")
            if memory.conversation_id:
                lines.append(f"Conversation: {memory.conversation_id[:12]}...")
            lines.append(f"Content: {text[:500]}{'...' if len(text) > 500 else ''}")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
_context_builder: Optional[MemoryContextBuilder] = None


async def get_context_builder() -> MemoryContextBuilder:
    """Get or create the singleton context builder instance."""
    global _context_builder

    if _context_builder is None:
        _context_builder = MemoryContextBuilder()
        logger.info("Memory context builder singleton created")

    return _context_builder


__all__ = ["MemoryContextBuilder", "get_context_builder"]

