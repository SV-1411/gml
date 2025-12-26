"""
API module for GML Infrastructure
Handles REST API endpoints and WebSocket connections
"""

# Import main app factory
from src.gml.api.main import app, create_app

__all__ = ["app", "create_app"]
