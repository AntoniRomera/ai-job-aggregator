"""Typed application settings loaded from environment / .env.

Everything has a default so the project runs fully offline with zero config.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["auto", "anthropic", "gemini", "heuristic"]


class Settings(BaseSettings):
    """Runtime configuration.

    Resolved (in order) from constructor args, environment variables, and a
    local ``.env`` file. Field names map to upper-snake-case env vars.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM salary estimator ---
    anthropic_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    llm_provider: LLMProvider = Field(default="auto")
    anthropic_model: str = Field(default="claude-opus-4-8")
    gemini_model: str = Field(default="gemini-2.0-flash")

    # --- Collection sources ---
    sources: str = Field(default="seed")

    # --- Storage ---
    db_url: str = Field(default="sqlite+aiosqlite:///collector/data/jobs.db")

    # --- Responsible use / networking ---
    rate_limit_seconds: float = Field(default=2.0)
    user_agent: str = Field(
        default="ai-job-aggregator/0.1 (+https://github.com/antoniromera/ai-job-aggregator)"
    )

    # --- API server ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")

    @property
    def source_list(self) -> list[str]:
        """Configured source adapter names, normalized."""
        return [s.strip().lower() for s in self.sources.split(",") if s.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        """Allowed CORS origins for the frontend."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
