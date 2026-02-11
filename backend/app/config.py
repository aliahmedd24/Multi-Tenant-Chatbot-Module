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

    # File Storage (use "uploads" for local dev so backend/uploads is used; set UPLOAD_DIR for production)
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    allowed_file_types: str = "pdf,docx,txt,csv"

    # AI/ML Providers
    llm_provider: str = "mock"
    llm_model: str = "gpt-4o"
    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    vector_db_provider: str = "mock"

    # API Keys
    openai_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "wafaa-knowledge"

    # RAG Settings
    chunk_size: int = 400
    chunk_overlap: int = 50
    max_context_chunks: int = 5
    max_files_per_tenant: int = 20

    # Monitoring
    sentry_dsn: str = ""
    prometheus_enabled: bool = False

    # Channel Webhooks
    webhook_verify_token: str = "wafaa-verify-token"
    whatsapp_api_version: str = "v18.0"
    instagram_api_version: str = "v18.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
