"""
Agent API Schemas

Pydantic models for agent-related API endpoints including registration,
response serialization, and pagination.

These schemas provide:
- Request validation for agent registration
- Response serialization from database models
- Pagination support for agent listings
- Type-safe data transfer objects
"""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class AgentRegisterRequest(BaseModel):
    """
    Request schema for registering a new agent.

    Validates agent registration data including agent ID format,
    name requirements, and capability list.

    Attributes:
        agent_id: Unique identifier for the agent (3-255 chars, alphanumeric + hyphens/underscores)
        name: Human-readable agent name (1-255 chars)
        version: Agent version string (default: "1.0.0")
        description: Optional detailed description of agent capabilities
        capabilities: List of capability names the agent provides

    Example:
        >>> request = AgentRegisterRequest(
        ...     agent_id="data-processor-001",
        ...     name="Data Processor Agent",
        ...     version="1.2.3",
        ...     description="Processes data files",
        ...     capabilities=["file_processing", "data_validation"]
        ... )
    """

    agent_id: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Unique identifier for the agent (alphanumeric, hyphens, underscores only)",
        examples=["data-processor-001", "nlp-agent-v2", "api_gateway_agent"],
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name for the agent",
        examples=["Data Processor Agent", "NLP Service", "API Gateway"],
    )

    version: Optional[str] = Field(
        default="1.0.0",
        max_length=50,
        description="Agent version string (semantic versioning recommended)",
        examples=["1.0.0", "2.1.3", "0.9.5-beta"],
    )

    description: Optional[str] = Field(
        default=None,
        description="Detailed description of agent purpose and capabilities",
        examples=["Processes CSV and JSON files", "Provides NLP capabilities"],
    )

    capabilities: List[str] = Field(
        ...,
        min_length=1,
        description="List of capability names this agent provides",
        examples=[["file_processing", "data_validation"], ["text_analysis", "sentiment"]],
    )

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id_format(cls, v: str) -> str:
        """
        Validate agent_id format.

        Agent IDs must:
        - Be 3-255 characters long
        - Contain only alphanumeric characters, hyphens, and underscores
        - Not start or end with a hyphen or underscore
        - Not contain consecutive hyphens or underscores

        Args:
            v: The agent_id value to validate

        Returns:
            Validated agent_id string

        Raises:
            ValueError: If agent_id format is invalid

        Example:
            >>> AgentRegisterRequest.validate_agent_id_format("agent-123")
            'agent-123'
            >>> AgentRegisterRequest.validate_agent_id_format("invalid agent")
            ValueError: agent_id must contain only alphanumeric characters, hyphens, and underscores
        """
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$", v):
            raise ValueError(
                "agent_id must contain only alphanumeric characters, hyphens, and underscores. "
                "Must start and end with alphanumeric character."
            )

        # Check for consecutive hyphens or underscores
        if "--" in v or "__" in v or "-_" in v or "_-" in v:
            raise ValueError("agent_id cannot contain consecutive hyphens or underscores")

        return v

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """
        Validate capabilities list.

        Ensures:
        - List is not empty
        - Each capability name is non-empty
        - No duplicate capabilities

        Args:
            v: List of capability names

        Returns:
            Validated list of unique capability names

        Raises:
            ValueError: If capabilities list is invalid
        """
        if not v:
            raise ValueError("capabilities list cannot be empty")

        # Remove duplicates while preserving order
        seen = set()
        unique_capabilities = []
        for cap in v:
            cap_clean = cap.strip()
            if not cap_clean:
                raise ValueError("capability names cannot be empty")
            if cap_clean not in seen:
                seen.add(cap_clean)
                unique_capabilities.append(cap_clean)

        return unique_capabilities

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "agent_id": "data-processor-001",
                "name": "Data Processor Agent",
                "version": "1.0.0",
                "description": "Processes CSV and JSON data files with validation",
                "capabilities": ["file_processing", "data_validation", "format_conversion"],
            }
        },
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class AgentResponse(BaseModel):
    """
    Basic agent response schema.

    Contains essential agent information for list views and basic operations.
    Includes authentication tokens and public keys for agent API access.

    Attributes:
        agent_id: Unique identifier for the agent
        name: Human-readable agent name
        status: Current agent status (active, inactive, error, maintenance)
        api_token: API authentication token (secret_token from database)
        public_key: Public key for agent authentication and encryption
        created_at: Timestamp when the agent was created

    Example:
        >>> response = AgentResponse(
        ...     agent_id="data-processor-001",
        ...     name="Data Processor Agent",
        ...     status="active",
        ...     api_token="sk_live_abc123...",
        ...     public_key="ssh-rsa AAAAB3...",
        ...     created_at=datetime.now()
        ... )
    """

    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable agent name")
    status: str = Field(..., description="Current agent status")
    api_token: Optional[str] = Field(
        default=None,
        description="API authentication token (only returned on creation)",
        alias="secret_token",
    )
    public_key: Optional[str] = Field(
        default=None,
        description="Public key for agent authentication and encryption",
    )
    created_at: datetime = Field(..., description="Timestamp when the agent was created")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both field name and alias
    )


