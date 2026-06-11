"""Tests for the async DB layer (upsert/dedupe/query helpers)."""

from __future__ import annotations

from collector.db import (
    get_job,
    get_job_by_external,
    jobs_missing_salary,
    list_jobs,
    session_scope,
    upsert_job,
)
from collector.models import Job, RawPosting


def _job(external_id: str, title: str = "Dev", **kwargs) -> Job:
    return Job.from_raw(
        RawPosting(external_id=external_id, source="seed", title=title, company="Acme", **kwargs)
    )


async def test_insert_and_fetch(initialized_db):
    settings = initialized_db
    async with session_scope(settings) as session:
        stored = await upsert_job(session, _job("a"))
        assert stored.id is not None
        jid = stored.id

    async with session_scope(settings) as session:
        fetched = await get_job(session, jid)
        assert fetched is not None
        assert fetched.external_id == "a"


async def test_upsert_dedupes_on_natural_key(initialized_db):
    settings = initialized_db
    async with session_scope(settings) as session:
        await upsert_job(session, _job("a", title="Old Title"))
    async with session_scope(settings) as session:
        await upsert_job(session, _job("a", title="New Title"))

    async with session_scope(settings) as session:
        all_jobs = await list_jobs(session)
        assert len(all_jobs) == 1
        assert all_jobs[0].title == "New Title"


async def test_get_by_external(initialized_db):
    settings = initialized_db
    async with session_scope(settings) as session:
        await upsert_job(session, _job("xyz"))
    async with session_scope(settings) as session:
        found = await get_job_by_external(session, "seed", "xyz")
        assert found is not None
        missing = await get_job_by_external(session, "seed", "nope")
        assert missing is None


async def test_jobs_missing_salary(initialized_db):
    settings = initialized_db
    async with session_scope(settings) as session:
        await upsert_job(session, _job("with-pay", salary_min=100_000, salary_max=120_000))
        await upsert_job(session, _job("no-pay"))

    async with session_scope(settings) as session:
        missing = await jobs_missing_salary(session)
        ids = {j.external_id for j in missing}
        assert "no-pay" in ids
        assert "with-pay" not in ids
