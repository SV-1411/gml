"""
Unit Tests for Agent Service

Tests for agent registration, retrieval, listing, and status management operations.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.agents import AgentRegisterRequest
from src.gml.db.models import Agent
from src.gml.services.agent_service import AgentService
from src.gml.services.exceptions import (
    AgentAlreadyExistsError,
    AgentNotFoundError,
    InvalidAgentStatusError,
)


# ============================================================================
# REGISTER AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_register_agent_success(db: AsyncSession):
    """
    Test successful agent registration.

    Verifies:
    - Agent is created in database
    - API token is generated and returned
    - Public key is generated and returned
    - All agent fields are correctly set
    - Agent starts with 'inactive' status
    """
    # Create registration request
    request = AgentRegisterRequest(
        agent_id="test-agent-001",
        name="Test Agent",
        version="1.0.0",
        description="A test agent for unit testing",
        capabilities=["test_capability", "another_capability"],
    )

    # Register agent
    result = await AgentService.register_agent(db, request)

    # Verify return values
    assert result is not None
    assert isinstance(result, dict)
    assert "agent_id" in result
    assert "api_token" in result
    assert "public_key" in result

    # Verify agent_id matches
    assert result["agent_id"] == "test-agent-001"

    # Verify API token is generated (should be a string)
    assert result["api_token"] is not None
    assert isinstance(result["api_token"], str)
    assert len(result["api_token"]) > 0

    # Verify public key is generated (should be PEM format)
    assert result["public_key"] is not None
    assert isinstance(result["public_key"], str)
    assert result["public_key"].startswith("-----BEGIN PUBLIC KEY-----")
    assert result["public_key"].endswith("-----END PUBLIC KEY-----\n")

    # Verify database entry
    query = select(Agent).where(Agent.agent_id == "test-agent-001")
    result_query = await db.execute(query)
    agent = result_query.scalar_one_or_none()

    assert agent is not None
    assert agent.agent_id == "test-agent-001"
    assert agent.name == "Test Agent"
    assert agent.version == "1.0.0"
    assert agent.description == "A test agent for unit testing"
    assert agent.status == "inactive"  # New agents start as inactive
    assert agent.secret_token == result["api_token"]  # Token stored in database
    assert agent.public_key == result["public_key"]  # Public key stored in database
    assert agent.created_at is not None
    assert agent.updated_at is None  # Not set on creation


@pytest.mark.asyncio
async def test_register_agent_with_minimal_data(db: AsyncSession):
    """
    Test agent registration with minimal required fields.

    Verifies that agent can be registered with only required fields.
    """
    request = AgentRegisterRequest(
        agent_id="minimal-agent",
        name="Minimal Agent",
        capabilities=["basic"],
    )

    result = await AgentService.register_agent(db, request)

    assert result["agent_id"] == "minimal-agent"
    assert result["api_token"] is not None
    assert result["public_key"] is not None

    # Verify defaults
    agent = await AgentService.get_agent(db, "minimal-agent", raise_if_not_found=False)
    assert agent is not None
    assert agent.version == "1.0.0"  # Default version
    assert agent.description is None  # Optional field


@pytest.mark.asyncio
async def test_register_duplicate_agent(db: AsyncSession):
    """
    Test that registering a duplicate agent raises AgentAlreadyExistsError.

    Verifies:
    - First registration succeeds
    - Second registration with same agent_id raises exception
    - Exception contains correct agent_id
    """
    # Register first agent
    request1 = AgentRegisterRequest(
        agent_id="duplicate-test",
        name="First Agent",
        capabilities=["test"],
    )
    result1 = await AgentService.register_agent(db, request1)
    assert result1["agent_id"] == "duplicate-test"

    # Try to register duplicate
    request2 = AgentRegisterRequest(
        agent_id="duplicate-test",
        name="Second Agent",
        capabilities=["test"],
    )

    with pytest.raises(AgentAlreadyExistsError) as exc_info:
        await AgentService.register_agent(db, request2)

    # Verify exception details
    assert exc_info.value.agent_id == "duplicate-test"
    assert "already exists" in str(exc_info.value).lower()

    # Verify only one agent exists in database
    query = select(Agent).where(Agent.agent_id == "duplicate-test")
    result_query = await db.execute(query)
    agents = result_query.scalars().all()
    assert len(agents) == 1
    assert agents[0].name == "First Agent"  # Original agent preserved


# ============================================================================
# GET AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_agent_success(db: AsyncSession):
    """
    Test successful agent retrieval.

    Verifies:
    - Agent can be retrieved by agent_id
    - All fields are correctly returned
    - Agent object is properly populated
    """
    # Register an agent first
    request = AgentRegisterRequest(
        agent_id="get-test-agent",
        name="Get Test Agent",
        version="2.0.0",
        description="Agent for get testing",
        capabilities=["get_test"],
    )
    await AgentService.register_agent(db, request)

    # Get the agent
    agent = await AgentService.get_agent(db, "get-test-agent")

    # Verify agent is returned
    assert agent is not None
    assert isinstance(agent, Agent)

    # Verify all fields
    assert agent.agent_id == "get-test-agent"
    assert agent.name == "Get Test Agent"
    assert agent.version == "2.0.0"
    assert agent.description == "Agent for get testing"
    assert agent.status == "inactive"
    assert agent.secret_token is not None
    assert agent.public_key is not None
    assert agent.created_at is not None


@pytest.mark.asyncio
async def test_get_agent_not_found(db: AsyncSession):
    """
    Test retrieval of non-existent agent.

    Verifies:
    - AgentNotFoundError is raised when agent doesn't exist
    - Exception contains correct agent_id
    - When raise_if_not_found=False, None is returned
    """
    # Try to get non-existent agent with default behavior (raise)
    with pytest.raises(AgentNotFoundError) as exc_info:
        await AgentService.get_agent(db, "non-existent-agent")

    assert exc_info.value.agent_id == "non-existent-agent"
    assert "not found" in str(exc_info.value).lower()

    # Try to get non-existent agent with raise_if_not_found=False
    agent = await AgentService.get_agent(
        db, "non-existent-agent", raise_if_not_found=False
    )
    assert agent is None


@pytest.mark.asyncio
async def test_get_agent_returns_none_when_not_found(db: AsyncSession):
    """
    Test that get_agent returns None when raise_if_not_found=False.

    Verifies the optional behavior for non-existent agents.
    """
    agent = await AgentService.get_agent(
        db, "another-non-existent", raise_if_not_found=False
    )
    assert agent is None


# ============================================================================
# LIST AGENTS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_agents(db: AsyncSession):
    """
    Test listing agents with pagination.

    Verifies:
    - All agents are returned when no filters applied
    - Pagination works correctly
    - Total count is accurate
    - has_more flag is correct
    - Results are ordered by created_at descending
    """
    # Register 3 agents
    agents_data = [
        {
            "agent_id": "list-agent-1",
            "name": "List Agent 1",
            "version": "1.0.0",
            "capabilities": ["test1"],
        },
        {
            "agent_id": "list-agent-2",
            "name": "List Agent 2",
            "version": "1.0.0",
            "capabilities": ["test2"],
        },
        {
            "agent_id": "list-agent-3",
            "name": "List Agent 3",
            "version": "1.0.0",
            "capabilities": ["test3"],
        },
    ]

    for agent_data in agents_data:
        request = AgentRegisterRequest(**agent_data)
        await AgentService.register_agent(db, request)

    # List all agents
    result = await AgentService.list_agents(db, skip=0, limit=100)

    # Verify result structure
    assert result is not None
    assert isinstance(result, dict)
    assert "agents" in result
    assert "total" in result
    assert "limit" in result
    assert "offset" in result
    assert "has_more" in result

    # Verify counts
    assert result["total"] == 3
    assert len(result["agents"]) == 3
    assert result["limit"] == 100
    assert result["offset"] == 0
    assert result["has_more"] is False  # All agents returned

    # Verify all agents are present
    agent_ids = {agent.agent_id for agent in result["agents"]}
    assert "list-agent-1" in agent_ids
    assert "list-agent-2" in agent_ids
    assert "list-agent-3" in agent_ids

    # Verify agents are ordered by created_at descending (newest first)
    agents = result["agents"]
    for i in range(len(agents) - 1):
        assert agents[i].created_at >= agents[i + 1].created_at


@pytest.mark.asyncio
async def test_list_agents_with_pagination(db: AsyncSession):
    """
    Test listing agents with pagination limits.

    Verifies:
    - Skip and limit work correctly
    - has_more flag is set correctly
    - Total count includes all agents regardless of pagination
    """
    # Register 5 agents
    for i in range(5):
        request = AgentRegisterRequest(
            agent_id=f"paginated-agent-{i}",
            name=f"Paginated Agent {i}",
            capabilities=[f"cap{i}"],
        )
        await AgentService.register_agent(db, request)

    # List with pagination (skip=0, limit=2)
    result1 = await AgentService.list_agents(db, skip=0, limit=2)

    assert result1["total"] == 5
    assert len(result1["agents"]) == 2
    assert result1["limit"] == 2
    assert result1["offset"] == 0
    assert result1["has_more"] is True  # More agents exist

    # List next page (skip=2, limit=2)
    result2 = await AgentService.list_agents(db, skip=2, limit=2)

    assert result2["total"] == 5
    assert len(result2["agents"]) == 2
    assert result2["limit"] == 2
    assert result2["offset"] == 2
    assert result2["has_more"] is True  # More agents exist

    # List last page (skip=4, limit=2)
    result3 = await AgentService.list_agents(db, skip=4, limit=2)

    assert result3["total"] == 5
    assert len(result3["agents"]) == 1  # Only 1 agent left
    assert result3["limit"] == 2
    assert result3["offset"] == 4
    assert result3["has_more"] is False  # No more agents

    # Verify no overlap between pages
    page1_ids = {agent.agent_id for agent in result1["agents"]}
    page2_ids = {agent.agent_id for agent in result2["agents"]}
    page3_ids = {agent.agent_id for agent in result3["agents"]}

    assert page1_ids.isdisjoint(page2_ids)
    assert page2_ids.isdisjoint(page3_ids)
    assert page1_ids.isdisjoint(page3_ids)


@pytest.mark.asyncio
async def test_list_agents_with_status_filter(db: AsyncSession):
    """
    Test listing agents filtered by status.

    Verifies:
    - Status filter works correctly
    - Only agents with matching status are returned
    - Total count reflects filtered results
    """
    # Register agents with different statuses
    agents_data = [
        {
            "agent_id": "active-agent-1",
            "name": "Active Agent 1",
            "capabilities": ["test"],
        },
        {
            "agent_id": "active-agent-2",
            "name": "Active Agent 2",
            "capabilities": ["test"],
        },
        {
            "agent_id": "inactive-agent-1",
            "name": "Inactive Agent 1",
            "capabilities": ["test"],
        },
    ]

    for agent_data in agents_data:
        request = AgentRegisterRequest(**agent_data)
        await AgentService.register_agent(db, request)

    # Update some agents to active status
    await AgentService.update_agent_status(db, "active-agent-1", "active")
    await AgentService.update_agent_status(db, "active-agent-2", "active")

    # List active agents
    active_result = await AgentService.list_agents(db, skip=0, limit=100, status="active")

    assert active_result["total"] == 2
    assert len(active_result["agents"]) == 2
    agent_ids = {agent.agent_id for agent in active_result["agents"]}
    assert "active-agent-1" in agent_ids
    assert "active-agent-2" in agent_ids
    assert "inactive-agent-1" not in agent_ids

    # Verify all agents have active status
    for agent in active_result["agents"]:
        assert agent.status == "active"

    # List inactive agents
    inactive_result = await AgentService.list_agents(
        db, skip=0, limit=100, status="inactive"
    )

    assert inactive_result["total"] == 1
    assert len(inactive_result["agents"]) == 1
    assert inactive_result["agents"][0].agent_id == "inactive-agent-1"
    assert inactive_result["agents"][0].status == "inactive"


@pytest.mark.asyncio
async def test_list_agents_with_invalid_status(db: AsyncSession):
    """
    Test that listing with invalid status raises InvalidAgentStatusError.

    Verifies:
    - InvalidAgentStatusError is raised for invalid status
    - Exception contains the invalid status and valid statuses
    """
    with pytest.raises(InvalidAgentStatusError) as exc_info:
        await AgentService.list_agents(db, skip=0, limit=100, status="invalid_status")

    assert exc_info.value.status == "invalid_status"
    assert "invalid" in str(exc_info.value).lower()
    assert len(exc_info.value.valid_statuses) > 0


@pytest.mark.asyncio
async def test_list_agents_empty_database(db: AsyncSession):
    """
    Test listing agents when database is empty.

    Verifies:
    - Empty list is returned
    - Total count is 0
    - has_more is False
    """
    result = await AgentService.list_agents(db, skip=0, limit=100)

    assert result["total"] == 0
    assert len(result["agents"]) == 0
    assert result["has_more"] is False
    assert result["limit"] == 100
    assert result["offset"] == 0


@pytest.mark.asyncio
async def test_list_agents_limit_capped_at_100(db: AsyncSession):
    """
    Test that list limit is capped at 100.

    Verifies that even if limit > 100 is requested, it's capped at 100.
    """
    # Register one agent
    request = AgentRegisterRequest(
        agent_id="limit-test",
        name="Limit Test",
        capabilities=["test"],
    )
    await AgentService.register_agent(db, request)

    # Request with limit > 100
    result = await AgentService.list_agents(db, skip=0, limit=200)

    assert result["limit"] == 100  # Capped at 100


# ============================================================================
# UPDATE AGENT STATUS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_agent_status_success(db: AsyncSession):
    """
    Test successful agent status update.

    Verifies:
    - Status is updated correctly
    - last_heartbeat is set
    - updated_at is set
    - Agent is returned with updated values
    """
    # Register an agent
    request = AgentRegisterRequest(
        agent_id="status-update-test",
        name="Status Update Test",
        capabilities=["test"],
    )
    await AgentService.register_agent(db, request)

    # Verify initial status
    agent_before = await AgentService.get_agent(db, "status-update-test")
    assert agent_before.status == "inactive"
    assert agent_before.last_heartbeat is None

    # Update status
    updated_agent = await AgentService.update_agent_status(
        db, "status-update-test", "active"
    )

    # Verify updated values
    assert updated_agent.status == "active"
    assert updated_agent.last_heartbeat is not None
    assert updated_agent.updated_at is not None

    # Verify in database
    agent_after = await AgentService.get_agent(db, "status-update-test")
    assert agent_after.status == "active"
    assert agent_after.last_heartbeat is not None
    assert agent_after.updated_at is not None


@pytest.mark.asyncio
async def test_update_agent_status_not_found(db: AsyncSession):
    """
    Test updating status of non-existent agent.

    Verifies that AgentNotFoundError is raised.
    """
    with pytest.raises(AgentNotFoundError) as exc_info:
        await AgentService.update_agent_status(db, "non-existent", "active")

    assert exc_info.value.agent_id == "non-existent"


@pytest.mark.asyncio
async def test_update_agent_status_invalid_status(db: AsyncSession):
    """
    Test updating agent status with invalid status.

    Verifies that InvalidAgentStatusError is raised.
    """
    # Register an agent
    request = AgentRegisterRequest(
        agent_id="invalid-status-test",
        name="Invalid Status Test",
        capabilities=["test"],
    )
    await AgentService.register_agent(db, request)

    # Try to update with invalid status
    with pytest.raises(InvalidAgentStatusError) as exc_info:
        await AgentService.update_agent_status(db, "invalid-status-test", "invalid")

    assert exc_info.value.status == "invalid"
    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_agent_status_all_valid_statuses(db: AsyncSession):
    """
    Test updating agent status with all valid status values.

    Verifies that all valid statuses can be set.
    """
    # Register an agent
    request = AgentRegisterRequest(
        agent_id="all-statuses-test",
        name="All Statuses Test",
        capabilities=["test"],
    )
    await AgentService.register_agent(db, request)

    valid_statuses = ["active", "inactive", "error", "maintenance"]

    for status in valid_statuses:
        updated_agent = await AgentService.update_agent_status(
            db, "all-statuses-test", status
        )
        assert updated_agent.status == status
        assert updated_agent.last_heartbeat is not None

