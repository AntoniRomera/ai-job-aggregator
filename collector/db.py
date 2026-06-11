"""Async SQLite (or Postgres) engine/session setup and query helpers.

Uses SQLModel over an async SQLAlchemy engine (aiosqlite). The engine URL is
configurable, so swapping to Postgres is a one-line change in `.env`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .config import Settings, get_settings
from .models import Job

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _ensure_sqlite_dir(db_url: str) -> None:
    """Create the parent directory for a file-backed SQLite database."""
    marker = "sqlite+aiosqlite:///"
    if db_url.startswith(marker):
        path = db_url[len(marker) :]
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return (and lazily create) the process-wide async engine."""
    global _engine, _sessionmaker
    if _engine is None:
        settings = settings or get_settings()
        _ensure_sqlite_dir(settings.db_url)
        _engine = create_async_engine(settings.db_url, echo=False, future=True)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


def get_sessionmaker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return the configured async session factory."""
    if _sessionmaker is None:
        get_engine(settings)
    assert _sessionmaker is not None  # populated by get_engine
    return _sessionmaker


async def init_db(settings: Settings | None = None) -> None:
    """Create all tables if they don't exist."""
    engine = get_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def session_scope(settings: Settings | None = None) -> AsyncIterator[AsyncSession]:
    """Async context manager yielding a session with commit/rollback handling."""
    factory = get_sessionmaker(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def upsert_job(session: AsyncSession, job: Job) -> Job:
    """Insert a job, or update the existing row matching (source, external_id).

    Returns the persisted row. Preserves the original `collected_at` on update.
    """
    existing = await get_job_by_external(session, job.source, job.external_id)
    if existing is None:
        session.add(job)
        await session.flush()
        return job

    # Update mutable fields in place.
    existing.title = job.title
    existing.company = job.company
    existing.location = job.location
    existing.remote = job.remote
    existing.description = job.description
    existing.url = job.url
    existing.stack = job.stack
    existing.salary_min = job.salary_min
    existing.salary_max = job.salary_max
    existing.salary_currency = job.salary_currency
    existing.salary_period = job.salary_period
    existing.salary_source = job.salary_source
    existing.salary_confidence = job.salary_confidence
    existing.salary_rationale = job.salary_rationale
    existing.posted_at = job.posted_at
    existing.enriched_at = job.enriched_at
    session.add(existing)
    await session.flush()
    return existing


async def get_job_by_external(session: AsyncSession, source: str, external_id: str) -> Job | None:
    """Look up a single job by its natural key."""
    result = await session.exec(
        select(Job).where(Job.source == source, Job.external_id == external_id)
    )
    return result.first()


async def get_job(session: AsyncSession, job_id: int) -> Job | None:
    """Look up a single job by primary key."""
    return await session.get(Job, job_id)


async def list_jobs(session: AsyncSession) -> Sequence[Job]:
    """Return all stored jobs, newest collection first."""
    result = await session.exec(select(Job).order_by(Job.collected_at.desc()))  # type: ignore[attr-defined]
    return result.all()


async def jobs_missing_salary(session: AsyncSession) -> Sequence[Job]:
    """Return jobs that have no salary band yet (candidates for estimation)."""
    result = await session.exec(select(Job).where(Job.salary_min.is_(None)))  # type: ignore[union-attr]
    return result.all()
