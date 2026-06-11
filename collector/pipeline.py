"""Pipeline orchestration: collect -> dedupe/store -> enrich -> persist.

This is the core of the `run` command. It is fully async and degrades
gracefully: live sources that need Playwright are skipped (with a warning) if
the browser can't launch, and salary estimation always falls back to the
offline heuristic.
"""

from __future__ import annotations

import logging

from .config import Settings, get_settings
from .db import init_db, jobs_missing_salary, list_jobs, session_scope, upsert_job
from .fetcher import BrowserFetcher, FetchError
from .llm import get_estimator
from .llm.base import SalaryEstimator
from .models import Job, RawPosting
from .sources import resolve_sources
from .sources.base import Source

logger = logging.getLogger("collector.pipeline")


async def collect(settings: Settings, sources: list[Source]) -> list[RawPosting]:
    """Run all configured source adapters and return the combined postings."""
    needs_browser = any(s.requires_network for s in sources)
    fetcher: BrowserFetcher | None = None
    postings: list[RawPosting] = []

    try:
        if needs_browser:
            try:
                fetcher = BrowserFetcher(settings)
                await fetcher.start()
            except FetchError as exc:
                logger.warning("Browser unavailable (%s); skipping live sources", exc)
                fetcher = None

        for source in sources:
            if source.requires_network and fetcher is None:
                logger.warning("Skipping '%s' — no browser available", source.name)
                continue
            try:
                results = await source.fetch(fetcher, settings)
                logger.info("Source '%s' returned %d postings", source.name, len(results))
                postings.extend(results)
            except Exception as exc:  # one bad adapter shouldn't kill the run
                logger.error("Source '%s' failed: %s", source.name, exc)
    finally:
        if fetcher is not None:
            await fetcher.close()

    return postings


async def store(settings: Settings, postings: list[RawPosting]) -> list[Job]:
    """Upsert raw postings into the database, deduping on (source, external_id)."""
    stored: list[Job] = []
    async with session_scope(settings) as session:
        for raw in postings:
            job = Job.from_raw(raw)
            persisted = await upsert_job(session, job)
            stored.append(persisted)
    logger.info("Stored/updated %d jobs", len(stored))
    return stored


async def enrich(settings: Settings, estimator: SalaryEstimator | None = None) -> int:
    """Estimate salaries for stored jobs that lack a salary band.

    Returns the number of jobs enriched.
    """
    estimator = estimator or get_estimator(settings)
    enriched = 0
    async with session_scope(settings) as session:
        candidates = await jobs_missing_salary(session)
        logger.info("Enriching %d jobs without salary via %s", len(candidates), estimator.name)
        for job in candidates:
            raw = RawPosting(
                external_id=job.external_id,
                source=job.source,
                title=job.title,
                company=job.company,
                location=job.location,
                remote=job.remote,
                description=job.description,
                url=job.url,
                stack=job.stack_list,
            )
            estimate = await estimator.estimate(raw)
            job.apply_estimate(estimate, estimator.name)  # type: ignore[arg-type]
            session.add(job)
            enriched += 1
    logger.info("Enriched %d jobs", enriched)
    return enriched


async def run_pipeline(settings: Settings | None = None) -> dict[str, int]:
    """Full pipeline: collect -> store -> enrich. Returns a summary."""
    settings = settings or get_settings()
    await init_db(settings)

    sources = resolve_sources(settings.source_list)
    logger.info("Configured sources: %s", ", ".join(s.name for s in sources))

    postings = await collect(settings, sources)
    await store(settings, postings)
    enriched = await enrich(settings)

    async with session_scope(settings) as session:
        total = len(await list_jobs(session))

    summary = {"collected": len(postings), "enriched": enriched, "total_in_db": total}
    logger.info("Pipeline complete: %s", summary)
    return summary


async def seed_only(settings: Settings | None = None) -> int:
    """Load only the seed dataset into the DB (no enrichment). Returns count."""
    from .sources.seed import SeedSource

    settings = settings or get_settings()
    await init_db(settings)
    postings = await SeedSource().fetch(None, settings)
    stored = await store(settings, postings)
    return len(stored)
