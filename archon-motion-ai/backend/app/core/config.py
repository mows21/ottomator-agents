"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://archon:archon@localhost:5432/archon"
    sync_database_url: str = "postgresql://archon:archon@localhost:5432/archon"
    redis_url: str = "redis://localhost:6379"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_secret: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # MCP
    mcp_server_port: int = 8001
    mcp_auth_token: str = "dev-mcp-token"

    # Feature Flags
    enable_analytics: bool = True
    enable_websockets: bool = True
    debug: bool = False

    # External Integrations
    github_token: str = ""
    notion_api_key: str = ""
    google_drive_credentials: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Logging
    log_level: str = "INFO"

    # AI Models
    default_model: str = "claude-3-5-sonnet-20241022"
    embedding_model: str = "text-embedding-3-small"

    # Scheduling
    schedule_lookahead_days: int = 14
    default_work_hours_per_day: int = 8
    default_work_days_per_week: int = 5


settings = Settings()
