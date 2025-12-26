"""
Memory API Schemas

Pydantic models for memory-related API endpoints including writing,
retrieval, semantic search, and vector embedding support.

These schemas provide:
- Request validation for writing memories
- Response serialization from database models
- Semantic search request/response handling
- Vector embedding dimension constants
- Type-safe data transfer objects
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


# ============================================================================
# VECTOR EMBEDDING DIMENSIONS
# ============================================================================

# Common embedding model dimensions for semantic search
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "text-embedding-3-mini": 1536,
}

# Default embedding dimension (OpenAI text-embedding-3-small)
DEFAULT_EMBEDDING_DIMENSION = 1536

# Supported embedding dimensions
SUPPORTED_EMBEDDING_DIMENSIONS = [1536, 3072, 384, 768, 1024]


# ============================================================================
# ENUMS
# ============================================================================


class MemoryType(str, Enum):
    """
    Memory type enumeration.

    Represents different types of memories stored by agents:
    - episodic: Event-based memories (what happened when)
    - semantic: Fact-based memories (what is known)
    - procedural: Skill-based memories (how to do things)
    """

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

    def __str__(self) -> str:
        """Return string representation of memory type."""
        return self.value


class MemoryVisibility(str, Enum):
    """
    Memory visibility level enumeration.

    Controls who can access a memory:
    - all: All agents can read
    - organization: Only agents in the same organization
    - private: Only the owning agent
    """

    ALL = "all"
    ORGANIZATION = "organization"
    PRIVATE = "private"

    def __str__(self) -> str:
        """Return string representation of visibility."""
        return self.value


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class MemoryWriteRequest(BaseModel):
    """
    Request schema for writing a new memory.

    Validates memory data including conversation context, content,
    memory type, visibility, and tags for semantic search.

    Attributes:
        conversation_id: ID of the conversation this memory belongs to
        content: JSON content of the memory (dict)
        memory_type: Type of memory (episodic, semantic, procedural)
        visibility: Visibility level (default: 'all')
        tags: List of tags for categorization and search

    Example:
        >>> request = MemoryWriteRequest(
        ...     conversation_id="conv-xyz-456",
        ...     content={"text": "User prefers dark mode", "preference": "dark"},
        ...     memory_type=MemoryType.SEMANTIC,
        ...     visibility=MemoryVisibility.ALL,
        ...     tags=["ui", "preference", "user-settings"]
        ... )
    """

    conversation_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="ID of the conversation this memory belongs to",
        examples=["conv-xyz-456", "conversation-001"],
    )

    content: Dict[str, Any] = Field(
        ...,
        description="JSON content of the memory (must be a dictionary)",
        examples=[
            {"text": "User prefers dark mode", "preference": "dark"},
            {"action": "login", "timestamp": "2024-01-15T10:30:00Z"},
        ],
    )

    memory_type: MemoryType = Field(
        ...,
        description="Type of memory (episodic, semantic, procedural)",
    )

    visibility: MemoryVisibility = Field(
        default=MemoryVisibility.ALL,
        description="Visibility level (all, organization, private)",
    )

    tags: List[str] = Field(
        default_factory=list,
        description="List of tags for categorization and search",
        examples=[["ui", "preference"], ["workflow", "automation"]],
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content structure.

        Ensures content is a non-empty dictionary suitable for JSON storage
        and vector embedding generation.

        Args:
            v: The content dictionary

        Returns:
            Validated content dictionary

        Raises:
            ValueError: If content is empty or invalid
        """
        if not isinstance(v, dict):
            raise ValueError("content must be a dictionary/JSON object")

        if not v:
            raise ValueError("content cannot be empty")

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """
        Validate tags list.

        Ensures tags are non-empty strings and removes duplicates.

        Args:
            v: List of tag strings

        Returns:
            Validated list of unique tags
        """
        if not v:
            return []

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in v:
            tag_clean = tag.strip()
            if tag_clean and tag_clean not in seen:
                seen.add(tag_clean)
                unique_tags.append(tag_clean)

        return unique_tags

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "conversation_id": "conv-xyz-456",
                "content": {
                    "text": "User prefers dark mode interface",
                    "preference": "dark",
                    "context": "UI settings",
                },
                "memory_type": "semantic",
                "visibility": "all",
                "tags": ["ui", "preference", "user-settings"],
            }
        },
    )


