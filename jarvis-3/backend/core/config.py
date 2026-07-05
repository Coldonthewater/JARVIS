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
    # All keys are optional at the settings level — the AI engine decides
    # at runtime which providers are actually usable based on what's
    # configured, rather than the whole app refusing to start. This
    # matters because the local model alone should be enough to run
    # Jarvis with zero cloud keys configured.

    # Cloud providers (API keys, NOT the same as a ChatGPT/Gemini
    # consumer subscription — these come from platform.openai.com and
    # Google AI Studio, billed separately by usage).
    anthropic_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    google_api_key: str | None = Field(default=None)

    # Local provider (Ollama running on this machine or the LAN).
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1")

    # Routing: which provider handles LOCAL-tier vs CLOUD-tier requests.
    # LOCAL: everyday conversation, app control, smart home, weather,
    #        remembering preferences, automations, offline use.
    # CLOUD: complex code, long-term planning, research, summarizing
    #        large documents, or anything the local model answers
    #        unconfidently (auto-escalated — see ai/router.py).
    # Values must match a key in engine.py's provider registry:
    # "ollama", "openai", "gemini", "anthropic".
    ai_local_provider: str = Field(default="ollama")
    ai_cloud_provider: str = Field(default="openai")
    # If the local provider is unreachable, escalate to this one rather
    # than failing the request outright.
    ai_fallback_provider: str = Field(default="openai")

    # Phrases that, if found in a local model's response, trigger an
    # automatic retry via the cloud provider — this is the "confidence
    # escalation" behavior: even a request classified as LOCAL gets
    # bumped to CLOUD if the local model itself signals uncertainty.
    # Comma-separated so it's tunable via .env without a code change.
    ai_uncertainty_phrases: str = Field(
        default="i'm not sure,i am not sure,i don't know,i do not know,"
        "i'm not certain,i am not certain,i cannot determine,unclear,"
        "i don't have enough information"
    )

    @property
    def ai_uncertainty_phrase_list(self) -> list[str]:
        """Parsed, trimmed list — what the router actually checks against."""
        return [p.strip().lower() for p in self.ai_uncertainty_phrases.split(",") if p.strip()]

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
