"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central runtime configuration for the backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "AI Engineering Lab"
    app_version: str = "1.0.0"
    environment: str = "development"
    api_prefix: str = ""
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Phase 2 LLM reviewer settings (server-side only).
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: float = 30.0


settings = Settings()
