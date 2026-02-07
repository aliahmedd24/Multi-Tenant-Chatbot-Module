"""Application configuration using Pydantic Settings.

Loads configuration from environment variables with type validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://wafaa:dev@localhost:5432/wafaa"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Vector Database
    vector_db_provider: Literal["pinecone", "weaviate"] = "pinecone"
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "wafaa-knowledge"
    weaviate_url: str = "http://localhost:8080"

    # LLM Providers
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Meta (WhatsApp/Instagram)
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = ""

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Cached application settings instance.
    """
    return Settings()


settings = get_settings()
