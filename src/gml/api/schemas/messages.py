"""
Message API Schemas

Pydantic models for message-related API endpoints including sending,
response serialization, status tracking, and pagination.

These schemas provide:
- Request validation for sending messages between agents
- Response serialization from database models
- Status tracking with enum validation
- Pagination support for message listings
- Type-safe data transfer objects
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer, field_validator


# ============================================================================
# ENUMS
# ============================================================================


class MessageStatus(str, Enum):
    """
    Message delivery status enumeration.

    Represents the current state of a message in the delivery pipeline.
    """

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    TIMEOUT = "timeout"

    def __str__(self) -> str:
        """Return string representation of status."""
        return self.value


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class MessageSendRequest(BaseModel):
    """
    Request schema for sending a message to an agent.

    Validates message data including recipient, action, payload, and
    optional timeout and callback configuration.

    Attributes:
        to_agent_id: ID of the receiving agent
        action: Action or command to execute (optional)
        payload: JSON payload containing message data (optional)
        timeout_seconds: Timeout for message processing in seconds (default: 60)
        callback_url: Optional URL to call after message processing

    Example:
        >>> request = MessageSendRequest(
        ...     to_agent_id="agent-002",
        ...     action="process_data",
        ...     payload={"data": "example", "priority": "high"},
        ...     timeout_seconds=120,
        ...     callback_url="https://example.com/webhook"
        ... )
    """

    to_agent_id: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="ID of the receiving agent",
        examples=["agent-002", "data-processor-001"],
    )

    action: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Action or command to execute",
        examples=["process_data", "analyze_text", "generate_report"],
    )

    payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON payload containing message data",
        examples=[
            {"data": "example", "priority": "high"},
            {"text": "Hello world", "language": "en"},
        ],
    )

    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Timeout for message processing in seconds (1-3600)",
        examples=[60, 120, 300],
    )

    callback_url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional URL to call after message processing",
        examples=["https://example.com/webhook", "https://api.example.com/callback"],
    )

    @field_validator("to_agent_id")
    @classmethod
    def validate_agent_id_format(cls, v: str) -> str:
        """
        Validate agent ID format.

        Agent IDs must:
        - Be 3-255 characters long
        - Contain only alphanumeric characters, hyphens, and underscores
        - Not start or end with a hyphen or underscore

        Args:
            v: The agent_id value to validate

        Returns:
            Validated agent_id string

        Raises:
            ValueError: If agent_id format is invalid
        """
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$", v):
            raise ValueError(
                "to_agent_id must contain only alphanumeric characters, hyphens, and underscores. "
                "Must start and end with alphanumeric character."
            )

        # Check for consecutive hyphens or underscores
        if "--" in v or "__" in v or "-_" in v or "_-" in v:
            raise ValueError("to_agent_id cannot contain consecutive hyphens or underscores")

        return v

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Validate payload structure.

        Ensures payload is a valid JSON-serializable dictionary.
        Pydantic automatically handles JSON validation, but we can add
        custom validation here if needed.

        Args:
            v: The payload dictionary

        Returns:
            Validated payload dictionary
        """
        if v is not None and not isinstance(v, dict):
            raise ValueError("payload must be a dictionary/JSON object")
        return v

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "to_agent_id": "data-processor-001",
                "action": "process_data",
                "payload": {
                    "file_path": "/data/input.csv",
                    "format": "csv",
                    "options": {"delimiter": ",", "header": True},
                },
                "timeout_seconds": 120,
                "callback_url": "https://api.example.com/webhook",
            }
        },
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class MessageResponse(BaseModel):
    """
    Basic message response schema.

    Contains essential message information for quick status checks
    and message tracking.

    Attributes:
        message_id: Unique identifier for the message
        status: Current message delivery status
        created_at: Timestamp when the message was created
        estimated_delivery: Estimated delivery time (calculated from timeout)

    Example:
        >>> response = MessageResponse(
        ...     message_id="msg-abc-123",
        ...     status=MessageStatus.PENDING,
        ...     created_at=datetime.now(),
        ...     estimated_delivery=datetime.now()
        ... )
    """

    message_id: str = Field(..., description="Unique identifier for the message")
    status: MessageStatus = Field(..., description="Current message delivery status")
    created_at: datetime = Field(..., description="Timestamp when the message was created")
    estimated_delivery: Optional[datetime] = Field(
        default=None,
        description="Estimated delivery time based on timeout",
    )

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()

    @field_serializer("estimated_delivery")
    def serialize_estimated_delivery(self, value: datetime | None) -> str | None:
        """Serialize optional datetime to ISO format string."""
        return value.isoformat() if value else None

    @field_serializer("status")
    def serialize_status(self, value: MessageStatus) -> str:
        """Serialize status enum to string."""
        return value.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class MessageStatusResponse(BaseModel):
    """
    Detailed message status response schema.

    Extends MessageResponse with additional details including agent IDs,
    latency metrics, and response data.

    Attributes:
        message_id: Unique identifier for the message
        status: Current message delivery status
        created_at: Timestamp when the message was created
        estimated_delivery: Estimated delivery time
        from_agent_id: ID of the sending agent (if available)
        to_agent_id: ID of the receiving agent
        latency_ms: Message processing latency in milliseconds (if delivered)
        response: JSON response from message processing (if available)

    Example:
        >>> response = MessageStatusResponse(
        ...     message_id="msg-abc-123",
        ...     status=MessageStatus.DELIVERED,
        ...     from_agent_id="agent-001",
        ...     to_agent_id="agent-002",
        ...     latency_ms=150,
        ...     response={"result": "success", "data": "processed"}
        ... )
    """

    message_id: str = Field(..., description="Unique identifier for the message")
    status: MessageStatus = Field(..., description="Current message delivery status")
    created_at: datetime = Field(..., description="Timestamp when the message was created")
    estimated_delivery: Optional[datetime] = Field(
        default=None,
        description="Estimated delivery time based on timeout",
    )
    from_agent_id: Optional[str] = Field(
        default=None,
        description="ID of the sending agent",
    )
    to_agent_id: str = Field(..., description="ID of the receiving agent")
    latency_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Message processing latency in milliseconds (if delivered)",
    )
    response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON response from message processing",
    )

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()

    @field_serializer("estimated_delivery")
    def serialize_estimated_delivery(self, value: datetime | None) -> str | None:
        """Serialize optional datetime to ISO format string."""
        return value.isoformat() if value else None

    @field_serializer("status")
    def serialize_status(self, value: MessageStatus) -> str:
        """Serialize status enum to string."""
        return value.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class MessageListResponse(BaseModel):
    """
    Paginated list of messages response schema.

    Provides pagination metadata along with a list of message status responses.
    Supports offset-based pagination for message history queries.

    Attributes:
        messages: List of MessageStatusResponse objects
        total: Total number of messages matching the query
        limit: Maximum number of messages per page
        offset: Number of messages skipped (for offset-based pagination)
        has_more: Whether there are more messages beyond the current page

    Example:
        >>> response = MessageListResponse(
        ...     messages=[msg1, msg2, msg3],
        ...     total=50,
        ...     limit=10,
        ...     offset=0,
        ...     has_more=True
        ... )
    """

    messages: List[MessageStatusResponse] = Field(
        ...,
        description="List of message status responses for the current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of messages matching the query",
    )
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Maximum number of messages per page",
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Number of messages skipped (for offset-based pagination)",
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more messages beyond the current page",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "messages": [
                    {
                        "message_id": "msg-abc-123",
                        "status": "delivered",
                        "created_at": "2024-01-15T10:30:00Z",
                        "estimated_delivery": "2024-01-15T10:30:60Z",
                        "from_agent_id": "agent-001",
                        "to_agent_id": "agent-002",
                        "latency_ms": 150,
                        "response": {"result": "success"},
                    }
                ],
                "total": 50,
                "limit": 10,
                "offset": 0,
                "has_more": True,
            }
        },
    )

