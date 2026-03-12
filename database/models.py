"""
SQLAlchemy ORM models for Claude Analytics Platform.

This module defines ORM models that map to database tables
defined in schema.sql using SQLAlchemy 2.0 mapped_column API.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean,
    BigInteger,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .connection import Base


class Employee(Base):
    """
    Employee dimension table.

    Stores employee metadata including practice, level, and location.
    """
    __tablename__ = "employees"

    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    practice: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    user_accounts: Mapped[List["UserAccount"]] = relationship("UserAccount", back_populates="employee")

    def __repr__(self) -> str:
        return f"<Employee(id={self.employee_id}, email='{self.email}', practice='{self.practice}', level='{self.level}')>"


class UserAccount(Base):
    """
    User accounts from telemetry data.

    Links telemetry user IDs to employee records and stores
    system information (hostname, profile, etc.).
    """
    __tablename__ = "user_accounts"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_uuid: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    employee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_profile: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    employee: Mapped[Optional["Employee"]] = relationship("Employee", back_populates="user_accounts")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user")
    api_requests: Mapped[List["APIRequest"]] = relationship("APIRequest", back_populates="user")
    tool_decisions: Mapped[List["ToolDecision"]] = relationship("ToolDecision", back_populates="user")
    tool_results: Mapped[List["ToolResult"]] = relationship("ToolResult", back_populates="user")
    user_prompts: Mapped[List["UserPrompt"]] = relationship("UserPrompt", back_populates="user")
    api_errors: Mapped[List["APIError"]] = relationship("APIError", back_populates="user")

    def __repr__(self) -> str:
        return f"<UserAccount(user_id='{self.user_id}', employee_id={self.employee_id})>"


class Model(Base):
    """
    Claude models dimension table.

    Stores Claude model metadata (haiku, sonnet, opus variants).
    """
    __tablename__ = "models"

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    model_family: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    api_requests: Mapped[List["APIRequest"]] = relationship("APIRequest", back_populates="model")
    api_errors: Mapped[List["APIError"]] = relationship("APIError", back_populates="model")

    def __repr__(self) -> str:
        return f"<Model(id={self.model_id}, name='{self.model_name}', family='{self.model_family}')>"


class Tool(Base):
    """
    Tools dimension table.

    Stores Claude Code tool metadata (Read, Write, Bash, etc.).
    """
    __tablename__ = "tools"

    tool_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tool_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    tool_decisions: Mapped[List["ToolDecision"]] = relationship("ToolDecision", back_populates="tool")
    tool_results: Mapped[List["ToolResult"]] = relationship("ToolResult", back_populates="tool")

    def __repr__(self) -> str:
        return f"<Tool(id={self.tool_id}, name='{self.tool_name}', category='{self.tool_category}')>"


class Session(Base):
    """
    Coding sessions dimension table.

    Represents a single Claude Code session with environment metadata.
    """
    __tablename__ = "sessions"

    session_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("user_accounts.user_id"), nullable=True)
    terminal_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    architecture: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    claude_code_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    session_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount", back_populates="sessions")
    api_requests: Mapped[List["APIRequest"]] = relationship("APIRequest", back_populates="session")
    tool_decisions: Mapped[List["ToolDecision"]] = relationship("ToolDecision", back_populates="session")
    tool_results: Mapped[List["ToolResult"]] = relationship("ToolResult", back_populates="session")
    user_prompts: Mapped[List["UserPrompt"]] = relationship("UserPrompt", back_populates="session")
    api_errors: Mapped[List["APIError"]] = relationship("APIError", back_populates="session")

    def __repr__(self) -> str:
        return f"<Session(id={self.session_id}, user_id='{self.user_id}', terminal='{self.terminal_type}')>"


class APIRequest(Base):
    """
    API request events fact table.

    Stores Claude API request events with token usage and cost data.
    """
    __tablename__ = "api_requests"

    request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sessions.session_id"),
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("user_accounts.user_id"),
        nullable=True,
        index=True
    )
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("models.model_id"),
        nullable=True,
        index=True
    )
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="api_requests")
    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount", back_populates="api_requests")
    model: Mapped[Optional["Model"]] = relationship("Model", back_populates="api_requests")

    def __repr__(self) -> str:
        return f"<APIRequest(id={self.request_id}, model_id={self.model_id}, cost=${self.cost_usd:.4f})>"


class ToolDecision(Base):
    """
    Tool decision events fact table.

    Stores tool permission decisions (accept/reject).
    """
    __tablename__ = "tool_decisions"

    decision_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sessions.session_id"),
        nullable=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("user_accounts.user_id"),
        nullable=True
    )
    tool_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tools.tool_id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="tool_decisions")
    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount", back_populates="tool_decisions")
    tool: Mapped[Optional["Tool"]] = relationship("Tool", back_populates="tool_decisions")

    def __repr__(self) -> str:
        return f"<ToolDecision(id={self.decision_id}, tool_id={self.tool_id}, decision='{self.decision}')>"


class ToolResult(Base):
    """
    Tool result events fact table.

    Stores tool execution results with success/failure and duration.
    """
    __tablename__ = "tool_results"

    result_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sessions.session_id"),
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("user_accounts.user_id"),
        nullable=True,
        index=True
    )
    tool_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tools.tool_id"), nullable=True)
    decision_type: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_source: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    result_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="tool_results")
    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount", back_populates="tool_results")
    tool: Mapped[Optional["Tool"]] = relationship("Tool", back_populates="tool_results")

    def __repr__(self) -> str:
        return f"<ToolResult(id={self.result_id}, tool_id={self.tool_id}, success={self.success})>"


class UserPrompt(Base):
    """
    User prompt events fact table.

    Stores user prompt events with prompt length.
    """
    __tablename__ = "user_prompts"

    prompt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sessions.session_id"),
        nullable=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("user_accounts.user_id"),
        nullable=True
    )
    prompt_length: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="user_prompts")
    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount", back_populates="user_prompts")

    def __repr__(self) -> str:
        return f"<UserPrompt(id={self.prompt_id}, length={self.prompt_length})>"


class APIError(Base):
    """
    API error events fact table.

    Stores API error events with error messages and status codes.
    """
    __tablename__ = "api_errors"

    error_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sessions.session_id"),
        nullable=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("user_accounts.user_id"),
        nullable=True
    )
    model_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("models.model_id"), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="api_errors")
    user: Mapped[Optional["UserAccount"]] = relationship("UserAccount", back_populates="api_errors")
    model: Mapped[Optional["Model"]] = relationship("Model", back_populates="api_errors")

    def __repr__(self) -> str:
        return f"<APIError(id={self.error_id}, status='{self.status_code}', message='{self.error_message[:50]}')>"
