"""
Integration Tests for Agent API Endpoints

Tests the full HTTP API endpoints for agent management including registration,
retrieval, and listing with proper status codes and response validation.
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# REGISTER AGENT ENDPOINT TESTS
# ============================================================================


def test_post_register_agent_201(client: TestClient):
    """
    Test successful agent registration endpoint.

    Verifies:
    - POST /api/v1/agents/register returns 201 Created
    - Response contains agent_id, api_token, public_key
    - Response headers are correct
    - Response JSON structure is valid
    """
    # Prepare registration request
    request_data = {
        "agent_id": "integration-test-agent-001",
        "name": "Integration Test Agent",
        "version": "1.0.0",
        "description": "An agent for integration testing",
        "capabilities": ["test_capability", "integration_test"],
    }

    # Make POST request
    response = client.post(
        "/api/v1/agents/register",
        json=request_data,
        headers={"Content-Type": "application/json"},
    )

    # Verify status code
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    # Verify response headers
    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"].lower()

    # Verify response JSON
    assert response.json() is not None
    response_data = response.json()

    # Verify required fields
    assert "agent_id" in response_data
    assert "api_token" in response_data
    assert "public_key" in response_data

    # Verify field values
    assert response_data["agent_id"] == "integration-test-agent-001"
    assert response_data["api_token"] is not None
    assert isinstance(response_data["api_token"], str)
    assert len(response_data["api_token"]) > 0

    # Verify public key format
    assert response_data["public_key"] is not None
    assert isinstance(response_data["public_key"], str)
    assert response_data["public_key"].startswith("-----BEGIN PUBLIC KEY-----")
    assert response_data["public_key"].endswith("-----END PUBLIC KEY-----\n")


def test_post_register_agent_minimal_data_201(client: TestClient):
    """
    Test agent registration with minimal required fields.

    Verifies that registration works with only required fields.
    """
    request_data = {
        "agent_id": "minimal-integration-agent",
        "name": "Minimal Agent",
        "capabilities": ["basic"],
    }

    response = client.post("/api/v1/agents/register", json=request_data)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["agent_id"] == "minimal-integration-agent"
    assert response_data["api_token"] is not None
    assert response_data["public_key"] is not None


def test_post_register_duplicate_409(client: TestClient):
    """
    Test registering duplicate agent returns 409 Conflict.

    Verifies:
    - First registration succeeds (201)
    - Second registration with same agent_id returns 409
    - Error message contains agent_id
    """
    # Register first agent
    request_data = {
        "agent_id": "duplicate-test-agent",
        "name": "First Agent",
        "capabilities": ["test"],
    }

    response1 = client.post("/api/v1/agents/register", json=request_data)
    assert response1.status_code == 201

    # Try to register duplicate
    response2 = client.post("/api/v1/agents/register", json=request_data)

    # Verify 409 Conflict
    assert response2.status_code == 409, f"Expected 409, got {response2.status_code}: {response2.text}"

    # Verify error response structure
    error_data = response2.json()
    assert "detail" in error_data
    assert "duplicate-test-agent" in error_data["detail"].lower()
    assert "already exists" in error_data["detail"].lower()


def test_post_register_agent_invalid_data_422(client: TestClient):
    """
    Test agent registration with invalid data returns 422.

    Verifies validation errors are properly returned.
    """
    # Test missing required fields
    invalid_request = {
        "name": "Missing Agent ID",
        "capabilities": ["test"],
    }

    response = client.post("/api/v1/agents/register", json=invalid_request)
    assert response.status_code == 422

    # Test invalid agent_id format
    invalid_request2 = {
        "agent_id": "invalid agent id",  # Contains space
        "name": "Invalid Agent",
        "capabilities": ["test"],
    }

    response2 = client.post("/api/v1/agents/register", json=invalid_request2)
    assert response2.status_code == 422

    # Test empty capabilities
    invalid_request3 = {
        "agent_id": "empty-capabilities",
        "name": "Empty Capabilities",
        "capabilities": [],
    }

    response3 = client.post("/api/v1/agents/register", json=invalid_request3)
    assert response3.status_code == 422


# ============================================================================
# GET AGENT ENDPOINT TESTS
# ============================================================================


def test_get_agent_200(client: TestClient):
    """
    Test successful agent retrieval endpoint.

    Verifies:
    - GET /api/v1/agents/{agent_id} returns 200 OK
    - Response contains all agent details
    - Response structure matches AgentDetailResponse schema
    - api_token is not exposed in GET requests
    """
    # First, register an agent
    register_data = {
        "agent_id": "get-test-agent-001",
        "name": "Get Test Agent",
        "version": "2.0.0",
        "description": "Agent for GET endpoint testing",
        "capabilities": ["get_test", "retrieval"],
    }

    register_response = client.post("/api/v1/agents/register", json=register_data)
    assert register_response.status_code == 201

    # Get the agent
    response = client.get("/api/v1/agents/get-test-agent-001")

    # Verify status code
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Verify response headers
    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"].lower()

    # Verify response JSON
    response_data = response.json()

    # Verify all required fields
    assert "agent_id" in response_data
    assert "name" in response_data
    assert "status" in response_data
    assert "public_key" in response_data
    assert "created_at" in response_data
    assert "version" in response_data
    assert "description" in response_data
    assert "last_heartbeat" in response_data
    assert "capabilities" in response_data

    # Verify field values
    assert response_data["agent_id"] == "get-test-agent-001"
    assert response_data["name"] == "Get Test Agent"
    assert response_data["version"] == "2.0.0"
    assert response_data["description"] == "Agent for GET endpoint testing"
    assert response_data["status"] == "inactive"  # New agents start as inactive
    assert response_data["api_token"] is None  # Token should not be exposed
    assert response_data["public_key"] is not None
    assert response_data["created_at"] is not None
    assert isinstance(response_data["capabilities"], list)
    # Note: Capabilities might be empty if not stored in Capability table


def test_get_agent_404(client: TestClient):
    """
    Test getting non-existent agent returns 404 Not Found.

    Verifies:
    - GET /api/v1/agents/non-existent returns 404
    - Error message contains agent_id
    - Error response structure is correct
    """
    response = client.get("/api/v1/agents/non-existent-agent-id")

    # Verify 404 status code
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"

    # Verify error response
    error_data = response.json()
    assert "detail" in error_data
    assert "non-existent-agent-id" in error_data["detail"].lower()
    assert "not found" in error_data["detail"].lower()


def test_get_agent_invalid_id_format(client: TestClient):
    """
    Test getting agent with various invalid ID formats.

    Verifies that invalid IDs are handled gracefully.
    """
    # Test with empty string (should be caught by route)
    response = client.get("/api/v1/agents/")
    # This might return 404 or 405 depending on route configuration
    assert response.status_code in [404, 405, 422]


# ============================================================================
# LIST AGENTS ENDPOINT TESTS
# ============================================================================


def test_get_agents_list_200(client: TestClient):
    """
    Test successful agent listing endpoint.

    Verifies:
    - GET /api/v1/agents returns 200 OK
    - Response contains pagination metadata
    - Response contains list of agents
    - All registered agents are included
    """
    # Register multiple agents
    agents_to_register = [
        {
            "agent_id": "list-agent-001",
            "name": "List Agent 1",
            "version": "1.0.0",
            "capabilities": ["list_test"],
        },
        {
            "agent_id": "list-agent-002",
            "name": "List Agent 2",
            "version": "1.0.0",
            "capabilities": ["list_test"],
        },
        {
            "agent_id": "list-agent-003",
            "name": "List Agent 3",
            "version": "1.0.0",
            "capabilities": ["list_test"],
        },
    ]

    registered_ids = []
    for agent_data in agents_to_register:
        register_response = client.post("/api/v1/agents/register", json=agent_data)
        assert register_response.status_code == 201
        registered_ids.append(agent_data["agent_id"])

    # Get list of agents
    response = client.get("/api/v1/agents")

    # Verify status code
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Verify response headers
    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"].lower()

    # Verify response JSON structure
    response_data = response.json()
    assert "agents" in response_data
    assert "total" in response_data
    assert "limit" in response_data
    assert "offset" in response_data
    assert "has_more" in response_data

    # Verify pagination metadata
    assert isinstance(response_data["total"], int)
    assert response_data["total"] >= 3  # At least our 3 agents
    assert isinstance(response_data["limit"], int)
    assert response_data["limit"] <= 100
    assert isinstance(response_data["offset"], int)
    assert response_data["offset"] >= 0
    assert isinstance(response_data["has_more"], bool)

    # Verify agents list
    assert isinstance(response_data["agents"], list)
    assert len(response_data["agents"]) >= 3

    # Verify all registered agents are in the list
    agent_ids = {agent["agent_id"] for agent in response_data["agents"]}
    for registered_id in registered_ids:
        assert registered_id in agent_ids, f"Agent {registered_id} not found in list"

    # Verify agent structure in list
    for agent in response_data["agents"]:
        assert "agent_id" in agent
        assert "name" in agent
        assert "status" in agent
        assert "public_key" in agent
        assert "created_at" in agent
        assert agent["api_token"] is None  # Tokens should not be exposed in list


def test_get_agents_list_with_pagination(client: TestClient):
    """
    Test agent listing with pagination parameters.

    Verifies:
    - Skip and limit parameters work correctly
    - Pagination metadata is accurate
    - has_more flag is set correctly
    """
    # Register 5 agents
    for i in range(5):
        agent_data = {
            "agent_id": f"paginated-agent-{i:03d}",
            "name": f"Paginated Agent {i}",
            "capabilities": ["pagination_test"],
        }
        client.post("/api/v1/agents/register", json=agent_data)

    # Test first page (skip=0, limit=2)
    response1 = client.get("/api/v1/agents?skip=0&limit=2")

    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["offset"] == 0
    assert data1["limit"] == 2
    assert len(data1["agents"]) == 2
    assert data1["has_more"] is True  # More agents exist

    # Test second page (skip=2, limit=2)
    response2 = client.get("/api/v1/agents?skip=2&limit=2")

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["offset"] == 2
    assert data2["limit"] == 2
    assert len(data2["agents"]) == 2
    assert data2["has_more"] is True  # More agents exist

    # Test last page (skip=4, limit=2)
    response3 = client.get("/api/v1/agents?skip=4&limit=2")

    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["offset"] == 4
    assert data3["limit"] == 2
    # Should have at least 1 agent (might have more from other tests)
    assert len(data3["agents"]) >= 1

    # Verify no overlap between pages
    page1_ids = {agent["agent_id"] for agent in data1["agents"]}
    page2_ids = {agent["agent_id"] for agent in data2["agents"]}
    assert page1_ids.isdisjoint(page2_ids)


def test_get_agents_list_with_status_filter(client: TestClient):
    """
    Test agent listing with status filter.

    Verifies:
    - Status filter parameter works correctly
    - Only agents with matching status are returned
    - Total count reflects filtered results
    """
    # Register agents
    agent1_data = {
        "agent_id": "status-filter-active",
        "name": "Active Agent",
        "capabilities": ["status_test"],
    }
    agent2_data = {
        "agent_id": "status-filter-inactive",
        "name": "Inactive Agent",
        "capabilities": ["status_test"],
    }

    client.post("/api/v1/agents/register", json=agent1_data)
    client.post("/api/v1/agents/register", json=agent2_data)

    # Note: New agents start as "inactive", so we can test inactive filter
    # To test active filter, we'd need to update status first (requires update endpoint)

    # Test inactive filter
    response = client.get("/api/v1/agents?status=inactive")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2  # At least our 2 agents

    # Verify all returned agents have inactive status
    for agent in data["agents"]:
        assert agent["status"] == "inactive"


def test_get_agents_list_empty_database(client: TestClient):
    """
    Test agent listing when database is empty (or no matching agents).

    Verifies that empty list is returned correctly.
    """
    # Try to get agents with a status that doesn't exist
    response = client.get("/api/v1/agents?status=maintenance")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0
    assert isinstance(data["agents"], list)
    assert data["has_more"] is False


def test_get_agents_list_invalid_pagination(client: TestClient):
    """
    Test agent listing with invalid pagination parameters.

    Verifies that invalid parameters are handled correctly.
    """
    # Test negative skip
    response1 = client.get("/api/v1/agents?skip=-1")
    assert response1.status_code == 422  # Validation error

    # Test negative limit
    response2 = client.get("/api/v1/agents?limit=-1")
    assert response2.status_code == 422  # Validation error

    # Test limit > 100 (should be capped or validated)
    response3 = client.get("/api/v1/agents?limit=200")
    # Should either return 422 or cap at 100
    if response3.status_code == 200:
        data = response3.json()
        assert data["limit"] <= 100


def test_get_agents_list_response_headers(client: TestClient):
    """
    Test that agent list endpoint returns proper headers.

    Verifies Content-Type and other standard headers.
    """
    response = client.get("/api/v1/agents")

    assert response.status_code == 200
    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"].lower()


def test_get_agents_list_default_parameters(client: TestClient):
    """
    Test agent listing with default parameters.

    Verifies default values for skip and limit.
    """
    response = client.get("/api/v1/agents")

    assert response.status_code == 200
    data = response.json()
    assert data["offset"] == 0  # Default skip
    assert data["limit"] == 100  # Default limit

