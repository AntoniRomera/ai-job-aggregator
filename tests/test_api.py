"""Tests for the FastAPI app, driven through httpx ASGITransport (no live server).

The API uses the process-wide settings/engine, so we point the cached settings
at an in-memory database and pre-seed it before exercising the endpoints.
"""

from __future__ import annotations

import collector.config as config_module
import collector.db as db_module
import httpx
import pytest
from collector.config import Settings
from collector.db import init_db, session_scope, upsert_job
from collector.models import Job, RawPosting


@pytest.fixture
async def client(monkeypatch):
    test_settings = Settings(db_url="sqlite+aiosqlite:///:memory:")

    # Point the cached get_settings() at our in-memory config.
    config_module.get_settings.cache_clear()
    monkeypatch.setattr(config_module, "get_settings", lambda: test_settings)

    # Reset and create the shared engine against the in-memory DB.
    db_module._engine = None
    db_module._sessionmaker = None
    await init_db(test_settings)

    # Seed a couple of jobs.
    async with session_scope(test_settings) as session:
        remote_job = Job.from_raw(
            RawPosting(
                external_id="r1",
                source="seed",
                title="Remote Python Engineer",
                company="Acme",
                location="Remote (US)",
                remote=True,
                stack=["Python", "FastAPI"],
            )
        )
        remote_job.salary_min, remote_job.salary_max = 150_000, 180_000
        await upsert_job(session, remote_job)

        onsite_job = Job.from_raw(
            RawPosting(
                external_id="o1",
                source="seed",
                title="Onsite Java Engineer",
                company="Globex",
                location="New York, NY",
                remote=False,
                stack=["Java"],
            )
        )
        onsite_job.salary_min, onsite_job.salary_max = 120_000, 140_000
        await upsert_job(session, onsite_job)

    # Import the app AFTER patching so create_app() reads test settings.
    from collector.api import create_app

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    db_module._engine = None
    db_module._sessionmaker = None


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["jobs"] == 2


async def test_list_all_jobs(client):
    resp = await client.get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 2


async def test_filter_remote(client):
    resp = await client.get("/api/jobs", params={"remote": "true"})
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "r1"


async def test_filter_by_stack(client):
    resp = await client.get("/api/jobs", params={"stack": "FastAPI"})
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["company"] == "Acme"


async def test_filter_by_location_substring(client):
    resp = await client.get("/api/jobs", params={"location": "new york"})
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "o1"


async def test_filter_min_pay(client):
    resp = await client.get("/api/jobs", params={"min_pay": 145_000})
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "r1"


async def test_search_query(client):
    resp = await client.get("/api/jobs", params={"q": "globex"})
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["company"] == "Globex"


async def test_get_one_and_404(client):
    listing = (await client.get("/api/jobs")).json()
    jid = listing[0]["id"]
    ok = await client.get(f"/api/jobs/{jid}")
    assert ok.status_code == 200

    missing = await client.get("/api/jobs/999999")
    assert missing.status_code == 404


async def test_meta_facets(client):
    resp = await client.get("/api/meta")
    body = resp.json()
    assert body["count"] == 2
    assert "Python" in body["stacks"]
    assert "Java" in body["stacks"]
    assert body["remote_count"] == 1
