"""
Memory Versions API Routes

Provides memory versioning endpoints using Supabase.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory-versions", tags=["memory-versions"])


@router.get(
    "/{context_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get memory versions",
)
async def get_memory_versions(
    context_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Get all versions of a memory."""
    try:
        versions = await db.select(
            "memory_versions",
            filters={"context_id": context_id},
            order="version_number desc",
            limit=limit,
        )

        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for memory '{context_id}'",
            )

        return {
            "context_id": context_id,
            "versions": versions,
            "total": len(versions),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get memory versions",
        )


@router.get(
    "/{context_id}/{version_number}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get specific memory version",
)
async def get_memory_version(
    context_id: str,
    version_number: int,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Get a specific version of a memory."""
    try:
        versions = await db.select(
            "memory_versions",
            filters={
                "context_id": context_id,
                "version_number": version_number,
            },
            limit=1,
        )

        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found for memory '{context_id}'",
            )

        return versions[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get memory version",
        )


@router.post(
    "/{context_id}/rollback/{version_number}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Rollback to version",
)
async def rollback_memory(
    context_id: str,
    version_number: int,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Rollback memory to a specific version."""
    try:
        # Get the version to rollback to
        versions = await db.select(
            "memory_versions",
            filters={
                "context_id": context_id,
                "version_number": version_number,
            },
            limit=1,
        )

        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found",
            )

        version = versions[0]

        # Update memory with version content
        await db.update("memories", {
            "content": version["content"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, {"context_id": context_id})

        logger.info(f"Rolled back memory {context_id} to version {version_number}")

        return {
            "context_id": context_id,
            "rolled_back_to": version_number,
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rollback memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback memory",
        )


__all__ = ["router"]
