"""
Agent Service

Business logic layer for agent management operations including registration,
retrieval, listing, and status updates.

This service handles:
- Agent registration with API token and DID generation
- Agent retrieval and validation
- Paginated agent listings with filtering
- Agent status updates and heartbeat tracking
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.agents import AgentRegisterRequest
from src.gml.core.security import generate_api_key, generate_did
from src.gml.db.models import Agent
from src.gml.services.exceptions import (
    AgentAlreadyExistsError,
    AgentNotFoundError,
    InvalidAgentStatusError,
)

logger = logging.getLogger(__name__)

# Valid agent statuses
VALID_STATUSES = ["active", "inactive", "error", "maintenance"]


class AgentService:
    """
    Service class for agent management operations.

    Provides business logic for agent registration, retrieval, listing,
    and status management with proper error handling and validation.
    """

    @staticmethod
    async def register_agent(
        db: AsyncSession, request: AgentRegisterRequest
    ) -> Dict[str, str]:
        """
        Register a new agent in the system.

        Creates a new agent with:
        - Unique agent ID validation
        - Generated API token for authentication
        - Generated DID (Decentralized Identifier) and public key
        - Database persistence

        Args:
            db: Async database session
            request: Agent registration request with agent details

        Returns:
            Dictionary containing:
                - agent_id: The registered agent ID
                - api_token: Generated API authentication token
                - public_key: Generated public key in PEM format

        Raises:
            AgentAlreadyExistsError: If agent with the same agent_id already exists
            Exception: For database or cryptographic errors

        Example:
            >>> from src.gml.api.schemas.agents import AgentRegisterRequest
            >>> request = AgentRegisterRequest(
            ...     agent_id="data-processor-001",
            ...     name="Data Processor",
            ...     capabilities=["file_processing"]
            ... )
            >>> result = await AgentService.register_agent(db, request)
            >>> print(result["agent_id"])
            'data-processor-001'
        """
        try:
            # Check if agent already exists
            existing_agent = await AgentService.get_agent(db, request.agent_id, raise_if_not_found=False)
            if existing_agent:
                raise AgentAlreadyExistsError(request.agent_id)

            # Generate API token
            api_token = generate_api_key()
            logger.debug(f"Generated API token for agent: {request.agent_id}")

            # Generate DID and public key pair
            did = generate_did(method="key")
            public_key_pem, _ = AgentService._generate_key_pair()
            logger.debug(f"Generated DID and public key for agent: {request.agent_id}")

            # Create agent in database
            agent = Agent(
                agent_id=request.agent_id,
                name=request.name,
                version=request.version,
                description=request.description,
                status="inactive",  # New agents start as inactive
                secret_token=api_token,  # Store the API token
                public_key=public_key_pem,
                created_at=datetime.now(timezone.utc),
            )

            db.add(agent)
            await db.commit()
            await db.refresh(agent)

            logger.info(f"Successfully registered agent: {request.agent_id}")

            return {
                "agent_id": agent.agent_id,
                "api_token": api_token,
                "public_key": public_key_pem,
            }

        except AgentAlreadyExistsError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to register agent {request.agent_id}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def get_agent(
        db: AsyncSession, agent_id: str, raise_if_not_found: bool = True
    ) -> Optional[Agent]:
        """
        Retrieve an agent by ID.

        Queries the database for an agent with the given agent_id.

        Args:
            db: Async database session
            agent_id: Unique identifier of the agent
            raise_if_not_found: If True, raises AgentNotFoundError when agent not found.
                                If False, returns None.

        Returns:
            Agent model instance if found, None if not found and raise_if_not_found=False

        Raises:
            AgentNotFoundError: If agent not found and raise_if_not_found=True

        Example:
            >>> agent = await AgentService.get_agent(db, "data-processor-001")
            >>> print(agent.name)
            'Data Processor'
        """
        try:
            result = await db.execute(
                select(Agent).where(Agent.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()

            if agent is None and raise_if_not_found:
                raise AgentNotFoundError(agent_id)

            return agent

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve agent {agent_id}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def list_agents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List agents with pagination and optional status filtering.

        Retrieves a paginated list of agents, optionally filtered by status.
        Returns total count and pagination metadata.

        Args:
            db: Async database session
            skip: Number of agents to skip (for pagination)
            limit: Maximum number of agents to return (default: 100, max: 100)
            status: Optional status filter (active, inactive, error, maintenance)

        Returns:
            Dictionary containing:
                - agents: List of Agent model instances
                - total: Total number of agents matching the query
                - limit: Applied limit
                - offset: Applied offset (skip)
                - has_more: Boolean indicating if more results exist

        Raises:
            InvalidAgentStatusError: If invalid status is provided
            Exception: For database errors

        Example:
            >>> result = await AgentService.list_agents(db, skip=0, limit=10, status="active")
            >>> print(f"Found {result['total']} active agents")
            >>> for agent in result['agents']:
            ...     print(agent.agent_id)
        """
        try:
            # Validate status if provided
            if status is not None and status not in VALID_STATUSES:
                raise InvalidAgentStatusError(status, VALID_STATUSES)

            # Build query
            query = select(Agent)

            # Apply status filter if provided
            if status is not None:
                query = query.where(Agent.status == status)

            # Get total count
            count_query = select(func.count(Agent.id))
            if status is not None:
                count_query = count_query.where(Agent.status == status)
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            query = query.offset(skip).limit(min(limit, 100))  # Cap at 100
            query = query.order_by(Agent.created_at.desc())

            # Execute query
            result = await db.execute(query)
            agents = result.scalars().all()

            has_more = (skip + len(agents)) < total

            logger.debug(
                f"Listed {len(agents)} agents (skip={skip}, limit={limit}, status={status})"
            )

            return {
                "agents": list(agents),
                "total": total,
                "limit": min(limit, 100),
                "offset": skip,
                "has_more": has_more,
            }

        except InvalidAgentStatusError:
            raise
        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def update_agent_status(
        db: AsyncSession, agent_id: str, new_status: str
    ) -> Agent:
        """
        Update agent status and heartbeat timestamp.

        Updates the agent's status and sets the last_heartbeat timestamp
        to the current time. Validates the status before updating.

        Args:
            db: Async database session
            agent_id: Unique identifier of the agent
            new_status: New status value (active, inactive, error, maintenance)

        Returns:
            Updated Agent model instance

        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStatusError: If invalid status is provided
            Exception: For database errors

        Example:
            >>> agent = await AgentService.update_agent_status(db, "agent-001", "active")
            >>> print(agent.status)
            'active'
            >>> print(agent.last_heartbeat)
            2024-01-15 10:30:00+00:00
        """
        try:
            # Validate status
            if new_status not in VALID_STATUSES:
                raise InvalidAgentStatusError(new_status, VALID_STATUSES)

            # Get agent
            agent = await AgentService.get_agent(db, agent_id)
            if agent is None:
                raise AgentNotFoundError(agent_id)

            # Update status and heartbeat
            agent.status = new_status
            agent.last_heartbeat = datetime.now(timezone.utc)
            agent.updated_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(agent)

            logger.info(f"Updated agent {agent_id} status to {new_status}")

            return agent

        except (AgentNotFoundError, InvalidAgentStatusError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to update agent {agent_id} status: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    def _generate_key_pair() -> tuple[str, str]:
        """
        Generate an RSA key pair for agent authentication.

        Creates a 2048-bit RSA key pair and returns both public and private
        keys in PEM format. The private key should be securely stored by the agent.

        Returns:
            Tuple of (public_key_pem, private_key_pem) strings

        Raises:
            Exception: If key generation fails

        Example:
            >>> public_key, private_key = AgentService._generate_key_pair()
            >>> isinstance(public_key, str)
            True
            >>> public_key.startswith("-----BEGIN PUBLIC KEY-----")
            True
        """
        try:
            # Generate 2048-bit RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Serialize private key
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")

            # Serialize public key
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

            return public_key_pem, private_key_pem

        except Exception as e:
            logger.error(f"Failed to generate key pair: {str(e)}", exc_info=True)
            raise

