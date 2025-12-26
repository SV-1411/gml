"""
API Schemas Module

This module contains Pydantic models for request/response validation
and serialization for the GML Infrastructure API.

Schemas are organized by resource type:
- agents: Agent registration and response schemas
- messages: Message request/response schemas
- memory: Memory write/search schemas with semantic search support
- capabilities: Capability schemas (future)
"""

from src.gml.api.schemas.agents import (
    AgentDetailResponse,
    AgentListResponse,
    AgentRegisterRequest,
    AgentResponse,
)
from src.gml.api.schemas.messages import (
    MessageListResponse,
    MessageSendRequest,
    MessageStatus,
    MessageStatusResponse,
    MessageResponse,
)
from src.gml.api.schemas.memory import (
    DEFAULT_EMBEDDING_DIMENSION,
    EMBEDDING_DIMENSIONS,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryType,
    MemoryVisibility,
    MemoryWriteRequest,
    SUPPORTED_EMBEDDING_DIMENSIONS,
)

__all__ = [
    # Agent schemas
    "AgentRegisterRequest",
    "AgentResponse",
    "AgentDetailResponse",
    "AgentListResponse",
    # Message schemas
    "MessageSendRequest",
    "MessageResponse",
    "MessageStatusResponse",
    "MessageListResponse",
    "MessageStatus",
    # Memory schemas
    "MemoryWriteRequest",
    "MemoryResponse",
    "MemorySearchRequest",
    "MemorySearchResult",
    "MemoryType",
    "MemoryVisibility",
    # Vector embedding constants
    "EMBEDDING_DIMENSIONS",
    "DEFAULT_EMBEDDING_DIMENSION",
    "SUPPORTED_EMBEDDING_DIMENSIONS",
]

