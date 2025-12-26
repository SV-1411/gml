"""
Database Models for GML Infrastructure

This module defines SQLAlchemy ORM models for the core database tables:
- Agent: AI agent registry and configuration
- Message: Inter-agent communication and message queue
- Capability: Agent capabilities and feature registry
- Memory: Agent memory and context storage
- Cost: Cost tracking and billing records
- AuditLog: Audit trail and event logging
- Connection: Agent connection and relationship tracking

All models use SQLAlchemy 2.0 async syntax and include:
- Proper type hints
- Default values and constraints
- Indexes for performance
- Timestamp tracking
- JSON fields for flexible data storage

Usage:
    >>> from src.gml.db.models import Agent, Message, Capability, Memory, Cost, AuditLog, Connection
    >>> from src.gml.db import DatabaseSession
    >>>
    >>> async with DatabaseSession() as db:
    >>>     agent = Agent(
    >>>         agent_id="agent-123",
    >>>         name="My Agent",
    >>>         owner_id="user-456"
    >>>     )
    >>>     db.add(agent)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.gml.db import Base


# ============================================================================
# AGENT MODEL
# ============================================================================


class Agent(Base):
    """
    Agent model representing an AI agent in the system.

    Stores agent configuration, status, and metadata for multi-agent
    orchestration. Each agent has a unique identifier and can be part
    of an organization with configurable capabilities.

    Attributes:
        id: Auto-incrementing primary key
        agent_id: Unique identifier for the agent (user-defined)
        name: Human-readable name for the agent
        version: Version string for the agent (e.g., "1.0.0")
        description: Detailed description of agent purpose and capabilities
        owner_id: User ID of the agent owner
        organization: Organization identifier for multi-tenancy
        status: Current agent status (active, inactive, error, maintenance)
        last_heartbeat: Timestamp of last heartbeat/health check
        error_message: Last error message if status is 'error'
        config: JSON configuration object for agent settings
        environment: Deployment environment (development, staging, production)
        public_key: Public key for agent authentication and encryption
        secret_token: Hashed secret token for agent API authentication
        created_at: Timestamp of agent creation
        updated_at: Timestamp of last update

    Indexes:
        - agent_id (unique)
        - status (for filtering active agents)
        - organization (for multi-tenancy queries)
        - created_at (for temporal queries)

    Example:
        >>> agent = Agent(
        ...     agent_id="data-processor-001",
        ...     name="Data Processor",
        ...     version="1.2.3",
        ...     owner_id="user-123",
        ...     organization="acme-corp",
        ...     status="active",
        ...     config={"max_workers": 4, "timeout": 300}
        ... )
    """

    __tablename__ = "agents"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Unique identifier
    agent_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique identifier for the agent",
    )

    # Basic information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable agent name",
    )

    version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Agent version (e.g., 1.0.0)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of agent capabilities",
    )

    # Ownership and organization
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User ID of agent owner",
    )

    organization: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Organization identifier for multi-tenancy",
    )

    # Status and health
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="inactive",
        server_default="inactive",
        index=True,
        comment="Agent status: active, inactive, error, maintenance",
    )

    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last heartbeat",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last error message if status is error",
    )

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON configuration object",
    )

    environment: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Deployment environment (dev, staging, prod)",
    )

    # Authentication
    public_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Public key for authentication and encryption",
    )

    secret_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed secret token for API authentication",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp of agent creation",
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        server_default=func.now(),
        comment="Timestamp of last update",
    )

    def __repr__(self) -> str:
        """String representation of Agent."""
        return (
            f"<Agent(id={self.id}, agent_id='{self.agent_id}', "
            f"name='{self.name}', status='{self.status}')>"
        )


# ============================================================================
# MESSAGE MODEL
# ============================================================================


class Message(Base):
    """
    Message model for inter-agent communication.

    Represents messages exchanged between agents in the system.
    Includes delivery tracking, retry logic, and callback support
    for asynchronous message processing.

    Attributes:
        id: Auto-incrementing primary key
        message_id: Unique identifier for the message
        from_agent_id: ID of the sending agent
        to_agent_id: ID of the receiving agent
        action: Action or command to execute
        payload: JSON payload containing message data
        status: Message delivery status (pending, delivered, failed, expired)
        delivery_attempts: Number of delivery attempts made
        max_retries: Maximum number of retry attempts
        callback_url: URL to call after message processing
        response: JSON response from message processing
        timeout_seconds: Timeout for message processing in seconds
        created_at: Timestamp of message creation
        delivered_at: Timestamp of successful delivery
        failed_at: Timestamp of failure (if applicable)

    Indexes:
        - to_agent_id (for querying messages by recipient)
        - status (for filtering by delivery status)
        - created_at (for temporal queries and cleanup)

    Example:
        >>> message = Message(
        ...     message_id="msg-abc-123",
        ...     from_agent_id="agent-001",
        ...     to_agent_id="agent-002",
        ...     action="process_data",
        ...     payload={"data": "example", "priority": "high"},
        ...     timeout_seconds=300,
        ...     max_retries=3
        ... )
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Unique identifier
    message_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Unique identifier for the message",
    )

    # Agent references
    from_agent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="ID of the sending agent",
    )

    to_agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the receiving agent",
    )

    # Message content
    action: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Action or command to execute",
    )

    payload: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON payload containing message data",
    )

    # Delivery status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="Message status: pending, delivered, failed, expired",
    )

    delivery_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of delivery attempts made",
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
        comment="Maximum number of retry attempts",
    )

    # Callback and response
    callback_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="URL to call after message processing",
    )

    response: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON response from message processing",
    )

    # Timeout
    timeout_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Timeout for message processing in seconds",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp of message creation",
    )

    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of successful delivery",
    )

    failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of failure",
    )

    def __repr__(self) -> str:
        """String representation of Message."""
        return (
            f"<Message(id={self.id}, message_id='{self.message_id}', "
            f"from='{self.from_agent_id}', to='{self.to_agent_id}', "
            f"status='{self.status}')>"
        )


