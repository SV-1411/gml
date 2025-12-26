"""
API Routes Module

FastAPI routers for different API endpoints.
Routes are organized by resource type for better maintainability.
"""

from src.gml.api.routes.agents import router as agents_router
from src.gml.api.routes.batch_operations import router as batch_operations_router
from src.gml.api.routes.chat import router as chat_router
from src.gml.api.routes.conversations import router as conversations_router
from src.gml.api.routes.health import router as health_router
from src.gml.api.routes.memory import router as memory_router
from src.gml.api.routes.memory_versions import router as memory_versions_router
from src.gml.api.routes.ollama import router as ollama_router
from src.gml.api.routes.search import router as search_router
from src.gml.api.routes.storage import router as storage_router

__all__ = ["agents_router", "batch_operations_router", "chat_router", "conversations_router", "memory_router", "memory_versions_router", "health_router", "search_router", "ollama_router", "storage_router"]

