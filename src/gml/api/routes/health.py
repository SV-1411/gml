"""
Health Check API Routes

Simplified health check endpoints for production.
"""

import logging
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", summary="Basic health check")
async def health_check() -> Dict:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "gml-api",
    }


@router.get("/health/ready", summary="Readiness check")
async def readiness_check(
    db: SupabaseDB = Depends(get_db),
) -> Dict:
    """Check if service is ready to accept requests."""
    checks = {
        "database": False,
        "vector_db": False,
    }
    
    # Check Supabase
    try:
        await db.select("agents", limit=1)
        checks["database"] = True
    except Exception as e:
        logger.warning(f"Database check failed: {str(e)}")
    
    # Check Pinecone
    try:
        from src.gml.services.memory_store import get_memory_store
        store = await get_memory_store()
        stats = await store.get_stats()
        checks["vector_db"] = True
    except Exception as e:
        logger.warning(f"Vector DB check failed: {str(e)}")
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/health/live", summary="Liveness check")
async def liveness_check() -> Dict:
    """Kubernetes liveness probe endpoint."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["router"]
