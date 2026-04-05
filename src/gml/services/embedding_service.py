"""
Embedding Service for GML Infrastructure

Provides text embedding generation using OpenAI's embedding API or Ollama with:
- Single and batch embedding generation
- Text chunking for optimal vector sizes
- Caching to avoid re-embedding same text
- Error handling and retry logic
- Production-ready configuration
- Support for both OpenAI and Ollama embeddings

Usage:
    >>> from src.gml.services.embedding_service import get_embedding_service
    >>> 
    >>> service = await get_embedding_service()
    >>> 
    >>> # Generate single embedding
    >>> embedding = await service.generate_embedding("Hello, world!")
    >>> print(f"Embedding dimension: {len(embedding)}")
    >>> 
    >>> # Generate batch embeddings
    >>> texts = ["Text 1", "Text 2", "Text 3"]
    >>> embeddings = await service.embed_batch(texts)
    >>> print(f"Generated {len(embeddings)} embeddings")
    >>> 
    >>> # Chunk text for optimal embedding
    >>> chunks = service.chunk_text("Long text here...", chunk_size=512)
"""

import hashlib
import json
import logging
import re
from typing import List, Optional

import httpx
import numpy as np
from openai import AsyncOpenAI, OpenAIError
from openai.types import CreateEmbeddingResponse

from src.gml.cache.redis_client import get_redis_client
from src.gml.core.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

settings = get_settings()

# OpenAI Embedding Model Configuration
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSION = 1536

# Cache configuration
CACHE_TTL = 86400  # 24 hours in seconds
CACHE_PREFIX = "embedding:"

# API Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0  # seconds
DEFAULT_BATCH_SIZE = 100  # OpenAI's recommended batch size


