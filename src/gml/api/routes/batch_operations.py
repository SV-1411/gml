"""
Batch Operations API Routes for GML Infrastructure

Provides batch operations for memory management at scale:
- Batch create memories
- Batch delete memories
- Batch export memories
- Memory consolidation (merge duplicates)
- Batch reindexing for semantic search

Usage:
    POST /api/v1/memories/batch/create
    POST /api/v1/memories/batch/delete
    POST /api/v1/memories/batch/export
    POST /api/v1/memories/consolidate
    POST /api/v1/memories/batch/reindex
"""

import asyncio
import csv
import gzip
import io
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.memory import MemoryType, MemoryVisibility, MemoryWriteRequest
from src.gml.db.database import get_db
from src.gml.db.models import Agent, Memory, MemoryVersion, MemoryVector
from src.gml.services.embedding_service import get_embedding_service
from src.gml.services.memory_store import get_memory_store
from src.gml.services.memory_versioning import get_versioning_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories/batch", tags=["batch-operations"])

# Performance targets
BATCH_CREATE_TARGET_MS = 5000  # 5 seconds for 1000 items
BATCH_DELETE_TARGET_MS = 3000  # 3 seconds for 1000 items


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class BatchCreateRequest(BaseModel):
    """Request model for batch memory creation."""

    memories: List[MemoryWriteRequest] = Field(
        ..., min_length=1, max_length=1000, description="List of memories to create"
    )
    skip_duplicates: bool = Field(
        True, description="Skip duplicate memories instead of failing"
    )
    validate_all: bool = Field(
        True, description="Validate all memories before creating any"
    )


class BatchCreateResponse(BaseModel):
    """Response model for batch create."""

    created: List[dict]
    skipped: List[dict]
    failed: List[dict]
    total_requested: int
    total_created: int
    total_skipped: int
    total_failed: int
    execution_time_ms: float


class BatchDeleteRequest(BaseModel):
    """Request model for batch memory deletion."""

    context_ids: List[str] = Field(
        ..., min_length=1, max_length=1000, description="List of memory context IDs to delete"
    )
    soft_delete: bool = Field(
        True, description="Soft delete (archive) instead of hard delete"
    )
    cascade: bool = Field(
        True, description="Delete related data (versions, vectors)"
    )


class BatchDeleteResponse(BaseModel):
    """Response model for batch delete."""

    deleted: List[str]
    failed: List[dict]
    total_requested: int
    total_deleted: int
    total_failed: int
    execution_time_ms: float


class BatchExportRequest(BaseModel):
    """Request model for batch export."""

    context_ids: Optional[List[str]] = Field(
        None, description="Specific memory IDs to export (None = all)"
    )
    format: str = Field("json", description="Export format: json, csv")
    include_versions: bool = Field(False, description="Include version history")
    include_vectors: bool = Field(False, description="Include vector embeddings")
    compress: bool = Field(True, description="Compress large exports")
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Additional filters (memory_type, agent_id, etc.)"
    )


class ConsolidateRequest(BaseModel):
    """Request model for memory consolidation."""

    similarity_threshold: float = Field(
        0.85, ge=0.0, le=1.0, description="Similarity threshold for duplicate detection"
    )
    dry_run: bool = Field(True, description="Dry run mode (don't actually merge)")
    merge_strategy: str = Field(
        "newest", description="Merge strategy: newest, oldest, longest"
    )


class ConsolidateResponse(BaseModel):
    """Response model for consolidation."""

    duplicates_found: List[Dict[str, Any]]
    merged: List[Dict[str, Any]]
    total_duplicates: int
    total_merged: int
    execution_time_ms: float
    dry_run: bool


class BatchReindexRequest(BaseModel):
    """Request model for batch reindexing."""

    context_ids: Optional[List[str]] = Field(
        None, description="Specific memory IDs to reindex (None = all)"
    )
    batch_size: int = Field(100, ge=1, le=500, description="Batch size for parallel processing")
    force: bool = Field(False, description="Force reindex even if already indexed")


class BatchReindexResponse(BaseModel):
    """Response model for batch reindex."""

    indexed: List[str]
    failed: List[dict]
    total_requested: int
    total_indexed: int
    total_failed: int
    execution_time_ms: float


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_current_agent_id(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
) -> Optional[str]:
    """Get current agent ID from request headers."""
    return x_agent_id


