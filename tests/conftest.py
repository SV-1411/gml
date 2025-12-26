"""
Pytest Configuration and Fixtures

Centralized test configuration and reusable fixtures for unit and integration tests.

Fixtures provided:
- test_database: SQLite in-memory database setup
- event_loop: Async event loop for async tests
- db: Database session fixture
- client: FastAPI TestClient fixture
- sample_agent_data: Test data for agents
- sample_message_data: Test data for messages

Usage:
    >>> def test_example(db, sample_agent_data):
    ...     # Use db session and sample data
    ...     pass
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from src.gml.api.main import create_app
from src.gml.db.database import Base, get_db
from src.gml.db.models import Agent, Message

# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

# Set test environment variables
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL.replace("+aiosqlite", "")


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.

    This fixture ensures a single event loop is used for all async tests
    in the session, preventing event loop conflicts.

    Yields:
        asyncio.AbstractEventLoop: Event loop for async operations
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_database() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create an in-memory SQLite database for testing.

    Creates all tables, yields the engine, and cleans up after tests.
    Uses SQLite in-memory database for fast test execution.

    Yields:
        AsyncEngine: Database engine for test operations

    Example:
        >>> async def test_something(test_database):
        ...     # Database is ready with all tables
        ...     pass
    """
    # Create async engine with SQLite in-memory database
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Disable SQL logging in tests
        poolclass=StaticPool,  # Required for SQLite in-memory
        connect_args={
            "check_same_thread": False,  # SQLite requirement
        },
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db(test_database: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.

    Provides a fresh database session for each test with automatic
    cleanup to ensure test isolation.

    Args:
        test_database: Database engine fixture

    Yields:
        AsyncSession: Database session for test operations

    Example:
        >>> async def test_agent_creation(db):
        ...     agent = Agent(agent_id="test-001", name="Test Agent")
        ...     db.add(agent)
        ...     await db.commit()
        ...     # Test assertions
    """
    # Create session factory
    async_session_maker = async_sessionmaker(
        test_database,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        # Cleanup: Rollback any uncommitted changes
        await session.rollback()


# ============================================================================
# FASTAPI CLIENT FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def client(db: AsyncSession) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient for API testing.

    Overrides the database dependency to use the test database session.
    Provides a test client for making HTTP requests to the API.

    Note: TestClient is synchronous but works with async dependencies
    through FastAPI's dependency injection system.

    Args:
        db: Database session fixture

    Yields:
        TestClient: FastAPI test client

    Example:
        >>> def test_api_endpoint(client):
        ...     response = client.get("/api/v1/agents")
        ...     assert response.status_code == 200
    """
    app = create_app()

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup: Remove overrides
    app.dependency_overrides.clear()


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_agent_data() -> Dict:
    """
    Sample agent data for testing.

    Returns a dictionary with agent registration data that can be used
    to create test agents.

    Returns:
        Dictionary with agent test data

    Example:
        >>> def test_agent_creation(db, sample_agent_data):
        ...     agent = Agent(**sample_agent_data)
        ...     db.add(agent)
        ...     await db.commit()
    """
    return {
        "agent_id": "test-agent-001",
        "name": "Test Agent",
        "version": "1.0.0",
        "description": "A test agent for unit testing",
        "status": "inactive",
        "organization": "test-org",
        "owner_id": "test-user-001",
        "environment": "test",
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_message_data() -> Dict:
    """
    Sample message data for testing.

    Returns a dictionary with message data that can be used
    to create test messages.

    Returns:
        Dictionary with message test data

    Example:
        >>> def test_message_creation(db, sample_message_data):
        ...     message = Message(**sample_message_data)
        ...     db.add(message)
        ...     await db.commit()
    """
    return {
        "message_id": "test-msg-001",
        "from_agent_id": "test-agent-001",
        "to_agent_id": "test-agent-002",
        "action": "test_action",
        "payload": {"test": "data", "value": 123},
        "status": "pending",
        "timeout_seconds": 60,
        "max_retries": 3,
        "delivery_attempts": 0,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
async def sample_agent(db: AsyncSession, sample_agent_data: Dict) -> Agent:
    """
    Create a sample agent in the test database.

    Creates and persists a test agent, returning the created instance.

    Args:
        db: Database session
        sample_agent_data: Sample agent data fixture

    Returns:
        Created Agent instance

    Example:
        >>> async def test_agent_operations(sample_agent):
        ...     assert sample_agent.agent_id == "test-agent-001"
    """
    agent = Agent(**sample_agent_data)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.fixture
async def sample_message(
    db: AsyncSession, sample_message_data: Dict, sample_agent: Agent
) -> Message:
    """
    Create a sample message in the test database.

    Creates and persists a test message, returning the created instance.
    Requires sample_agent to exist.

    Args:
        db: Database session
        sample_message_data: Sample message data fixture
        sample_agent: Sample agent fixture (for to_agent_id)

    Returns:
        Created Message instance

    Example:
        >>> async def test_message_operations(sample_message):
        ...     assert sample_message.status == "pending"
    """
    # Ensure to_agent_id matches sample_agent
    message_data = sample_message_data.copy()
    message_data["to_agent_id"] = sample_agent.agent_id

    message = Message(**message_data)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


# ============================================================================
# INTEGRATION TEST FIXTURES (Optional - Testcontainers)
# ============================================================================


@pytest.fixture(scope="session")
def docker_available() -> bool:
    """
    Check if Docker is available for testcontainers.

    Returns:
        True if Docker is available, False otherwise
    """
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_container(docker_available: bool):
    """
    Create a PostgreSQL testcontainer for integration tests.

    Requires testcontainers library and Docker to be available.
    This fixture is optional and only runs if Docker is available.

    Args:
        docker_available: Docker availability check

    Yields:
        PostgreSQL container instance

    Example:
        >>> @pytest.mark.integration
        >>> def test_with_postgres(postgres_container):
        ...     # Use real PostgreSQL for integration tests
        ...     pass
    """
    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    try:
        from testcontainers.postgres import PostgresContainer

        with PostgresContainer("postgres:15-alpine") as postgres:
            yield postgres
    except ImportError:
        pytest.skip("testcontainers library not installed")


@pytest.fixture(scope="session")
def redis_container(docker_available: bool):
    """
    Create a Redis testcontainer for integration tests.

    Requires testcontainers library and Docker to be available.
    This fixture is optional and only runs if Docker is available.

    Args:
        docker_available: Docker availability check

    Yields:
        Redis container instance

    Example:
        >>> @pytest.mark.integration
        >>> def test_with_redis(redis_container):
        ...     # Use real Redis for integration tests
        ...     pass
    """
    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    try:
        from testcontainers.redis import RedisContainer

        with RedisContainer("redis:7-alpine") as redis:
            yield redis
    except ImportError:
        pytest.skip("testcontainers library not installed")


# ============================================================================
# UTILITY FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
async def cleanup_database(db: AsyncSession):
    """
    Clean up database state after each test.

    This fixture runs automatically after each test to ensure
    a clean database state for the next test. It truncates all tables.

    Args:
        db: Database session
    """
    yield

    # Clean up all tables after test
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(table.delete())
    await db.commit()

