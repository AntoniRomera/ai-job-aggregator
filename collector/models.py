"""Data models: SQLModel tables + Pydantic schemas.

``Job`` is the single persisted table (SQLModel) and doubles as the FastAPI
serialization shape. ``RawPosting`` is what source adapters return before
storage/enrichment. ``SalaryEstimate`` is the structured output the LLM
estimators produce.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel
from pydantic import Field as PydField
from sqlmodel import Field, SQLModel

PayPeriod = Literal["year", "month", "day", "hour"]
SalarySource = Literal["posting", "anthropic", "gemini", "heuristic"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RawPosting(BaseModel):
    """A posting as scraped/loaded from a source, before enrichment."""

    external_id: str
    source: str
    title: str
    company: str
    location: str = ""
    remote: bool = False
    description: str = ""
    url: str = ""
    stack: list[str] = PydField(default_factory=list)
    # Salary fields are optional — many postings omit them, which is exactly
    # what triggers the LLM estimator.
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "USD"
    salary_period: PayPeriod = "year"
    posted_at: datetime | None = None


class SalaryEstimate(BaseModel):
    """Structured salary range. Used both as the LLM output schema and as the
    canonical estimate attached to a Job."""

    salary_min: float = PydField(description="Lower bound of the estimated annual salary.")
    salary_max: float = PydField(description="Upper bound of the estimated annual salary.")
    currency: str = PydField(default="USD", description="ISO 4217 currency code.")
    period: PayPeriod = PydField(default="year", description="Pay period the range refers to.")
    confidence: float = PydField(
        default=0.5, ge=0.0, le=1.0, description="Estimator confidence, 0-1."
    )
    rationale: str = PydField(
        default="", description="One- or two-sentence justification for the range."
    )


class Job(SQLModel, table=True):
    """Enriched posting persisted to SQLite and served by the API."""

    __tablename__ = "jobs"

    id: int | None = Field(default=None, primary_key=True)

    # Natural key: dedupe on (source, external_id).
    source: str = Field(index=True)
    external_id: str = Field(index=True)

    title: str
    company: str = Field(index=True)
    location: str = Field(default="", index=True)
    remote: bool = Field(default=False, index=True)
    description: str = Field(default="")
    url: str = Field(default="")

    # Tech stack stored as a comma-separated string for portability across
    # SQLite/Postgres; exposed as a list via `stack_list`.
    stack: str = Field(default="")

    # Final salary band (from the posting or an estimate).
    salary_min: float | None = Field(default=None, index=True)
    salary_max: float | None = Field(default=None, index=True)
    salary_currency: str = Field(default="USD")
    salary_period: str = Field(default="year")
    salary_source: str = Field(default="posting")
    salary_confidence: float | None = Field(default=None)
    salary_rationale: str = Field(default="")

    posted_at: datetime | None = Field(default=None)
    collected_at: datetime = Field(default_factory=_utcnow)
    enriched_at: datetime | None = Field(default=None)

    @property
    def stack_list(self) -> list[str]:
        return [s for s in self.stack.split(",") if s]

    @classmethod
    def from_raw(cls, raw: RawPosting) -> Job:
        """Build a Job row from a RawPosting (no enrichment yet)."""
        return cls(
            source=raw.source,
            external_id=raw.external_id,
            title=raw.title,
            company=raw.company,
            location=raw.location,
            remote=raw.remote,
            description=raw.description,
            url=raw.url,
            stack=",".join(raw.stack),
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            salary_currency=raw.salary_currency,
            salary_period=raw.salary_period,
            salary_source="posting" if raw.salary_min is not None else "heuristic",
            posted_at=raw.posted_at,
        )

    def apply_estimate(self, estimate: SalaryEstimate, source: SalarySource) -> None:
        """Attach an LLM/heuristic salary estimate to this job in place."""
        self.salary_min = estimate.salary_min
        self.salary_max = estimate.salary_max
        self.salary_currency = estimate.currency
        self.salary_period = estimate.period
        self.salary_source = source
        self.salary_confidence = estimate.confidence
        self.salary_rationale = estimate.rationale
        self.enriched_at = _utcnow()


class JobRead(BaseModel):
    """API response shape for a single job (mirrors the frontend `Job` type)."""

    id: int
    source: str
    external_id: str
    title: str
    company: str
    location: str
    remote: bool
    description: str
    url: str
    stack: list[str]
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    salary_period: str
    salary_source: str
    salary_confidence: float | None
    salary_rationale: str
    posted_at: datetime | None
    collected_at: datetime
    enriched_at: datetime | None

    @classmethod
    def from_job(cls, job: Job) -> JobRead:
        return cls(
            id=job.id or 0,
            source=job.source,
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location,
            remote=job.remote,
            description=job.description,
            url=job.url,
            stack=job.stack_list,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            salary_period=job.salary_period,
            salary_source=job.salary_source,
            salary_confidence=job.salary_confidence,
            salary_rationale=job.salary_rationale,
            posted_at=job.posted_at,
            collected_at=job.collected_at,
            enriched_at=job.enriched_at,
        )
