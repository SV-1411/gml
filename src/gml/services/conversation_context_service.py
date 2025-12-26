"""
Conversation Context Service

Aggregates complete conversation context including:
- Full conversation history
- All related memories
- Agent state snapshots
- Decision points
- Memory relationships

Usage:
    >>> from src.gml.services.conversation_context_service import get_context_service
    >>> 
    >>> service = await get_context_service()
    >>> context = await service.get_full_context(
    ...     conversation_id="conv-123",
    ...     context_level="full"
    ... )
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Agent, ChatMessage, Memory
from src.gml.services.conversation_tracker import get_conversation_tracker

logger = logging.getLogger(__name__)


class ConversationContextService:
    """
    Service for aggregating complete conversation context.
    
    Fetches and combines conversation history, related memories,
    agent state, and relationships into a coherent context object.
    """

    def __init__(self) -> None:
        """Initialize conversation context service."""
        logger.info("ConversationContextService initialized")

    async def get_full_context(
        self,
        conversation_id: str,
        context_level: str = "full",
        agent_id: Optional[str] = None,
        filter_date_from: Optional[datetime] = None,
        filter_date_to: Optional[datetime] = None,
        filter_types: Optional[List[str]] = None,
        min_relevance: float = 0.0,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Get full conversation context.

        Args:
            conversation_id: Conversation ID
            context_level: Context level (minimal, full, detailed)
            agent_id: Optional agent ID filter
            filter_date_from: Filter memories from date
            filter_date_to: Filter memories to date
            filter_types: Filter by memory types
            min_relevance: Minimum relevance score
            db: Database session

        Returns:
            Complete context dictionary
        """
        if not db:
            raise ValueError("Database session required")

        try:
            # Get conversation messages
            messages = await self._get_conversation_messages(
                conversation_id=conversation_id,
                db=db,
            )

            if not messages:
                return {
                    "conversation_id": conversation_id,
                    "error": "Conversation not found",
                    "messages": [],
                    "memories": [],
                    "agent_state": None,
                    "relationships": [],
                }

            # Extract agent_id if not provided
            if not agent_id and messages:
                agent_id = messages[0].agent_id

            # Get all memories referenced in conversation
            memory_ids = set()
            for msg in messages:
                if msg.used_memories:
                    memory_ids.update(msg.used_memories)

            # Also get memories from same conversation
            result = await db.execute(
                select(Memory).where(
                    and_(
                        Memory.conversation_id == conversation_id,
                        Memory.agent_id == agent_id,
                    )
                )
            )
            conversation_memories = result.scalars().all()
            memory_ids.update(m.context_id for m in conversation_memories)

            # Load all related memories
            memories = await self._load_memories(
                memory_ids=list(memory_ids),
                agent_id=agent_id,
                filter_date_from=filter_date_from,
                filter_date_to=filter_date_to,
                filter_types=filter_types,
                db=db,
            )

            # Get agent state if available
            agent_state = await self._get_agent_state(
                agent_id=agent_id,
                conversation_id=conversation_id,
                db=db,
            )

            # Build memory relationships
            relationships = await self._build_relationships(
                memories=memories,
                messages=messages,
                db=db,
            )

            # Build context object
            context = {
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "context_level": context_level,
                "generated_at": datetime.now().isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "used_memories": msg.used_memories or [],
                        "metadata": msg.message_metadata or {},
                    }
                    for msg in messages
                ],
                "memories": [
                    {
                        "context_id": m.context_id,
                        "content": m.content,
                        "memory_type": m.memory_type,
                        "created_at": m.created_at.isoformat(),
                        "tags": m.tags or [],
                    }
                    for m in memories
                ],
                "agent_state": agent_state,
                "relationships": relationships,
                "statistics": {
                    "message_count": len(messages),
                    "memory_count": len(memories),
                    "user_messages": sum(1 for m in messages if m.role == "user"),
                    "assistant_messages": sum(1 for m in messages if m.role == "assistant"),
                    "unique_memories_used": len(memory_ids),
                },
            }

            # Add detailed info if requested
            if context_level in ["full", "detailed"]:
                context["decision_points"] = await self._extract_decision_points(
                    messages=messages,
                    memories=memories,
                )
                context["knowledge_gaps"] = await self._identify_knowledge_gaps(
                    messages=messages,
                    memories=memories,
                )

            if context_level == "detailed":
                context["memory_clusters"] = await self._cluster_memories(memories)
                context["conflicts"] = await self._identify_conflicts(memories)

            return context

        except Exception as e:
            logger.error(f"Error getting full context: {str(e)}", exc_info=True)
            raise

    async def _get_conversation_messages(
        self,
        conversation_id: str,
        db: AsyncSession,
    ) -> List[ChatMessage]:
        """Get all messages in conversation."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def _load_memories(
        self,
        memory_ids: List[str],
        agent_id: Optional[str],
        filter_date_from: Optional[datetime],
        filter_date_to: Optional[datetime],
        filter_types: Optional[List[str]],
        db: AsyncSession,
    ) -> List[Memory]:
        """Load memories by IDs with filtering."""
        if not memory_ids:
            return []

        query = select(Memory).where(Memory.context_id.in_(memory_ids))

        if agent_id:
            query = query.where(Memory.agent_id == agent_id)

        if filter_date_from:
            query = query.where(Memory.created_at >= filter_date_from)

        if filter_date_to:
            query = query.where(Memory.created_at <= filter_date_to)

        if filter_types:
            query = query.where(Memory.memory_type.in_(filter_types))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _get_agent_state(
        self,
        agent_id: Optional[str],
        conversation_id: str,
        db: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """Get agent state for conversation."""
        if not agent_id:
            return None

        try:
            result = await db.execute(
                select(Agent).where(Agent.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()

            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "status": agent.status,
                }
        except Exception as e:
            logger.warning(f"Error getting agent state: {str(e)}")

        return None

    async def _build_relationships(
        self,
        memories: List[Memory],
        messages: List[ChatMessage],
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """Build memory relationship graph."""
        relationships = []

        # Relationships from messages to memories
        for msg in messages:
            if msg.used_memories:
                for mem_id in msg.used_memories:
                    relationships.append({
                        "source": f"message-{msg.id}",
                        "target": mem_id,
                        "type": "uses",
                        "timestamp": msg.created_at.isoformat(),
                    })

        # Relationships between memories (same conversation/tags)
        memory_by_id = {m.context_id: m for m in memories}
        for i, mem1 in enumerate(memories):
            for mem2 in memories[i + 1:]:
                # Check if related (same tags, conversation, etc.)
                if mem1.conversation_id == mem2.conversation_id:
                    relationships.append({
                        "source": mem1.context_id,
                        "target": mem2.context_id,
                        "type": "same_conversation",
                        "strength": 0.5,
                    })

                # Check tag overlap
                tags1 = set(mem1.tags or [])
                tags2 = set(mem2.tags or [])
                if tags1 and tags2 and tags1.intersection(tags2):
                    overlap = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
                    if overlap > 0.3:
                        relationships.append({
                            "source": mem1.context_id,
                            "target": mem2.context_id,
                            "type": "similar_tags",
                            "strength": overlap,
                        })

        return relationships

    async def _extract_decision_points(
        self,
        messages: List[ChatMessage],
        memories: List[Memory],
    ) -> List[Dict[str, Any]]:
        """Extract decision points from conversation."""
        decision_points = []

        # Look for decision-making patterns in messages
        decision_keywords = ["decide", "choose", "option", "select", "prefer", "should"]
        
        for msg in messages:
            content_lower = msg.content.lower()
            if any(keyword in content_lower for keyword in decision_keywords):
                decision_points.append({
                    "message_id": msg.id,
                    "timestamp": msg.created_at.isoformat(),
                    "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                })

        return decision_points

    async def _identify_knowledge_gaps(
        self,
        messages: List[ChatMessage],
        memories: List[Memory],
    ) -> List[Dict[str, Any]]:
        """Identify knowledge gaps in conversation."""
        gaps = []

        # Look for questions without answers
        question_keywords = ["?", "what", "how", "why", "when", "where", "who"]

        for i, msg in enumerate(messages):
            if msg.role == "user" and any(keyword in msg.content.lower() for keyword in question_keywords):
                # Check if next message answers it
                if i + 1 < len(messages) and messages[i + 1].role == "assistant":
                    next_msg = messages[i + 1].content.lower()
                    # Simple check: if next message is short or doesn't answer, might be a gap
                    if len(next_msg) < 50:
                        gaps.append({
                            "question_id": msg.id,
                            "question": msg.content[:200],
                            "timestamp": msg.created_at.isoformat(),
                            "type": "unanswered_question",
                        })

        return gaps

    async def _cluster_memories(self, memories: List[Memory]) -> List[Dict[str, Any]]:
        """Cluster related memories."""
        clusters = []

        # Group by memory type
        by_type: Dict[str, List[Memory]] = {}
        for mem in memories:
            mem_type = mem.memory_type or "unknown"
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(mem)

        for mem_type, mems in by_type.items():
            clusters.append({
                "cluster_id": f"type-{mem_type}",
                "type": mem_type,
                "memory_ids": [m.context_id for m in mems],
                "count": len(mems),
            })

        return clusters

    async def _identify_conflicts(self, memories: List[Memory]) -> List[Dict[str, Any]]:
        """Identify conflicting information in memories."""
        conflicts = []

        # Simple conflict detection: look for contradictory statements
        # This is a simplified version - could be enhanced with semantic analysis
        for i, mem1 in enumerate(memories):
            content1 = str(mem1.content).lower()
            for mem2 in memories[i + 1:]:
                content2 = str(mem2.content).lower()
                # Check for negation patterns (simplified)
                if ("not" in content1 and content2.replace("not", "").strip() in content1) or \
                   ("not" in content2 and content1.replace("not", "").strip() in content2):
                    conflicts.append({
                        "memory1_id": mem1.context_id,
                        "memory2_id": mem2.context_id,
                        "type": "negation_conflict",
                        "description": "Potential conflicting information detected",
                    })

        return conflicts


# Singleton instance
_context_service: Optional[ConversationContextService] = None


async def get_context_service() -> ConversationContextService:
    """Get or create the singleton context service instance."""
    global _context_service

    if _context_service is None:
        _context_service = ConversationContextService()
        logger.info("Conversation context service singleton created")

    return _context_service


__all__ = ["ConversationContextService", "get_context_service"]

