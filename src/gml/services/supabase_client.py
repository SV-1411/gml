"""
Supabase Client for GML Infrastructure

Provides Supabase database operations with async support for:
- CRUD operations on all tables
- Authentication and authorization
- Real-time subscriptions (future)
- File storage (future)

Usage:
    >>> from src.gml.services.supabase_client import get_supabase_client
    >>> 
    >>> client = await get_supabase_client()
    >>> 
    >>> # Query memories
    >>> memories = await client.from_("memories").select("*").eq("agent_id", "agent-123").execute()
    >>> 
    >>> # Insert memory
    >>> result = await client.from_("memories").insert({
    >>>     "agent_id": "agent-123",
    >>>     "content": "Hello world",
    >>>     "memory_type": "semantic"
    >>> }).execute()
"""

import logging
from typing import Any, Dict, List, Optional, Union

from supabase import AsyncClient, create_async_client
from supabase.lib.client_options import ClientOptions

from src.gml.core.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_supabase_client: Optional[AsyncClient] = None


async def get_supabase_client() -> AsyncClient:
    """
    Get or create the singleton Supabase client instance.

    Returns:
        AsyncClient instance

    Raises:
        ValueError: If Supabase URL or service key is not configured
    """
    global _supabase_client

    if _supabase_client is None:
        settings = get_settings()

        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError(
                "Supabase URL and service key must be configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY in environment."
            )

        # Create async Supabase client
        _supabase_client = await create_async_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY,
            options=ClientOptions(
                postgrest_client_timeout=30,
                storage_client_timeout=30,
                schema="public",
            ),
        )

        logger.info(f"✓ Supabase client initialized for: {settings.SUPABASE_URL}")

    return _supabase_client


async def close_supabase_client() -> None:
    """
    Close the Supabase client connection.

    Should be called on application shutdown.
    """
    global _supabase_client

    if _supabase_client is not None:
        # Note: Supabase async client doesn't have explicit close method
        # Just clear the reference
        _supabase_client = None
        logger.info("✓ Supabase client connection closed")


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

class SupabaseDB:
    """
    Database operations wrapper for Supabase.

    Provides a SQLAlchemy-like interface for compatibility with existing code.
    """

    def __init__(self, client: AsyncClient):
        self.client = client

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Select records from a table.

        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dict of column: value filters
            order: Order by clause (e.g., "created_at desc")
            limit: Maximum number of records

        Returns:
            List of records
        """
        query = self.client.from_(table).select(columns)

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        if order:
            query = query.order(order)

        if limit:
            query = query.limit(limit)

        result = await query.execute()
        return result.data or []

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        returning: str = "*",
    ) -> List[Dict[str, Any]]:
        """
        Insert records into a table.

        Args:
            table: Table name
            data: Single record or list of records
            returning: Columns to return (default: "*")

        Returns:
            List of inserted records
        """
        result = await self.client.from_(table).insert(data, returning=returning).execute()
        return result.data or []

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        returning: str = "*",
    ) -> List[Dict[str, Any]]:
        """
        Update records in a table.

        Args:
            table: Table name
            data: Update data
            filters: Dict of column: value filters (WHERE clause)
            returning: Columns to return (default: "*")

        Returns:
            List of updated records
        """
        query = self.client.from_(table).update(data, returning=returning)

        for key, value in filters.items():
            query = query.eq(key, value)

        result = await query.execute()
        return result.data or []

    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        returning: str = "*",
    ) -> List[Dict[str, Any]]:
        """
        Delete records from a table.

        Args:
            table: Table name
            filters: Dict of column: value filters (WHERE clause)
            returning: Columns to return (default: "*")

        Returns:
            List of deleted records
        """
        query = self.client.from_(table).delete(returning=returning)

        for key, value in filters.items():
            query = query.eq(key, value)

        result = await query.execute()
        return result.data or []

    async def get_by_id(
        self,
        table: str,
        record_id: Union[int, str],
        id_column: str = "id",
        columns: str = "*",
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single record by ID.

        Args:
            table: Table name
            record_id: Record ID
            id_column: ID column name (default: "id")
            columns: Columns to select (default: "*")

        Returns:
            Record or None if not found
        """
        records = await self.select(table, columns, {id_column: record_id}, limit=1)
        return records[0] if records else None

    async def count(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count records in a table.

        Args:
            table: Table name
            filters: Optional filters

        Returns:
            Record count
        """
        query = self.client.from_(table).select("count", count="exact")

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = await query.execute()
        return result.count or 0


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "get_supabase_client",
    "close_supabase_client",
    "SupabaseDB",
]