# ============================================================================
# CAPABILITY MODEL
# ============================================================================


class Capability(Base):
    """
    Capability model representing agent capabilities and features.

    Defines the actions and operations that an agent can perform.
    Includes capability metadata, performance metrics, and access control
    for capability discovery and usage tracking.

    Attributes:
        id: Auto-incrementing primary key
        agent_id: ID of the agent that provides this capability
        capability_name: Name of the capability (e.g., "text_analysis")
        category: Category for capability grouping (e.g., "nlp", "vision")
        description: Detailed description of capability functionality
        parameters: JSON schema defining input parameters
        output_schema: JSON schema defining output format
        cost_per_call: Cost per capability invocation (for billing)
        avg_latency_ms: Average latency in milliseconds
        success_rate: Success rate as decimal (0.0 to 1.0)
        is_public: Whether capability is publicly accessible
        deprecated: Whether capability is deprecated
        last_used: Timestamp of last capability usage

    Indexes:
        - agent_id (for querying capabilities by agent)
        - capability_name (for capability lookup)
        - Composite index on (agent_id, capability_name) for uniqueness

    Example:
        >>> capability = Capability(
        ...     agent_id="agent-123",
        ...     capability_name="sentiment_analysis",
        ...     category="nlp",
        ...     description="Analyze text sentiment",
        ...     parameters={"text": "string", "language": "string"},
        ...     output_schema={"sentiment": "string", "score": "float"},
        ...     cost_per_call=0.001,
        ...     is_public=True
        ... )
    """

    __tablename__ = "capabilities"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Agent reference
    agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the agent that provides this capability",
    )

    # Capability identification
    capability_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Name of the capability",
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Category for grouping (nlp, vision, data, etc.)",
    )

    # Description and schemas
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of capability functionality",
    )

    parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON schema defining input parameters",
    )

    output_schema: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON schema defining output format",
    )

    # Performance and cost metrics
    cost_per_call: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Cost per capability invocation for billing",
    )

    avg_latency_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Average latency in milliseconds",
    )

    success_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Success rate as decimal (0.0 to 1.0)",
    )

    # Access control and lifecycle
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether capability is publicly accessible",
    )

    deprecated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether capability is deprecated",
    )

    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last capability usage",
    )

    # Composite index for uniqueness
    __table_args__ = (
        Index(
            "idx_agent_capability",
            "agent_id",
            "capability_name",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        """String representation of Capability."""
        return (
            f"<Capability(id={self.id}, agent_id='{self.agent_id}', "
            f"name='{self.capability_name}', category='{self.category}')>"
        )


# ============================================================================
# MEMORY MODEL
# ============================================================================


class Memory(Base):
    """
    Memory model for agent memory and context storage.

    Stores agent memories, context, and conversation history with support
    for versioning, tagging, and access control. Memories can be shared
    across agents or kept private.

    Attributes:
        id: Auto-incrementing primary key
        context_id: Unique identifier for the memory context
        agent_id: ID of the agent that owns this memory
        conversation_id: ID of the conversation this memory belongs to
        content: JSON content of the memory
        memory_type: Type of memory (episodic, semantic, procedural, etc.)
        tags: JSON array of tags for categorization and search
        visibility: Visibility level (all, organization, private)
        readable_by: JSON array of agent IDs that can read this memory
        version: Version number of the memory
        previous_version_id: ID of the previous version (for versioning)
        created_at: Timestamp of memory creation
        expires_at: Optional expiration timestamp for temporary memories

    Indexes:
        - context_id (unique)
        - agent_id (for querying memories by agent)
        - conversation_id (for querying by conversation)
        - created_at (for temporal queries)
        - expires_at (for cleanup of expired memories)

    Example:
        >>> memory = Memory(
        ...     context_id="ctx-abc-123",
        ...     agent_id="agent-001",
        ...     conversation_id="conv-xyz-456",
        ...     content={"text": "User prefers dark mode", "preference": "dark"},
        ...     memory_type="preference",
        ...     tags=["ui", "preference", "user-settings"],
        ...     visibility="all",
        ...     version=1
        ... )
    """

    __tablename__ = "memories"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Unique identifier
    context_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique identifier for the memory context",
    )

    # Agent and conversation references
    agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the agent that owns this memory",
    )

    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID of the conversation this memory belongs to",
    )

    # Memory content
    content: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON content of the memory",
    )

    memory_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Type of memory (episodic, semantic, procedural, etc.)",
    )

    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON array of tags for categorization",
    )

    # Access control
    visibility: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="all",
        server_default="all",
        comment="Visibility level: all, organization, private",
    )

    readable_by: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON array of agent IDs that can read this memory",
    )

    # Versioning
    version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Version number of the memory",
    )

    previous_version_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID of the previous version",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp of memory creation",
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Optional expiration timestamp for temporary memories",
    )

    def __repr__(self) -> str:
        """String representation of Memory."""
        return (
            f"<Memory(id={self.id}, context_id='{self.context_id}', "
            f"agent_id='{self.agent_id}', memory_type='{self.memory_type}')>"
        )


