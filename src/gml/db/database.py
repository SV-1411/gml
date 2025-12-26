"""
Database Module for GML Infrastructure

Provides async SQLAlchemy database connectivity with PostgreSQL using asyncpg driver.

Features:
    - Async engine with connection pooling
    - Async session management for FastAPI
    - Declarative base for ORM models
    - Database health checks
    - Automatic table creation
    - Proper connection cleanup
    - Debug logging support

Usage:
    >>> from src.gml.db.database import get_db, init_db
    >>>
    >>> # Initialize database tables
    >>> await init_db()
    >>>
    >>> # Use in FastAPI endpoints
    >>> @app.get("/items")
    >>> async def get_items(db: AsyncSession = Depends(get_db)):
    >>>     result = await db.execute(select(Item))
    >>>     return result.scalars().all()
"""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from src.gml.core.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

settings = get_settings()

# ============================================================================
# DATABASE ENGINE
# ============================================================================

# Create async engine with connection pooling
# Lazy initialization - engine created on first access to avoid import-time connection
_engine: Optional[AsyncEngine] = None


def _get_database_url() -> str:
    """
    Get database URL with asyncpg driver.
    
    Returns:
        Database URL with asyncpg driver
    """
    db_url = settings.DATABASE_URL
    # Ensure URL uses asyncpg driver
    if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not db_url.startswith("postgresql"):
        # If it's a test URL (sqlite), use as-is
        pass
    return db_url


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.
    
    Returns:
        AsyncEngine instance
    """
    global _engine
    if _engine is None:
        db_url = _get_database_url()
        
        # For SQLite (testing), use different connect_args
        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}
        else:
            # PostgreSQL connect args
            connect_args = {
                "server_settings": {
                    "application_name": settings.APP_NAME,
                },
                "timeout": 10,  # Connection timeout in seconds
                "command_timeout": 60,  # Query timeout in seconds
            }
        
        _engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,  # Enable SQL query logging in debug mode
            pool_size=settings.database_pool_size,  # 5 for dev, 20 for prod
            max_overflow=10,  # Additional connections beyond pool_size
            pool_timeout=30,  # Timeout for getting connection from pool
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connection health before using
            connect_args=connect_args,
        )
    return _engine


# For backward compatibility - create engine on first access
@property
def engine() -> AsyncEngine:
    """Get the database engine (lazy initialization)."""
    return get_engine()

# ============================================================================
# SESSION FACTORY
# ============================================================================

# Create async session factory (lazy initialization)
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def get_session_factory() -> async_sessionmaker:
    """
    Get or create the async session factory.
    
    Returns:
        async_sessionmaker instance
    """
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,  # Manual commit required
            autoflush=False,  # Manual flush required
        )
    return _AsyncSessionLocal


# For backward compatibility - use function call
def AsyncSessionLocal():
    """Get async session factory (backward compatibility)."""
    return get_session_factory()

# ============================================================================
# DECLARATIVE BASE
# ============================================================================

# Base class for all ORM models
Base = declarative_base()

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session management.

    Provides an async database session that automatically handles:
    - Session creation
    - Transaction management
    - Session cleanup
    - Error handling

    Yields:
        AsyncSession: Database session for the request

    Raises:
        SQLAlchemyError: If database operation fails

    Example:
        >>> from fastapi import Depends
        >>> from src.gml.db.database import get_db
        >>>
        >>> @app.get("/users/{user_id}")
        >>> async def get_user(
        >>>     user_id: str,
        >>>     db: AsyncSession = Depends(get_db)
        >>> ):
        >>>     result = await db.execute(
        >>>         select(User).where(User.id == user_id)
        >>>     )
        >>>     return result.scalar_one_or_none()
    """
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    Creates all tables defined by models inheriting from Base.
    Safe to call multiple times - won't recreate existing tables.

    Raises:
        SQLAlchemyError: If table creation fails

    Example:
        >>> import asyncio
        >>> from src.gml.db.database import init_db
        >>>
        >>> asyncio.run(init_db())
    """
    try:
        logger.info("Initializing database tables...")

        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✓ Database tables initialized successfully")

    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise


# ============================================================================
# DATABASE CLEANUP
# ============================================================================


async def close_db() -> None:
    """
    Close database connections and cleanup resources.

    Should be called on application shutdown to properly close
    all database connections in the pool.

    Example:
        >>> from fastapi import FastAPI
        >>> from src.gml.db.database import close_db
        >>>
        >>> app = FastAPI()
        >>>
        >>> @app.on_event("shutdown")
        >>> async def shutdown_event():
        >>>     await close_db()
    """
    try:
        logger.info("Closing database connections...")
        if _engine is not None:
            await _engine.dispose()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}", exc_info=True)
        raise


# ============================================================================
# HEALTH CHECK
# ============================================================================


async def health_check() -> bool:
    """
    Verify database connectivity and health.

    Performs a simple query to check if the database is accessible
    and responding correctly.

    Returns:
        bool: True if database is healthy, False otherwise

    Example:
        >>> from src.gml.db.database import health_check
        >>>
        >>> @app.get("/health/db")
        >>> async def check_db_health():
        >>>     healthy = await health_check()
        >>>     if healthy:
        >>>         return {"status": "healthy"}
        >>>     raise HTTPException(status_code=503, detail="Database unhealthy")
    """
    try:
        async with get_session_factory()() as session:
            # Execute simple query to verify connectivity
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()

            if value == 1:
                logger.debug("Database health check: OK")
                return True
            else:
                logger.warning("Database health check: Unexpected result")
                return False

    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}", exc_info=True)
        return False


# ============================================================================
# CONTEXT MANAGER
# ============================================================================


class DatabaseSession:
    """
    Context manager for database sessions (non-FastAPI usage).

    Use this when you need a database session outside of FastAPI
    request handlers (e.g., background tasks, scripts, tests).

    Example:
        >>> from src.gml.db.database import DatabaseSession
        >>>
        >>> async def background_task():
        >>>     async with DatabaseSession() as db:
        >>>         result = await db.execute(select(User))
        >>>         users = result.scalars().all()
        >>>         # Session automatically committed and closed
    """

    def __init__(self) -> None:
        """Initialize the session context manager."""
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        """Enter the context and create a new session."""
        self.session = get_session_factory()()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context and cleanup session."""
        if self.session is not None:
            try:
                if exc_type is not None:
                    # Exception occurred, rollback
                    await self.session.rollback()
                else:
                    # No exception, commit
                    await self.session.commit()
            except SQLAlchemyError as e:
                logger.error(f"Error during session cleanup: {str(e)}", exc_info=True)
                await self.session.rollback()
            finally:
                await self.session.close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


