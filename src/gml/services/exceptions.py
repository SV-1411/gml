"""
Service Layer Exceptions

Custom exceptions for service layer operations.
These exceptions provide clear error handling for business logic operations.
"""


class ServiceException(Exception):
    """Base exception for service layer operations."""

    pass


class AgentNotFoundError(ServiceException):
    """Raised when an agent is not found in the database."""

    def __init__(self, agent_id: str) -> None:
        """
        Initialize AgentNotFoundError.

        Args:
            agent_id: The agent ID that was not found
        """
        self.agent_id = agent_id
        super().__init__(f"Agent with ID '{agent_id}' not found")


class AgentAlreadyExistsError(ServiceException):
    """Raised when attempting to register an agent that already exists."""

    def __init__(self, agent_id: str) -> None:
        """
        Initialize AgentAlreadyExistsError.

        Args:
            agent_id: The agent ID that already exists
        """
        self.agent_id = agent_id
        super().__init__(f"Agent with ID '{agent_id}' already exists")


class InvalidAgentStatusError(ServiceException):
    """Raised when attempting to set an invalid agent status."""

    def __init__(self, status: str, valid_statuses: list[str]) -> None:
        """
        Initialize InvalidAgentStatusError.

        Args:
            status: The invalid status that was attempted
            valid_statuses: List of valid status values
        """
        self.status = status
        self.valid_statuses = valid_statuses
        super().__init__(
            f"Invalid status '{status}'. Valid statuses: {', '.join(valid_statuses)}"
        )