# ============================================================================
# COST MODEL
# ============================================================================


class Cost(Base):
    """
    Cost model for tracking expenses and billing records.

    Records costs associated with agent operations, API calls, and resource
    usage. Supports multiple currencies and billing period tracking for
    financial reporting and cost analysis.

    Attributes:
        id: Auto-incrementing primary key
        cost_type: Type of cost (api_call, compute, storage, bandwidth, etc.)
        agent_id: ID of the agent associated with this cost
        amount: Cost amount
        currency: Currency code (USD, EUR, etc.)
        request_id: Optional request ID for tracking specific requests
        message_id: Optional message ID if cost is associated with a message
        created_at: Timestamp when the cost was incurred
        billing_period: Billing period identifier (e.g., "2024-01")

    Indexes:
        - agent_id (for querying costs by agent)
        - cost_type (for filtering by cost type)
        - created_at (for temporal queries)
        - billing_period (for billing period queries)
        - message_id (for linking to messages)

    Example:
        >>> cost = Cost(
        ...     cost_type="api_call",
        ...     agent_id="agent-001",
        ...     amount=0.001,
        ...     currency="USD",
        ...     request_id="req-123",
        ...     billing_period="2024-01"
        ... )
    """

    __tablename__ = "costs"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Cost details
    cost_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of cost (api_call, compute, storage, bandwidth, etc.)",
    )

    agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the agent associated with this cost",
    )

    amount: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Cost amount",
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
        server_default="USD",
        comment="Currency code (USD, EUR, etc.)",
    )

    # References
    request_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional request ID for tracking specific requests",
    )

    message_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Optional message ID if cost is associated with a message",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when the cost was incurred",
    )

    billing_period: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Billing period identifier (e.g., 2024-01)",
    )

    def __repr__(self) -> str:
        """String representation of Cost."""
        return (
            f"<Cost(id={self.id}, cost_type='{self.cost_type}', "
            f"agent_id='{self.agent_id}', amount={self.amount} {self.currency})>"
        )


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================


