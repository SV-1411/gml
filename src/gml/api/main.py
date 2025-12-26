"""
FastAPI Application Factory and Configuration

This module initializes and configures the FastAPI application with middleware,
exception handlers, health checks, and router management.

Features:
    - CORS middleware for cross-origin requests
    - Request/response logging and timing
    - Global exception handling
    - Health check endpoints
    - API documentation endpoints
    - Structured router inclusion pattern
    - Prometheus metrics collection
    - Request latency tracking
    - Error rate monitoring
"""

import logging
from typing import Any, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.gml.api.middleware import setup_middleware
from src.gml.monitoring.metrics import metrics

__version__ = "0.1.0"
__api_title__ = "GML Infrastructure API"
__api_description__ = "Graph Machine Learning infrastructure service with vector embeddings and AI capabilities"

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


class APIInfoResponse(BaseModel):
    """API information response model."""

    name: str
    version: str
    description: str
    docs_url: str
    redoc_url: str


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    status_code: int
    detail: str | None = None


def create_app(
    title: str = __api_title__,
    version: str = __version__,
    description: str = __api_description__,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory function initializes the FastAPI app with all necessary
    middleware, exception handlers, and routes. It follows a modular pattern
    for easy testing and customization.

    Args:
        title: API title for OpenAPI documentation
        version: API version for OpenAPI documentation
        description: API description for OpenAPI documentation

    Returns:
        Configured FastAPI application instance

    Example:
        >>> app = create_app()
        >>> # or with custom parameters
        >>> app = create_app(title="Custom API", version="1.0.0")
    """
    app = FastAPI(
        title=title,
        version=version,
        description=description,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    setup_middleware(app)
    _configure_exception_handlers(app)
    _configure_routes(app)

    logger.info(f"FastAPI application initialized: {title} v{version}")

    return app


# Middleware configuration moved to src/gml/api/middleware.py


def _configure_exception_handlers(app: FastAPI) -> None:
    """
    Configure global exception handlers for the application.

    Handles:
        - Validation errors (422)
        - Not found errors (404)
        - Generic exceptions (500)
        - Custom application exceptions

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle unexpected exceptions globally.

        Args:
            request: The incoming request
            exc: The caught exception

        Returns:
            JSON error response with 500 status
        """
        request_id = request.headers.get("x-request-id", "unknown")

        # Record error metric
        metrics.increment_http_errors(
            status_code=500, endpoint=request.url.path
        )

        logger.error(
            f"[{request_id}] Unhandled exception: {str(exc)}",
            exc_info=exc,
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal server error",
                status_code=500,
                detail="An unexpected error occurred. Please try again later.",
            ).model_dump(),
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle 404 Not Found errors.

        Args:
            request: The incoming request
            exc: The caught exception

        Returns:
            JSON error response with 404 status
        """
        # Record error metric
        metrics.increment_http_errors(
            status_code=404, endpoint=request.url.path
        )

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                error="Not found",
                status_code=404,
                detail=f"Endpoint {request.url.path} not found.",
            ).model_dump(),
        )

    # TODO: Add custom exception handlers for domain-specific errors
    # @app.exception_handler(ValidationError)
    # async def validation_error_handler(request: Request, exc: ValidationError):
    #     return JSONResponse(status_code=422, content={"errors": exc.errors()})


def _configure_routes(app: FastAPI) -> None:
    """
    Configure all routes and routers for the application.

    Routes are organized in a modular structure:
    - Health check routes
    - API routes (imported from routers)
    - Webhook routes (future)
    - Admin routes (future)

    Args:
        app: FastAPI application instance
    """

    @app.get(
        "/",
        response_model=APIInfoResponse,
        tags=["info"],
        summary="API Information",
        description="Returns information about the GML Infrastructure API",
    )
    async def root() -> APIInfoResponse:
        """
        Get API information and documentation links.

        Returns:
            APIInfoResponse with API metadata and documentation URLs

        Example:
            GET /
            {
                "name": "GML Infrastructure API",
                "version": "0.1.0",
                "description": "Graph Machine Learning...",
                "docs_url": "/api/docs",
                "redoc_url": "/api/redoc"
            }
        """
        return APIInfoResponse(
            name=__api_title__,
            version=__version__,
            description=__api_description__,
            docs_url="/api/docs",
            redoc_url="/api/redoc",
        )

    # Include API routers - Import here to avoid circular imports
    try:
        from src.gml.api.routes import agents_router, batch_operations_router, chat_router, conversations_router, health_router, memory_router, memory_versions_router, ollama_router, search_router, storage_router
        
        # Health router (no prefix for /health and /metrics)
        app.include_router(health_router)
        
        # API v1 routers
        app.include_router(agents_router, prefix="/api/v1")
        app.include_router(memory_router, prefix="/api/v1")
        app.include_router(memory_versions_router, prefix="/api/v1")
        app.include_router(batch_operations_router, prefix="/api/v1")
        app.include_router(chat_router, prefix="/api/v1")
        app.include_router(conversations_router, prefix="/api/v1")
        app.include_router(search_router, prefix="/api/v1")
        app.include_router(ollama_router, prefix="/api/v1")
        app.include_router(storage_router, prefix="/api/v1")
        
        logger.info("All routes configured successfully")
        logger.info("Registered routers: agents, health, memory, memory-versions, batch-operations, chat, conversations, search, ollama, storage")
        
    except ImportError as e:
        logger.error(f"Failed to import routers: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Failed to configure routes: {e}", exc_info=True)
        raise

    # TODO: Add webhook routes
    # from src.gml.webhooks.routes import router as webhook_router
    # app.include_router(webhook_router, prefix="/webhooks")

    # TODO: Add admin routes (with authentication)
    # from src.gml.admin.routes import router as admin_router
    # app.include_router(admin_router, prefix="/admin", tags=["admin"])


# Create the default application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
