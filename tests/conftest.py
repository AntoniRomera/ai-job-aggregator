"""Shared pytest fixtures.

Every fixture here keeps the suite fully offline: an in-memory SQLite database
and a Settings object with no API keys (so the estimator factory degrades to the
deterministic heuristic).
"""

from __future__ import annotations

import collector.db as db_module
import pytest
from collector.config import Settings
from collector.db import init_db
from collector.models import RawPosting


@pytest.fixture
def settings() -> Settings:
    """In-memory, key-less settings — fully offline."""
    return Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        anthropic_api_key=None,
        gemini_api_key=None,
        llm_provider="auto",
        sources="seed",
    )


@pytest.fixture(autouse=True)
def _reset_engine():
    """Reset the module-level engine/sessionmaker between tests so each test
    gets a fresh in-memory database."""
    db_module._engine = None
    db_module._sessionmaker = None
    yield
    db_module._engine = None
    db_module._sessionmaker = None


@pytest.fixture
async def initialized_db(settings: Settings) -> Settings:
    """Create tables in the in-memory DB and return the settings to use."""
    await init_db(settings)
    return settings


@pytest.fixture
def sample_posting() -> RawPosting:
    return RawPosting(
        external_id="t-001",
        source="seed",
        title="Senior Python Engineer",
        company="Acme",
        location="San Francisco, CA",
        remote=False,
        description="Build APIs with FastAPI and Postgres.",
        url="https://example.com/jobs/t-001",
        stack=["Python", "FastAPI", "AWS"],
    )
