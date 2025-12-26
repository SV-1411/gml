"""
Memory Versioning API Routes

Provides endpoints for managing memory versions:
- List version history
- Get specific version
- Revert to previous version
- Generate diffs between versions

Usage:
    GET /api/v1/memories/{context_id}/versions
    GET /api/v1/memories/{context_id}/versions/{version}
    POST /api/v1/memories/{context_id}/versions/revert
    GET /api/v1/memories/{context_id}/diff
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.database import get_db
from src.gml.db.models import Memory
from src.gml.services.memory_versioning import get_versioning_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories/{context_id}/versions", tags=["memory-versions"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class VersionResponse(BaseModel):
    """Response model for a single version."""

    id: int
    context_id: str
    version_number: int
    change_type: str
    author_id: Optional[str]
    semantic_summary: Optional[str]
    parent_version_id: Optional[int]
    is_archived: bool
    compressed: bool
    created_at: str

    class Config:
        from_attributes = True


class VersionHistoryResponse(BaseModel):
    """Response model for version history."""

    context_id: str
    versions: List[VersionResponse]
    total: int
    limit: int
    offset: int


class RevertRequest(BaseModel):
    """Request model for reverting to a version."""

    version_number: int = Field(..., description="Version number to revert to")
    author_id: Optional[str] = Field(None, description="ID of user/agent performing revert")


class DiffResponse(BaseModel):
    """Response model for version diff."""

    context_id: str
    version1: int
    version2: Optional[int]
    unified_diff: str
    side_by_side: List[str]
    statistics: dict


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_current_agent_id(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
) -> Optional[str]:
    """Get current agent ID from request headers."""
    return x_agent_id


# ============================================================================
# VERSIONING ENDPOINTS
# ============================================================================


@router.get(
    "",
    response_model=VersionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="List memory versions",
    description="Get version history for a memory with pagination",
)
async def list_versions(
    context_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of versions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> VersionHistoryResponse:
    """
    List all versions of a memory.

    Returns version history sorted by version number (newest first).

    Args:
        context_id: Memory context ID
        limit: Maximum number of versions to return
        offset: Offset for pagination
        db: Database session
        agent_id: Current agent ID

    Returns:
        VersionHistoryResponse with list of versions

    Raises:
        HTTPException 404: If memory not found
        HTTPException 500: For server errors
    """
    try:
        # Verify memory exists
        result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        # Get version history
        versioning_service = await get_versioning_service()
        versions = await versioning_service.get_version_history(
            context_id=context_id,
            limit=limit,
            offset=offset,
            db=db,
        )

        return VersionHistoryResponse(
            context_id=context_id,
            versions=[VersionResponse.model_validate(v) for v in versions],
            total=len(versions),
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing versions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {str(e)}",
        )


@router.get(
    "/{version_number}",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific version",
    description="Retrieve a specific version of a memory",
)
async def get_version(
    context_id: str,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> VersionResponse:
    """
    Get a specific version of a memory.

    Args:
        context_id: Memory context ID
        version_number: Version number to retrieve
        db: Database session
        agent_id: Current agent ID

    Returns:
        VersionResponse with version details

    Raises:
        HTTPException 404: If memory or version not found
        HTTPException 500: For server errors
    """
    try:
        # Verify memory exists
        result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        # Get version
        versioning_service = await get_versioning_service()
        version = await versioning_service.get_version(
            context_id=context_id,
            version_number=version_number,
            db=db,
        )

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found for memory '{context_id}'",
            )

        return VersionResponse.model_validate(version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version: {str(e)}",
        )


@router.post(
    "/revert",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Revert to version",
    description="Revert memory to a previous version",
)
async def revert_to_version(
    context_id: str,
    request: RevertRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """
    Revert memory to a previous version.

    Creates a new version with content from the specified version.

    Args:
        context_id: Memory context ID
        request: Revert request with version number
        db: Database session
        agent_id: Current agent ID

    Returns:
        Dictionary with success message and updated memory info

    Raises:
        HTTPException 404: If memory or version not found
        HTTPException 500: For server errors
    """
    try:
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Verify memory exists
        result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        # Revert to version
        versioning_service = await get_versioning_service()
        updated_memory = await versioning_service.revert_to_version(
            context_id=context_id,
            version_number=request.version_number,
            author_id=request.author_id or agent_id,
            db=db,
        )

        logger.info(
            f"Memory {context_id} reverted to version {request.version_number} by {agent_id}"
        )

        return {
            "success": True,
            "message": f"Memory reverted to version {request.version_number}",
            "context_id": context_id,
            "version_number": request.version_number,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error reverting to version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revert to version: {str(e)}",
        )


@router.get(
    "/diff",
    response_model=DiffResponse,
    status_code=status.HTTP_200_OK,
    summary="Get version diff",
    description="Generate diff between two versions of a memory",
)
async def get_version_diff(
    context_id: str,
    version1: int = Query(..., description="First version number"),
    version2: Optional[int] = Query(None, description="Second version number (None = current)"),
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> DiffResponse:
    """
    Get diff between two versions of a memory.

    Args:
        context_id: Memory context ID
        version1: First version number
        version2: Second version number (None = compare with current)
        db: Database session
        agent_id: Current agent ID

    Returns:
        DiffResponse with diff information

    Raises:
        HTTPException 404: If memory or version not found
        HTTPException 500: For server errors
    """
    try:
        # Verify memory exists
        result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        # Generate diff
        versioning_service = await get_versioning_service()
        diff = await versioning_service.generate_diff(
            context_id=context_id,
            version1=version1,
            version2=version2,
            db=db,
        )

        return DiffResponse(
            context_id=diff["context_id"],
            version1=diff["version1"],
            version2=diff["version2"],
            unified_diff=diff["unified_diff"],
            side_by_side=diff["side_by_side"],
            statistics=diff["statistics"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating diff: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diff: {str(e)}",
        )


__all__ = ["router"]

