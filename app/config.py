"""
Application configuration.

Settings are loaded from environment variables (via a `.env` file in
development). Keeping all configuration in one place makes it easy for
teammates to run the backend with their own local settings without
touching code.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    app_name: str = "Smart Blind Stick Backend"
    environment: str = "development"

    # Database
    # Default: local SQLite file. Swap DATABASE_URL for a PostgreSQL DSN
    # later (e.g. postgresql+psycopg2://user:pass@host:5432/dbname) without
    # touching any application code.
    database_url: str = "sqlite:///./smart_blind_stick.db"

    # Device online/offline threshold (seconds since last check-in)
    device_offline_after_seconds: int = 60

    # Event history default page size
    default_event_limit: int = 50
    default_location_history_limit: int = 50

    # Guardian mobile app: authentication
    # IMPORTANT: override JWT_SECRET_KEY in production (.env) -- this
    # default is only safe for local development.
    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (avoids re-reading env on every call)."""
    return Settings()
