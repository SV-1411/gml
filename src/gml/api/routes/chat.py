"""
Chat API Routes

Provides chat functionality with automatic memory injection:
- POST /api/v1/chat/message - Send chat message with memory context
- GET /api/v1/chat/conversations/{id}/history - Get conversation history
- POST /api/v1/chat/conversations/{id}/summary - Generate conversation summary

Usage:
    POST /api/v1/chat/message
    {
        "agent_id": "agent-123",
        "conversation_id": "conv-456",
        "message": "Hello, what do you remember about me?"
    }
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.database import get_db
from src.gml.db.models import Agent
from src.gml.services.chat_memory_injection import get_memory_injector
from src.gml.services.conversation_tracker import get_conversation_tracker
from src.gml.services.llm_service import get_llm_service
from src.gml.services.response_processor import get_response_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ChatMessageRequest(BaseModel):
    """Request model for chat message."""

    agent_id: str = Field(..., description="Agent ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (auto-generated if not provided)")
    message: str = Field(..., min_length=1, description="User message")
    stream: bool = Field(False, description="Stream response")
    relevance_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Memory relevance threshold")
    max_memories: int = Field(10, ge=1, le=50, description="Maximum memories to include")


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""

    message: str
    response: str
    used_memories: list[str]
    conversation_id: str
    execution_time_ms: float
    token_usage: Optional[dict] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_current_agent_id(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
) -> Optional[str]:
    """Get current agent ID from request headers."""
    return x_agent_id


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Send a chat message with automatic memory injection",
)
async def send_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> ChatMessageResponse:
    """
    Send chat message with automatic memory injection.

    Automatically loads relevant memories, builds prompt, calls LLM,
    and tracks conversation.

    Args:
        request: Chat message request
        db: Database session
        agent_id: Current agent ID from headers

    Returns:
        ChatMessageResponse with response and metadata

    Raises:
        HTTPException 404: If agent not found
        HTTPException 500: For server errors
    """
    start_time = time.time()

    try:
        # Use agent_id from request or header
        effective_agent_id = request.agent_id or agent_id
        if not effective_agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide agent_id in request or X-Agent-ID header.",
            )

        # Verify agent exists
        from sqlalchemy import select
        result = await db.execute(
            select(Agent).where(Agent.agent_id == effective_agent_id)
        )
        agent = result.scalar_one_or_none()

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{effective_agent_id}' not found",
            )

        # Generate conversation_id if not provided
        import uuid
        conversation_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:12]}"

        # Get services
        memory_injector = await get_memory_injector()
        llm_service = await get_llm_service()
        conversation_tracker = await get_conversation_tracker()
        response_processor = await get_response_processor()

        # Build prompt with memories
        prompt_data = await memory_injector.build_prompt_with_memories(
            user_message=request.message,
            agent_id=effective_agent_id,
            conversation_id=conversation_id,
            relevance_threshold=request.relevance_threshold,
            max_memories=request.max_memories,
            max_tokens=2000,
            db=db,
        )

        # Store user message
        await conversation_tracker.store_message(
            agent_id=effective_agent_id,
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            used_memories=prompt_data["used_memories"],
            db=db,
        )

        # Build messages for LLM
        messages = [
            {"role": "system", "content": prompt_data["system_prompt"]},
            {"role": "user", "content": request.message},
        ]

        # Get conversation history (optional: include recent history)
        history = await conversation_tracker.get_conversation_history(
            conversation_id=conversation_id,
            limit=5,
            db=db,
        )

        # Add recent history (excluding current message)
        for msg in history[-5:-1] if len(history) > 1 else []:
            if msg.role in ["user", "assistant"]:
                messages.insert(-1, {"role": msg.role, "content": msg.content})

        # Call LLM
        if request.stream:
            # Streaming response handled separately
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Streaming not yet implemented in this endpoint",
            )

        llm_response = await llm_service.chat_completion(
            messages=messages,
            stream=False,
            temperature=0.7,
            max_tokens=1000,
        )

        response_text = llm_response.get("content", "") if isinstance(llm_response, dict) else str(llm_response)

        # Process response
        processed = response_processor.process_response(
            response=response_text,
            agent_id=effective_agent_id,
            conversation_id=conversation_id,
        )

        # Store assistant message
        await conversation_tracker.store_message(
            agent_id=effective_agent_id,
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            used_memories=prompt_data["used_memories"],
            metadata={
                "extracted_memories": processed["extracted_memories"],
                "action_items": processed["action_items"],
                "token_usage": llm_response.get("usage") if isinstance(llm_response, dict) else None,
            },
            db=db,
        )

        # Create memories from extracted content if any
        for memory_text in processed["extracted_memories"][:3]:  # Limit to 3
            try:
                await conversation_tracker.create_memory_from_chat(
                    conversation_id=conversation_id,
                    content=memory_text,
                    agent_id=effective_agent_id,
                    memory_type="episodic",
                    db=db,
                )
            except Exception as e:
                logger.warning(f"Failed to create memory from chat: {str(e)}")

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"Chat message processed in {execution_time:.2f}ms for agent {effective_agent_id}"
        )

        return ChatMessageResponse(
            message=request.message,
            response=response_text,
            used_memories=prompt_data["used_memories"],
            conversation_id=conversation_id,
            execution_time_ms=execution_time,
            token_usage=llm_response.get("usage") if isinstance(llm_response, dict) else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}",
        )


@router.get(
    "/conversations/{conversation_id}/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="Retrieve conversation message history",
)
async def get_conversation_history(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get conversation history.

    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages
        db: Database session

    Returns:
        Dictionary with conversation history
    """
    try:
        conversation_tracker = await get_conversation_tracker()
        messages = await conversation_tracker.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit,
            db=db,
        )

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "used_memories": msg.used_memories or [],
                }
                for msg in messages
            ],
            "total": len(messages),
        }

    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}",
        )


@router.post(
    "/conversations/{conversation_id}/summary",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Generate conversation summary",
    description="Generate a summary of the conversation",
)
async def generate_conversation_summary(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate conversation summary.

    Args:
        conversation_id: Conversation ID
        db: Database session

    Returns:
        Dictionary with summary
    """
    try:
        conversation_tracker = await get_conversation_tracker()
        summary = await conversation_tracker.generate_summary(
            conversation_id=conversation_id,
            db=db,
        )

        return {
            "conversation_id": conversation_id,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


__all__ = ["router"]

