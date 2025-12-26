"""
Search API Routes for GML Infrastructure

Provides comprehensive search endpoints for memories:
- Semantic search with vector embeddings
- Keyword search (text matching)
- Hybrid search (semantic + keyword combination)
- Search with conversation context
- Caching and performance optimization

Usage:
    POST /api/v1/search/semantic
    POST /api/v1/search/keyword
    POST /api/v1/search/hybrid
"""

import hashlib
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.memory import MemorySearchResult, MemoryType
from src.gml.db.database import get_db
from src.gml.db.models import Memory, SearchCache, SearchHistory
from src.gml.services.embedding_service import get_embedding_service
from src.gml.services.memory_store import get_memory_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# Search cache TTL (1 hour)
SEARCH_CACHE_TTL = 3600


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity score (0.0-1.0)"
    )
    memory_type: Optional[MemoryType] = Field(None, description="Filter by memory type")
    conversation_id: Optional[str] = Field(None, description="Filter by conversation ID")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")
    use_cache: bool = Field(True, description="Whether to use search cache")


class KeywordSearchRequest(BaseModel):
    """Request model for keyword search."""

    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results")
    memory_type: Optional[MemoryType] = Field(None, description="Filter by memory type")
    conversation_id: Optional[str] = Field(None, description="Filter by conversation ID")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search (semantic + keyword)."""

    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    semantic_weight: float = Field(
        0.7, ge=0.0, le=1.0, description="Weight for semantic search (0.0-1.0)"
    )
    keyword_weight: float = Field(
        0.3, ge=0.0, le=1.0, description="Weight for keyword search (0.0-1.0)"
    )
    memory_type: Optional[MemoryType] = Field(None, description="Filter by memory type")
    conversation_id: Optional[str] = Field(None, description="Filter by conversation ID")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")
    use_cache: bool = Field(True, description="Whether to use search cache")


class SearchResponse(BaseModel):
    """Response model for search results."""

    query: str
    query_type: str
    results: List[MemorySearchResult]
    total: int
    execution_time_ms: float
    cached: bool = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_current_agent_id(
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
) -> Optional[str]:
    """Get current agent ID from request headers."""
    return x_agent_id


def generate_cache_key(
    query: str,
    query_type: str,
    top_k: int,
    threshold: Optional[float],
    memory_type: Optional[str],
    conversation_id: Optional[str],
    agent_id: Optional[str],
) -> str:
    """
    Generate cache key for search query.

    Args:
        query: Search query text
        query_type: Type of search (semantic, keyword, hybrid)
        top_k: Number of results
        threshold: Similarity threshold
        memory_type: Memory type filter
        conversation_id: Conversation ID filter
        agent_id: Agent ID filter

    Returns:
        Cache key string
    """
    key_parts = [
        query_type,
        query.lower().strip(),
        str(top_k),
        str(threshold) if threshold else "",
        memory_type or "",
        conversation_id or "",
        agent_id or "",
    ]
    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode("utf-8")).hexdigest()


async def get_cached_results(
    cache_key: str, db: AsyncSession
) -> Optional[List[MemorySearchResult]]:
    """
    Retrieve cached search results.

    Args:
        cache_key: Cache key
        db: Database session

    Returns:
        Cached results or None if not found or expired
    """
    try:
        result = await db.execute(
            select(SearchCache).where(SearchCache.cache_key == cache_key)
        )
        cache_entry = result.scalar_one_or_none()

        if not cache_entry:
            return None

        # Check if expired
        if cache_entry.expires_at and cache_entry.expires_at < datetime.now(timezone.utc):
            # Delete expired cache
            await db.delete(cache_entry)
            await db.commit()
            return None

        # Deserialize results
        if cache_entry.results:
            results = []
            for item in cache_entry.results.get("results", []):
                # Fetch memory from database
                memory_result = await db.execute(
                    select(Memory).where(Memory.context_id == item["context_id"])
                )
                memory = memory_result.scalar_one_or_none()

                if memory:
                    results.append(
                        MemorySearchResult(
                            context_id=memory.context_id,
                            content=memory.content or {},
                            similarity_score=item.get("score", 0.0),
                            created_by=memory.agent_id,
                            created_at=memory.created_at,
                        )
                    )

            return results

        return None

    except Exception as e:
        logger.warning(f"Error retrieving cached results: {str(e)}")
        return None


async def cache_results(
    cache_key: str,
    query_text: str,
    results: List[MemorySearchResult],
    ttl_seconds: int,
    db: AsyncSession,
) -> None:
    """
    Cache search results.

    Args:
        cache_key: Cache key
        query_text: Search query text
        results: Search results to cache
        ttl_seconds: Time-to-live in seconds
        db: Database session
    """
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        # Serialize results (store context_ids and scores)
        results_data = {
            "results": [
                {
                    "context_id": r.context_id,
                    "score": r.similarity_score,
                }
                for r in results
            ]
        }

        cache_entry = SearchCache(
            cache_key=cache_key,
            query_text=query_text,
            results=results_data,
            result_count=len(results),
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
        )

        db.add(cache_entry)
        await db.commit()

    except Exception as e:
        logger.warning(f"Error caching results: {str(e)}")
        # Don't fail the request if caching fails


async def record_search_history(
    search_id: str,
    agent_id: Optional[str],
    query_text: str,
    query_type: str,
    result_count: int,
    execution_time_ms: float,
    filters: Dict[str, Any],
    db: AsyncSession,
) -> None:
    """
    Record search query in history for analytics.

    Args:
        search_id: Unique search identifier
        agent_id: Agent ID
        query_text: Search query text
        query_type: Type of search
        result_count: Number of results
        execution_time_ms: Execution time in milliseconds
        filters: Search filters applied
        db: Database session
    """
    try:
        history_entry = SearchHistory(
            search_id=search_id,
            agent_id=agent_id,
            query_text=query_text,
            query_type=query_type,
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            filters=filters,
        )

        db.add(history_entry)
        await db.commit()

    except Exception as e:
        logger.warning(f"Error recording search history: {str(e)}")
        # Don't fail the request if history recording fails


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================


@router.post(
    "/semantic",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search",
    description="Perform semantic similarity search using vector embeddings",
)
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> SearchResponse:
    """
    Perform semantic search on memories.

    Uses vector embeddings to find semantically similar memories.
    Results are ranked by cosine similarity score.

    Args:
        request: Semantic search request
        db: Database session
        agent_id: Current agent ID

    Returns:
        SearchResponse with ranked results

    Raises:
        HTTPException 400: If query is invalid
        HTTPException 500: For server errors
    """
    start_time = time.time()
    search_id = f"search-{uuid.uuid4().hex[:12]}"

    try:
        # Generate cache key
        cache_key = generate_cache_key(
            query=request.query,
            query_type="semantic",
            top_k=request.top_k,
            threshold=request.threshold,
            memory_type=request.memory_type.value if request.memory_type else None,
            conversation_id=request.conversation_id,
            agent_id=request.agent_id or agent_id,
        )

        # Check cache
        cached_results = None
        if request.use_cache:
            cached_results = await get_cached_results(cache_key, db)

        if cached_results is not None:
            logger.debug(f"Cache hit for semantic search: {request.query[:50]}")
            execution_time = (time.time() - start_time) * 1000

            # Record history
            await record_search_history(
                search_id=search_id,
                agent_id=request.agent_id or agent_id,
                query_text=request.query,
                query_type="semantic",
                result_count=len(cached_results),
                execution_time_ms=execution_time,
                filters={
                    "top_k": request.top_k,
                    "threshold": request.threshold,
                    "memory_type": request.memory_type.value if request.memory_type else None,
                    "conversation_id": request.conversation_id,
                },
                db=db,
            )

            return SearchResponse(
                query=request.query,
                query_type="semantic",
                results=cached_results[: request.top_k],
                total=len(cached_results),
                execution_time_ms=execution_time,
                cached=True,
            )

        # Generate query embedding
        embedding_service = await get_embedding_service()
        query_embedding = await embedding_service.generate_embedding(request.query)

        # Perform vector search
        memory_store = await get_memory_store()
        search_results = await memory_store.search_similar(
            query_embedding=query_embedding,
            top_k=request.top_k * 2,  # Get more for filtering
            threshold=request.threshold,
            memory_type=request.memory_type.value if request.memory_type else None,
            agent_id=request.agent_id or agent_id,
            conversation_id=request.conversation_id,
        )

        # Fetch full memory objects
        results = []
        for context_id, score, metadata in search_results:
            memory_result = await db.execute(
                select(Memory).where(Memory.context_id == context_id)
            )
            memory = memory_result.scalar_one_or_none()

            if memory:
                results.append(
                    MemorySearchResult(
                        context_id=memory.context_id,
                        content=memory.content or {},
                        similarity_score=score,
                        created_by=memory.agent_id,
                        created_at=memory.created_at,
                    )
                )

        # Limit results
        results = results[: request.top_k]

        execution_time = (time.time() - start_time) * 1000

        # Cache results
        if request.use_cache and results:
            await cache_results(
                cache_key=cache_key,
                query_text=request.query,
                results=results,
                ttl_seconds=SEARCH_CACHE_TTL,
                db=db,
            )

        # Record history
        await record_search_history(
            search_id=search_id,
            agent_id=request.agent_id or agent_id,
            query_text=request.query,
            query_type="semantic",
            result_count=len(results),
            execution_time_ms=execution_time,
            filters={
                "top_k": request.top_k,
                "threshold": request.threshold,
                "memory_type": request.memory_type.value if request.memory_type else None,
                "conversation_id": request.conversation_id,
            },
            db=db,
        )

        logger.info(
            f"Semantic search completed: query='{request.query[:50]}', "
            f"results={len(results)}, time={execution_time:.2f}ms"
        )

        return SearchResponse(
            query=request.query,
            query_type="semantic",
            results=results,
            total=len(results),
            execution_time_ms=execution_time,
            cached=False,
        )

    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post(
    "/keyword",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Keyword search",
    description="Perform keyword-based text search on memories",
)
async def keyword_search(
    request: KeywordSearchRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> SearchResponse:
    """
    Perform keyword search on memories.

    Uses text matching to find memories containing query keywords.
    Results are ranked by relevance (simple keyword frequency).

    Args:
        request: Keyword search request
        db: Database session
        agent_id: Current agent ID

    Returns:
        SearchResponse with ranked results
    """
    start_time = time.time()
    search_id = f"search-{uuid.uuid4().hex[:12]}"

    try:
        # Build database query
        query = select(Memory)

        # Apply filters
        filter_agent_id = request.agent_id or agent_id
        if filter_agent_id:
            query = query.where(Memory.agent_id == filter_agent_id)

        if request.memory_type:
            query = query.where(Memory.memory_type == request.memory_type.value)

        if request.conversation_id:
            query = query.where(Memory.conversation_id == request.conversation_id)

        # Get all matching memories
        result = await db.execute(query)
        all_memories = result.scalars().all()

        # Simple keyword matching and scoring
        query_lower = request.query.lower()
        query_words = set(query_lower.split())

        scored_memories = []
        embedding_service = await get_embedding_service()

        for memory in all_memories:
            # Extract text from content
            text = embedding_service.extract_text_from_content(memory.content or {})
            text_lower = text.lower()

            # Simple keyword frequency score
            score = 0.0
            for word in query_words:
                score += text_lower.count(word)

            if score > 0:
                # Normalize score
                score = min(score / len(query_words), 1.0)
                scored_memories.append((memory, score))

        # Sort by score (descending)
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        # Convert to results
        results = []
        for memory, score in scored_memories[: request.top_k]:
            results.append(
                MemorySearchResult(
                    context_id=memory.context_id,
                    content=memory.content or {},
                    similarity_score=score,
                    created_by=memory.agent_id,
                    created_at=memory.created_at,
                )
            )

        execution_time = (time.time() - start_time) * 1000

        # Record history
        await record_search_history(
            search_id=search_id,
            agent_id=filter_agent_id,
            query_text=request.query,
            query_type="keyword",
            result_count=len(results),
            execution_time_ms=execution_time,
            filters={
                "top_k": request.top_k,
                "memory_type": request.memory_type.value if request.memory_type else None,
                "conversation_id": request.conversation_id,
            },
            db=db,
        )

        logger.info(
            f"Keyword search completed: query='{request.query[:50]}', "
            f"results={len(results)}, time={execution_time:.2f}ms"
        )

        return SearchResponse(
            query=request.query,
            query_type="keyword",
            results=results,
            total=len(results),
            execution_time_ms=execution_time,
            cached=False,
        )

    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post(
    "/hybrid",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid search",
    description="Perform hybrid search combining semantic and keyword search",
)
async def hybrid_search(
    request: HybridSearchRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Depends(get_current_agent_id),
) -> SearchResponse:
    """
    Perform hybrid search combining semantic and keyword search.

    Combines results from both semantic and keyword searches with weighted scores.

    Args:
        request: Hybrid search request
        db: Database session
        agent_id: Current agent ID

    Returns:
        SearchResponse with ranked results
    """
    start_time = time.time()
    search_id = f"search-{uuid.uuid4().hex[:12]}"

    try:
        # Normalize weights
        total_weight = request.semantic_weight + request.keyword_weight
        if total_weight > 0:
            semantic_weight = request.semantic_weight / total_weight
            keyword_weight = request.keyword_weight / total_weight
        else:
            semantic_weight = 0.5
            keyword_weight = 0.5

        # Perform both searches
        semantic_request = SemanticSearchRequest(
            query=request.query,
            top_k=request.top_k * 2,
            threshold=request.threshold,
            memory_type=request.memory_type,
            conversation_id=request.conversation_id,
            agent_id=request.agent_id,
            use_cache=request.use_cache,
        )

        keyword_request = KeywordSearchRequest(
            query=request.query,
            top_k=request.top_k * 2,
            memory_type=request.memory_type,
            conversation_id=request.conversation_id,
            agent_id=request.agent_id,
        )

        # Run searches
        semantic_response = await semantic_search(semantic_request, db, agent_id)
        keyword_response = await keyword_search(keyword_request, db, agent_id)

        # Combine results
        result_scores: Dict[str, float] = {}

        # Add semantic results with weight
        for result in semantic_response.results:
            score = result.similarity_score * semantic_weight
            result_scores[result.context_id] = score

        # Add keyword results with weight (merge if exists)
        for result in keyword_response.results:
            if result.context_id in result_scores:
                result_scores[result.context_id] += result.similarity_score * keyword_weight
            else:
                result_scores[result.context_id] = result.similarity_score * keyword_weight

        # Create combined results
        all_results_map: Dict[str, MemorySearchResult] = {}
        for result in semantic_response.results + keyword_response.results:
            if result.context_id not in all_results_map:
                all_results_map[result.context_id] = result

        # Sort by combined score
        combined_results = []
        for context_id, score in sorted(
            result_scores.items(), key=lambda x: x[1], reverse=True
        ):
            if context_id in all_results_map:
                result = all_results_map[context_id]
                # Update score with combined score
                result.similarity_score = score
                combined_results.append(result)

        # Limit results
        results = combined_results[: request.top_k]

        execution_time = (time.time() - start_time) * 1000

        # Record history
        await record_search_history(
            search_id=search_id,
            agent_id=request.agent_id or agent_id,
            query_text=request.query,
            query_type="hybrid",
            result_count=len(results),
            execution_time_ms=execution_time,
            filters={
                "top_k": request.top_k,
                "threshold": request.threshold,
                "semantic_weight": request.semantic_weight,
                "keyword_weight": request.keyword_weight,
                "memory_type": request.memory_type.value if request.memory_type else None,
                "conversation_id": request.conversation_id,
            },
            db=db,
        )

        logger.info(
            f"Hybrid search completed: query='{request.query[:50]}', "
            f"results={len(results)}, time={execution_time:.2f}ms"
        )

        return SearchResponse(
            query=request.query,
            query_type="hybrid",
            results=results,
            total=len(results),
            execution_time_ms=execution_time,
            cached=False,
        )

    except Exception as e:
        logger.error(f"Error in hybrid search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


__all__ = ["router"]

