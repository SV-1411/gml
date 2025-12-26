"""
Agent API Routes

FastAPI router for agent management endpoints including registration,
retrieval, and listing with proper error handling and status codes.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.agents import (
    AgentDetailResponse,
    AgentListResponse,
    AgentRegisterRequest,
    AgentResponse,
)
from src.gml.db.database import get_db
from src.gml.db.models import Agent, Capability, Memory
from src.gml.monitoring.metrics import metrics
from src.gml.services import AgentService, CostService
from src.gml.services.exceptions import (
    AgentAlreadyExistsError,
    AgentNotFoundError,
    InvalidAgentStatusError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentStatusUpdate(BaseModel):
    """Request model for updating agent status."""
    status: str


async def get_agent_capabilities(
    db: AsyncSession, agent_id: str
) -> list[str]:
    """
    Get list of capability names for an agent.

    Args:
        db: Database session
        agent_id: Agent ID

    Returns:
        List of capability names
    """
    result = await db.execute(
        select(Capability.capability_name).where(Capability.agent_id == agent_id)
    )
    capabilities = result.scalars().all()
    return list(capabilities)


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
    description="Register a new agent in the system and receive API credentials",
)
async def register_agent(
    request: AgentRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Register a new agent.

    Creates a new agent with:
    - Unique agent ID
    - Generated API token
    - Generated public key (DID)
    - Initial status: inactive

    Also records the agent registration cost.

    Args:
        request: Agent registration request with agent details
        db: Database session (dependency injection)

    Returns:
        Dictionary containing:
            - agent_id: Registered agent ID
            - api_token: API authentication token (only shown once)
            - public_key: Public key for authentication

    Raises:
        HTTPException 409: If agent with same agent_id already exists
        HTTPException 500: For server errors

    Example:
        POST /api/v1/agents/register
        {
            "agent_id": "data-processor-001",
            "name": "Data Processor",
            "version": "1.0.0",
            "capabilities": ["file_processing"]
        }

        Response 201:
        {
            "agent_id": "data-processor-001",
            "api_token": "gml_abc123...",
            "public_key": "-----BEGIN PUBLIC KEY-----..."
        }
    """
    try:
        # Register agent
        result = await AgentService.register_agent(db, request)

        # Record registration cost
        try:
            await CostService.record_cost(
                db=db,
                cost_type="agent_registration",
                agent_id=request.agent_id,
                amount=CostService.get_cost_for_operation("agent_registration"),
                request_id=f"register-{request.agent_id}",
            )
        except Exception as cost_error:
            # Log cost recording error but don't fail registration
            logger.warning(
                f"Failed to record cost for agent registration {request.agent_id}: {str(cost_error)}"
            )

        # Auto-increment agent registration metric
        metrics.increment_agents_registered()

        logger.info(f"Agent registered successfully: {request.agent_id}")

        return result

    except AgentAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with ID '{e.agent_id}' already exists",
        )
    except Exception as e:
        logger.error(f"Failed to register agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register agent. Please try again later.",
        )


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent details",
    description="Retrieve detailed information about a specific agent",
)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentDetailResponse:
    """
    Get agent details by ID.

    Retrieves comprehensive agent information including capabilities,
    version, description, and heartbeat status.

    Args:
        agent_id: Unique identifier of the agent
        db: Database session (dependency injection)

    Returns:
        AgentDetailResponse with full agent details

    Raises:
        HTTPException 404: If agent not found
        HTTPException 500: For server errors

    Example:
        GET /api/v1/agents/data-processor-001

        Response 200:
        {
            "agent_id": "data-processor-001",
            "name": "Data Processor",
            "status": "active",
            "version": "1.0.0",
            "description": "Processes data files",
            "capabilities": ["file_processing"],
            ...
        }
    """
    try:
        # Get agent
        agent = await AgentService.get_agent(db, agent_id)

        if agent is None:
            raise AgentNotFoundError(agent_id)

        # Get capabilities
        capabilities = await get_agent_capabilities(db, agent_id)

        # Build response
        response = AgentDetailResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            status=agent.status,
            api_token=None,  # Don't expose token in GET requests
            public_key=agent.public_key,
            created_at=agent.created_at,
            version=agent.version,
            description=agent.description,
            last_heartbeat=agent.last_heartbeat,
            capabilities=capabilities,
        )

        return response

    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{e.agent_id}' not found",
        )
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent. Please try again later.",
        )


