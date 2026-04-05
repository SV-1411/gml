"""
Search API Routes

Provides search endpoints using Supabase.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "/memories",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search memories",
)
async def search_memories(
    q: str = Query(..., min_length=1, description="Search query"),
    agent_id: Optional[str] = Query(None),
    memory_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Search memories by content (text search)."""
    try:
        # Build filters
        filters = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if memory_type:
            filters["memory_type"] = memory_type

        # Use Supabase full-text search or ILIKE
        # For now, use simple select with filters
        memories = await db.select(
            "memories",
            filters=filters if filters else None,
            order="created_at desc",
            limit=limit,
        )

        # Filter by text content (simple contains check)
        results = []
        query_lower = q.lower()
        for memory in memories:
            content = memory.get("content", {})
            if isinstance(content, dict):
                content_str = str(content).lower()
            else:
                content_str = str(content).lower() if content else ""
            
            if query_lower in content_str:
                results.append(memory)

        return {
            "query": q,
            "results": results[:limit],
            "total": len(results),
        }

    except Exception as e:
        logger.error(f"Failed to search memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memories",
        )


@router.get(
    "/messages",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search messages",
)
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    conversation_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Search messages by content."""
    try:
        filters = {}
        if conversation_id:
            filters["conversation_id"] = conversation_id

        messages = await db.select(
            "messages",
            filters=filters if filters else None,
            order="created_at desc",
            limit=limit,
        )

        # Filter by text content
        results = []
        query_lower = q.lower()
        for msg in messages:
            content = msg.get("content", {})
            if isinstance(content, dict):
                content_str = str(content).lower()
            else:
                content_str = str(content).lower() if content else ""
            
            if query_lower in content_str:
                results.append(msg)

        return {
            "query": q,
            "results": results[:limit],
            "total": len(results),
        }

    except Exception as e:
        logger.error(f"Failed to search messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages",
        )


__all__ = ["router"]
