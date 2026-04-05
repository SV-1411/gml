"""
Conversations API Routes

Provides conversation management endpoints using Supabase.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get(
    "",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List conversations",
)
async def list_conversations(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """List conversations with optional filtering."""
    try:
        filters = {}
        if agent_id:
            filters["agent_id"] = agent_id

        messages = await db.select(
            "messages",
            filters=filters if filters else None,
            order="created_at desc",
            limit=limit,
        )

        # Group by conversation_id
        conversations = {}
        for msg in messages:
            conv_id = msg.get("conversation_id")
            if conv_id and conv_id not in conversations:
                conversations[conv_id] = {
                    "conversation_id": conv_id,
                    "agent_id": msg.get("agent_id"),
                    "last_message_at": msg.get("created_at"),
                    "message_count": 0,
                }
            if conv_id:
                conversations[conv_id]["message_count"] += 1

        return {
            "conversations": list(conversations.values()),
            "total": len(conversations),
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get(
    "/{conversation_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get conversation details",
)
async def get_conversation(
    conversation_id: str,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Get conversation details."""
    try:
        messages = await db.select(
            "messages",
            filters={"conversation_id": conversation_id},
            order="created_at asc",
        )

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found",
            )

        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "total": len(messages),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation",
)
async def delete_conversation(
    conversation_id: str,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Delete a conversation and all its messages."""
    try:
        # Check if exists
        messages = await db.select(
            "messages",
            filters={"conversation_id": conversation_id},
            limit=1,
        )

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found",
            )

        # Delete all messages
        await db.delete("messages", {"conversation_id": conversation_id})

        logger.info(f"Deleted conversation: {conversation_id}")

        return {
            "conversation_id": conversation_id,
            "success": True,
            "message": "Conversation deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


__all__ = ["router"]