class MemorySearchRequest(BaseModel):
    """
    Request schema for semantic search of memories.

    Supports semantic search using vector embeddings with optional
    filtering by memory type and conversation ID.

    Attributes:
        query: Search query text (will be embedded for semantic search)
        memory_type: Optional filter by memory type
        conversation_id: Optional filter by conversation ID
        limit: Maximum number of results to return (default: 10, max: 100)

    Example:
        >>> request = MemorySearchRequest(
        ...     query="user interface preferences",
        ...     memory_type=MemoryType.SEMANTIC,
        ...     conversation_id="conv-xyz-456",
        ...     limit=20
        ... )
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text (will be embedded for semantic search)",
        examples=["user interface preferences", "how to login", "data processing workflow"],
    )

    memory_type: Optional[MemoryType] = Field(
        default=None,
        description="Optional filter by memory type",
    )

    conversation_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional filter by conversation ID",
        examples=["conv-xyz-456", "conversation-001"],
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return (1-100)",
        examples=[10, 20, 50],
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """
        Validate search query.

        Ensures query is non-empty and suitable for embedding.

        Args:
            v: The search query string

        Returns:
            Validated and trimmed query string

        Raises:
            ValueError: If query is empty after trimming
        """
        query_clean = v.strip()
        if not query_clean:
            raise ValueError("query cannot be empty")
        return query_clean

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "query": "user interface preferences",
                "memory_type": "semantic",
                "conversation_id": "conv-xyz-456",
                "limit": 10,
            }
        },
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class MemoryResponse(BaseModel):
    """
    Basic memory response schema.

    Contains essential memory information including context ID, agent ID,
    memory type, creation timestamp, version, and embedding dimensions
    for semantic search.

    Attributes:
        context_id: Unique identifier for the memory context
        agent_id: ID of the agent that owns this memory
        memory_type: Type of memory
        created_at: Timestamp when the memory was created
        version: Version number of the memory
        embedding_dimensions: Vector embedding dimensions (for semantic search)

    Example:
        >>> response = MemoryResponse(
        ...     context_id="ctx-abc-123",
        ...     agent_id="agent-001",
        ...     memory_type=MemoryType.SEMANTIC,
        ...     created_at=datetime.now(),
        ...     version=1,
        ...     embedding_dimensions=1536
        ... )
    """

    context_id: str = Field(..., description="Unique identifier for the memory context")
    agent_id: str = Field(..., description="ID of the agent that owns this memory")
    memory_type: Optional[MemoryType] = Field(
        default=None,
        description="Type of memory",
    )
    created_at: datetime = Field(..., description="Timestamp when the memory was created")
    version: Optional[int] = Field(
        default=None,
        ge=1,
        description="Version number of the memory",
    )
    embedding_dimensions: Optional[int] = Field(
        default=DEFAULT_EMBEDDING_DIMENSION,
        description="Vector embedding dimensions (for semantic search)",
        examples=[1536, 3072],
    )

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()

    @field_serializer("memory_type")
    def serialize_memory_type(self, value: MemoryType | None) -> str | None:
        """Serialize memory type enum to string."""
        return value.value if value else None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemorySearchResult(BaseModel):
    """
    Memory search result schema with similarity scoring.

    Represents a single memory result from semantic search with
    similarity score, content, and metadata.

    Attributes:
        context_id: Unique identifier for the memory context
        content: JSON content of the memory
        similarity_score: Cosine similarity score (0.0 to 1.0)
        created_by: ID of the agent that created this memory
        created_at: Timestamp when the memory was created

    Example:
        >>> result = MemorySearchResult(
        ...     context_id="ctx-abc-123",
        ...     content={"text": "User prefers dark mode", "preference": "dark"},
        ...     similarity_score=0.92,
        ...     created_by="agent-001",
        ...     created_at=datetime.now()
        ... )
    """

    context_id: str = Field(..., description="Unique identifier for the memory context")
    content: Dict[str, Any] = Field(..., description="JSON content of the memory")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0.0 to 1.0, higher is more similar)",
        examples=[0.92, 0.85, 0.78],
    )
    created_by: str = Field(
        ...,
        description="ID of the agent that created this memory",
        alias="agent_id",
    )
    created_at: datetime = Field(..., description="Timestamp when the memory was created")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat()

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both field name and alias
    )

