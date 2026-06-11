"""Worked-example live adapter: RemoteOK.

RemoteOK publishes a documented JSON API and permits non-abusive automated
access. This adapter is the reference implementation of the ``Source`` contract
for a real board. It is **opt-in** (enable via ``SOURCES=remoteok``) and is
gated behind a robots.txt check + per-domain rate limiting.

It uses the Playwright fetcher (consistent with the rest of the collector) to
retrieve the API endpoint, then parses the embedded JSON. Network is never
required by the project: the default ``seed`` source keeps everything offline.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from ..config import Settings
from ..fetcher import BrowserFetcher, FetchError
from ..models import RawPosting
from ..robots import is_allowed

logger = logging.getLogger("collector.sources.remoteok")

API_URL = "https://remoteok.com/api"

# Pull the JSON array out of the rendered page (Playwright wraps it in <pre>).
_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def _parse_epoch(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)  # type: ignore[arg-type]
    except (TypeError, ValueError, OSError):
        return None


class RemoteOKSource:
    """Adapter for the RemoteOK public job API."""

    name = "remoteok"
    requires_network = True

    async def fetch(self, fetcher: BrowserFetcher | None, settings: Settings) -> list[RawPosting]:
        if fetcher is None:
            raise FetchError("RemoteOK adapter requires a BrowserFetcher")

        if not await is_allowed(API_URL, settings.user_agent):
            logger.warning("robots.txt disallows %s — skipping RemoteOK", API_URL)
            return []

        html = await fetcher.get_text(API_URL)
        match = _JSON_ARRAY_RE.search(html)
        if not match:
            logger.warning("Could not locate JSON payload in RemoteOK response")
            return []

        try:
            records = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse RemoteOK JSON: %s", exc)
            return []

        postings: list[RawPosting] = []
        for rec in records:
            # The first element of the RemoteOK feed is a legal/metadata notice.
            if not isinstance(rec, dict) or "id" not in rec or "position" not in rec:
                continue
            tags = rec.get("tags") or []
            salary_min = rec.get("salary_min") or None
            salary_max = rec.get("salary_max") or None
            postings.append(
                RawPosting(
                    external_id=str(rec["id"]),
                    source=self.name,
                    title=rec.get("position", "").strip() or "Unknown role",
                    company=rec.get("company", "").strip() or "Unknown",
                    location=rec.get("location", "").strip(),
                    remote=True,  # RemoteOK is remote-only by definition.
                    description=re.sub(r"<[^>]+>", " ", rec.get("description", "")).strip(),
                    url=rec.get("url", ""),
                    stack=[str(t) for t in tags],
                    salary_min=float(salary_min) if salary_min else None,
                    salary_max=float(salary_max) if salary_max else None,
                    salary_currency="USD",
                    salary_period="year",
                    posted_at=_parse_epoch(rec.get("epoch")),
                )
            )

        logger.info("RemoteOK: collected %d postings", len(postings))
        return postings
