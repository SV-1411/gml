"""
Memory Store Service for GML Infrastructure

Provides vector database integration with Pinecone for semantic search:
- Vector storage and indexing
- Similarity search with metadata filtering
- Automatic index management

Usage:
    >>> from src.gml.services.memory_store import get_memory_store
    >>> 
    >>> store = await get_memory_store()
    >>> 
    >>> # Store a memory with embedding
    >>> await store.upsert_memory(
    ...     context_id="ctx-123",
    ...     embedding=[0.1, 0.2, ...],
    ...     metadata={"agent_id": "agent-1", "memory_type": "semantic"}
    ... )
    >>> 
    >>> # Search similar memories
    >>> results = await store.search_similar(
    ...     query_embedding=[0.1, 0.2, ...],
    ...     top_k=10
    ... )
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.gml.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Pinecone vector dimension (OpenAI text-embedding-3-small = 1536)
VECTOR_DIMENSION = 1536


class MemoryStore:
    """
    Vector database service for memory storage using Pinecone.
    
    Features:
        - Managed vector database (no infrastructure)
        - Metadata filtering
        - Automatic index management
        - Serverless (free tier available)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None,
    ) -> None:
        """
        Initialize memory store with Pinecone client.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment/region
            index_name: Pinecone index name
        """
        self.api_key = api_key or settings.PINECONE_API_KEY
        self.environment = environment or settings.PINECONE_ENVIRONMENT
        self.index_name = index_name or settings.PINECONE_INDEX_NAME
        self._index = None
        self._pc = None

        logger.info(
            f"MemoryStore initialized: index={self.index_name}, "
            f"environment={self.environment}"
        )

    def _context_id_to_vector_id(self, context_id: str) -> str:
        """
        Convert context_id to a valid Pinecone vector ID.
        
        Pinecone IDs must be alphanumeric strings.
        Uses SHA-256 hash for deterministic mapping.
        """
        hash_bytes = hashlib.sha256(context_id.encode()).digest()
        return hash_bytes.hex()[:36]  # UUID-like format

    async def _get_index(self):
        """Get or initialize Pinecone index."""
        if self._index is not None:
            return self._index

        try:
            from pinecone import Pinecone, ServerlessSpec
            
            # Initialize Pinecone client
            self._pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists, create if not
            existing_indexes = [idx.name for idx in self._pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self._pc.create_index(
                    name=self.index_name,
                    dimension=VECTOR_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.environment,
                    ),
                )
                # Wait for index to be ready
                import time
                while not self._pc.describe_index(self.index_name).status.ready:
                    time.sleep(1)
            
            self._index = self._pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            return self._index

        except ImportError:
            raise ImportError(
                "Pinecone client not installed. Install with: pip install pinecone"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise

    async def ensure_collection(self) -> bool:
        """Ensure the Pinecone index exists (creates if needed)."""
        try:
            await self._get_index()
            return True
        except Exception as e:
            logger.error(f"Failed to ensure index: {str(e)}")
            return False

    async def upsert_memory(
        self,
        context_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        replace: bool = True,
    ) -> bool:
        """
        Store or update a memory vector.
        
        Args:
            context_id: Unique memory identifier
            embedding: Vector embedding
            metadata: Metadata dict (agent_id, memory_type, etc.)
            replace: Whether to replace existing (always True for Pinecone)
            
        Returns:
            True if successful
        """
        try:
            index = await self._get_index()
            vector_id = self._context_id_to_vector_id(context_id)
            
            # Add context_id to metadata for retrieval
            metadata_with_id = {**metadata, "context_id": context_id}
            
            # Upsert to Pinecone
            index.upsert([
                (vector_id, embedding, metadata_with_id)
            ])
            
            logger.debug(f"Upserted memory {context_id} to Pinecone")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert memory: {str(e)}")
            return False

    async def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        threshold: float = 0.0,
        memory_type: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar memories.
        
        Args:
            query_embedding: Query vector
            top_k: Maximum results
            threshold: Minimum similarity score
            memory_type: Filter by memory type
            conversation_id: Filter by conversation
            agent_id: Filter by agent
            
        Returns:
            List of (context_id, score, metadata) tuples
        """
        try:
            index = await self._get_index()
            
            # Build metadata filter
            filter_dict = {}
            if memory_type:
                filter_dict["memory_type"] = {"$eq": memory_type}
            if conversation_id:
                filter_dict["conversation_id"] = {"$eq": conversation_id}
            if agent_id:
                filter_dict["agent_id"] = {"$eq": agent_id}
            
            # Query Pinecone
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None,
            )
            
            # Parse results
            matches = []
            for match in results.matches:
                if match.score >= threshold:
                    metadata = match.metadata or {}
                    context_id = metadata.pop("context_id", match.id)
                    matches.append((context_id, match.score, metadata))
            
            logger.debug(f"Found {len(matches)} similar memories")
            return matches

        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []

    async def delete_memory(self, context_id: str) -> bool:
        """Delete a memory by context_id."""
        try:
            index = await self._get_index()
            vector_id = self._context_id_to_vector_id(context_id)
            index.delete([vector_id])
            logger.debug(f"Deleted memory {context_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {str(e)}")
            return False

    async def delete_by_agent(self, agent_id: str) -> int:
        """Delete all memories for an agent."""
        try:
            index = await self._get_index()
            # Delete by metadata filter
            index.delete(
                filter={"agent_id": {"$eq": agent_id}},
                delete_all=False,
            )
            logger.info(f"Deleted memories for agent {agent_id}")
            return 0  # Pinecone doesn't return count
        except Exception as e:
            logger.error(f"Failed to delete agent memories: {str(e)}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            index = await self._get_index()
            stats = index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}


# Singleton instance
_store: Optional[MemoryStore] = None


async def get_memory_store() -> MemoryStore:
    """Get or create memory store singleton."""
    global _store
    if _store is None:
        _store = MemoryStore()
        await _store.ensure_collection()
    return _store


__all__ = ["MemoryStore", "get_memory_store", "VECTOR_DIMENSION"]