async def execute_raw_query(query: str) -> list:
    """
    Execute a raw SQL query and return results.

    Use sparingly - prefer ORM queries when possible.

    Args:
        query: Raw SQL query string

    Returns:
        List of result rows

    Raises:
        SQLAlchemyError: If query execution fails

    Example:
        >>> results = await execute_raw_query("SELECT * FROM users LIMIT 10")
    """
    try:
        async with get_session_factory()() as session:
            result = await session.execute(text(query))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Raw query failed: {str(e)}", exc_info=True)
        raise


async def get_database_info() -> dict:
    """
    Get database connection and configuration information.

    Returns:
        Dictionary with database metadata

    Example:
        >>> info = await get_database_info()
        >>> print(f"Database: {info['database']}")
    """
    try:
        async with get_session_factory()() as session:
            # Get PostgreSQL version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()

            # Get current database name
            result = await session.execute(text("SELECT current_database()"))
            database = result.scalar()

            # Get current user
            result = await session.execute(text("SELECT current_user"))
            user = result.scalar()

            return {
                "database": database,
                "user": user,
                "version": version,
                "pool_size": settings.database_pool_size,
                "echo": settings.DEBUG,
            }

    except SQLAlchemyError as e:
        logger.error(f"Failed to get database info: {str(e)}", exc_info=True)
        return {}


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if settings.is_development:
    logger.info(f"Database engine initialized: {settings.DATABASE_URL.split('@')[-1]}")
    logger.info(f"Pool size: {settings.database_pool_size}, Echo: {settings.DEBUG}")


# ============================================================================
# MAIN - FOR TESTING
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_database():
        """Test database connectivity and operations."""
        print("=" * 60)
        print("DATABASE MODULE - TEST")
        print("=" * 60)

        # Health check
        print("\n1. Health Check:")
        is_healthy = await health_check()
        print(f"   Database Healthy: {is_healthy}")

        # Database info
        print("\n2. Database Information:")
        info = await get_database_info()
        for key, value in info.items():
            if key == "version":
                print(f"   {key}: {value[:50]}...")
            else:
                print(f"   {key}: {value}")

        # Test session
        print("\n3. Session Test:")
        async with DatabaseSession() as db:
            result = await db.execute(text("SELECT 1 as test_value"))
            test_value = result.scalar()
            print(f"   Query Result: {test_value}")

        # Raw query test
        print("\n4. Raw Query Test:")
        results = await execute_raw_query("SELECT 1 as num UNION SELECT 2 UNION SELECT 3")
        print(f"   Results: {results}")

        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)

    try:
        asyncio.run(test_database())
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
