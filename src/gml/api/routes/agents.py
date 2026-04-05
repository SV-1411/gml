"""
Agent API Routes

FastAPI router for agent management using Supabase.
"""

import logging
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.gml.api.dependencies import get_db
from src.gml.api.schemas.agents import (
    AgentDetailResponse,
    AgentListResponse,
    AgentRegisterRequest,
    AgentResponse,
)
from src.gml.services.supabase_client import SupabaseDB
from src.gml.monitoring.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentStatusUpdate(BaseModel):
    """Request model for updating agent status."""
    status: str


async def get_agent_capabilities(db: SupabaseDB, agent_id: str) -> list[str]:
    """Get list of capability names for an agent."""
    capabilities = await db.select("capabilities", filters={"agent_id": agent_id})
    return [cap["capability_name"] for cap in capabilities]


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
)
async def register_agent(
    request: AgentRegisterRequest,
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Register a new agent with generated API token."""
    try:
        # Check if agent already exists
        existing = await db.select("agents", filters={"agent_id": request.agent_id}, limit=1)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent with ID '{request.agent_id}' already exists",
            )

        # Generate API token and public key
        import secrets
        api_token = f"gml_{secrets.token_urlsafe(32)}"
        public_key = secrets.token_urlsafe(64)

        # Create agent
        now = datetime.now(timezone.utc).isoformat()
        agents = await db.insert("agents", {
            "agent_id": request.agent_id,
            "name": request.name,
            "description": request.description,
            "version": request.version,
            "status": "inactive",
            "api_token": api_token,
            "public_key": public_key,
            "created_at": now,
            "updated_at": now,
        })

        # Add capabilities
        if request.capabilities:
            for cap in request.capabilities:
                await db.insert("capabilities", {
                    "agent_id": request.agent_id,
                    "capability_name": cap,
                    "created_at": now,
                })

        # Auto-increment agent registration metric
        metrics.increment_agents_registered()

        logger.info(f"Agent registered successfully: {request.agent_id}")

        return {
            "agent_id": request.agent_id,
            "api_token": api_token,
            "public_key": public_key,
        }

    except HTTPException:
        raise
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
)
async def get_agent(
    agent_id: str,
    db: SupabaseDB = Depends(get_db),
) -> AgentDetailResponse:
    """Get agent details by ID."""
    try:
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        
        if not agents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID '{agent_id}' not found",
            )

        agent = agents[0]
        capabilities = await get_agent_capabilities(db, agent_id)

        return AgentDetailResponse(
            agent_id=agent["agent_id"],
            name=agent["name"],
            status=agent["status"],
            api_token=None,  # Don't expose token in GET requests
            public_key=agent.get("public_key"),
            created_at=datetime.fromisoformat(agent["created_at"].replace("Z", "+00:00")) if agent.get("created_at") else None,
            version=agent.get("version"),
            description=agent.get("description"),
            last_heartbeat=datetime.fromisoformat(agent["last_heartbeat"].replace("Z", "+00:00")) if agent.get("last_heartbeat") else None,
            capabilities=capabilities,
        )

    except HTTPException:
        raise
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
)
async def update_agent_status(
    agent_id: str,
    status_update: AgentStatusUpdate,
    db: SupabaseDB = Depends(get_db),
) -> AgentDetailResponse:
    """Update agent status."""
    valid_statuses = ["active", "inactive", "error", "maintenance"]
    
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_update.status}'. Valid statuses: {', '.join(valid_statuses)}",
        )

    try:
        # Check if agent exists
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        
        if not agents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with ID '{agent_id}' not found",
            )

        # Update status
        now = datetime.now(timezone.utc).isoformat()
        await db.update("agents", {
            "status": status_update.status,
            "last_heartbeat": now,
            "updated_at": now,
        }, {"agent_id": agent_id})

        # Get updated agent
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        agent = agents[0]
        capabilities = await get_agent_capabilities(db, agent_id)

        logger.info(f"Agent {agent_id} status updated to {status_update.status}")

        return AgentDetailResponse(
            agent_id=agent["agent_id"],
            name=agent["name"],
            status=agent["status"],
            api_token=None,
            public_key=agent.get("public_key"),
            created_at=datetime.fromisoformat(agent["created_at"].replace("Z", "+00:00")) if agent.get("created_at") else None,
            version=agent.get("version"),
            description=agent.get("description"),
            last_heartbeat=datetime.fromisoformat(agent["last_heartbeat"].replace("Z", "+00:00")) if agent.get("last_heartbeat") else None,
            capabilities=capabilities,
        )

    except HTTPException:
        raise
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
)
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    organization: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: SupabaseDB = Depends(get_db),
) -> AgentListResponse:
    """List agents with pagination and filtering."""
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if organization:
            filters["organization"] = organization

        # Get total count
        total = await db.count("agents", filters if filters else None)

        # Get paginated agents
        agents = await db.select(
            "agents",
            filters=filters if filters else None,
            order="created_at desc",
            limit=min(limit, 100),
        )

        # Apply skip manually (Supabase client doesn't have offset)
        agents = agents[skip:skip + limit] if skip > 0 else agents[:limit]

        has_more = (skip + len(agents)) < total

        # Convert to response models
        agent_responses = [
            AgentResponse(
                agent_id=agent["agent_id"],
                name=agent["name"],
                status=agent["status"],
                api_token=None,
                public_key=agent.get("public_key"),
                created_at=datetime.fromisoformat(agent["created_at"].replace("Z", "+00:00")) if agent.get("created_at") else None,
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
)
async def initialize_agent(
    agent_id: str,
    conversation_id: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    max_tokens: int = Query(4000, ge=100, le=16000),
    strategy: str = Query("hybrid"),
    format_type: str = Query("narrative"),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Initialize agent with relevant memories."""
    start_time = time.time()

    try:
        # Verify agent exists
        agents = await db.select("agents", filters={"agent_id": agent_id}, limit=1)
        
        if not agents:
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
        query_hash = hashlib.md5(query.encode() if query else b"").hexdigest() if query else None
        cached_context = await cache_manager.get_cached_context(
            agent_id=agent_id,
            conversation_id=conversation_id,
            query_hash=query_hash,
        )

        if cached_context:
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
            formatted = formatter.format(
                memories=context["memories"],
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