@router.patch(
    "/{agent_id}/status",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update agent status",
    description="Update agent status (active, inactive, error, maintenance)",
)
async def update_agent_status(
    agent_id: str,
    status_update: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> AgentDetailResponse:
    """
    Update agent status.

    Updates the agent's status and sets the last_heartbeat timestamp.
    Valid statuses: active, inactive, error, maintenance

    Args:
        agent_id: Unique identifier of the agent
        status_update: Status update request with new status
        db: Database session (dependency injection)

    Returns:
        AgentDetailResponse with updated agent details

    Raises:
        HTTPException 400: If invalid status provided
        HTTPException 404: If agent not found
        HTTPException 500: For server errors

    Example:
        PATCH /api/v1/agents/data-processor-001/status
        {
            "status": "active"
        }

        Response 200:
        {
            "agent_id": "data-processor-001",
            "status": "active",
            "last_heartbeat": "2024-01-15T10:30:00Z",
            ...
        }
    """
    try:
        # Update agent status
        agent = await AgentService.update_agent_status(
            db, agent_id, status_update.status
        )

        # Get capabilities
        capabilities = await get_agent_capabilities(db, agent_id)

        # Build response
        response = AgentDetailResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            status=agent.status,
            api_token=None,
            public_key=agent.public_key,
            created_at=agent.created_at,
            version=agent.version,
            description=agent.description,
            last_heartbeat=agent.last_heartbeat,
            capabilities=capabilities,
        )

        logger.info(f"Agent {agent_id} status updated to {status_update.status}")

        return response

    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{e.agent_id}' not found",
        )
    except InvalidAgentStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{e.status}'. Valid statuses: {', '.join(e.valid_statuses)}",
        )
    except Exception as e:
        logger.error(f"Failed to update agent status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent status. Please try again later.",
        )


@router.get(
    "",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List agents",
    description="Get paginated list of agents with optional filtering",
)
async def list_agents(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by agent status (active, inactive, error, maintenance)",
    ),
    organization: Optional[str] = Query(
        None,
        description="Filter by organization identifier",
    ),
    skip: int = Query(0, ge=0, description="Number of agents to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of agents to return"),
    db: AsyncSession = Depends(get_db),
) -> AgentListResponse:
    """
    List agents with pagination and filtering.

    Retrieves a paginated list of agents with optional filtering by
    status and organization. Results are ordered by creation date (newest first).

    Args:
        status_filter: Optional status filter (active, inactive, error, maintenance)
        organization: Optional organization filter
        skip: Number of agents to skip (for pagination)
        limit: Maximum number of agents to return (1-100)
        db: Database session (dependency injection)

    Returns:
        AgentListResponse with paginated agent list and metadata

    Raises:
        HTTPException 400: If invalid status filter provided
        HTTPException 500: For server errors

    Example:
        GET /api/v1/agents?status=active&skip=0&limit=10

        Response 200:
        {
            "agents": [...],
            "total": 25,
            "limit": 10,
            "offset": 0,
            "has_more": true
        }
    """
    try:
        # Build query with filters
        query = select(Agent)

        # Apply status filter if provided
        if status_filter:
            query = query.where(Agent.status == status_filter)

        # Apply organization filter if provided
        if organization:
            query = query.where(Agent.organization == organization)

        # Get total count
        count_query = select(func.count(Agent.id))
        if status_filter:
            count_query = count_query.where(Agent.status == status_filter)
        if organization:
            count_query = count_query.where(Agent.organization == organization)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(min(limit, 100))
        query = query.order_by(Agent.created_at.desc())

        # Execute query
        result = await db.execute(query)
        agents = result.scalars().all()

        has_more = (skip + len(agents)) < total

        # Convert to response models (without api_token for security)
        agent_responses = [
            AgentResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                status=agent.status,
                api_token=None,  # Don't expose tokens in list
                public_key=agent.public_key,
                created_at=agent.created_at,
            )
            for agent in agents
        ]

        return AgentListResponse(
            agents=agent_responses,
            total=total,
            limit=min(limit, 100),
            offset=skip,
            has_more=has_more,
        )

    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents. Please try again later.",
        )


