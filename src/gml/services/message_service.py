"""
Message Service

Business logic layer for inter-agent message operations including sending,
status tracking, response handling, and retry logic.

This service handles:
- Message creation and Redis Pub/Sub publishing
- Message status retrieval
- Pending message queries
- Response handling and delivery confirmation
- Failed message retry logic with timeout handling
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.api.schemas.messages import MessageSendRequest
from src.gml.db.models import Agent, Message
from src.gml.services.exceptions import AgentNotFoundError

logger = logging.getLogger(__name__)

# Redis channel prefix for message notifications
REDIS_MESSAGE_CHANNEL_PREFIX = "gml:messages:"


class MessageService:
    """
    Service class for message management operations.

    Provides business logic for sending messages between agents,
    tracking delivery status, handling responses, and retrying failed messages.
    """

    @staticmethod
    async def send_message(
        db: AsyncSession,
        redis_client: Redis,
        request: MessageSendRequest,
        from_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to an agent.

        Creates a new message, validates the recipient exists, saves to database,
        and publishes to Redis Pub/Sub for async delivery.

        Args:
            db: Async database session
            redis_client: Redis client for Pub/Sub
            request: Message send request with recipient and content
            from_agent_id: Optional ID of the sending agent

        Returns:
            Dictionary containing:
                - message_id: Unique message identifier
                - status: Message status (pending)

        Raises:
            AgentNotFoundError: If recipient agent doesn't exist
            Exception: For database or Redis errors

        Example:
            >>> from src.gml.api.schemas.messages import MessageSendRequest
            >>> request = MessageSendRequest(
            ...     to_agent_id="agent-002",
            ...     action="process_data",
            ...     payload={"data": "example"}
            ... )
            >>> result = await MessageService.send_message(db, redis, request, "agent-001")
            >>> print(result["message_id"])
            'msg-uuid-123'
        """
        try:
            # Validate recipient agent exists
            recipient = await db.execute(
                select(Agent).where(Agent.agent_id == request.to_agent_id)
            )
            agent = recipient.scalar_one_or_none()
            if agent is None:
                raise AgentNotFoundError(request.to_agent_id)

            # Generate unique message ID
            message_id = f"msg-{uuid.uuid4().hex[:12]}"

            # Create message in database within transaction
            async with db.begin():
                message = Message(
                    message_id=message_id,
                    from_agent_id=from_agent_id,
                    to_agent_id=request.to_agent_id,
                    action=request.action,
                    payload=request.payload,
                    status="pending",
                    timeout_seconds=request.timeout_seconds,
                    callback_url=str(request.callback_url) if request.callback_url else None,
                    max_retries=3,  # Default max retries
                    delivery_attempts=0,
                    created_at=datetime.now(timezone.utc),
                )

                db.add(message)
                await db.flush()  # Flush to get the ID

                # Publish to Redis Pub/Sub after successful DB save
                channel = f"{REDIS_MESSAGE_CHANNEL_PREFIX}{request.to_agent_id}"
                message_data = {
                    "message_id": message_id,
                    "from_agent_id": from_agent_id,
                    "to_agent_id": request.to_agent_id,
                    "action": request.action,
                    "payload": request.payload,
                    "timeout_seconds": request.timeout_seconds,
                    "callback_url": str(request.callback_url) if request.callback_url else None,
                    "created_at": message.created_at.isoformat(),
                }

                try:
                    await redis_client.publish(channel, json.dumps(message_data))
                    logger.debug(f"Published message {message_id} to Redis channel {channel}")
                except Exception as redis_error:
                    logger.warning(
                        f"Failed to publish message {message_id} to Redis: {str(redis_error)}"
                    )
                    # Don't fail the transaction if Redis publish fails
                    # Message is still saved in DB and can be retrieved via polling

                await db.commit()

            logger.info(
                f"Message {message_id} sent from {from_agent_id} to {request.to_agent_id}"
            )

            return {
                "message_id": message_id,
                "status": "pending",
            }

        except AgentNotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to send message: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def get_message_status(
        db: AsyncSession, message_id: str
    ) -> Optional[Message]:
        """
        Get message status and details.

        Retrieves a message by ID including response data if available.

        Args:
            db: Async database session
            message_id: Unique message identifier

        Returns:
            Message model instance with response data, or None if not found

        Raises:
            Exception: For database errors

        Example:
            >>> message = await MessageService.get_message_status(db, "msg-abc-123")
            >>> print(message.status)
            'delivered'
            >>> print(message.response)
            {'result': 'success'}
        """
        try:
            result = await db.execute(
                select(Message).where(Message.message_id == message_id)
            )
            message = result.scalar_one_or_none()

            if message is None:
                logger.debug(f"Message {message_id} not found")
                return None

            return message

        except Exception as e:
            logger.error(f"Failed to get message status {message_id}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def get_pending_messages(
        db: AsyncSession, agent_id: str
    ) -> List[Message]:
        """
        Get all pending messages for an agent.

        Retrieves all messages with status 'pending' for the specified agent,
        ordered by creation time (oldest first).

        Args:
            db: Async database session
            agent_id: ID of the agent to get pending messages for

        Returns:
            List of Message model instances with status 'pending'

        Raises:
            Exception: For database errors

        Example:
            >>> messages = await MessageService.get_pending_messages(db, "agent-002")
            >>> print(f"Found {len(messages)} pending messages")
            >>> for msg in messages:
            ...     print(msg.message_id)
        """
        try:
            result = await db.execute(
                select(Message)
                .where(Message.to_agent_id == agent_id)
                .where(Message.status == "pending")
                .order_by(Message.created_at.asc())
            )
            messages = result.scalars().all()

            logger.debug(f"Found {len(messages)} pending messages for agent {agent_id}")

            return list(messages)

        except Exception as e:
            logger.error(
                f"Failed to get pending messages for agent {agent_id}: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    async def send_response(
        db: AsyncSession, message_id: str, response: Dict[str, Any]
    ) -> Message:
        """
        Send response to a message and mark as delivered.

        Updates message status to 'delivered', stores the response data,
        and sets the delivered_at timestamp.

        Args:
            db: Async database session
            message_id: Unique message identifier
            response: Response data to store (dict/JSON)

        Returns:
            Updated Message model instance

        Raises:
            ValueError: If message not found or already delivered
            Exception: For database errors

        Example:
            >>> response = {"result": "success", "data": "processed"}
            >>> message = await MessageService.send_response(db, "msg-abc-123", response)
            >>> print(message.status)
            'delivered'
            >>> print(message.delivered_at)
            2024-01-15 10:30:00+00:00
        """
        try:
            async with db.begin():
                # Get message
                result = await db.execute(
                    select(Message).where(Message.message_id == message_id)
                )
                message = result.scalar_one_or_none()

                if message is None:
                    raise ValueError(f"Message {message_id} not found")

                if message.status == "delivered":
                    raise ValueError(f"Message {message_id} already delivered")

                # Update message with response
                message.status = "delivered"
                message.response = response
                message.delivered_at = datetime.now(timezone.utc)

                await db.commit()
                await db.refresh(message)

            logger.info(f"Response sent for message {message_id}")

            return message

        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to send response for message {message_id}: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    async def retry_failed_messages(
        db: AsyncSession, redis_client: Redis
    ) -> int:
        """
        Retry failed messages that haven't exceeded max retries.

        Finds messages with status 'failed' or 'timeout' that have
        delivery_attempts < max_retries, increments attempts, and republishes
        to Redis. Handles timeout expiration checks.

        Args:
            db: Async database session
            redis_client: Redis client for Pub/Sub

        Returns:
            Number of messages retried

        Raises:
            Exception: For database or Redis errors

        Example:
            >>> retried_count = await MessageService.retry_failed_messages(db, redis)
            >>> print(f"Retried {retried_count} messages")
        """
        try:
            retried_count = 0
            current_time = datetime.now(timezone.utc)

            async with db.begin():
                # Find failed messages that can be retried
                result = await db.execute(
                    select(Message)
                    .where(Message.status.in_(["failed", "timeout"]))
                    .where(Message.delivery_attempts < Message.max_retries)
                    .order_by(Message.created_at.asc())
                )
                failed_messages = result.scalars().all()

                for message in failed_messages:
                    # Check if message has timed out
                    if message.timeout_seconds:
                        elapsed = (current_time - message.created_at).total_seconds()
                        if elapsed > message.timeout_seconds:
                            # Mark as timeout if not already
                            if message.status != "timeout":
                                message.status = "timeout"
                                message.failed_at = current_time
                            continue  # Skip retrying timed-out messages

                    # Increment delivery attempts
                    message.delivery_attempts += 1
                    message.status = "pending"  # Reset to pending for retry
                    message.failed_at = None  # Clear previous failure timestamp

                    # Republish to Redis
                    channel = f"{REDIS_MESSAGE_CHANNEL_PREFIX}{message.to_agent_id}"
                    message_data = {
                        "message_id": message.message_id,
                        "from_agent_id": message.from_agent_id,
                        "to_agent_id": message.to_agent_id,
                        "action": message.action,
                        "payload": message.payload,
                        "timeout_seconds": message.timeout_seconds,
                        "callback_url": str(message.callback_url) if message.callback_url else None,
                        "created_at": message.created_at.isoformat(),
                        "retry_attempt": message.delivery_attempts,
                    }

                    try:
                        await redis_client.publish(channel, json.dumps(message_data))
                        logger.debug(
                            f"Retried message {message.message_id} (attempt {message.delivery_attempts})"
                        )
                        retried_count += 1
                    except Exception as redis_error:
                        logger.warning(
                            f"Failed to republish message {message.message_id} to Redis: {str(redis_error)}"
                        )
                        # Mark as failed if Redis publish fails
                        message.status = "failed"
                        message.failed_at = current_time

                await db.commit()

            if retried_count > 0:
                logger.info(f"Retried {retried_count} failed messages")

            return retried_count

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to retry failed messages: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def mark_message_failed(
        db: AsyncSession, message_id: str, error_message: Optional[str] = None
    ) -> Message:
        """
        Mark a message as failed.

        Updates message status to 'failed' and sets failed_at timestamp.
        Used when message delivery fails or processing errors occur.

        Args:
            db: Async database session
            message_id: Unique message identifier
            error_message: Optional error message to store

        Returns:
            Updated Message model instance

        Raises:
            ValueError: If message not found
            Exception: For database errors

        Example:
            >>> message = await MessageService.mark_message_failed(
            ...     db, "msg-abc-123", "Connection timeout"
            ... )
        """
        try:
            async with db.begin():
                result = await db.execute(
                    select(Message).where(Message.message_id == message_id)
                )
                message = result.scalar_one_or_none()

                if message is None:
                    raise ValueError(f"Message {message_id} not found")

                message.status = "failed"
                message.failed_at = datetime.now(timezone.utc)

                # Store error message if provided (could extend Message model for this)
                # For now, we'll log it
                if error_message:
                    logger.warning(f"Message {message_id} failed: {error_message}")

                await db.commit()
                await db.refresh(message)

            logger.info(f"Marked message {message_id} as failed")

            return message

        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to mark message {message_id} as failed: {str(e)}", exc_info=True
            )
            raise