class AuditLog(Base):
    """
    Audit log model for tracking system events and changes.

    Provides comprehensive audit trail for security, compliance, and debugging.
    Records all significant events, changes, and actions performed in the system
    with actor information and request context.

    Attributes:
        id: Auto-incrementing primary key
        event_id: Unique identifier for the audit event
        event_type: Type of event (create, update, delete, access, etc.)
        actor_id: ID of the user or agent that performed the action
        resource_type: Type of resource affected (agent, message, capability, etc.)
        resource_id: ID of the resource that was affected
        action: Description of the action performed
        changes: JSON object containing before/after state or change details
        ip_address: IP address of the request origin
        user_agent: User agent string from the request
        request_id: Request ID for correlating related events
        created_at: Timestamp of the event (immutable)

    Indexes:
        - event_id (unique)
        - event_type (for filtering by event type)
        - actor_id (for querying actions by actor)
        - resource_type and resource_id (for querying by resource)
        - created_at (for temporal queries)
        - request_id (for correlating related events)

    Example:
        >>> audit_log = AuditLog(
        ...     event_id="evt-abc-123",
        ...     event_type="update",
        ...     actor_id="user-456",
        ...     resource_type="agent",
        ...     resource_id="agent-001",
        ...     action="Updated agent status",
        ...     changes={"status": {"old": "inactive", "new": "active"}},
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0...",
        ...     request_id="req-789"
        ... )
    """

    __tablename__ = "audit_logs"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Unique identifier
    event_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique identifier for the audit event",
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of event (create, update, delete, access, etc.)",
    )

    actor_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID of the user or agent that performed the action",
    )

    # Resource information
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Type of resource affected (agent, message, capability, etc.)",
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID of the resource that was affected",
    )

    action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the action performed",
    )

    changes: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON object containing before/after state or change details",
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address of the request origin (supports IPv6)",
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent string from the request",
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Request ID for correlating related events",
    )

    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp of the event (immutable)",
    )

    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"<AuditLog(id={self.id}, event_id='{self.event_id}', "
            f"event_type='{self.event_type}', actor_id='{self.actor_id}', "
            f"resource_type='{self.resource_type}')>"
        )


# ============================================================================
# CONNECTION MODEL
# ============================================================================


class Connection(Base):
    """
    Connection model for tracking agent relationships and connections.

    Represents connections between agents, tracking communication patterns,
    connection types, and usage frequency. Supports both active and inactive
    connections for historical analysis.

    Attributes:
        id: Auto-incrementing primary key
        source_agent_id: ID of the source agent
        target_agent_id: ID of the target agent
        connection_type: Type of connection (direct, indirect, broadcast, etc.)
        frequency: Frequency of communication (high, medium, low, or numeric)
        is_active: Whether the connection is currently active
        created_at: Timestamp when the connection was established
        last_used: Timestamp of last communication through this connection

    Constraints:
        - UNIQUE constraint on (source_agent_id, target_agent_id)

    Indexes:
        - source_agent_id (for querying connections from an agent)
        - target_agent_id (for querying connections to an agent)
        - is_active (for filtering active connections)
        - last_used (for finding recently used connections)
        - Composite unique index on (source_agent_id, target_agent_id)

    Example:
        >>> connection = Connection(
        ...     source_agent_id="agent-001",
        ...     target_agent_id="agent-002",
        ...     connection_type="direct",
        ...     frequency="high",
        ...     is_active=True
        ... )
    """

    __tablename__ = "connections"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Agent references
    source_agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the source agent",
    )

    target_agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the target agent",
    )

    # Connection details
    connection_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Type of connection (direct, indirect, broadcast, etc.)",
    )

    frequency: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Frequency of communication (high, medium, low, or numeric)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Whether the connection is currently active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the connection was established",
    )

    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp of last communication through this connection",
    )

    # Unique constraint on source + target
    __table_args__ = (
        UniqueConstraint(
            "source_agent_id",
            "target_agent_id",
            name="uq_connection_source_target",
        ),
        Index(
            "idx_connection_source_target",
            "source_agent_id",
            "target_agent_id",
        ),
    )

    def __repr__(self) -> str:
        """String representation of Connection."""
        return (
            f"<Connection(id={self.id}, source='{self.source_agent_id}', "
            f"target='{self.target_agent_id}', type='{self.connection_type}', "
            f"active={self.is_active})>"
        )


