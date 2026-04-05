"""
FastAPI Dependencies

Common dependencies for API routes, including database access.
"""

import logging
from typing import AsyncGenerator, Optional

from src.gml.services.supabase_client import get_supabase_client, SupabaseDB

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[SupabaseDB, None]:
    """
    Get Supabase database dependency for FastAPI routes.
    
    Replaces SQLAlchemy AsyncSession with SupabaseDB wrapper.
    
    Yields:
        SupabaseDB instance for database operations
    """
    try:
        client = await get_supabase_client()
        db = SupabaseDB(client)
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