# ============================================================================
# EMBEDDING SERVICE CLASS
# ============================================================================


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI API.

    Features:
        - Single and batch embedding generation
        - Redis-based caching to avoid re-embedding
        - Automatic retry on API failures
        - Efficient batch processing
        - Error handling and logging

    Attributes:
        client: OpenAI async client instance
        model: Embedding model name
        dimension: Embedding dimension
        cache_enabled: Whether caching is enabled
        max_retries: Maximum retry attempts
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_EMBEDDING_MODEL,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        cache_enabled: bool = True,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: Embedding model name
            dimension: Embedding dimension (1536 for text-embedding-3-small)
            cache_enabled: Enable caching of embeddings
            max_retries: Maximum retry attempts for API calls
            timeout: Request timeout in seconds
            batch_size: Maximum batch size for batch operations
        """
        # Get API key from settings if not provided
        api_key = api_key or settings.OPENAI_API_KEY
        self.has_openai_key = bool(api_key and api_key != "dummy-key" and api_key.startswith("sk-"))
        
        if not self.has_openai_key:
            logger.info(
                "OpenAI API key not found. Will use Ollama for embeddings or zero vectors as fallback. "
                "Set OPENAI_API_KEY in environment for OpenAI embeddings."
            )
            # Don't create OpenAI client if no key
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)
        # Use model from settings if not provided
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        self.timeout = timeout
        self.batch_size = batch_size

        logger.info(
            f"Embedding service initialized: model={model}, dimension={dimension}, "
            f"cache_enabled={cache_enabled}"
        )

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for a text.

        Args:
            text: Input text

        Returns:
            Cache key string
        """
        # Create hash of text for cache key
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{CACHE_PREFIX}{text_hash}"

    async def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding for text.

        Args:
            text: Input text

        Returns:
            Cached embedding vector or None if not found
        """
        if not self.cache_enabled:
            return None

        try:
            redis_client = await get_redis_client()

            # Check if Redis is available (returns None if not configured)
            if redis_client is None or not await redis_client.health_check():
                logger.debug("Redis not available, skipping cache")
                return None

            cache_key = self._get_cache_key(text)
            cached_data = await redis_client.redis.get(cache_key)
            if cached_data:
                embedding = json.loads(cached_data)
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return embedding
        except Exception as e:
            logger.warning(f"Error retrieving cached embedding: {str(e)}")
            # Continue without cache on error

        return None

    async def _cache_embedding(self, text: str, embedding: List[float]) -> None:
        """
        Cache embedding for text.

        Args:
            text: Input text
            embedding: Embedding vector to cache
        """
        if not self.cache_enabled:
            return

        try:
            redis_client = await get_redis_client()

            # Check if Redis is available (returns None if not configured)
            if redis_client is None or not await redis_client.health_check():
                logger.debug("Redis not available, skipping cache")
                return

            cache_key = self._get_cache_key(text)
            # Store embedding as JSON with TTL
            embedding_json = json.dumps(embedding)
            await redis_client.redis.setex(cache_key, CACHE_TTL, embedding_json)
            logger.debug(f"Cached embedding for text: {text[:50]}...")
        except Exception as e:
            logger.warning(f"Error caching embedding: {str(e)}")
            # Continue without caching on error

    async def generate_embedding(
        self,
        text: str,
        use_cache: bool = True,
        _use_ollama_fallback: bool = True,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed
            use_cache: Whether to use cache (default: True)
            _use_ollama_fallback: Internal flag to prevent recursion (default: True)

        Returns:
            1536-dimensional embedding vector

        Raises:
            ValueError: If text is empty
            OpenAIError: If API call fails after retries
            httpx.HTTPError: If network error occurs

        Example:
            >>> embedding = await service.generate_embedding("Hello, world!")
            >>> print(f"Dimension: {len(embedding)}")  # 1536
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()

        # Check cache first
        if use_cache and self.cache_enabled:
            cached_embedding = await self._get_cached_embedding(text)
            if cached_embedding is not None:
                return cached_embedding

        # Generate embedding via API
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")

            # Check if we have OpenAI client
            if not self.has_openai_key or not self.client:
                # Fallback to Ollama if allowed
                if _use_ollama_fallback:
                    logger.debug("OpenAI not available, trying Ollama")
                    return await self.generate_embedding_ollama(text, use_cache=use_cache)
                else:
                    # Return zero vector as last resort
                    logger.warning("No embedding service available, returning zero vector")
                    zero_vector = [0.0] * self.dimension
                    if use_cache:
                        await self._cache_embedding(text, zero_vector)
                    return zero_vector

            response: CreateEmbeddingResponse = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimension,
            )

            # Extract embedding vector
            embedding = response.data[0].embedding

            # Validate dimension
            if len(embedding) != self.dimension:
                logger.warning(
                    f"Unexpected embedding dimension: {len(embedding)} "
                    f"(expected {self.dimension})"
                )

            # Cache the embedding
            if use_cache:
                await self._cache_embedding(text, embedding)

            logger.debug(f"Generated embedding (dimension: {len(embedding)})")
            return embedding

        except (OpenAIError, httpx.HTTPError) as e:
            logger.warning(f"OpenAI API error: {str(e)}")
            # Fallback to Ollama only if flag is True and we haven't already tried
            if _use_ollama_fallback:
                try:
                    return await self.generate_embedding_ollama(text, use_cache=False)
                except Exception:
                    # Return zero vector if both fail
                    logger.warning("Both OpenAI and Ollama failed, returning zero vector")
                    return [0.0] * self.dimension
            else:
                # Return zero vector instead of raising
                logger.warning("OpenAI failed and fallback disabled, returning zero vector")
                return [0.0] * self.dimension
        except Exception as e:
            logger.warning(f"Unexpected error during OpenAI embedding: {str(e)}")
            # Last resort: try Ollama only if flag is True
            if _use_ollama_fallback:
                try:
                    return await self.generate_embedding_ollama(text, use_cache=False)
                except Exception:
                    logger.warning("All embedding methods failed, returning zero vector")
                    return [0.0] * self.dimension
            else:
                logger.warning("Embedding failed, returning zero vector")
                return [0.0] * self.dimension

    async def embed_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Handles caching, batching, and error recovery automatically.
        Texts are processed in batches to respect API limits.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache (default: True)
            batch_size: Batch size for API calls (defaults to self.batch_size)

        Returns:
            List of embedding vectors (same order as input texts)

        Raises:
            ValueError: If texts list is empty
            OpenAIError: If API call fails after retries

        Example:
            >>> texts = ["Text 1", "Text 2", "Text 3"]
            >>> embeddings = await service.embed_batch(texts)
            >>> print(f"Generated {len(embeddings)} embeddings")
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        batch_size = batch_size or self.batch_size
        all_embeddings: List[List[float]] = []

        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = await self._embed_batch_internal(
                batch_texts, use_cache=use_cache
            )
            all_embeddings.extend(batch_embeddings)

        logger.info(f"Generated {len(all_embeddings)} embeddings for {len(texts)} texts")
        return all_embeddings

    async def _embed_batch_internal(
        self,
        texts: List[str],
        use_cache: bool = True,
    ) -> List[List[float]]:
        """
        Internal method to embed a batch of texts.

        Handles caching lookup and API calls for a single batch.

        Args:
            texts: List of texts to embed (should be <= batch_size)
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        # Clean and validate texts
        cleaned_texts = [text.strip() if text else "" for text in texts]
        if any(not text for text in cleaned_texts):
            raise ValueError("All texts must be non-empty")

        # Check cache for all texts
        cached_embeddings: List[Optional[List[float]]] = []
        texts_to_embed: List[str] = []
        text_indices: List[int] = []  # Track original indices

        if use_cache and self.cache_enabled:
            for idx, text in enumerate(cleaned_texts):
                cached = await self._get_cached_embedding(text)
                cached_embeddings.append(cached)
                if cached is None:
                    texts_to_embed.append(text)
                    text_indices.append(idx)
        else:
            texts_to_embed = cleaned_texts
            text_indices = list(range(len(cleaned_texts)))
            cached_embeddings = [None] * len(cleaned_texts)

        # Generate embeddings for uncached texts
        if texts_to_embed:
            try:
                logger.debug(f"Generating embeddings for {len(texts_to_embed)} texts via API")

                response: CreateEmbeddingResponse = await self.client.embeddings.create(
                    model=self.model,
                    input=texts_to_embed,
                    dimensions=self.dimension,
                )

                # Extract embeddings (order matches input)
                new_embeddings = [item.embedding for item in response.data]

                # Validate dimensions
                for embedding in new_embeddings:
                    if len(embedding) != self.dimension:
                        logger.warning(
                            f"Unexpected embedding dimension: {len(embedding)} "
                            f"(expected {self.dimension})"
                        )

                # Cache new embeddings
                if use_cache:
                    for text, embedding in zip(texts_to_embed, new_embeddings):
                        await self._cache_embedding(text, embedding)

                # Merge cached and new embeddings
                embedding_idx = 0
                for idx in range(len(cleaned_texts)):
                    if cached_embeddings[idx] is not None:
                        continue
                    cached_embeddings[idx] = new_embeddings[embedding_idx]
                    embedding_idx += 1

            except OpenAIError as e:
                logger.error(f"OpenAI API error during batch embedding: {str(e)}")
                raise
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during batch embedding: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during batch embedding: {str(e)}")
                raise

        # Return embeddings in original order
        return [emb for emb in cached_embeddings if emb is not None]

    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings generated by this service.

        Returns:
            Embedding dimension (1536 for text-embedding-3-small)
        """
        return self.dimension

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separator: str = "\n\n",
    ) -> List[str]:
        """
        Chunk text into optimal sized pieces for embedding.

        Splits text into chunks with overlap to preserve context.
        Tries to split on separators (paragraphs, sentences) first.

        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk (default: 512)
            chunk_overlap: Characters to overlap between chunks (default: 50)
            separator: Separator to split on (default: "\n\n" for paragraphs)

        Returns:
            List of text chunks

        Example:
            >>> service = EmbeddingService()
            >>> chunks = service.chunk_text("Long text...", chunk_size=512)
            >>> print(f"Split into {len(chunks)} chunks")
        """
        if not text or len(text) <= chunk_size:
            return [text]

        chunks: List[str] = []
        current_pos = 0

        while current_pos < len(text):
            # Calculate end position
            end_pos = min(current_pos + chunk_size, len(text))

            # Try to find a good break point near the end
            chunk = text[current_pos:end_pos]

            if end_pos < len(text):
                # Look for separator in the last 20% of chunk
                search_start = max(0, len(chunk) - chunk_size // 5)
                last_separator = chunk.rfind(separator, search_start)

                if last_separator > search_start:
                    # Found a good break point
                    chunk = chunk[: last_separator + len(separator)].strip()
                    end_pos = current_pos + last_separator + len(separator)

            chunks.append(chunk.strip())

            # Move position with overlap
            if end_pos >= len(text):
                break
            current_pos = end_pos - chunk_overlap

        return chunks

    def extract_text_from_content(self, content: dict) -> str:
        """
        Extract text from memory content dictionary for embedding.

        Handles various content formats and extracts meaningful text.

        Args:
            content: Memory content dictionary

        Returns:
            Extracted text string

        Example:
            >>> content = {"text": "Hello", "metadata": {"type": "note"}}
            >>> text = service.extract_text_from_content(content)
            >>> print(text)  # "Hello"
        """
        if not content:
            return ""

        # Try common text fields
        text_fields = ["text", "content", "message", "description", "summary"]
        for field in text_fields:
            if field in content and isinstance(content[field], str):
                return content[field]

        # If no text field found, stringify the entire content
        # Filter out non-textual fields
        text_parts = []
        for key, value in content.items():
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (int, float, bool)):
                text_parts.append(f"{key}: {value}")

        return " ".join(text_parts) if text_parts else str(content)

    async def generate_embedding_ollama(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[float]:
        """
        Generate embedding using Ollama (local model).

        Uses Ollama's embedding API for local embedding generation.
        Falls back to OpenAI if Ollama is unavailable.

        Args:
            text: Input text to embed
            model: Ollama model name (defaults to nomic-embed-text)
            use_cache: Whether to use cache

        Returns:
            Embedding vector (1536 dimensions, normalized to match OpenAI)

        Raises:
            ValueError: If text is empty
            httpx.HTTPError: If Ollama API call fails

        Example:
            >>> embedding = await service.generate_embedding_ollama("Hello, world!")
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()
        model = model or "nomic-embed-text"  # Ollama embedding model

        # Check cache first
        if use_cache and self.cache_enabled:
            cached_embedding = await self._get_cached_embedding(text)
            if cached_embedding is not None:
                return cached_embedding

        try:
            logger.debug(f"Generating embedding via Ollama for: {text[:100]}...")

            # Ollama embedding endpoint
            ollama_url = settings.OLLAMA_BASE_URL.replace("/v1", "") if settings.OLLAMA_BASE_URL else "http://localhost:11434"
            embedding_url = f"{ollama_url}/api/embeddings"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    embedding_url,
                    json={"model": model, "prompt": text},
                )
                response.raise_for_status()
                data = response.json()

                embedding = data.get("embedding", [])

                if not embedding:
                    raise ValueError("Ollama returned empty embedding")

                # Normalize to target dimension if needed
                if len(embedding) != self.dimension:
                    logger.warning(
                        f"Ollama embedding dimension {len(embedding)} != {self.dimension}, "
                        "normalizing..."
                    )
                    # Pad or truncate to match expected dimension
                    if len(embedding) > self.dimension:
                        embedding = embedding[:self.dimension]
                    else:
                        embedding = embedding + [0.0] * (self.dimension - len(embedding))

                # Cache the embedding
                if use_cache:
                    await self._cache_embedding(text, embedding)

                logger.debug(f"Generated Ollama embedding (dimension: {len(embedding)})")
                return embedding

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            # Don't fallback to OpenAI to prevent recursion
            # If Ollama fails and we don't have OpenAI key, create a zero vector as last resort
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "dummy-key":
                logger.warning("Ollama failed and no OpenAI key, returning zero vector")
                zero_vector = [0.0] * self.dimension
                if use_cache:
                    await self._cache_embedding(text, zero_vector)
                return zero_vector
            # Only try OpenAI if we have a key
            logger.info("Falling back to OpenAI embeddings...")
            return await self.generate_embedding(text, use_cache=use_cache, _use_ollama_fallback=False)
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {str(e)}")
            # Don't fallback to OpenAI to prevent recursion
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "dummy-key":
                logger.warning("Ollama connection failed and no OpenAI key, returning zero vector")
                zero_vector = [0.0] * self.dimension
                if use_cache:
                    await self._cache_embedding(text, zero_vector)
                return zero_vector
            logger.info("Falling back to OpenAI embeddings...")
            return await self.generate_embedding(text, use_cache=use_cache, _use_ollama_fallback=False)
        except Exception as e:
            logger.error(f"Unexpected error with Ollama embeddings: {str(e)}")
            # Don't recursively call - just raise or return zero vector
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "dummy-key":
                logger.warning("Ollama error and no OpenAI key, returning zero vector")
                return [0.0] * self.dimension
            raise

    async def clear_cache(self, text: Optional[str] = None) -> int:
        """
        Clear embedding cache.

        Args:
            text: Specific text to clear from cache (None = clear all)

        Returns:
            Number of cache entries cleared
        """
        try:
            redis_client = await get_redis_client()

            # Check if Redis is available (returns None if not configured)
            if redis_client is None or not await redis_client.health_check():
                logger.warning("Redis not available, cannot clear cache")
                return 0

            if text:
                # Clear specific text
                cache_key = self._get_cache_key(text)
                result = await redis_client.redis.delete(cache_key)
                logger.info(f"Cleared cache for text: {text[:50]}...")
                return 1 if result else 0
            else:
                # Clear all embedding cache entries
                pattern = f"{CACHE_PREFIX}*"
                keys = await redis_client.redis.keys(pattern)
                if keys:
                    count = await redis_client.redis.delete(*keys)
                    logger.info(f"Cleared {count} cache entries")
                    return count
                return 0

        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_embedding_service: Optional[EmbeddingService] = None


async def get_embedding_service() -> EmbeddingService:
    """
    Get or create the singleton embedding service instance.

    Returns:
        EmbeddingService instance

    Example:
        >>> service = await get_embedding_service()
        >>> embedding = await service.generate_embedding("Hello!")
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        logger.info("Embedding service singleton created")

    return _embedding_service


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_EMBEDDING_DIMENSION",
    "DEFAULT_BATCH_SIZE",
]

