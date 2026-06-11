"""FastAPI app serving enriched postings as JSON.

Endpoints:
    GET /api/health          -> liveness + job count
    GET /api/jobs            -> filterable list of enriched postings
    GET /api/jobs/{id}       -> a single posting
    GET /api/meta            -> filter facets (stacks, locations) for the UI

The frontend (web/) consumes these; CORS is enabled for the Vite dev server.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import get_job, init_db, list_jobs, session_scope
from .models import JobRead


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ensure the database/tables exist before serving requests."""
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Job Aggregator API",
        version="0.1.0",
        description="Enriched job postings with LLM-estimated salary bands.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, object]:
        async with session_scope() as session:
            jobs = await list_jobs(session)
        return {"status": "ok", "jobs": len(jobs)}

    @app.get("/api/jobs", response_model=list[JobRead])
    async def get_jobs(
        stack: list[str] | None = Query(default=None, description="Filter by stack tags (AND)."),
        location: str | None = Query(default=None, description="Case-insensitive substring."),
        remote: bool | None = Query(default=None, description="Filter remote/on-site."),
        min_pay: float | None = Query(default=None, description="Minimum estimated salary_max."),
        max_pay: float | None = Query(default=None, description="Maximum estimated salary_min."),
        q: str | None = Query(default=None, description="Search title/company/description."),
    ) -> list[JobRead]:
        async with session_scope() as session:
            jobs = await list_jobs(session)

        results = []
        for job in jobs:
            if remote is not None and job.remote != remote:
                continue
            if location and location.lower() not in job.location.lower():
                continue
            if stack:
                job_stack = {s.lower() for s in job.stack_list}
                if not all(tag.lower() in job_stack for tag in stack):
                    continue
            if min_pay is not None and (job.salary_max is None or job.salary_max < min_pay):
                continue
            if max_pay is not None and (job.salary_min is None or job.salary_min > max_pay):
                continue
            if q:
                blob = f"{job.title} {job.company} {job.description}".lower()
                if q.lower() not in blob:
                    continue
            results.append(JobRead.from_job(job))
        return results

    @app.get("/api/jobs/{job_id}", response_model=JobRead)
    async def get_one(job_id: int) -> JobRead:
        async with session_scope() as session:
            job = await get_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobRead.from_job(job)

    @app.get("/api/meta")
    async def meta() -> dict[str, object]:
        """Filter facets for the UI: distinct stacks and locations."""
        async with session_scope() as session:
            jobs = await list_jobs(session)
        stacks: set[str] = set()
        locations: set[str] = set()
        for job in jobs:
            stacks.update(job.stack_list)
            if job.location:
                locations.add(job.location)
        return {
            "count": len(jobs),
            "stacks": sorted(stacks),
            "locations": sorted(locations),
            "remote_count": sum(1 for j in jobs if j.remote),
        }

    return app


app = create_app()
