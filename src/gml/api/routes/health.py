"""
Health Check API Routes

FastAPI router for health check and metrics endpoints including basic health,
Prometheus metrics, and detailed service health checks.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import Gauge, generate_latest, REGISTRY
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.core.config import get_settings
from src.gml.db.database import AsyncSessionLocal, get_db
from src.gml.monitoring.metrics import metrics

logger = logging.getLogger(__name__)

# Compatibility for asyncio.timeout (available in Python 3.11+)
if sys.version_info >= (3, 11):
    asyncio_timeout = asyncio.timeout
else:
    # Fallback for Python < 3.11
    import async_timeout
    def asyncio_timeout(seconds):
        return async_timeout.timeout(seconds)

router = APIRouter(tags=["health"])

# Prometheus metrics - Check if already registered to avoid duplication on reload
def _get_or_create_gauge(name, description, labels=None):
    """Get existing gauge or create new one to avoid duplication errors on reload."""
    try:
        # Try to find existing metric in registry
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        # Not found, create new one
        return Gauge(name, description, labels or [])
    except Exception:
        # If anything fails, create new one anyway
        return Gauge(name, description, labels or [])

agents_active_gauge = _get_or_create_gauge(
    "gml_agents_active",
    "Number of active agents",
    ["status"],
)

messages_count_gauge = _get_or_create_gauge(
    "gml_messages_count",
    "Current number of messages",
    ["status"],
)

costs_total_gauge = _get_or_create_gauge(
    "gml_costs_total",
    "Total costs incurred",
    ["cost_type"],
)

# Health check timeout (seconds)
HEALTH_CHECK_TIMEOUT = 5.0


async def check_database_health(db: Optional[AsyncSession] = None) -> tuple[bool, Optional[str]]:
    """
    Check database connectivity with timeout.

    Args:
        db: Optional database session. If not provided, creates a new one.

    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        async with asyncio_timeout(HEALTH_CHECK_TIMEOUT):
            if db is None:
                # Create a new session if not provided
                from src.gml.db.database import get_session_factory
                session_factory = get_session_factory()
                async with session_factory() as session:
                    result = await session.execute(text("SELECT 1"))
                    value = result.scalar()
                    if value == 1:
                        return True, None
                    return False, "Unexpected database response"
            else:
                # Use provided session
                result = await db.execute(text("SELECT 1"))
                value = result.scalar()
                if value == 1:
                    return True, None
                return False, "Unexpected database response"
    except asyncio.TimeoutError:
        return False, "Database health check timed out"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        return False, str(e)


