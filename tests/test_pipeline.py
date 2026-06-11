"""End-to-end offline pipeline test: seed -> store -> enrich.

Uses the default seed source and the heuristic estimator (no keys), so the whole
flow runs without network access.
"""

from __future__ import annotations

from collector.db import list_jobs, session_scope
from collector.pipeline import enrich, run_pipeline, seed_only


async def test_seed_only_loads_jobs(initialized_db):
    settings = initialized_db
    count = await seed_only(settings)
    assert count > 0
    async with session_scope(settings) as session:
        jobs = await list_jobs(session)
    assert len(jobs) == count


async def test_full_pipeline_enriches_missing_salaries(initialized_db):
    settings = initialized_db
    summary = await run_pipeline(settings)
    assert summary["collected"] > 0
    assert summary["total_in_db"] > 0

    async with session_scope(settings) as session:
        jobs = await list_jobs(session)

    # Every stored job ends with a salary band (from posting or estimator).
    assert all(j.salary_min is not None and j.salary_max is not None for j in jobs)


async def test_enrich_is_idempotent(initialized_db):
    settings = initialized_db
    await seed_only(settings)
    first = await enrich(settings)
    second = await enrich(settings)
    assert first >= 0
    # Second pass has nothing left missing a salary.
    assert second == 0
