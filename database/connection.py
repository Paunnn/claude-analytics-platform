"""
Database connection management.

This module provides functions for creating database engines,
sessions, and initializing the database using SQLAlchemy 2.0 async API.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text, pool
from sqlalchemy.orm import DeclarativeBase
import logging

from config import settings


logger = logging.getLogger(__name__)


# Global engine and sessionmaker instances
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_async_database_url() -> str:
    """
    Convert DATABASE_URL to async format.

    Replaces postgresql:// with postgresql+asyncpg://

    Returns:
        str: Async database URL
    """
    url = settings.database_url

    # Replace sync driver with async driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def get_engine() -> AsyncEngine:
    """
    Create and configure SQLAlchemy async engine.

    Returns:
        AsyncEngine: Configured SQLAlchemy async engine with connection pooling

    Example:
        >>> engine = get_engine()
        >>> async with engine.connect() as conn:
        ...     result = await conn.execute(text("SELECT 1"))
    """
    global _engine

    if _engine is None:
        async_url = get_async_database_url()

        _engine = create_async_engine(
            async_url,
            echo=settings.log_level == "DEBUG",
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            poolclass=pool.QueuePool,
        )

        logger.info(f"Created async database engine: {async_url.split('@')[1] if '@' in async_url else 'localhost'}")

    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Create an async sessionmaker instance.

    Returns:
        async_sessionmaker: Configured async session factory

    Example:
        >>> SessionLocal = get_sessionmaker()
        >>> async with SessionLocal() as session:
        ...     result = await session.execute(select(Employee))
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Created async session factory")

    return _async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database sessions.

    Yields:
        AsyncSession: SQLAlchemy async database session

    Example:
        >>> @app.get("/users")
        >>> async def get_users(db: AsyncSession = Depends(get_session)):
        ...     result = await db.execute(select(Employee))
        ...     return result.scalars().all()
    """
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function should be called on application startup.
    It creates tables defined in models.py if they don't exist.

    Example:
        >>> await init_db()
        >>> print("Database initialized successfully")
    """
    engine = get_engine()

    async with engine.begin() as conn:
        # Import models to register them
        from . import models  # noqa: F401

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")


async def test_connection() -> bool:
    """
    Test database connection.

    Returns:
        bool: True if connection successful, False otherwise

    Example:
        >>> if await test_connection():
        ...     print("Database is accessible")
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def close_engine() -> None:
    """
    Close database engine and dispose of connection pool.

    Should be called on application shutdown.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database engine closed")
