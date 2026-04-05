"""
Memory API Routes

FastAPI router for memory management endpoints using Supabase.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.gml.api.dependencies import get_db
from src.gml.api.schemas.memory import (
    DEFAULT_EMBEDDING_DIMENSION,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryType,
    MemoryVisibility,
    MemoryWriteRequest,
)
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


async def get_current_agent_id(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
) -> Optional[str]:
    """Get current agent ID from request headers."""
    return x_agent_id


def check_memory_access(
    memory: dict, agent_id: Optional[str], agent_organization: Optional[str] = None
) -> bool:
    """
    Check if an agent has access to a memory.
    
    Access control rules:
    - 'all': All agents can read
    - 'organization': Only agents in the same organization
    - 'private': Only the owning agent
    - readable_by list: Only agents in the list
    """
    if not agent_id:
        return False

    # Owner always has access
    if memory.get("agent_id") == agent_id:
        return True

    # Check visibility
    visibility = memory.get("visibility", "private")
    
    if visibility == "all":
        return True

    if visibility == "organization":
        if agent_organization:
            return True  # TODO: Implement organization check

    if visibility == "private":
        return False

    # Check readable_by list
    readable_by = memory.get("readable_by", [])
    if readable_by and agent_id in readable_by:
        return True

    return False


async def generate_embedding(content: dict, model: str = "text-embedding-3-small") -> List[float]:
    """Generate vector embedding for memory content."""
    from src.gml.services.embedding_service import get_embedding_service

    embedding_service = await get_embedding_service()

    # Extract text from content
    text = embedding_service.extract_text_from_content(content)

    if not text:
        logger.warning("Empty text extracted from content, using placeholder")
        return [0.0] * DEFAULT_EMBEDDING_DIMENSION

    # Generate embedding
    embedding = await embedding_service.generate_embedding(text)
    logger.debug(f"Generated embedding for content: {len(embedding)} dimensions")
    return embedding


async def semantic_search(
    query_embedding: List[float],
    memory_type: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10,
    db: SupabaseDB = None,
    agent_id: Optional[str] = None,
) -> List[tuple[dict, float]]:
    """Perform semantic search on memories using vector similarity."""
    from src.gml.services.memory_store import get_memory_store

    memory_store = await get_memory_store()

    # Perform vector search
    search_results = await memory_store.search_similar(
        query_embedding=query_embedding,
        top_k=limit,
        memory_type=memory_type,
        conversation_id=conversation_id,
        agent_id=agent_id,
    )

    # If no database session, return empty results
    if not db:
        logger.warning("No database session provided for semantic search")
        return []

    # Fetch full memory objects
    results = []
    for context_id, score, metadata in search_results:
        memories = await db.select("memories", filters={"context_id": context_id}, limit=1)
        if memories:
            results.append((memories[0], score))

    logger.debug(
        f"Semantic search completed: {len(results)} results for "
        f"memory_type={memory_type}, conversation_id={conversation_id}"
    )

    return results


@router.post(
    "/write",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Write a new memory",
)
async def write_memory(
    request: MemoryWriteRequest,
    db: SupabaseDB = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """Write a new memory with embedding generation."""
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Verify agent exists
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        if not agents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found",
            )

        # Generate unique context_id
        context_id = f"ctx-{uuid.uuid4().hex[:12]}"

        # Generate embedding
        embedding = await generate_embedding(request.content)
        logger.debug(f"Generated embedding for memory {context_id}")

        # Store embedding in Qdrant
        from src.gml.services.memory_store import get_memory_store

        memory_store = await get_memory_store()
        await memory_store.ensure_collection()

        # Store vector in Qdrant
        await memory_store.upsert_memory(
            context_id=context_id,
            embedding=embedding,
            metadata={
                "agent_id": agent_id,
                "memory_type": request.memory_type.value,
                "conversation_id": request.conversation_id,
            },
        )

        # Store vector metadata in database
        await db.insert("memory_vectors", {
            "context_id": context_id,
            "embedding_dimension": len(embedding),
            "embedding_model": "text-embedding-3-small",
            "is_indexed": True,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        })

        # Create memory in database
        now = datetime.now(timezone.utc).isoformat()
        memories = await db.insert("memories", {
            "context_id": context_id,
            "agent_id": agent_id,
            "conversation_id": request.conversation_id,
            "content": request.content,
            "memory_type": request.memory_type.value,
            "tags": request.tags,
            "visibility": request.visibility.value,
            "version": 1,
            "created_at": now,
            "updated_at": now,
        })

        memory = memories[0] if memories else None

        # Create initial version
        try:
            await db.insert("memory_versions", {
                "context_id": context_id,
                "version_number": 1,
                "content": request.content,
                "author_id": agent_id,
                "change_type": "added",
                "created_at": now,
            })
            logger.debug(f"Created initial version for memory {context_id}")
        except Exception as version_error:
            logger.warning(f"Failed to create initial version: {str(version_error)}")

        logger.info(f"Memory written successfully: {context_id} by agent {agent_id}")

        return {
            "context_id": context_id,
            "version": 1,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to write memory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write memory. Please try again later.",
        )


@router.get(
    "/{context_id}",
    response_model=MemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get memory by context ID",
)
async def get_memory(
    context_id: str,
    db: SupabaseDB = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> MemoryResponse:
    """Get memory by context ID with access control."""
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Get memory
        memories = await db.select("memories", filters={"context_id": context_id}, limit=1)
        
        if not memories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        memory = memories[0]

        # Get agent for organization check
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        agent_organization = agents[0].get("organization") if agents else None

        # Check access control
        if not check_memory_access(memory, agent_id, agent_organization):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to memory '{context_id}'",
            )

        # Build response
        return MemoryResponse(
            context_id=memory["context_id"],
            agent_id=memory["agent_id"],
            memory_type=MemoryType(memory["memory_type"]) if memory.get("memory_type") else None,
            created_at=datetime.fromisoformat(memory["created_at"].replace("Z", "+00:00")) if memory.get("created_at") else None,
            version=memory.get("version", 1),
            embedding_dimensions=DEFAULT_EMBEDDING_DIMENSION,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory {context_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory. Please try again later.",
        )


@router.patch(
    "/{context_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update memory",
)
async def update_memory(
    context_id: str,
    request: MemoryWriteRequest,
    db: SupabaseDB = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """Update an existing memory with automatic versioning."""
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Get memory
        memories = await db.select("memories", filters={"context_id": context_id}, limit=1)
        
        if not memories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        memory = memories[0]

        # Verify agent ownership
        if memory["agent_id"] != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own memories",
            )

        # Update memory
        now = datetime.now(timezone.utc).isoformat()
        update_data = {
            "content": request.content,
            "updated_at": now,
        }
        
        if request.memory_type:
            update_data["memory_type"] = request.memory_type.value
        if request.tags:
            update_data["tags"] = request.tags
        if request.visibility:
            update_data["visibility"] = request.visibility.value

        await db.update("memories", update_data, {"context_id": context_id})

        # Update embedding in Qdrant
        try:
            embedding = await generate_embedding(request.content)
            from src.gml.services.memory_store import get_memory_store

            memory_store = await get_memory_store()
            await memory_store.upsert_memory(
                context_id=context_id,
                embedding=embedding,
                metadata={
                    "agent_id": agent_id,
                    "memory_type": request.memory_type.value if request.memory_type else memory["memory_type"],
                    "conversation_id": request.conversation_id or memory.get("conversation_id"),
                },
            )
        except Exception as embed_error:
            logger.warning(f"Failed to update embedding: {str(embed_error)}")

        # Create new version
        try:
            # Get current version count
            versions = await db.select("memory_versions", filters={"context_id": context_id})
            version_num = len(versions) + 1
            
            await db.insert("memory_versions", {
                "context_id": context_id,
                "version_number": version_num,
                "content": request.content,
                "author_id": agent_id,
                "change_type": "modified",
                "created_at": now,
            })
        except Exception as version_error:
            logger.warning(f"Failed to create version: {str(version_error)}")

        logger.info(f"Memory updated successfully: {context_id} by agent {agent_id}")

        return {
            "context_id": context_id,
            "success": True,
            "message": "Memory updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update memory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory. Please try again later.",
        )


@router.post(
    "/search",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search memories semantically",
)
async def search_memories(
    request: MemorySearchRequest,
    db: SupabaseDB = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """Search memories using semantic similarity."""
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Generate query embedding
        query_embedding = await generate_embedding({"text": request.query})
        logger.debug(f"Generated query embedding for: {request.query}")

        # Perform semantic search
        search_results = await semantic_search(
            query_embedding=query_embedding,
            memory_type=request.memory_type.value if request.memory_type else None,
            conversation_id=request.conversation_id,
            limit=request.limit,
            db=db,
            agent_id=agent_id,
        )

        # Fallback to database search if semantic search returns empty
        if not search_results:
            logger.debug("Semantic search returned empty, using database fallback")
            
            filters = {"agent_id": agent_id}
            if request.memory_type:
                filters["memory_type"] = request.memory_type.value
            if request.conversation_id:
                filters["conversation_id"] = request.conversation_id

            memories = await db.select(
                "memories",
                filters=filters,
                order="created_at desc",
                limit=request.limit,
            )

            search_results = [(memory, 0.5) for memory in memories]

        # Get agent for organization check
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        agent_organization = agents[0].get("organization") if agents else None

        # Filter results by access control
        results = []
        for memory, similarity_score in search_results:
            if check_memory_access(memory, agent_id, agent_organization):
                results.append(
                    MemorySearchResult(
                        context_id=memory["context_id"],
                        content=memory.get("content", {}),
                        similarity_score=similarity_score,
                        created_by=memory["agent_id"],
                        created_at=datetime.fromisoformat(memory["created_at"].replace("Z", "+00:00")) if memory.get("created_at") else None,
                    )
                )

        # Limit results
        results = results[: request.limit]

        logger.info(
            f"Memory search completed: query='{request.query}', results={len(results)}"
        )

        return {
            "query": request.query,
            "results": results,
            "total": len(results),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search memories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memories. Please try again later.",
        )


@router.delete(
    "/{context_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete memory",
)
async def delete_memory(
    context_id: str,
    db: SupabaseDB = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """Delete a memory by context ID."""
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Get memory
        memories = await db.select("memories", filters={"context_id": context_id}, limit=1)
        
        if not memories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        memory = memories[0]

        # Verify agent ownership
        if memory["agent_id"] != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own memories",
            )

        # Delete from Qdrant
        try:
            from src.gml.services.memory_store import get_memory_store
            memory_store = await get_memory_store()
            await memory_store.delete_memory(context_id)
        except Exception as qdrant_error:
            logger.warning(f"Failed to delete from Qdrant: {str(qdrant_error)}")

        # Delete from database
        await db.delete("memories", {"context_id": context_id})
        await db.delete("memory_vectors", {"context_id": context_id})
        await db.delete("memory_versions", {"context_id": context_id})

        logger.info(f"Memory deleted successfully: {context_id} by agent {agent_id}")

        return {
            "context_id": context_id,
            "success": True,
            "message": "Memory deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory. Please try again later.",
        )
