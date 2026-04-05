"""
Batch Operations API Routes

Provides batch operation endpoints using Supabase.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchMemoryRequest(BaseModel):
    """Request model for batch memory operations."""
    memories: List[dict]


class BatchDeleteRequest(BaseModel):
    """Request model for batch delete operations."""
    context_ids: List[str]


@router.post(
    "/memories",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Batch create memories",
)
async def batch_create_memories(
    request: BatchMemoryRequest,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Create multiple memories at once."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        # Prepare batch insert
        memories_data = []
        for mem in request.memories:
            mem["created_at"] = now
            mem["updated_at"] = now
            memories_data.append(mem)

        # Insert all memories
        created = await db.insert("memories", memories_data)

        logger.info(f"Batch created {len(created)} memories")

        return {
            "created": len(created),
            "memories": created,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to batch create memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch create memories",
        )


@router.delete(
    "/memories",
    status_code=status.HTTP_200_OK,
    summary="Batch delete memories",
)
async def batch_delete_memories(
    request: BatchDeleteRequest,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Delete multiple memories at once."""
    try:
        deleted_count = 0
        
        for context_id in request.context_ids:
            await db.delete("memories", {"context_id": context_id})
            await db.delete("memory_vectors", {"context_id": context_id})
            await db.delete("memory_versions", {"context_id": context_id})
            deleted_count += 1

        logger.info(f"Batch deleted {deleted_count} memories")

        return {
            "deleted": deleted_count,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to batch delete memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch delete memories",
        )


@router.post(
    "/export",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Export memories",
)
async def export_memories(
    agent_id: Optional[str] = None,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Export all memories for an agent."""
    try:
        filters = {}
        if agent_id:
            filters["agent_id"] = agent_id

        memories = await db.select("memories", filters=filters if filters else None)
        versions = await db.select("memory_versions", filters=filters if filters else None)

        return {
            "agent_id": agent_id,
            "memories": memories,
            "versions": versions,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_memories": len(memories),
            "total_versions": len(versions),
        }

    except Exception as e:
        logger.error(f"Failed to export memories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export memories",
        )


__all__ = ["router"]