# ============================================================================
# MODEL EXPORTS
# ============================================================================

# ============================================================================
# MEMORY VECTOR MODEL
# ============================================================================


class MemoryVector(Base):
    """
    Memory Vector model for tracking embedding metadata.

    Stores metadata about memory embeddings stored in Qdrant,
    including embedding status, dimensions, and version tracking.

    Attributes:
        id: Auto-incrementing primary key
        context_id: Foreign key to Memory context_id
        embedding_dimension: Dimension of the embedding vector
        embedding_model: Model used to generate embedding
        is_indexed: Whether the vector is indexed in Qdrant
        indexed_at: Timestamp when vector was indexed
        created_at: Timestamp when vector metadata was created
        updated_at: Timestamp of last update
    """

    __tablename__ = "memory_vectors"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Reference to memory
    context_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Memory context_id (foreign key to memories.context_id)",
    )

    # Embedding metadata
    embedding_dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Dimension of embedding vector (e.g., 1536)",
    )

    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Model used to generate embedding",
    )

    # Indexing status
    is_indexed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Whether the vector is indexed in Qdrant",
    )

    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when vector was indexed in Qdrant",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when vector metadata was created",
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        server_default=func.now(),
        comment="Timestamp of last update",
    )

    def __repr__(self) -> str:
        """String representation of MemoryVector."""
        return (
            f"<MemoryVector(id={self.id}, context_id='{self.context_id}', "
            f"dimension={self.embedding_dimension}, indexed={self.is_indexed})>"
        )


# ============================================================================
# SEARCH CACHE MODEL
# ============================================================================


class SearchCache(Base):
    """
    Search cache model for caching search results with TTL.

    Caches semantic search results to improve performance for repeated queries.
    Supports time-to-live (TTL) for cache expiration.

    Attributes:
        id: Auto-incrementing primary key
        cache_key: Unique cache key (hash of query + filters)
        query_text: Original search query text
        results: JSON array of search result IDs and scores
        result_count: Number of results cached
        ttl_seconds: Time-to-live in seconds
        expires_at: Timestamp when cache expires
        created_at: Timestamp when cache was created
    """

    __tablename__ = "search_cache"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Cache key (hash of query + filters)
    cache_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique cache key (hash of query + filters)",
    )

    # Query information
    query_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original search query text",
    )

    # Cached results
    results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON array of search results (context_ids and scores)",
    )

    result_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of results cached",
    )

    # TTL management
    ttl_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3600,
        server_default="3600",
        comment="Time-to-live in seconds",
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp when cache expires",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when cache was created",
    )

    def __repr__(self) -> str:
        """String representation of SearchCache."""
        return (
            f"<SearchCache(id={self.id}, cache_key='{self.cache_key[:20]}...', "
            f"results={self.result_count}, expires_at={self.expires_at})>"
        )


# ============================================================================
# SEARCH HISTORY MODEL
# ============================================================================


class SearchHistory(Base):
    """
    Search history model for tracking search queries and performance.

    Records search queries for analytics, debugging, and performance monitoring.
    Includes query metadata, result counts, and execution time.

    Attributes:
        id: Auto-incrementing primary key
        search_id: Unique identifier for the search
        agent_id: ID of the agent performing the search
        query_text: Search query text
        query_type: Type of search (semantic, keyword, hybrid)
        result_count: Number of results returned
        execution_time_ms: Query execution time in milliseconds
        filters: JSON object with search filters applied
        created_at: Timestamp when search was performed
    """

    __tablename__ = "search_history"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Unique search identifier
    search_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique identifier for the search",
    )

    # Agent information
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID of the agent performing the search",
    )

    # Query information
    query_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Search query text",
    )

    query_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of search: semantic, keyword, hybrid",
    )

    # Results
    result_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of results returned",
    )

    execution_time_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Query execution time in milliseconds",
    )

    # Filters
    filters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON object with search filters applied",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when search was performed",
    )

    def __repr__(self) -> str:
        """String representation of SearchHistory."""
        return (
            f"<SearchHistory(id={self.id}, search_id='{self.search_id}', "
            f"query_type='{self.query_type}', results={self.result_count}, "
            f"time={self.execution_time_ms}ms)>"
        )


