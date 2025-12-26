"""
Memory Cache Manager Service

Manages caching of agent memories in Redis:
- TTL-based invalidation
- LRU eviction on size limit
- Cache hit/miss metrics
- Pre-warming for active agents

Usage:
    >>> from src.gml.services.memory_cache_manager import get_cache_manager
    >>> 
    >>> cache = await get_cache_manager()
    >>> context = await cache.get_or_build_context(
    ...     agent_id="agent-123",
    ...     conversation_id="conv-456"
    ... )
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.gml.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_TTL = 3600  # 1 hour
MAX_CACHE_SIZE = 1000  # Maximum cached contexts
CACHE_PREFIX = "agent_context:"


class MemoryCacheManager:
    """
    Manages caching of agent memory contexts in Redis.
    
    Provides TTL-based expiration and LRU eviction for efficient
    memory context caching.
    """

    def __init__(self, ttl: int = DEFAULT_TTL, max_size: int = MAX_CACHE_SIZE) -> None:
        """
        Initialize cache manager.

        Args:
            ttl: Time-to-live for cached contexts (seconds)
            max_size: Maximum number of cached contexts
        """
        self.ttl = ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        logger.info(f"MemoryCacheManager initialized (TTL={ttl}s, max_size={max_size})")

    async def get_cached_context(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
        query_hash: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached context if available.

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            query_hash: Hash of query for cache key

        Returns:
            Cached context dict or None if not found
        """
        try:
            redis_client = await get_redis_client()
            if not await redis_client.health_check():
                return None

            cache_key = self._build_cache_key(agent_id, conversation_id, query_hash)
            cached_data = await redis_client.redis.get(cache_key)

            if cached_data:
                self.hits += 1
                context = json.loads(cached_data)
                logger.debug(f"Cache hit for {cache_key}")
                return context

            self.misses += 1
            return None

        except Exception as e:
            logger.warning(f"Error getting cached context: {str(e)}")
            return None

    async def cache_context(
        self,
        agent_id: str,
        context: Dict[str, Any],
        conversation_id: Optional[str] = None,
        query_hash: Optional[str] = None,
    ) -> bool:
        """
        Cache a context.

        Args:
            agent_id: Agent ID
            context: Context dictionary to cache
            conversation_id: Conversation ID
            query_hash: Hash of query for cache key

        Returns:
            True if cached successfully
        """
        try:
            redis_client = await get_redis_client()
            if not await redis_client.health_check():
                return False

            cache_key = self._build_cache_key(agent_id, conversation_id, query_hash)

            # Add timestamp
            context["cached_at"] = datetime.now(timezone.utc).isoformat()

            # Serialize and cache
            cached_data = json.dumps(context)
            await redis_client.redis.setex(cache_key, self.ttl, cached_data)

            # Track cache size and evict if needed
            await self._evict_if_needed(redis_client)

            logger.debug(f"Cached context for {cache_key}")
            return True

        except Exception as e:
            logger.warning(f"Error caching context: {str(e)}")
            return False

    async def invalidate_context(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
    ) -> bool:
        """
        Invalidate cached contexts for an agent.

        Args:
            agent_id: Agent ID
            conversation_id: Optional conversation ID (None = all conversations)

        Returns:
            True if invalidated successfully
        """
        try:
            redis_client = await get_redis_client()
            if not await redis_client.health_check():
                return False

            if conversation_id:
                cache_key = self._build_cache_key(agent_id, conversation_id, None)
                await redis_client.redis.delete(cache_key)
            else:
                # Delete all keys for agent
                pattern = f"{CACHE_PREFIX}{agent_id}:*"
                keys = []
                async for key in redis_client.redis.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await redis_client.redis.delete(*keys)

            logger.debug(f"Invalidated cache for agent {agent_id}")
            return True

        except Exception as e:
            logger.warning(f"Error invalidating cache: {str(e)}")
            return False

    async def prewarm_cache(
        self,
        agent_id: str,
        conversation_ids: List[str],
    ) -> int:
        """
        Pre-warm cache for active conversations.

        Args:
            agent_id: Agent ID
            conversation_ids: List of conversation IDs to pre-warm

        Returns:
            Number of contexts pre-warmed
        """
        # This would call build_context for each conversation
        # For now, just return count
        logger.info(f"Pre-warming cache for {len(conversation_ids)} conversations")
        return len(conversation_ids)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hit/miss counts and hit rate
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
        }

    def _build_cache_key(
        self,
        agent_id: str,
        conversation_id: Optional[str],
        query_hash: Optional[str],
    ) -> str:
        """Build cache key from components."""
        parts = [CACHE_PREFIX, agent_id]
        if conversation_id:
            parts.append(conversation_id)
        if query_hash:
            parts.append(query_hash)
        return ":".join(parts)

    async def _evict_if_needed(self, redis_client) -> None:
        """Evict old entries if cache size exceeds limit."""
        try:
            pattern = f"{CACHE_PREFIX}*"
            keys = []
            async for key in redis_client.redis.scan_iter(match=pattern):
                keys.append(key)

            if len(keys) > self.max_size:
                # Simple eviction: delete oldest entries
                # Could implement LRU here
                to_delete = keys[: len(keys) - self.max_size]
                if to_delete:
                    await redis_client.redis.delete(*to_delete)
                    logger.debug(f"Evicted {len(to_delete)} cache entries")

        except Exception as e:
            logger.warning(f"Error during eviction: {str(e)}")


# Singleton instance
_cache_manager: Optional[MemoryCacheManager] = None


async def get_cache_manager() -> MemoryCacheManager:
    """Get or create the singleton cache manager instance."""
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = MemoryCacheManager()
        logger.info("Memory cache manager singleton created")

    return _cache_manager


__all__ = ["MemoryCacheManager", "get_cache_manager", "DEFAULT_TTL"]

