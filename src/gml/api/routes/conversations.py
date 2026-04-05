"""
Conversations API Routes

Provides conversation management endpoints using Supabase.
Supports importing conversations from external AI platforms (ChatGPT, Claude, etc).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ============================================================================
# REQUEST MODELS
# ============================================================================


class ImportedMessage(BaseModel):
    """A message from an external AI platform."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


class ImportConversationRequest(BaseModel):
    """Request to import a conversation from external platform."""
    platform: str  # "chatgpt", "claude", "gemini", "other"
    messages: List[ImportedMessage]
    title: Optional[str] = None
    agent_id: Optional[str] = None


# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================


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


# ============================================================================
# IMPORT ENDPOINTS
# ============================================================================


@router.post(
    "/import",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Import conversation from external AI platform",
)
async def import_conversation(
    request: ImportConversationRequest,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """
    Import a conversation from ChatGPT, Claude, or other AI platforms.
    
    This allows you to bring conversations from other platforms into GML
    for unified memory management and retrieval.
    
    Args:
        request: Import request with platform, messages, and optional metadata
        
    Returns:
        Dictionary with new conversation_id and import summary
    """
    try:
        # Generate new conversation ID
        conversation_id = f"conv-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Default agent for imported conversations
        agent_id = request.agent_id or "imported"
        
        # Store all messages
        imported_count = 0
        for msg in request.messages:
            await db.insert("messages", {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "role": msg.role,
                "content": {"text": msg.content},
                "metadata": {
                    "imported_from": request.platform,
                    "original_timestamp": msg.timestamp,
                },
                "created_at": msg.timestamp or now,
            })
            imported_count += 1
        
        # Create conversation metadata record
        await db.insert("conversations", {
            "conversation_id": conversation_id,
            "agent_id": agent_id,
            "title": request.title or f"Imported from {request.platform}",
            "platform": request.platform,
            "message_count": imported_count,
            "created_at": now,
            "updated_at": now,
        })
        
        logger.info(
            f"Imported {imported_count} messages from {request.platform} "
            f"to conversation {conversation_id}"
        )
        
        return {
            "conversation_id": conversation_id,
            "platform": request.platform,
            "messages_imported": imported_count,
            "title": request.title or f"Imported from {request.platform}",
        }
        
    except Exception as e:
        logger.error(f"Failed to import conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import conversation: {str(e)}",
        )


@router.post(
    "/import/batch",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Batch import multiple conversations",
)
async def batch_import_conversations(
    conversations: List[ImportConversationRequest],
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """
    Import multiple conversations at once.
    
    Useful for migrating all your AI conversations to GML.
    """
    try:
        imported = []
        for conv in conversations:
            result = await import_conversation(conv, db)
            imported.append(result)
        
        return {
            "total_conversations": len(imported),
            "total_messages": sum(c["messages_imported"] for c in imported),
            "conversations": imported,
        }
        
    except Exception as e:
        logger.error(f"Failed batch import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed batch import: {str(e)}",
        )


__all__ = ["router"]
