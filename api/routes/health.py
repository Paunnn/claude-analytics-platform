"""
Health check endpoints.

Provides endpoints for monitoring service health and readiness.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from typing import Dict, Any
import logging

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.

    Returns:
        Dictionary with status

    Example:
        GET /health/
        Response: {"status": "healthy"}
    """
    return {"status": "healthy", "service": "claude-analytics-api"}


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check including database connectivity.

    Returns:
        Dictionary with detailed health status

    Example:
        GET /health/ready
        Response: {
            "status": "ready",
            "database": "connected",
            "checks": {...}
        }
    """
    checks = {}
    overall_status = "ready"

    # Check database connection
    try:
        sync_url = settings.database_url
        if 'asyncpg' in sync_url:
            sync_url = sync_url.replace('postgresql+asyncpg://', 'postgresql://')

        engine = create_engine(sync_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        checks["database"] = "connected"
        engine.dispose()
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error(f"Database health check failed: {e}")

    return {
        "status": overall_status,
        "checks": checks,
        "environment": settings.environment
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe for orchestrators (Kubernetes, etc.).

    Returns:
        Dictionary with status
    """
    return {"status": "alive"}
