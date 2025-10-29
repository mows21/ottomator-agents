"""Configuration management for AI Dream Command Center backend."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Database
    supabase_url: str = ""
    supabase_key: str = ""

    # Monitoring
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Optional
    sentry_dsn: str = ""
    redis_url: str = "redis://localhost:6379"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
