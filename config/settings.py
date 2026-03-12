"""
Application settings and configuration management.

This module uses Pydantic Settings for type-safe configuration
with environment variable support and validation.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        database_url: PostgreSQL connection string
        redis_url: Redis connection string
        api_host: API server host
        api_port: API server port
        environment: Application environment (development/staging/production)
        log_level: Logging level
        secret_key: Secret key for JWT/encryption
        enable_ml_forecasting: Enable ML forecasting features
        enable_anomaly_detection: Enable anomaly detection
        enable_streaming: Enable real-time streaming
    """

    # Database Settings
    database_url: str = Field(
        default="postgresql://claude:analytics@localhost:5432/claude_analytics",
        description="PostgreSQL connection URL"
    )
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_url: str = Field(default="http://localhost:8000", description="API base URL")

    # Dashboard Settings
    dashboard_port: int = Field(default=8501, description="Dashboard port")

    # Environment
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for encryption"
    )
    api_key: Optional[str] = Field(default=None, description="API authentication key")

    # ML Configuration
    ml_model_path: str = Field(
        default="./analytics/models/",
        description="Path to ML models"
    )
    enable_ml_forecasting: bool = Field(
        default=True,
        description="Enable ML forecasting features"
    )
    enable_anomaly_detection: bool = Field(
        default=True,
        description="Enable anomaly detection"
    )

    # Streaming Configuration
    enable_streaming: bool = Field(
        default=True,
        description="Enable real-time streaming"
    )
    stream_batch_size: int = Field(
        default=100,
        description="Batch size for streaming"
    )
    stream_interval_seconds: int = Field(
        default=5,
        description="Streaming interval in seconds"
    )

    # Caching
    enable_caching: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
