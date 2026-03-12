"""
FastAPI application entry point.

This module initializes the FastAPI application with all routes,
middleware, and configuration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from api.routes import analytics, users, health, streaming

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles:
    - Database connection initialization
    - Resource cleanup on shutdown
    """
    # Startup logic
    logger.info("Starting Claude Analytics API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database_url.split('@')[-1]}")  # Hide credentials

    yield

    # Shutdown logic
    logger.info("Shutting down Claude Analytics API")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Claude Analytics API",
        description="Analytics API for Claude Code usage data",
        version="1.0.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(analytics.router)
    app.include_router(users.router)
    app.include_router(streaming.router)

    return app


# Create application instance
app = create_app()


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns API information and available endpoints.
    """
    return {
        "service": "Claude Analytics API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "endpoints": {
            "health": "/health/",
            "analytics": "/analytics/",
            "users": "/users/",
            "websocket": "ws://localhost:8000/ws/metrics",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/version")
async def version():
    """
    Get API version information.

    Returns:
        Dictionary with version and environment info
    """
    return {
        "version": "1.0.0",
        "environment": settings.environment,
        "python_version": sys.version,
        "log_level": settings.log_level
    }


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )
