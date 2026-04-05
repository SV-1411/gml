"""
Redis Client for GML Infrastructure

Provides async Redis connection management, Pub/Sub messaging, and message queue
operations with production-ready features including:
- Connection pooling
- Automatic reconnection
- Retry logic with exponential backoff
- Error handling and logging
- Health checks

Usage:
    >>> from src.gml.cache.redis_client import get_redis_client
    >>> 
    >>> # Get Redis client instance
    >>> redis_client = await get_redis_client()
    >>> 
    >>> # Publish a message
    >>> await redis_client.publish("agent:agent-123", {"action": "ping"})
    >>> 
    >>> # Subscribe to a channel
    >>> async for message in redis_client.subscribe("agent:agent-123"):
    >>>     print(f"Received: {message}")
    >>> 
    >>> # Get pending messages for an agent
    >>> messages = await redis_client.get_pending_messages("agent-123")
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import PubSub
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
    RedisError,
)

from src.gml.core.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

settings = get_settings()

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0

# Connection pool configuration
DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_CONNECTIONS = 50
DEFAULT_SOCKET_TIMEOUT = 5.0
DEFAULT_SOCKET_CONNECT_TIMEOUT = 5.0


# ============================================================================
# REDIS CLIENT CLASS
# ============================================================================


class RedisClient:
    """
    Production-ready async Redis client with Pub/Sub and queue management.

    Features:
        - Connection pooling for efficient resource usage
        - Automatic reconnection on connection failures
        - Retry logic with exponential backoff
        - Pub/Sub messaging support
        - Message queue operations
        - Health checks and monitoring
        - Graceful error handling

    Attributes:
        redis: Redis async client instance
        pool: Connection pool instance
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (seconds)
        backoff_multiplier: Multiplier for exponential backoff
    """

    def __init__(
        self,
        url: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
        pool_size: int = DEFAULT_POOL_SIZE,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        socket_timeout: float = DEFAULT_SOCKET_TIMEOUT,
        socket_connect_timeout: float = DEFAULT_SOCKET_CONNECT_TIMEOUT,
    ) -> None:
        """
        Initialize Redis client with connection pooling.

        Args:
            url: Redis connection URL (defaults to settings.REDIS_URL)
            max_retries: Maximum retry attempts for operations
            retry_delay: Initial delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
            pool_size: Connection pool size
            max_connections: Maximum number of connections
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
        """
        self.url = url or settings.REDIS_URL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier

        # Create connection pool
        self.pool = ConnectionPool.from_url(
            self.url,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=True,  # Automatically decode responses to strings
            health_check_interval=30,  # Health check every 30 seconds
        )

        # Create Redis client from pool
        self.redis: Optional[Redis] = None
        self._is_connected = False

        logger.info(
            f"Redis client initialized: {self.url.split('@')[-1] if '@' in self.url else self.url}"
        )

    async def connect(self) -> None:
        """
        Establish connection to Redis server.

        Raises:
            RedisConnectionError: If connection fails after retries
        """
        if self._is_connected and self.redis is not None:
            try:
                await self.redis.ping()
                return
            except RedisError:
                logger.warning("Redis connection lost, reconnecting...")
                self._is_connected = False

        try:
            self.redis = Redis(connection_pool=self.pool)
            await self.redis.ping()
            self._is_connected = True
            logger.info("✓ Redis connection established")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self._is_connected = False
            raise RedisConnectionError(f"Unable to connect to Redis: {str(e)}") from e

    async def disconnect(self) -> None:
        """
        Close Redis connection and cleanup resources.

        Should be called on application shutdown.
        """
        if self.redis is not None:
            try:
                await self.redis.close()
                logger.info("✓ Redis connection closed")
            except RedisError as e:
                logger.warning(f"Error closing Redis connection: {str(e)}")
            finally:
                self.redis = None
                self._is_connected = False

        if self.pool is not None:
            try:
                await self.pool.aclose()
            except Exception as e:
                logger.warning(f"Error closing connection pool: {str(e)}")

    async def _ensure_connected(self) -> None:
        """
        Ensure Redis connection is active, reconnect if necessary.

        Raises:
            RedisConnectionError: If connection cannot be established
        """
        if not self._is_connected or self.redis is None:
            await self.connect()
        else:
            try:
                await self.redis.ping()
            except RedisError:
                logger.warning("Redis ping failed, reconnecting...")
                await self.connect()

    async def _retry_operation(
        self, operation, *args, **kwargs
    ) -> Any:
        """
        Execute operation with retry logic and exponential backoff.

        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result of the operation

        Raises:
            RedisError: If operation fails after all retries
        """
        delay = self.retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                await self._ensure_connected()
                return await operation(*args, **kwargs)
            except (RedisConnectionError, RedisTimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"Redis operation failed (attempt {attempt + 1}/{self.max_retries + 1}): "
                        f"{str(e)}. Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= self.backoff_multiplier
                    # Reset connection state to force reconnection
                    self._is_connected = False
                else:
                    logger.error(
                        f"Redis operation failed after {self.max_retries + 1} attempts: {str(e)}"
                    )
            except RedisError as e:
                # Non-recoverable errors (e.g., invalid command, type errors)
                logger.error(f"Redis operation error: {str(e)}")
                raise

        if last_exception:
            raise last_exception

    # ========================================================================
    # PUB/SUB OPERATIONS
    # ========================================================================

    async def publish(
        self,
        channel: str,
        message: Union[Dict[str, Any], str, bytes],
        retry: bool = True,
    ) -> int:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name (e.g., "agent:agent-123")
            message: Message to publish (dict will be JSON-encoded)
            retry: Whether to retry on failure

        Returns:
            Number of subscribers that received the message

        Raises:
            RedisError: If publish fails after retries

        Example:
            >>> await redis_client.publish("agent:agent-123", {"action": "ping"})
            >>> await redis_client.publish("notifications", "Hello World")
        """
        # Serialize message if it's a dict
        if isinstance(message, dict):
            message_str = json.dumps(message)
        elif isinstance(message, bytes):
            message_str = message.decode("utf-8")
        else:
            message_str = str(message)

        async def _publish() -> int:
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")
            return await self.redis.publish(channel, message_str)

        if retry:
            result = await self._retry_operation(_publish)
        else:
            await self._ensure_connected()
            result = await _publish()

        logger.debug(f"Published message to channel '{channel}': {message_str[:100]}")
        return result

    async def subscribe(
        self,
        *channels: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to one or more Redis channels and yield messages.

        Args:
            *channels: Channel names to subscribe to
            timeout: Optional timeout in seconds (None = no timeout)

        Yields:
            Dictionary with keys: 'channel', 'data', 'type'

        Raises:
            RedisConnectionError: If subscription fails
            ValueError: If no channels provided

        Example:
            >>> async for message in redis_client.subscribe("agent:agent-123"):
            >>>     print(f"Channel: {message['channel']}, Data: {message['data']}")
        """
        if not channels:
            raise ValueError("At least one channel must be provided")

        pubsub: Optional[PubSub] = None

        try:
            await self._ensure_connected()
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")

            pubsub = self.redis.pubsub()
            await pubsub.subscribe(*channels)

            logger.info(f"Subscribed to channels: {', '.join(channels)}")

            # Listen for messages
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=timeout,
                    )

                    if message is None:
                        # Timeout reached
                        if timeout is not None:
                            break
                        continue

                    # Parse message
                    if message["type"] == "message":
                        try:
                            # Try to parse as JSON
                            data = json.loads(message["data"])
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, return as string
                            data = message["data"]

                        yield {
                            "channel": message["channel"],
                            "data": data,
                            "type": message["type"],
                        }
                    elif message["type"] == "pmessage":
                        # Pattern-matched message
                        try:
                            data = json.loads(message["data"])
                        except (json.JSONDecodeError, TypeError):
                            data = message["data"]

                        yield {
                            "channel": message["channel"],
                            "pattern": message.get("pattern"),
                            "data": data,
                            "type": message["type"],
                        }

                except asyncio.TimeoutError:
                    if timeout is not None:
                        break
                    continue
                except RedisError as e:
                    logger.error(f"Error receiving message: {str(e)}")
                    # Try to reconnect
                    await self._ensure_connected()
                    if pubsub:
                        await pubsub.subscribe(*channels)

        except RedisError as e:
            logger.error(f"Subscription error: {str(e)}")
            raise
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe()
                    await pubsub.close()
                except Exception as e:
                    logger.warning(f"Error closing pubsub: {str(e)}")

    async def psubscribe(
        self,
        *patterns: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to one or more Redis channel patterns.

        Args:
            *patterns: Channel patterns (e.g., "agent:*")
            timeout: Optional timeout in seconds

        Yields:
            Dictionary with keys: 'channel', 'pattern', 'data', 'type'

        Example:
            >>> async for message in redis_client.psubscribe("agent:*"):
            >>>     print(f"Pattern: {message['pattern']}, Channel: {message['channel']}")
        """
        if not patterns:
            raise ValueError("At least one pattern must be provided")

        pubsub: Optional[PubSub] = None

        try:
            await self._ensure_connected()
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")

            pubsub = self.redis.pubsub()
            await pubsub.psubscribe(*patterns)

            logger.info(f"Subscribed to patterns: {', '.join(patterns)}")

            # Listen for messages (same logic as subscribe)
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=timeout,
                    )

                    if message is None:
                        if timeout is not None:
                            break
                        continue

                    if message["type"] == "pmessage":
                        try:
                            data = json.loads(message["data"])
                        except (json.JSONDecodeError, TypeError):
                            data = message["data"]

                        yield {
                            "channel": message["channel"],
                            "pattern": message.get("pattern"),
                            "data": data,
                            "type": message["type"],
                        }

                except asyncio.TimeoutError:
                    if timeout is not None:
                        break
                    continue
                except RedisError as e:
                    logger.error(f"Error receiving pattern message: {str(e)}")
                    await self._ensure_connected()
                    if pubsub:
                        await pubsub.psubscribe(*patterns)

        except RedisError as e:
            logger.error(f"Pattern subscription error: {str(e)}")
            raise
        finally:
            if pubsub:
                try:
                    await pubsub.punsubscribe()
                    await pubsub.close()
                except Exception as e:
                    logger.warning(f"Error closing pubsub: {str(e)}")

    # ========================================================================
    # MESSAGE QUEUE OPERATIONS
    # ========================================================================

    async def get_pending_messages(
        self,
        agent_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages from an agent's message queue.

        Uses Redis LIST operations to maintain a FIFO queue for each agent.
        Messages are stored as JSON strings in a list keyed by agent ID.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of messages to retrieve (None = all)

        Returns:
            List of message dictionaries

        Example:
            >>> messages = await redis_client.get_pending_messages("agent-123", limit=10)
            >>> for msg in messages:
            >>>     print(f"Action: {msg['action']}, Payload: {msg['payload']}")
        """
        queue_key = f"agent:queue:{agent_id}"

        async def _get_messages() -> List[Dict[str, Any]]:
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")

            # Get messages from the queue
            if limit is not None:
                # Get limited number of messages (without removing them)
                raw_messages = await self.redis.lrange(queue_key, 0, limit - 1)
            else:
                # Get all messages
                raw_messages = await self.redis.lrange(queue_key, 0, -1)

            # Parse JSON messages
            messages = []
            for raw_msg in raw_messages:
                try:
                    msg = json.loads(raw_msg)
                    messages.append(msg)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse message: {str(e)}")
                    continue

            return messages

        result = await self._retry_operation(_get_messages)
        logger.debug(f"Retrieved {len(result)} pending messages for agent '{agent_id}'")
        return result

    async def add_pending_message(
        self,
        agent_id: str,
        message: Dict[str, Any],
    ) -> int:
        """
        Add a message to an agent's pending message queue.

        Args:
            agent_id: Agent identifier
            message: Message dictionary to add

        Returns:
            New length of the queue after adding the message

        Example:
            >>> await redis_client.add_pending_message(
            ...     "agent-123",
            ...     {"action": "process", "payload": {"data": "test"}}
            ... )
        """
        queue_key = f"agent:queue:{agent_id}"

        async def _add_message() -> int:
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")

            message_str = json.dumps(message)
            return await self.redis.rpush(queue_key, message_str)

        result = await self._retry_operation(_add_message)
        logger.debug(f"Added message to queue for agent '{agent_id}'")
        return result

    async def remove_pending_message(
        self,
        agent_id: str,
        message: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Remove and return a message from an agent's queue (FIFO).

        Args:
            agent_id: Agent identifier
            message: Optional specific message to remove (if None, removes first)

        Returns:
            Removed message dictionary, or None if queue is empty

        Example:
            >>> msg = await redis_client.remove_pending_message("agent-123")
            >>> if msg:
            >>>     print(f"Processing: {msg['action']}")
        """
        queue_key = f"agent:queue:{agent_id}"

        async def _remove_message() -> Optional[str]:
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")

            # Remove from left (FIFO)
            raw_msg = await self.redis.lpop(queue_key)
            return raw_msg

        raw_msg = await self._retry_operation(_remove_message)

        if raw_msg is None:
            return None

        try:
            message = json.loads(raw_msg)
            logger.debug(f"Removed message from queue for agent '{agent_id}'")
            return message
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse removed message: {str(e)}")
            return None

    async def clear_pending_messages(self, agent_id: str) -> int:
        """
        Clear all pending messages for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Number of messages removed

        Example:
            >>> count = await redis_client.clear_pending_messages("agent-123")
            >>> print(f"Cleared {count} messages")
        """
        queue_key = f"agent:queue:{agent_id}"

        async def _clear_messages() -> int:
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")

            # Get count before deletion
            count = await self.redis.llen(queue_key)
            await self.redis.delete(queue_key)
            return count

        result = await self._retry_operation(_clear_messages)
        logger.info(f"Cleared {result} pending messages for agent '{agent_id}'")
        return result

    async def get_queue_length(self, agent_id: str) -> int:
        """
        Get the number of pending messages for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Number of pending messages

        Example:
            >>> count = await redis_client.get_queue_length("agent-123")
            >>> print(f"Queue has {count} messages")
        """
        queue_key = f"agent:queue:{agent_id}"

        async def _get_length() -> int:
            if self.redis is None:
                raise RedisConnectionError("Redis client not initialized")
            return await self.redis.llen(queue_key)

        return await self._retry_operation(_get_length)

    # ========================================================================
    # HEALTH CHECK & UTILITIES
    # ========================================================================

    async def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            await self._ensure_connected()
            if self.redis is None:
                return False
            await self.redis.ping()
            return True
        except RedisError as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            return False

    async def get_info(self) -> Dict[str, Any]:
        """
        Get Redis server information.

        Returns:
            Dictionary with Redis server info
        """
        try:
            await self._ensure_connected()
            if self.redis is None:
                return {}

            info = await self.redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        except RedisError as e:
            logger.error(f"Failed to get Redis info: {str(e)}")
            return {}


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_redis_client: Optional[RedisClient] = None
_redis_available: bool = True  # Track if Redis is available


async def get_redis_client() -> Optional[RedisClient]:
    """
    Get or create the singleton Redis client instance.

    Returns None if Redis is not configured (REDIS_URL empty) or connection fails,
    allowing the application to run in degraded mode without caching.

    Returns:
        RedisClient instance or None if unavailable

    Example:
        >>> redis_client = await get_redis_client()
        >>> if redis_client:
        >>>     await redis_client.publish("channel", {"data": "test"})
    """
    global _redis_client, _redis_available

    # If Redis was previously determined to be unavailable, return None early
    if not _redis_available:
        return None

    # Check if REDIS_URL is configured
    if not settings.REDIS_URL or settings.REDIS_URL.strip() == "":
        logger.info("Redis URL not configured, running without cache (degraded mode)")
        _redis_available = False
        return None

    if _redis_client is None:
        _redis_client = RedisClient()
        try:
            await _redis_client.connect()
        except RedisError as e:
            logger.warning(f"Redis connection failed, running without cache: {str(e)}")
            _redis_client = None
            _redis_available = False
            return None

    return _redis_client


def is_redis_available() -> bool:
    """
    Check if Redis is available for use.

    Returns:
        True if Redis client is connected, False otherwise
    """
    return _redis_available and _redis_client is not None and _redis_client._is_connected


async def close_redis_client() -> None:
    """
    Close the Redis client connection.

    Should be called on application shutdown.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.disconnect()
        _redis_client = None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "RedisClient",
    "get_redis_client",
    "close_redis_client",
    "is_redis_available",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
    "DEFAULT_BACKOFF_MULTIPLIER",
]