async def detect_duplicate(
    memory: MemoryWriteRequest,
    agent_id: str,
    db: AsyncSession,
    threshold: float = 0.9,
) -> Optional[Memory]:
    """
    Detect if a memory is a duplicate.

    Uses content similarity and metadata matching.

    Args:
        memory: Memory to check
        agent_id: Agent ID
        db: Database session
        threshold: Similarity threshold

    Returns:
        Duplicate Memory if found, None otherwise
    """
    try:
        # Extract text from content
        text = memory.content.get("text", "") if isinstance(memory.content, dict) else str(memory.content)

        # Search for similar memories
        query = select(Memory).where(Memory.agent_id == agent_id)

        if memory.memory_type:
            query = query.where(Memory.memory_type == memory.memory_type.value)

        if memory.conversation_id:
            query = query.where(Memory.conversation_id == memory.conversation_id)

        result = await db.execute(query)
        existing_memories = result.scalars().all()

        # Simple text matching (could be enhanced with embeddings)
        for existing in existing_memories:
            existing_text = existing.content.get("text", "") if isinstance(existing.content, dict) else str(existing.content)
            if existing_text and text:
                # Calculate simple similarity
                similarity = _text_similarity(existing_text, text)
                if similarity >= threshold:
                    return existing

        return None

    except Exception as e:
        logger.warning(f"Error detecting duplicate: {str(e)}")
        return None