async def check_redis_health() -> tuple[bool, Optional[str]]:
    """
    Check Redis connectivity with timeout.

    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        from redis.asyncio import Redis
        from redis.exceptions import ConnectionError as RedisConnectionError

        settings = get_settings()

        async with asyncio_timeout(HEALTH_CHECK_TIMEOUT):
            # Create temporary Redis client
            redis_client = Redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=2,
                socket_timeout=2,
            )

            try:
                # Test connection with PING
                await redis_client.ping()
                await redis_client.close()
                return True, None
            except RedisConnectionError as e:
                await redis_client.close()
                return False, f"Redis connection failed: {str(e)}"
            except Exception as e:
                await redis_client.close()
                return False, f"Redis error: {str(e)}"

    except ImportError:
        return False, "aioredis not available"
    except asyncio.TimeoutError:
        return False, "Redis health check timed out"
    except Exception as e:
        return False, f"Redis check error: {str(e)}"


async def check_qdrant_health() -> tuple[bool, Optional[str]]:
    """
    Check Qdrant connectivity with timeout.

    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        settings = get_settings()

        async with asyncio_timeout(HEALTH_CHECK_TIMEOUT):
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Qdrant health check endpoint
                health_url = f"{settings.QDRANT_URL}/healthz"
                response = await client.get(health_url)

                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"Qdrant returned status {response.status_code}"

    except httpx.TimeoutException:
        return False, "Qdrant health check timed out"
    except httpx.RequestError as e:
        return False, f"Qdrant connection error: {str(e)}"
    except asyncio.TimeoutError:
        return False, "Qdrant health check timed out"
    except Exception as e:
        return False, f"Qdrant check error: {str(e)}"


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Simple health check endpoint for load balancers and monitoring",
)
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.

    Returns a simple healthy status with timestamp.
    Used by load balancers and orchestrators for basic availability checks.

    Returns:
        Dictionary with status and timestamp

    Example:
        GET /health
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/metrics",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Prometheus metrics",
    description="Prometheus-formatted metrics endpoint with proper Content-Type header",
)
async def metrics_endpoint(
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Prometheus metrics endpoint.

    Returns Prometheus-formatted metrics including:
    - Application metrics (counters, gauges, histograms)
    - Active agents count by status
    - Messages processed count by status
    - Total costs by type
    - Request latency distributions
    - Error rates

    Metrics are updated on each request to reflect current state.
    Includes proper Content-Type header for Prometheus scraping.

    Args:
        db: Database session (dependency injection)

    Returns:
        Response with Prometheus-formatted metrics and Content-Type header

    Example:
        GET /metrics

        Response (Content-Type: text/plain; version=0.0.4; charset=utf-8):
        # HELP gml_agents_registered_total Total number of agents registered...
        # TYPE gml_agents_registered_total counter
        gml_agents_registered_total 42.0
        ...
    """
    try:
        # Update agent metrics (gauges)
        for status_value in ["active", "inactive", "error", "maintenance"]:
            result = await db.execute(
                text("SELECT COUNT(*) FROM agents WHERE status = :status"),
                {"status": status_value},
            )
            count = result.scalar() or 0
            agents_active_gauge.labels(status=status_value).set(count)
            # Also update the new metrics module
            metrics.set_active_agents(status=status_value, count=count)

        # Update message metrics (gauges)
        for status_value in ["pending", "delivered", "failed", "timeout"]:
            result = await db.execute(
                text("SELECT COUNT(*) FROM messages WHERE status = :status"),
                {"status": status_value},
            )
            count = result.scalar() or 0
            messages_count_gauge.labels(status=status_value).set(count)

        # Update pending messages gauge
        result = await db.execute(
            text("SELECT COUNT(*) FROM messages WHERE status = 'pending'")
        )
        pending_count = result.scalar() or 0
        metrics.set_pending_messages(pending_count)

        # Update cost metrics (total costs by type)
        result = await db.execute(
            text("SELECT cost_type, SUM(amount) FROM costs GROUP BY cost_type")
        )
        cost_rows = result.all()
        for row in cost_rows:
            cost_type = row[0] or "unknown"
            total_amount = float(row[1]) if row[1] else 0.0
            costs_total_gauge.labels(cost_type=cost_type).set(total_amount)
            # Also update the new metrics module
            metrics.set_total_costs_usd(cost_type=cost_type, amount=total_amount)

        # Generate Prometheus metrics from the metrics module registry
        # This includes all counters, gauges, and histograms
        metrics_content = metrics.generate_metrics()

        # Also include legacy metrics from the default registry
        legacy_metrics = generate_latest()

        # Combine both metric sets
        combined_metrics = legacy_metrics + metrics_content

        return Response(
            content=combined_metrics,
            media_type=metrics.get_content_type(),
        )

    except Exception as e:
        logger.error(f"Failed to generate metrics: {str(e)}", exc_info=True)
        # Return empty metrics on error rather than failing
        return Response(
            content=b"",
            media_type=metrics.get_content_type(),
        )


@router.get(
    "/api/v1/health/detailed",
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Comprehensive health check for all services with connectivity tests",
)
async def detailed_health_check() -> Dict[str, Dict[str, Optional[str]]]:
    """
    Detailed health check for all services.

    Checks connectivity to:
    - Database (PostgreSQL)
    - Redis cache
    - Qdrant vector database

    Each service check has a timeout to prevent hanging requests.
    Returns health status for each service.

    Returns:
        Dictionary with health status for each service:
        {
            "database": {"status": "healthy", "message": null},
            "redis": {"status": "healthy", "message": null},
            "qdrant": {"status": "healthy", "message": null}
        }

    Example:
        GET /api/v1/health/detailed

        Response 200:
        {
            "database": {"status": "healthy", "message": null},
            "redis": {"status": "healthy", "message": null},
            "qdrant": {"status": "healthy", "message": null}
        }
    """
    try:
        # Check all services - wrap in try/except to catch any unexpected errors
        db_healthy, db_error = await check_database_health()
        redis_healthy, redis_error = await check_redis_health()
        qdrant_healthy, qdrant_error = await check_qdrant_health()

        # Build response
        health_status = {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "message": db_error,
            },
            "redis": {
                "status": "healthy" if redis_healthy else "unhealthy",
                "message": redis_error,
            },
            "qdrant": {
                "status": "healthy" if qdrant_healthy else "unhealthy",
                "message": qdrant_error,
            },
        }

        # Always return 200 with health status, don't raise exceptions
        # This allows frontend to display detailed health information
        return health_status

    except Exception as e:
        # Log the error and return unhealthy status for all services
        logger.error(f"Health check failed with unexpected error: {str(e)}", exc_info=True)
        return {
            "database": {
                "status": "unhealthy",
                "message": f"Health check error: {str(e)}",
            },
            "redis": {
                "status": "unhealthy",
                "message": f"Health check error: {str(e)}",
            },
            "qdrant": {
                "status": "unhealthy",
                "message": f"Health check error: {str(e)}",
            },
        }