@router.post(
    "/{agent_id}/initialize",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Initialize agent with memories",
    description="Load relevant memories and build context window for agent",
)
async def initialize_agent(
    agent_id: str,
    conversation_id: Optional[str] = Query(None, description="Conversation ID for context"),
    query: Optional[str] = Query(None, description="Query string for semantic search"),
    max_tokens: int = Query(4000, ge=100, le=16000, description="Maximum tokens for context"),
    strategy: str = Query("hybrid", description="Initialization strategy (semantic, keyword, hybrid, all)"),
    format_type: str = Query("narrative", description="Context format (narrative, qa, structured)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initialize agent with relevant memories.

    Loads memories using specified strategy, builds optimized context window,
    caches results, and returns initialized agent state.

    Args:
        agent_id: Agent ID to initialize
        conversation_id: Optional conversation ID
        query: Optional query for semantic search
        max_tokens: Maximum tokens for context window
        strategy: Initialization strategy
        format_type: Context format type
        db: Database session

    Returns:
        Dictionary with:
        - agent_id: Agent ID
        - initialized_at: Initialization timestamp
        - memories_loaded: Number of memories loaded
        - token_count: Token count of context
        - formatted_context: Formatted context string
        - sources: List of memory source IDs
        - metadata: Additional metadata
        - execution_time_ms: Execution time in milliseconds

    Raises:
        HTTPException 404: If agent not found
        HTTPException 500: For server errors
    """
    import time

    start_time = time.time()

    try:
        # Verify agent exists
        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found",
            )

        # Import services
        from src.gml.services.memory_context_builder import get_context_builder
        from src.gml.services.memory_cache_manager import get_cache_manager
        from src.gml.services.context_formatter import get_context_formatter
        from src.gml.services.agent_state_manager import get_state_manager

        cache_manager = await get_cache_manager()
        context_builder = await get_context_builder()
        formatter = await get_context_formatter()
        state_manager = await get_state_manager()

        # Check cache first
        import hashlib
        query_hash = hashlib.md5(query.encode() if query else b"").hexdigest() if query else None
        cached_context = await cache_manager.get_cached_context(
            agent_id=agent_id,
            conversation_id=conversation_id,
            query_hash=query_hash,
        )

        if cached_context:
            # Use cached context
            context = cached_context
            logger.debug(f"Using cached context for agent {agent_id}")
        else:
            # Build context
            context = await context_builder.build_context(
                agent_id=agent_id,
                conversation_id=conversation_id,
                query=query,
                max_tokens=max_tokens,
                strategy=strategy,
                db=db,
            )

            # Format context
            memories = [
                Memory(
                    context_id=m["context_id"],
                    content=m["content"],
                    memory_type=m["memory_type"],
                    created_at=datetime.fromisoformat(m["created_at"]),
                )
                for m in context["memories"]
            ]
            formatted = formatter.format(
                memories=memories,
                format_type=format_type,
                include_metadata=True,
            )
            context["formatted_context"] = formatted

            # Cache context
            await cache_manager.cache_context(
                agent_id=agent_id,
                context=context,
                conversation_id=conversation_id,
                query_hash=query_hash,
            )

        # Initialize state
        state = await state_manager.initialize_agent(
            agent_id=agent_id,
            conversation_id=conversation_id,
            context=context,
            db=db,
        )

        execution_time = (time.time() - start_time) * 1000

        # Get cache stats
        cache_stats = cache_manager.get_cache_stats()

        logger.info(
            f"Agent {agent_id} initialized in {execution_time:.2f}ms "
            f"with {state['memories_loaded']} memories"
        )

        return {
            "agent_id": agent_id,
            "initialized_at": state["initialized_at"],
            "memories_loaded": state["memories_loaded"],
            "token_count": state["token_count"],
            "formatted_context": context.get("formatted_context", ""),
            "sources": state["sources"],
            "metadata": {
                **state["metadata"],
                "cache_stats": cache_stats,
            },
            "execution_time_ms": execution_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize agent: {str(e)}",
        )
