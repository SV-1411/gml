"""
Cost Service

Business logic layer for cost tracking and billing operations.

This service handles:
- Cost recording with automatic billing period assignment
- Agent cost aggregation and reporting
- Daily and monthly cost breakdowns
- Cost analysis by type and time period
"""

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.models import Cost

logger = logging.getLogger(__name__)

# Cost matrix: Default costs for different operations
COST_MATRIX = {
    "agent_registration": 0.01,
    "message_send": 0.01,
    "memory_write": 0.02,
    "memory_search": 0.05,
}


class CostService:
    """
    Service class for cost tracking and billing operations.

    Provides business logic for recording costs, aggregating expenses,
    and generating billing reports with proper date filtering.
    """

    @staticmethod
    async def record_cost(
        db: AsyncSession,
        cost_type: str,
        agent_id: str,
        amount: float,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Cost:
        """
        Record a cost in the database.

        Creates a new Cost record with automatic billing period assignment
        based on the current month. Includes all metadata for tracking.

        Args:
            db: Async database session
            cost_type: Type of cost (e.g., "agent_registration", "message_send")
            agent_id: ID of the agent associated with this cost
            amount: Cost amount
            currency: Currency code (default: "USD")
            metadata: Optional metadata dictionary (stored in request_id or other fields)
            request_id: Optional request ID for tracking
            message_id: Optional message ID if cost is associated with a message

        Returns:
            Created Cost model instance

        Raises:
            Exception: For database errors

        Example:
            >>> cost = await CostService.record_cost(
            ...     db,
            ...     cost_type="agent_registration",
            ...     agent_id="agent-001",
            ...     amount=0.01,
            ...     metadata={"source": "api", "user_id": "user-123"}
            ... )
            >>> print(cost.billing_period)
            '2024-01'
        """
        try:
            # Get current date and format billing period (YYYY-MM)
            current_date = datetime.now(timezone.utc)
            billing_period = current_date.strftime("%Y-%m")

            # Create cost record
            cost = Cost(
                cost_type=cost_type,
                agent_id=agent_id,
                amount=amount,
                currency=currency,
                request_id=request_id,
                message_id=message_id,
                billing_period=billing_period,
                created_at=current_date,
            )

            db.add(cost)
            await db.commit()
            await db.refresh(cost)

            logger.debug(
                f"Recorded cost: {cost_type} for agent {agent_id}, amount: {amount} {currency}"
            )

            return cost

        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to record cost for agent {agent_id}: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    async def get_agent_costs(
        db: AsyncSession,
        agent_id: str,
        start_date: date,
        end_date: date,
    ) -> float:
        """
        Get total costs for an agent within a date range.

        Sums all costs for the specified agent between start_date and end_date.
        Returns the total amount in the default currency.

        Args:
            db: Async database session
            agent_id: ID of the agent
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Total cost amount as float

        Raises:
            Exception: For database errors

        Example:
            >>> from datetime import date
            >>> total = await CostService.get_agent_costs(
            ...     db,
            ...     "agent-001",
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> print(f"Total costs: ${total:.2f}")
        """
        try:
            # Convert dates to datetime with timezone for comparison
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(
                tzinfo=timezone.utc
            )

            # Aggregate query
            result = await db.execute(
                select(func.sum(Cost.amount))
                .where(Cost.agent_id == agent_id)
                .where(Cost.created_at >= start_datetime)
                .where(Cost.created_at <= end_datetime)
            )

            total = result.scalar()
            total_amount = float(total) if total is not None else 0.0

            logger.debug(
                f"Total costs for agent {agent_id} from {start_date} to {end_date}: {total_amount}"
            )

            return total_amount

        except Exception as e:
            logger.error(
                f"Failed to get agent costs for {agent_id}: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    async def get_daily_costs(db: AsyncSession, date: date) -> Dict[str, Any]:
        """
        Get cost breakdown by type for a specific day.

        Groups all costs by cost_type for the given date and returns
        a breakdown with counts and totals.

        Args:
            db: Async database session
            date: Date to get costs for

        Returns:
            Dictionary containing:
                - date: The queried date
                - total: Total cost for the day
                - breakdown: Dictionary mapping cost_type to {
                    count: number of costs,
                    total: total amount
                  }

        Raises:
            Exception: For database errors

        Example:
            >>> from datetime import date
            >>> breakdown = await CostService.get_daily_costs(db, date(2024, 1, 15))
            >>> print(breakdown["total"])
            0.15
            >>> print(breakdown["breakdown"]["message_send"]["count"])
            5
        """
        try:
            # Convert date to datetime range for the day
            start_datetime = datetime.combine(date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            end_datetime = datetime.combine(date, datetime.max.time()).replace(
                tzinfo=timezone.utc
            )

            # Aggregate query: group by cost_type
            result = await db.execute(
                select(
                    Cost.cost_type,
                    func.count(Cost.id).label("count"),
                    func.sum(Cost.amount).label("total"),
                )
                .where(Cost.created_at >= start_datetime)
                .where(Cost.created_at <= end_datetime)
                .group_by(Cost.cost_type)
            )

            rows = result.all()

            breakdown = {}
            grand_total = 0.0

            for row in rows:
                cost_type = row.cost_type
                count = row.count
                total = float(row.total) if row.total is not None else 0.0

                breakdown[cost_type] = {
                    "count": count,
                    "total": total,
                }
                grand_total += total

            logger.debug(f"Daily costs for {date}: {len(breakdown)} types, total: {grand_total}")

            return {
                "date": date.isoformat(),
                "total": grand_total,
                "breakdown": breakdown,
            }

        except Exception as e:
            logger.error(f"Failed to get daily costs for {date}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def get_billing_period_costs(
        db: AsyncSession, agent_id: str, year: int, month: int
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for an agent in a specific billing period.

        Retrieves all costs for the agent in the specified month and returns
        a detailed breakdown by cost type with counts and totals.

        Args:
            db: Async database session
            agent_id: ID of the agent
            year: Year (e.g., 2024)
            month: Month (1-12)

        Returns:
            Dictionary containing:
                - agent_id: Agent ID
                - billing_period: Billing period (YYYY-MM)
                - total: Total cost for the period
                - breakdown: Dictionary mapping cost_type to {
                    count: number of costs,
                    total: total amount,
                    costs: list of individual cost records
                  }

        Raises:
            ValueError: If month is not in range 1-12
            Exception: For database errors

        Example:
            >>> breakdown = await CostService.get_billing_period_costs(
            ...     db, "agent-001", 2024, 1
            ... )
            >>> print(breakdown["billing_period"])
            '2024-01'
            >>> print(breakdown["total"])
            0.25
        """
        try:
            # Validate month
            if not (1 <= month <= 12):
                raise ValueError(f"Month must be between 1 and 12, got {month}")

            # Format billing period
            billing_period = f"{year:04d}-{month:02d}"

            # Get all costs for the agent in this billing period
            result = await db.execute(
                select(Cost)
                .where(Cost.agent_id == agent_id)
                .where(Cost.billing_period == billing_period)
                .order_by(Cost.created_at.asc())
            )

            costs = result.scalars().all()

            # Group by cost_type and calculate totals
            breakdown = {}
            grand_total = 0.0

            for cost in costs:
                cost_type = cost.cost_type
                amount = float(cost.amount)

                if cost_type not in breakdown:
                    breakdown[cost_type] = {
                        "count": 0,
                        "total": 0.0,
                        "costs": [],
                    }

                breakdown[cost_type]["count"] += 1
                breakdown[cost_type]["total"] += amount
                breakdown[cost_type]["costs"].append(
                    {
                        "id": cost.id,
                        "amount": amount,
                        "currency": cost.currency,
                        "request_id": cost.request_id,
                        "message_id": cost.message_id,
                        "created_at": cost.created_at.isoformat(),
                    }
                )

                grand_total += amount

            logger.debug(
                f"Billing period costs for agent {agent_id} in {billing_period}: "
                f"{len(costs)} costs, total: {grand_total}"
            )

            return {
                "agent_id": agent_id,
                "billing_period": billing_period,
                "total": grand_total,
                "breakdown": breakdown,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get billing period costs for agent {agent_id}: {str(e)}",
                exc_info=True,
            )
            raise

    @staticmethod
    async def get_costs_by_type(
        db: AsyncSession, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """
        Get cost summary grouped by type for a date range.

        Aggregates all costs by cost_type between start_date and end_date,
        returning counts and totals for each type.

        Args:
            db: Async database session
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dictionary containing:
                - start_date: Start date
                - end_date: End date
                - total: Grand total across all types
                - summary: Dictionary mapping cost_type to {
                    count: number of costs,
                    total: total amount
                  }

        Raises:
            Exception: For database errors

        Example:
            >>> from datetime import date
            >>> summary = await CostService.get_costs_by_type(
            ...     db,
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> print(summary["total"])
            1.25
            >>> print(summary["summary"]["message_send"]["count"])
            50
        """
        try:
            # Convert dates to datetime with timezone
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(
                tzinfo=timezone.utc
            )

            # Aggregate query: group by cost_type
            result = await db.execute(
                select(
                    Cost.cost_type,
                    func.count(Cost.id).label("count"),
                    func.sum(Cost.amount).label("total"),
                )
                .where(Cost.created_at >= start_datetime)
                .where(Cost.created_at <= end_datetime)
                .group_by(Cost.cost_type)
                .order_by(Cost.cost_type)
            )

            rows = result.all()

            summary = {}
            grand_total = 0.0

            for row in rows:
                cost_type = row.cost_type
                count = row.count
                total = float(row.total) if row.total is not None else 0.0

                summary[cost_type] = {
                    "count": count,
                    "total": total,
                }
                grand_total += total

            logger.debug(
                f"Costs by type from {start_date} to {end_date}: "
                f"{len(summary)} types, total: {grand_total}"
            )

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total": grand_total,
                "summary": summary,
            }

        except Exception as e:
            logger.error(
                f"Failed to get costs by type: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    def get_cost_for_operation(operation: str) -> float:
        """
        Get the default cost for an operation from the cost matrix.

        Args:
            operation: Operation name (e.g., "agent_registration", "message_send")

        Returns:
            Cost amount from COST_MATRIX, or 0.0 if not found

        Example:
            >>> cost = CostService.get_cost_for_operation("message_send")
            >>> print(cost)
            0.01
        """
        return COST_MATRIX.get(operation, 0.0)

