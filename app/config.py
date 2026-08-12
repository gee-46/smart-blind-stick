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

    # Milestone 2: WebSocket / real-time settings
    # How long a device WS connection has to send its auth message before
    # being disconnected.
    websocket_auth_timeout_seconds: float = 15.0
    # How often the background task scans devices for online<->offline
    # transitions and broadcasts them to monitors.
    heartbeat_check_interval_seconds: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (avoids re-reading env on every call)."""
    return Settings()