def _text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity (0.0-1.0)."""
    if not text1 or not text2:
        return 0.0

    # Simple word overlap similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


# ============================================================================
# BATCH OPERATIONS ENDPOINTS
# ============================================================================


@router.post(
    "/create",
    response_model=BatchCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch create memories",
    description="Create multiple memories in a single transaction",
)
async def batch_create_memories(
    request: BatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> BatchCreateResponse:
    """
    Batch create memories with transaction support.

    Creates multiple memories in a single transaction. If any memory fails
    and validate_all is True, all changes are rolled back.

    Args:
        request: Batch create request
        db: Database session
        agent_id: Current agent ID

    Returns:
        BatchCreateResponse with results

    Raises:
        HTTPException 401: If agent_id not provided
        HTTPException 400: If validation fails
        HTTPException 500: For server errors
    """
    start_time = time.time()

    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent ID required. Provide X-Agent-ID header.",
        )

    # Verify agent exists
    agent_result = await db.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    created = []
    skipped = []
    failed = []

    try:
        # Validate all if requested
        if request.validate_all:
            for i, mem in enumerate(request.memories):
                try:
                    # Basic validation
                    if not mem.content:
                        raise ValueError(f"Memory {i}: content is required")
                except Exception as e:
                    failed.append({"index": i, "error": str(e)})

            if failed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation failed for {len(failed)} memories",
                )

        # Process memories
        embedding_service = await get_embedding_service()
        memory_store = await get_memory_store()
        versioning_service = await get_versioning_service()

        try:
            await memory_store.ensure_collection()
        except Exception as e:
            logger.warning(f"Collection ensure failed (may already exist): {str(e)}")

        for i, mem_request in enumerate(request.memories):
            try:
                # Check for duplicates
                if request.skip_duplicates:
                    duplicate = await detect_duplicate(mem_request, agent_id, db)
                    if duplicate:
                        skipped.append({
                            "index": i,
                            "reason": "duplicate",
                            "existing_context_id": duplicate.context_id,
                        })
                        continue

                # Generate context_id
                context_id = f"ctx-{uuid.uuid4().hex[:12]}"

                # Generate embedding
                # Extract text from content dict
                content_dict = mem_request.content if isinstance(mem_request.content, dict) else {"text": str(mem_request.content)}
                text_for_embedding = content_dict.get("text", "") or str(content_dict)
                
                embedding = await embedding_service.generate_embedding(text_for_embedding)

                # Create memory
                memory = Memory(
                    context_id=context_id,
                    agent_id=agent_id,
                    conversation_id=mem_request.conversation_id,
                    content=mem_request.content,
                    memory_type=mem_request.memory_type.value,
                    tags=mem_request.tags if mem_request.tags else None,
                    visibility=mem_request.visibility.value,
                    version=1,
                    created_at=datetime.now(timezone.utc),
                )

                db.add(memory)

                # Store in Qdrant
                await memory_store.upsert_memory(
                    context_id=context_id,
                    embedding=embedding,
                    metadata={
                        "agent_id": agent_id,
                        "memory_type": mem_request.memory_type.value,
                        "conversation_id": mem_request.conversation_id,
                    },
                )

                # Create initial version
                await versioning_service.create_version(
                    memory=memory,
                    author_id=agent_id,
                    change_type="added",
                    db=db,
                )

                created.append({
                    "index": i,
                    "context_id": context_id,
                })

            except Exception as e:
                logger.error(f"Error creating memory {i}: {str(e)}")
                failed.append({"index": i, "error": str(e)})

        # Commit all or rollback
        if failed and not request.skip_duplicates:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create {len(failed)} memories",
            )

        await db.commit()

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"Batch create completed: {len(created)} created, "
            f"{len(skipped)} skipped, {len(failed)} failed in {execution_time:.2f}ms"
        )

        return BatchCreateResponse(
            created=created,
            skipped=skipped,
            failed=failed,
            total_requested=len(request.memories),
            total_created=len(created),
            total_skipped=len(skipped),
            total_failed=len(failed),
            execution_time_ms=execution_time,
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Batch create failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch create failed: {str(e)}",
        )


@router.post(
    "/delete",
    response_model=BatchDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch delete memories",
    description="Delete multiple memories with cascade support",
)
async def batch_delete_memories(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> BatchDeleteResponse:
    """
    Batch delete memories with soft delete and cascade support.

    Args:
        request: Batch delete request
        db: Database session
        agent_id: Current agent ID

    Returns:
        BatchDeleteResponse with results
    """
    start_time = time.time()

    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent ID required. Provide X-Agent-ID header.",
        )

    deleted = []
    failed = []

    try:
        memory_store = await get_memory_store()

        for context_id in request.context_ids:
            try:
                # Get memory
                result = await db.execute(
                    select(Memory).where(Memory.context_id == context_id)
                )
                memory = result.scalar_one_or_none()

                if not memory:
                    failed.append({"context_id": context_id, "error": "Not found"})
                    continue

                # Verify ownership
                if memory.agent_id != agent_id:
                    failed.append({"context_id": context_id, "error": "Access denied"})
                    continue

                if request.soft_delete:
                    # Soft delete: mark as deleted
                    memory.visibility = "private"  # Hide from searches
                    # Could add a deleted_at field
                    await db.commit()
                else:
                    # Hard delete: remove from Qdrant
                    if request.cascade:
                        await memory_store.delete_memory(context_id)

                    # Delete related data
                    if request.cascade:
                        # Delete versions
                        from sqlalchemy import delete
                        await db.execute(
                            delete(MemoryVersion).where(
                                MemoryVersion.context_id == context_id
                            )
                        )

                        # Delete vector metadata
                        await db.execute(
                            delete(MemoryVector).where(
                                MemoryVector.context_id == context_id
                            )
                        )

                    # Delete memory
                    await db.delete(memory)
                    await db.commit()

                deleted.append(context_id)

            except Exception as e:
                logger.error(f"Error deleting memory {context_id}: {str(e)}")
                failed.append({"context_id": context_id, "error": str(e)})

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"Batch delete completed: {len(deleted)} deleted, "
            f"{len(failed)} failed in {execution_time:.2f}ms"
        )

        return BatchDeleteResponse(
            deleted=deleted,
            failed=failed,
            total_requested=len(request.context_ids),
            total_deleted=len(deleted),
            total_failed=len(failed),
            execution_time_ms=execution_time,
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Batch delete failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch delete failed: {str(e)}",
        )


@router.post(
    "/export",
    summary="Batch export memories",
    description="Export memories to JSON or CSV format",
)
async def batch_export_memories(
    request: BatchExportRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
):
    """
    Export memories to JSON or CSV format.

    Args:
        request: Export request
        db: Database session
        agent_id: Current agent ID

    Returns:
        StreamingResponse with exported data
    """
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent ID required. Provide X-Agent-ID header.",
        )

    try:
        # Build query
        query = select(Memory).where(Memory.agent_id == agent_id)

        if request.context_ids:
            query = query.where(Memory.context_id.in_(request.context_ids))

        if request.filters:
            if "memory_type" in request.filters:
                query = query.where(Memory.memory_type == request.filters["memory_type"])

        result = await db.execute(query)
        memories = result.scalars().all()

        # Get versions if requested
        versioning_service = await get_versioning_service()
        versions_map = {}
        if request.include_versions:
            for memory in memories:
                versions = await versioning_service.get_version_history(
                    memory.context_id, limit=100, db=db
                )
                versions_map[memory.context_id] = [
                    {
                        "version_number": v.version_number,
                        "change_type": v.change_type,
                        "created_at": v.created_at.isoformat(),
                    }
                    for v in versions
                ]

        # Prepare export data
        export_data = []
        for memory in memories:
            item = {
                "context_id": memory.context_id,
                "agent_id": memory.agent_id,
                "conversation_id": memory.conversation_id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "visibility": memory.visibility,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat(),
            }

            if request.include_versions:
                item["versions"] = versions_map.get(memory.context_id, [])

            export_data.append(item)

        # Generate export
        if request.format == "csv":
            output = io.StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                for item in export_data:
                    # Flatten nested structures for CSV
                    flat_item = {}
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            flat_item[key] = json.dumps(value)
                        else:
                            flat_item[key] = value
                    writer.writerow(flat_item)
            content = output.getvalue().encode("utf-8")
            content_type = "text/csv"
            filename = f"memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            content = json.dumps(export_data, indent=2, default=str).encode("utf-8")
            content_type = "application/json"
            filename = f"memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Compress if requested and large
        if request.compress and len(content) > 10000:
            content = gzip.compress(content)
            filename += ".gz"
            content_type = "application/gzip"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        logger.error(f"Batch export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )


@router.post(
    "/consolidate",
    response_model=ConsolidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Consolidate duplicate memories",
    description="Find and merge duplicate memories",
)
async def consolidate_memories(
    request: ConsolidateRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> ConsolidateResponse:
    """
    Consolidate duplicate memories by finding and merging them.

    Args:
        request: Consolidate request
        db: Database session
        agent_id: Current agent ID

    Returns:
        ConsolidateResponse with results
    """
    start_time = time.time()

    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent ID required. Provide X-Agent-ID header.",
        )

    try:
        # Get all memories for agent
        result = await db.execute(
            select(Memory).where(Memory.agent_id == agent_id)
        )
        all_memories = result.scalars().all()

        duplicates_found = []
        merged = []

        # Find duplicates using similarity
        processed = set()
        embedding_service = await get_embedding_service()

        for i, memory1 in enumerate(all_memories):
            if memory1.context_id in processed:
                continue

            text1 = memory1.content.get("text", "") if isinstance(memory1.content, dict) else str(memory1.content)
            if not text1:
                continue

            # Generate embedding for comparison (optional, using text similarity for now)
            # embedding1 = await embedding_service.generate_embedding(text1)

            duplicates = [memory1]

            for j, memory2 in enumerate(all_memories[i + 1 :], start=i + 1):
                if memory2.context_id in processed:
                    continue

                text2 = memory2.content.get("text", "") if isinstance(memory2.content, dict) else str(memory2.content)
                if not text2:
                    continue

                # Calculate similarity
                similarity = _text_similarity(text1, text2)

                if similarity >= request.similarity_threshold:
                    duplicates.append(memory2)
                    processed.add(memory2.context_id)

            if len(duplicates) > 1:
                duplicates_found.append({
                    "group": len(duplicates_found) + 1,
                    "memories": [
                        {
                            "context_id": m.context_id,
                            "content": m.content,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in duplicates
                    ],
                })

                # Merge if not dry run
                if not request.dry_run:
                    # Select target based on strategy
                    if request.merge_strategy == "newest":
                        target = max(duplicates, key=lambda m: m.created_at)
                        sources = [m for m in duplicates if m.context_id != target.context_id]
                    elif request.merge_strategy == "oldest":
                        target = min(duplicates, key=lambda m: m.created_at)
                        sources = [m for m in duplicates if m.context_id != target.context_id]
                    else:  # longest
                        target = max(duplicates, key=lambda m: len(str(m.content)))
                        sources = [m for m in duplicates if m.context_id != target.context_id]

                    # Merge content
                    # Could implement more sophisticated merging
                    merged.append({
                        "target_context_id": target.context_id,
                        "source_context_ids": [s.context_id for s in sources],
                    })

                    # Delete sources (soft delete)
                    for source in sources:
                        source.visibility = "private"
                        processed.add(source.context_id)

                    await db.commit()

                processed.add(memory1.context_id)

        execution_time = (time.time() - start_time) * 1000

        return ConsolidateResponse(
            duplicates_found=duplicates_found,
            merged=merged,
            total_duplicates=len(duplicates_found),
            total_merged=len(merged),
            execution_time_ms=execution_time,
            dry_run=request.dry_run,
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Consolidation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consolidation failed: {str(e)}",
        )


@router.post(
    "/reindex",
    response_model=BatchReindexResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch reindex memories",
    description="Rebuild semantic search indexes for memories",
)
async def batch_reindex_memories(
    request: BatchReindexRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> BatchReindexResponse:
    """
    Batch reindex memories for semantic search.

    Args:
        request: Reindex request
        db: Database session
        agent_id: Current agent ID

    Returns:
        BatchReindexResponse with results
    """
    start_time = time.time()

    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent ID required. Provide X-Agent-ID header.",
        )

    try:
        # Get memories to reindex
        query = select(Memory).where(Memory.agent_id == agent_id)

        if request.context_ids:
            query = query.where(Memory.context_id.in_(request.context_ids))

        result = await db.execute(query)
        memories = result.scalars().all()

        indexed = []
        failed = []

        embedding_service = await get_embedding_service()
        memory_store = await get_memory_store()
        try:
            await memory_store.ensure_collection()
        except Exception as e:
            logger.warning(f"Collection ensure failed (may already exist): {str(e)}")

        # Process in batches
        for i in range(0, len(memories), request.batch_size):
            batch = memories[i : i + request.batch_size]

            # Process batch in parallel
            tasks = []
            for memory in batch:
                tasks.append(_reindex_single_memory(
                    memory, embedding_service, memory_store, request.force
                ))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for memory, result in zip(batch, results):
                if isinstance(result, Exception):
                    failed.append({
                        "context_id": memory.context_id,
                        "error": str(result),
                    })
                else:
                    indexed.append(memory.context_id)

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"Batch reindex completed: {len(indexed)} indexed, "
            f"{len(failed)} failed in {execution_time:.2f}ms"
        )

        return BatchReindexResponse(
            indexed=indexed,
            failed=failed,
            total_requested=len(memories),
            total_indexed=len(indexed),
            total_failed=len(failed),
            execution_time_ms=execution_time,
        )

    except Exception as e:
        logger.error(f"Batch reindex failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex failed: {str(e)}",
        )


async def _reindex_single_memory(
    memory: Memory,
    embedding_service,
    memory_store,
    force: bool,
) -> bool:
    """Reindex a single memory."""
    try:
        # Check if already indexed
        if not force:
            try:
                existing = await memory_store.get_memory(memory.context_id)
                if existing:
                    return True
            except Exception:
                # If get_memory fails, assume not indexed
                pass

        # Generate embedding
        # Extract text from content dict
        content_dict = memory.content if isinstance(memory.content, dict) else {"text": str(memory.content)}
        text_for_embedding = content_dict.get("text", "") or str(content_dict)
        
        embedding = await embedding_service.generate_embedding(text_for_embedding)

        # Store in Qdrant
        await memory_store.upsert_memory(
            context_id=memory.context_id,
            embedding=embedding,
            metadata={
                "agent_id": memory.agent_id,
                "memory_type": memory.memory_type,
                "conversation_id": memory.conversation_id,
            },
        )

        return True

    except Exception as e:
        logger.error(f"Error reindexing {memory.context_id}: {str(e)}")
        raise


__all__ = ["router"]

