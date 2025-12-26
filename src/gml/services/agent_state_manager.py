"""
Agent State Manager Service

Manages agent initialization state:
- Store initialization state
- Track loaded memories
- Track context window usage
- Support state updates
- Cleanup after completion
- Audit logging

Usage:
    >>> from src.gml.services.agent_state_manager import get_state_manager
    >>> 
    >>> manager = await get_state_manager()
    >>> state = await manager.initialize_agent(
    ...     agent_id="agent-123",
    ...     conversation_id="conv-456"
    ... )
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Agent, AuditLog

logger = logging.getLogger(__name__)


class AgentStateManager:
    """
    Manages agent initialization and state.
    
    Tracks agent initialization state, loaded memories, and context usage.
    """

    def __init__(self) -> None:
        """Initialize agent state manager."""
        self.active_states: Dict[str, Dict[str, Any]] = {}
        logger.info("AgentStateManager initialized")

    async def initialize_agent(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        context: Dict[str, Any],
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Initialize agent state.

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            context: Context dictionary from builder
            db: Database session

        Returns:
            Initialization state dictionary
        """
        try:
            state_key = f"{agent_id}:{conversation_id or 'default'}"

            state = {
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "initialized_at": datetime.now(timezone.utc).isoformat(),
                "memories_loaded": len(context.get("memories", [])),
                "token_count": context.get("token_count", 0),
                "sources": context.get("sources", []),
                "metadata": context.get("metadata", {}),
            }

            self.active_states[state_key] = state

            # Log initialization
            if db:
                await self._log_initialization(agent_id, conversation_id, state, db)

            logger.info(f"Agent {agent_id} initialized with {state['memories_loaded']} memories")
            return state

        except Exception as e:
            logger.error(f"Error initializing agent state: {str(e)}")
            raise

    async def get_state(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent state.

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID

        Returns:
            State dictionary or None if not found
        """
        state_key = f"{agent_id}:{conversation_id or 'default'}"
        return self.active_states.get(state_key)

    async def update_state(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update agent state.

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            updates: Dictionary of updates

        Returns:
            True if updated successfully
        """
        try:
            state_key = f"{agent_id}:{conversation_id or 'default'}"
            if state_key in self.active_states:
                self.active_states[state_key].update(updates)
                self.active_states[state_key]["updated_at"] = datetime.now(timezone.utc).isoformat()
                return True
            return False

        except Exception as e:
            logger.error(f"Error updating state: {str(e)}")
            return False

    async def cleanup_agent(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """
        Cleanup agent state after completion.

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            db: Database session

        Returns:
            True if cleaned up successfully
        """
        try:
            state_key = f"{agent_id}:{conversation_id or 'default'}"

            if state_key in self.active_states:
                state = self.active_states[state_key]
                state["cleaned_up_at"] = datetime.now(timezone.utc).isoformat()

                # Log cleanup
                if db:
                    await self._log_cleanup(agent_id, conversation_id, state, db)

                del self.active_states[state_key]
                logger.info(f"Agent {agent_id} state cleaned up")
                return True

            return False

        except Exception as e:
            logger.error(f"Error cleaning up agent state: {str(e)}")
            return False

    async def _log_initialization(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        state: Dict[str, Any],
        db: AsyncSession,
    ) -> None:
        """Log agent initialization to audit log."""
        try:
            log_entry = AuditLog(
                action="agent_initialized",
                agent_id=agent_id,
                details={
                    "conversation_id": conversation_id,
                    "memories_loaded": state["memories_loaded"],
                    "token_count": state["token_count"],
                    "sources_count": len(state["sources"]),
                },
                created_at=datetime.now(timezone.utc),
            )
            db.add(log_entry)
            await db.commit()

        except Exception as e:
            logger.warning(f"Error logging initialization: {str(e)}")

    async def _log_cleanup(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        state: Dict[str, Any],
        db: AsyncSession,
    ) -> None:
        """Log agent cleanup to audit log."""
        try:
            log_entry = AuditLog(
                action="agent_cleanup",
                agent_id=agent_id,
                details={
                    "conversation_id": conversation_id,
                    "initialized_at": state.get("initialized_at"),
                    "cleaned_up_at": state.get("cleaned_up_at"),
                },
                created_at=datetime.now(timezone.utc),
            )
            db.add(log_entry)
            await db.commit()

        except Exception as e:
            logger.warning(f"Error logging cleanup: {str(e)}")


# Singleton instance
_state_manager: Optional[AgentStateManager] = None


async def get_state_manager() -> AgentStateManager:
    """Get or create the singleton state manager instance."""
    global _state_manager

    if _state_manager is None:
        _state_manager = AgentStateManager()
        logger.info("Agent state manager singleton created")

    return _state_manager


__all__ = ["AgentStateManager", "get_state_manager"]

