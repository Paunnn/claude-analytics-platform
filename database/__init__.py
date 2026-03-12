"""
Database module for Claude Analytics Platform.

This module provides database connection management, ORM models,
and database utilities using SQLAlchemy 2.0 async API.
"""

from .connection import (
    Base,
    get_engine,
    get_sessionmaker,
    get_session,
    init_db,
    test_connection,
    close_engine,
)
from .models import (
    Employee,
    UserAccount,
    Model,
    Tool,
    Session,
    APIRequest,
    ToolDecision,
    ToolResult,
    UserPrompt,
    APIError,
)

__all__ = [
    # Connection
    "Base",
    "get_engine",
    "get_sessionmaker",
    "get_session",
    "init_db",
    "test_connection",
    "close_engine",
    # Models
    "Employee",
    "UserAccount",
    "Model",
    "Tool",
    "Session",
    "APIRequest",
    "ToolDecision",
    "ToolResult",
    "UserPrompt",
    "APIError",
]
