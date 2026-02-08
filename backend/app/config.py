"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Wafaa AI Concierge"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://wafaa_user:dev_password@localhost:5432/wafaa_db"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = ["http://localhost:5173"]

    # File Storage
    upload_dir: str = "/data/uploads"
    max_file_size_mb: int = 10
    allowed_file_types: str = "pdf,docx,txt,csv"

    # AI/ML
    llm_provider: str = "mock"
    embedding_provider: str = "mock"
    vector_db_provider: str = "mock"

    # Monitoring
    sentry_dsn: str = ""
    prometheus_enabled: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
