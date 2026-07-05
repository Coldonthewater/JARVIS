"""
Central configuration for the entire Jarvis backend.

Why this exists:
    Every other module (AI, voice, memory, integrations, gateway) needs
    configuration values (API keys, ports, log levels, etc). Rather than
    each module reading environment variables independently, they all
    import the single `settings` object defined here.

    This gives us:
      - One place to see every configurable value in the system
      - Validation at startup (the app fails fast with a clear error if
        a required value is missing, instead of crashing later mid-task)
      - Type safety (e.g., a port is guaranteed to be an int, not a string)

Design choice:
    We use Pydantic's BaseSettings, which automatically reads values from
    environment variables (and a .env file in development) and validates
    them against the types/defaults declared below.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Absolute path to the project root (two levels up from this file:
# backend/core/config.py -> backend/ -> jarvis/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Declarative definition of every configuration value Jarvis needs.

    Each field becomes an environment variable of the same name
    (case-insensitive). For example, `anthropic_api_key` is read from
    the ANTHROPIC_API_KEY environment variable.

    Fields with `...` (Ellipsis) as their default are REQUIRED — the app
    will refuse to start without them. Fields with a real default are
    optional and will fall back to that value.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "config" / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    app_name: str = "Jarvis"
    environment: str = Field(
        default="development",
        description="One of: development, production, test",
    )

    # --- Logging ---
    log_level: str = Field(default="INFO")
    log_dir: Path = Field(default=PROJECT_ROOT / "logs")

    # --- AI / Reasoning ---
    # Required once we build the AI module — optional for now so the
    # Module 1 skeleton can run without any keys configured yet.
    anthropic_api_key: str | None = Field(default=None)

    # --- Gateway (API server) ---
    gateway_host: str = Field(default="127.0.0.1")
    gateway_port: int = Field(default=8000)

    # --- Memory / Database ---
    database_url: str = Field(
        default=f"sqlite:///{PROJECT_ROOT / 'data' / 'jarvis.db'}"
    )

    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached, single instance of Settings.

    Why cached: reading and validating environment variables has a small
    cost, and settings don't change while the app is running. `lru_cache`
    ensures we only build this object once, and every module that calls
    get_settings() gets back the exact same instance.
    """
    return Settings()


# Convenience singleton — most modules will just do:
#   from backend.core.config import settings
settings = get_settings()
