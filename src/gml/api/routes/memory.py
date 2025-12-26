"""
Memory API Routes

FastAPI router for memory management endpoints including writing,
retrieval, and semantic search with proper error handling and access control.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.memory import (
    DEFAULT_EMBEDDING_DIMENSION,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryType,
    MemoryVisibility,
    MemoryWriteRequest,
)
from src.gml.db.database import get_db
from src.gml.db.models import Agent, Memory
from src.gml.services import CostService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


async def get_current_agent_id(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
) -> Optional[str]:
    """
    Get current agent ID from request headers.

    This is a placeholder for authentication middleware.
    In production, this should validate the agent's API token.

    Args:
        x_agent_id: Agent ID from X-Agent-ID header

    Returns:
        Agent ID if provided, None otherwise
    """
    return x_agent_id


def check_memory_access(
    memory: Memory, agent_id: Optional[str], agent_organization: Optional[str] = None
) -> bool:
    """
    Check if an agent has access to a memory.

    Access control rules:
    - 'all': All agents can read
    - 'organization': Only agents in the same organization
    - 'private': Only the owning agent
    - readable_by list: Only agents in the list

    Args:
        memory: Memory instance to check
        agent_id: ID of the agent requesting access
        agent_organization: Organization of the requesting agent

    Returns:
        True if access is granted, False otherwise
    """
    if not agent_id:
        return False

    # Owner always has access
    if memory.agent_id == agent_id:
        return True

    # Check visibility
    if memory.visibility == "all":
        return True

    if memory.visibility == "organization":
        # Get memory owner's organization
        # For now, we'll need to query the agent
        # In production, this should be optimized with joins
        if agent_organization:
            # This would require querying the agent's organization
            # Placeholder: assume same organization check
            return True  # TODO: Implement organization check

    if memory.visibility == "private":
        return False

    # Check readable_by list
    if memory.readable_by:
        readable_by_list = (
            memory.readable_by if isinstance(memory.readable_by, list) else []
        )
        if agent_id in readable_by_list:
            return True

    return False


async def generate_embedding(content: dict, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate vector embedding for memory content.

    Extracts text from content and generates embedding using the embedding service.

    Args:
        content: Memory content dictionary
        model: Embedding model to use (not used, service handles this)

    Returns:
        List of floats representing the embedding vector
    """
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
    db: AsyncSession = None,
    agent_id: Optional[str] = None,
) -> List[tuple[Memory, float]]:
    """
    Perform semantic search on memories using vector similarity.

    Uses Qdrant vector database for fast similarity search.

    Args:
        query_embedding: Query vector embedding
        memory_type: Optional filter by memory type
        conversation_id: Optional filter by conversation ID
        limit: Maximum number of results
        db: Database session (optional, used for fetching memory objects)
        agent_id: Optional filter by agent ID

    Returns:
        List of tuples (Memory, similarity_score)
    """
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
        memory_result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = memory_result.scalar_one_or_none()

        if memory:
            results.append((memory, score))

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
    description="Create a new memory with embedding generation and access control",
)
async def write_memory(
    request: MemoryWriteRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """
    Write a new memory.

    Creates a new memory with:
    - Generated context_id
    - Vector embedding generation (stub)
    - Access control settings
    - Version tracking

    Also records the memory write cost.

    Args:
        request: Memory write request with content and metadata
        db: Database session (dependency injection)
        agent_id: Current agent ID from headers

    Returns:
        Dictionary containing:
            - context_id: Unique memory context identifier
            - version: Memory version number

    Raises:
        HTTPException 401: If agent_id not provided
        HTTPException 500: For server errors

    Example:
        POST /api/v1/memory/write
        Headers: X-Agent-ID: agent-001
        {
            "conversation_id": "conv-xyz-456",
            "content": {"text": "User prefers dark mode"},
            "memory_type": "semantic",
            "visibility": "all",
            "tags": ["ui", "preference"]
        }

        Response 201:
        {
            "context_id": "ctx-abc-123",
            "version": 1
        }
    """
    try:
        # Validate agent_id
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

        # Generate unique context_id
        context_id = f"ctx-{uuid.uuid4().hex[:12]}"

        # Generate embedding
        embedding = await generate_embedding(request.content)
        logger.debug(f"Generated embedding for memory {context_id}")

        # Store embedding in Qdrant
        from src.gml.services.memory_store import get_memory_store
        from src.gml.db.models import MemoryVector

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
        vector_metadata = MemoryVector(
            context_id=context_id,
            embedding_dimension=len(embedding),
            embedding_model="text-embedding-3-small",  # Default model
            is_indexed=True,
            indexed_at=datetime.now(timezone.utc),
        )
        db.add(vector_metadata)

        # Create memory in database
        memory = Memory(
            context_id=context_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            content=request.content,
            memory_type=request.memory_type.value,
            tags=request.tags if request.tags else None,
            visibility=request.visibility.value,
            version=1,
            created_at=datetime.now(timezone.utc),
        )

        db.add(memory)
        await db.commit()
        await db.refresh(memory)

        # Create initial version
        try:
            from src.gml.services.memory_versioning import get_versioning_service
            versioning_service = await get_versioning_service()
            version = await versioning_service.create_version(
                memory=memory,
                author_id=agent_id,
                change_type="added",
                db=db,
            )
            logger.debug(f"Created initial version {version.version_number} for memory {context_id}")
        except Exception as version_error:
            logger.warning(
                f"Failed to create initial version for memory {context_id}: {str(version_error)}"
            )

        # Record memory write cost
        try:
            await CostService.record_cost(
                db=db,
                cost_type="memory_write",
                agent_id=agent_id,
                amount=CostService.get_cost_for_operation("memory_write"),
                request_id=f"memory-write-{context_id}",
            )
        except Exception as cost_error:
            logger.warning(
                f"Failed to record cost for memory write {context_id}: {str(cost_error)}"
            )

        logger.info(f"Memory written successfully: {context_id} by agent {agent_id}")

        return {
            "context_id": context_id,
            "version": memory.version or 1,
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
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
    description="Retrieve a memory by its context ID with access control",
)
async def get_memory(
    context_id: str,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> MemoryResponse:
    """
    Get memory by context ID.

    Retrieves memory content with access control checks.
    Only returns memory if the requesting agent has permission to read it.

    Args:
        context_id: Unique memory context identifier
        db: Database session (dependency injection)
        agent_id: Current agent ID from headers

    Returns:
        MemoryResponse with memory details

    Raises:
        HTTPException 401: If agent_id not provided
        HTTPException 403: If access denied
        HTTPException 404: If memory not found
        HTTPException 500: For server errors

    Example:
        GET /api/v1/memory/ctx-abc-123
        Headers: X-Agent-ID: agent-001

        Response 200:
        {
            "context_id": "ctx-abc-123",
            "agent_id": "agent-001",
            "memory_type": "semantic",
            "created_at": "2024-01-15T10:30:00Z",
            "version": 1,
            "embedding_dimensions": 1536
        }
    """
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Get memory
        result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = result.scalar_one_or_none()

        if memory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        # Get agent for organization check
        agent_result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        agent_organization = agent.organization if agent else None

        # Check access control
        if not check_memory_access(memory, agent_id, agent_organization):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to memory '{context_id}'",
            )

        # Build response
        response = MemoryResponse(
            context_id=memory.context_id,
            agent_id=memory.agent_id,
            memory_type=MemoryType(memory.memory_type) if memory.memory_type else None,
            created_at=memory.created_at,
            version=memory.version,
            embedding_dimensions=DEFAULT_EMBEDDING_DIMENSION,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get memory {context_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory. Please try again later.",
        )


@router.patch(
    "/{context_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update memory",
    description="Update an existing memory with automatic versioning",
)
async def update_memory(
    context_id: str,
    request: MemoryWriteRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """
    Update an existing memory.

    Updates memory content and automatically creates a new version.
    Also updates the vector embedding in Qdrant if content changed.

    Args:
        context_id: Memory context ID to update
        request: Updated memory content and metadata
        db: Database session
        agent_id: Current agent ID from headers

    Returns:
        Dictionary with updated memory info

    Raises:
        HTTPException 401: If agent_id not provided
        HTTPException 404: If memory not found
        HTTPException 500: For server errors
    """
    try:
        # Validate agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent ID required. Provide X-Agent-ID header.",
            )

        # Get memory
        result = await db.execute(
            select(Memory).where(Memory.context_id == context_id)
        )
        memory = result.scalar_one_or_none()

        if memory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory with context_id '{context_id}' not found",
            )

        # Verify agent ownership
        if memory.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own memories",
            )

        # Update memory content
        memory.content = request.content
        if request.memory_type:
            memory.memory_type = request.memory_type.value
        if request.tags:
            memory.tags = request.tags
        if request.visibility:
            memory.visibility = request.visibility.value

        await db.commit()
        await db.refresh(memory)

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
                    "memory_type": request.memory_type.value if request.memory_type else memory.memory_type,
                    "conversation_id": request.conversation_id or memory.conversation_id,
                },
            )
        except Exception as embed_error:
            logger.warning(f"Failed to update embedding: {str(embed_error)}")

        # Create new version automatically
        try:
            from src.gml.services.memory_versioning import get_versioning_service

            versioning_service = await get_versioning_service()
            version = await versioning_service.create_version(
                memory=memory,
                author_id=agent_id,
                change_type="modified",
                db=db,
            )
            logger.debug(f"Created version {version.version_number} for memory {context_id}")
        except Exception as version_error:
            logger.warning(f"Failed to create version: {str(version_error)}")

        logger.info(f"Memory updated successfully: {context_id} by agent {agent_id}")

        return {
            "context_id": context_id,
            "success": True,
            "message": "Memory updated successfully",
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
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
    description="Perform semantic search on memories using vector embeddings",
)
async def search_memories(
    request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> dict:
    """
    Search memories using semantic similarity.

    Performs vector similarity search on memories with optional filtering
    by memory type and conversation ID. Returns top-N results with similarity scores.

    Also records the memory search cost.

    Args:
        request: Search request with query and filters
        db: Database session (dependency injection)
        agent_id: Current agent ID from headers

    Returns:
        Dictionary containing:
            - query: The search query
            - results: List of MemorySearchResult objects
            - total: Total number of results found

    Raises:
        HTTPException 401: If agent_id not provided
        HTTPException 500: For server errors

    Example:
        POST /api/v1/memory/search
        Headers: X-Agent-ID: agent-001
        {
            "query": "user interface preferences",
            "memory_type": "semantic",
            "conversation_id": "conv-xyz-456",
            "limit": 10
        }

        Response 200:
        {
            "query": "user interface preferences",
            "results": [
                {
                    "context_id": "ctx-abc-123",
                    "content": {"text": "User prefers dark mode"},
                    "similarity_score": 0.92,
                    "created_by": "agent-001",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ],
            "total": 1
        }
    """
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

        # For now, fallback to database search if semantic search returns empty
        # This is a placeholder until vector search is implemented
        if not search_results:
            logger.debug("Semantic search stub returned empty, using database fallback")
            # Fallback: simple database query (not semantic)
            query = select(Memory).where(Memory.agent_id == agent_id)

            if request.memory_type:
                query = query.where(Memory.memory_type == request.memory_type.value)

            if request.conversation_id:
                query = query.where(Memory.conversation_id == request.conversation_id)

            query = query.limit(request.limit).order_by(Memory.created_at.desc())

            result = await db.execute(query)
            memories = result.scalars().all()

            # Convert to search results with placeholder similarity scores
            search_results = [
                (memory, 0.5) for memory in memories
            ]  # Placeholder similarity score

        # Get agent for organization check
        agent_result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        agent_organization = agent.organization if agent else None

        # Filter results by access control and convert to response format
        results = []
        for memory, similarity_score in search_results:
            # Check access control
            if check_memory_access(memory, agent_id, agent_organization):
                results.append(
                    MemorySearchResult(
                        context_id=memory.context_id,
                        content=memory.content or {},
                        similarity_score=similarity_score,
                        created_by=memory.agent_id,
                        created_at=memory.created_at,
                    )
                )

        # Limit results
        results = results[: request.limit]

        # Record memory search cost
        try:
            await CostService.record_cost(
                db=db,
                cost_type="memory_search",
                agent_id=agent_id,
                amount=CostService.get_cost_for_operation("memory_search"),
                request_id=f"memory-search-{request.query[:50]}",
            )
        except Exception as cost_error:
            logger.warning(
                f"Failed to record cost for memory search: {str(cost_error)}"
            )

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

