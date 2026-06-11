"""Offline seed adapter — the default source.

Reads the clearly-marked sample dataset at ``collector/data/seed_jobs.json`` so
``python -m collector run`` (and the whole API) works with no network access.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from ..config import Settings
from ..fetcher import BrowserFetcher
from ..models import RawPosting

logger = logging.getLogger("collector.sources.seed")

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_jobs.json"


def _parse_posted_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class SeedSource:
    """Loads RawPostings from the bundled JSON sample dataset."""

    name = "seed"
    requires_network = False

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or SEED_PATH

    async def fetch(self, fetcher: BrowserFetcher | None, settings: Settings) -> list[RawPosting]:
        logger.info("=== SEED DATA === loading sample postings from %s", self.path)
        with self.path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        records = payload.get("jobs", payload) if isinstance(payload, dict) else payload
        postings: list[RawPosting] = []
        for rec in records:
            postings.append(
                RawPosting(
                    external_id=str(rec["external_id"]),
                    source=self.name,
                    title=rec["title"],
                    company=rec["company"],
                    location=rec.get("location", ""),
                    remote=bool(rec.get("remote", False)),
                    description=rec.get("description", ""),
                    url=rec.get("url", ""),
                    stack=list(rec.get("stack", [])),
                    salary_min=rec.get("salary_min"),
                    salary_max=rec.get("salary_max"),
                    salary_currency=rec.get("salary_currency", "USD"),
                    salary_period=rec.get("salary_period", "year"),
                    posted_at=_parse_posted_at(rec.get("posted_at")),
                )
            )
        logger.info("=== SEED DATA === loaded %d postings", len(postings))
        return postings