# ============================================================================
# MODEL EXPORTS
# ============================================================================

# ============================================================================
# MEMORY VERSION MODEL
# ============================================================================


class MemoryVersion(Base):
    """
    Memory Version model for tracking memory changes over time.

    Stores complete snapshots of memory content at different points in time,
    allowing rollback, comparison, and audit trails. Supports version
    relationships and change tracking.

    Attributes:
        id: Auto-incrementing primary key
        context_id: Foreign key to Memory context_id
        version_number: Version number (auto-incrementing per memory)
        full_memory_text: Complete text content of the memory
        content: JSON content snapshot
        metadata: Version metadata (change type, author, etc.)
        change_type: Type of change (added, modified, deleted)
        author_id: ID of user/agent who created this version
        semantic_summary: Auto-generated summary of changes
        parent_version_id: ID of parent version (for version tree)
        is_archived: Whether version is archived to cheaper storage
        compressed: Whether content is compressed
        created_at: Timestamp when version was created
    """

    __tablename__ = "memory_versions"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Reference to memory
    context_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Memory context_id (foreign key to memories.context_id)",
    )

    # Version information
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Version number (auto-incrementing per memory)",
    )

    # Content snapshot
    full_memory_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Complete text content of the memory at this version",
    )

    content: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON content snapshot of the memory",
    )

    version_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Version metadata (tags, visibility, etc.)",
        name="metadata",  # Database column name
    )

    # Change tracking
    change_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="modified",
        server_default="modified",
        index=True,
        comment="Type of change: added, modified, deleted",
    )

    author_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID of user/agent who created this version",
    )

    semantic_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Auto-generated summary of changes in this version",
    )

    parent_version_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="ID of parent version (for version tree)",
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Whether version is archived to cheaper storage",
    )

    compressed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether content is compressed",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when version was created",
    )

    # Composite unique constraint
    __table_args__ = (
        Index(
            "idx_memory_version",
            "context_id",
            "version_number",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        """String representation of MemoryVersion."""
        return (
            f"<MemoryVersion(id={self.id}, context_id='{self.context_id}', "
            f"version={self.version_number}, change_type='{self.change_type}')>"
        )


# ============================================================================
# MODEL EXPORTS
# ============================================================================

# ============================================================================
# CHAT MESSAGE MODEL
# ============================================================================


class ChatMessage(Base):
    """
    Chat Message model for storing chat conversation messages.

    Stores user and assistant messages in chat conversations with
    links to agents and memories used in responses.

    Attributes:
        id: Auto-incrementing primary key
        conversation_id: Conversation ID (groups related messages)
        agent_id: Agent ID
        role: Message role (user, assistant, system)
        content: Message content
        used_memories: JSON array of memory context_ids used
        metadata: Additional metadata (token usage, model, etc.)
        created_at: Timestamp when message was created
    """

    __tablename__ = "chat_messages"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
    )

    # Conversation and agent
    conversation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Conversation ID (groups related messages)",
    )

    agent_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Agent ID",
    )

    # Message content
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Message role: user, assistant, system",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message content",
    )

    # Metadata
    used_memories: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="List of memory context_ids used in this message",
    )

    message_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional metadata (token usage, model, etc.)",
        name="metadata",  # Database column name
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when message was created",
    )

    def __repr__(self) -> str:
        """String representation of ChatMessage."""
        return (
            f"<ChatMessage(id={self.id}, conversation_id='{self.conversation_id}', "
            f"role='{self.role}', agent_id='{self.agent_id}')>"
        )


# ============================================================================
# MODEL EXPORTS
# ============================================================================

__all__ = [
    "Agent",
    "Message",
    "Capability",
    "Memory",
    "Cost",
    "AuditLog",
    "Connection",
    "MemoryVector",
    "SearchCache",
    "SearchHistory",
    "MemoryVersion",
    "ChatMessage",
]