class AgentDetailResponse(BaseModel):
    """
    Detailed agent response schema.

    Extends AgentResponse with additional details including version,
    description, heartbeat information, and associated capabilities.

    Attributes:
        agent_id: Unique identifier for the agent
        name: Human-readable agent name
        status: Current agent status
        api_token: API authentication token
        public_key: Public key for agent authentication
        created_at: Timestamp when the agent was created
        version: Agent version string
        description: Detailed description of agent capabilities
        last_heartbeat: Timestamp of last heartbeat/health check
        capabilities: List of capability names provided by this agent

    Example:
        >>> response = AgentDetailResponse(
        ...     agent_id="data-processor-001",
        ...     name="Data Processor Agent",
        ...     status="active",
        ...     version="1.2.3",
        ...     description="Processes data files",
        ...     last_heartbeat=datetime.now(),
        ...     capabilities=["file_processing", "data_validation"]
        ... )
    """

    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable agent name")
    status: str = Field(..., description="Current agent status")
    api_token: Optional[str] = Field(
        default=None,
        description="API authentication token",
        alias="secret_token",
    )
    public_key: Optional[str] = Field(
        default=None,
        description="Public key for agent authentication and encryption",
    )
    created_at: datetime = Field(..., description="Timestamp when the agent was created")
    version: Optional[str] = Field(
        default=None,
        description="Agent version string",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of agent capabilities",
    )
    last_heartbeat: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last heartbeat/health check",
    )
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of capability names provided by this agent",
    )

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()

    @field_serializer("last_heartbeat")
    def serialize_last_heartbeat(self, value: datetime | None) -> str | None:
        """Serialize optional datetime to ISO format string."""
        return value.isoformat() if value else None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class AgentListResponse(BaseModel):
    """
    Paginated list of agents response schema.

    Provides pagination metadata along with a list of agent responses.
    Supports cursor-based and offset-based pagination patterns.

    Attributes:
        agents: List of AgentResponse objects
        total: Total number of agents matching the query
        limit: Maximum number of agents per page
        offset: Number of agents skipped (for offset-based pagination)
        has_more: Whether there are more agents beyond the current page

    Example:
        >>> response = AgentListResponse(
        ...     agents=[agent1, agent2, agent3],
        ...     total=25,
        ...     limit=10,
        ...     offset=0,
        ...     has_more=True
        ... )
    """

    agents: List[AgentResponse] = Field(
        ...,
        description="List of agent responses for the current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of agents matching the query",
    )
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Maximum number of agents per page",
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Number of agents skipped (for offset-based pagination)",
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more agents beyond the current page",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "agents": [
                    {
                        "agent_id": "data-processor-001",
                        "name": "Data Processor Agent",
                        "status": "active",
                        "api_token": None,
                        "public_key": None,
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                ],
                "total": 25,
                "limit": 10,
                "offset": 0,
                "has_more": True,
            }
        },
    )

