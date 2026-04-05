"""
FastAPI Middleware Configuration

Centralized middleware for request/response processing, metrics collection,
and cross-cutting concerns.

Middleware order is important - they execute in reverse order (bottom-up).
"""

import logging
import time
from typing import Any, Callable

from fastapi import Request, status
from fastapi.responses import Response

from src.gml.monitoring.metrics import metrics

logger = logging.getLogger(__name__)


def setup_middleware(app) -> None:
    """
    Configure all middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    from fastapi.middleware.cors import CORSMiddleware
    from src.gml.core.config import get_settings

    settings = get_settings()

    # CORS middleware (first, so it wraps everything)
    # In production, set CORS_ORIGINS to your Vercel frontend URL
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging and metrics middleware
    @app.middleware("http")
    async def request_logging_middleware(
        request: Request, call_next: Callable
    ) -> Any:
        """
        Middleware for request/response logging, performance timing, and metrics collection.

        Logs:
            - Request method and path
            - Response status code
            - Request processing time

        Metrics:
            - Request latency (histogram)
            - HTTP errors (counter)
            - Auto-increments on all operations

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with timing header
        """
        request_id = request.headers.get("x-request-id", "unknown")
        start_time = time.time()

        # Exclude health check and metrics endpoints from logging to reduce noise
        skip_logging = request.url.path in ["/health", "/metrics"]

        if not skip_logging:
            logger.info(
                f"[{request_id}] {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

        try:
            response = await call_next(request)
        except Exception as e:
            # Record error metrics for exceptions
            status_code = getattr(e, "status_code", 500)
            metrics.increment_http_errors(
                status_code=status_code, endpoint=request.url.path
            )
            raise

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Record request latency metric
        metrics.record_request_latency(
            latency_seconds=process_time,
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        )

        # Record error metrics for HTTP error status codes (4xx, 5xx)
        if response.status_code >= 400:
            metrics.increment_http_errors(
                status_code=response.status_code, endpoint=request.url.path
            )

        if not skip_logging:
            logger.info(
                f"[{request_id}] Response: {response.status_code} ({process_time:.3f}s)",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                },
            )

        return response

    # TODO: Add authentication middleware (JWT verification)
    # @app.middleware("http")
    # async def auth_middleware(request: Request, call_next: Callable) -> Any:
    #     token = request.headers.get("Authorization")
    #     # Validate JWT token
    #     return await call_next(request)

    # TODO: Add rate limiting middleware
    # from slowapi import Limiter
    # from slowapi.util import get_remote_address
    # limiter = Limiter(key_func=get_remote_address)
    # app.state.limiter = limiter

    # TODO: Add request body size limiting middleware
    # app.add_middleware(MaxSizeMiddleware, max_size=104857600)  # 100MB

    # TODO: Add gzip compression middleware
    # from fastapi.middleware.gzip import GZipMiddleware
    # app.add_middleware(GZipMiddleware, minimum_size=1000)

    # TODO: Add HTTPS redirect middleware (production only)
    # from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    # if settings.environment == "production":
    #     app.add_middleware(HTTPSRedirectMiddleware)

    # TODO: Add trusted host middleware
    # from fastapi.middleware.trustedhost import TrustedHostMiddleware
    # app.add_middleware(
    #     TrustedHostMiddleware,
    #     allowed_hosts=["example.com", "*.example.com"]
    # )

