"""
Database module for GML Infrastructure
Handles database connections and models using Supabase
"""

from src.gml.db.database import (
    AsyncSessionLocal,
    Base,
    DatabaseSession,
    close_db,
    engine,
    execute_raw_query,
    get_database_info,
    get_db,
    health_check,
    init_db,
)
from src.gml.db.models import (
    Agent,
    AuditLog,
    Capability,
    ChatMessage,
    Connection,
    Cost,
    Memory,
    Message,
)

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "health_check",
    "DatabaseSession",
    "execute_raw_query",
    "get_database_info",
    "Agent",
    "Message",
    "ChatMessage",
    "Capability",
    "Memory",
    "Cost",
    "AuditLog",
    "Connection",
]
