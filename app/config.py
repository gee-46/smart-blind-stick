"""
Application configuration settings.

Settings are loaded from environment variables (via a `.env` file in
development). Keeping all configuration in one place makes it easy for
teammates to run the backend with their own local settings without
touching code.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment or defaults."""

    # Project Info
    app_name: str = "Smart Blind Stick Backend"
    version: str = "1.0.0"
    environment: str = "development"

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True

    # Database
    # Default: local SQLite file. Swap DATABASE_URL for a PostgreSQL DSN
    # later without touching application code.
    database_url: str = "sqlite:///./smart_blind_stick.db"

    # Device Monitoring
    device_offline_after_seconds: int = 60
    default_event_limit: int = 50
    default_location_history_limit: int = 50

    # Safety & Emergency Subsystem Configuration
    # Fall confirmation countdown window (seconds before auto-escalation to SOS)
    fall_confirmation_timeout_seconds: int = 20

    # Fall Detection Algorithm Thresholds (Multi-condition)
    # 1. Free fall / weightlessness drop acceleration magnitude threshold in g (1g = 9.81 m/s^2)
    fall_accel_free_fall_threshold: float = 0.6
    # 2. Impact acceleration spike magnitude threshold in g
    fall_accel_impact_threshold: float = 2.4
    # 3. Orientation tilt change threshold in degrees
    fall_tilt_threshold_degrees: float = 40.0
    # 4. Post-impact immobility duration threshold in seconds
    fall_immobility_duration_seconds: float = 2.5

    # Guardian Notification Settings (Supported: mock, log, sms, firebase, email)
    notification_adapter: str = "mock"
    guardian_name: str = "Primary Guardian"
    guardian_phone: str = "+1-555-0199"
    guardian_email: str = "guardian@smartblindstick.example"
    fcm_server_key: Optional[str] = None

    # Simulator Settings
    simulator_base_url: str = "http://127.0.0.1:8000"
    simulator_device_id: str = "STICK_001"
    simulator_interval_seconds: int = 5

    # =========================================================================
    # Uppercase aliases for backward-compatibility with feature branches
    # =========================================================================
    @property
    def PROJECT_NAME(self) -> str:
        return self.app_name

    @property
    def VERSION(self) -> str:
        return self.version

    @property
    def ENVIRONMENT(self) -> str:
        return self.environment

    @property
    def HOST(self) -> str:
        return self.host

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def RELOAD(self) -> bool:
        return self.reload

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def DEVICE_OFFLINE_AFTER_SECONDS(self) -> int:
        return self.device_offline_after_seconds

    @property
    def DEFAULT_EVENT_LIMIT(self) -> int:
        return self.default_event_limit

    @property
    def DEFAULT_LOCATION_HISTORY_LIMIT(self) -> int:
        return self.default_location_history_limit

    @property
    def FALL_CONFIRMATION_TIMEOUT_SECONDS(self) -> int:
        return self.fall_confirmation_timeout_seconds

    @property
    def FALL_ACCEL_FREE_FALL_THRESHOLD(self) -> float:
        return self.fall_accel_free_fall_threshold

    @property
    def FALL_ACCEL_IMPACT_THRESHOLD(self) -> float:
        return self.fall_accel_impact_threshold

    @property
    def FALL_TILT_THRESHOLD_DEGREES(self) -> float:
        return self.fall_tilt_threshold_degrees

    @property
    def FALL_IMMOBILITY_DURATION_SECONDS(self) -> float:
        return self.fall_immobility_duration_seconds

    @property
    def NOTIFICATION_ADAPTER(self) -> str:
        return self.notification_adapter

    @property
    def GUARDIAN_NAME(self) -> str:
        return self.guardian_name

    @property
    def GUARDIAN_PHONE(self) -> str:
        return self.guardian_phone

    @property
    def GUARDIAN_EMAIL(self) -> str:
        return self.guardian_email

    @property
    def FCM_SERVER_KEY(self) -> Optional[str]:
        return self.fcm_server_key

    @property
    def SIMULATOR_BASE_URL(self) -> str:
        return self.simulator_base_url

    @property
    def SIMULATOR_DEVICE_ID(self) -> str:
        return self.simulator_device_id

    @property
    def SIMULATOR_INTERVAL_SECONDS(self) -> int:
        return self.simulator_interval_seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
