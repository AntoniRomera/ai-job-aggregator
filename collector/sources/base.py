"""The documented adapter contract.

Adding a new job board is one file implementing ``Source`` plus one entry in
the registry (``collector/sources/__init__.py``). An adapter's only job is to
return a list of ``RawPosting`` objects; storage and enrichment are handled by
the pipeline.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..config import Settings
from ..fetcher import BrowserFetcher
from ..models import RawPosting


@runtime_checkable
class Source(Protocol):
    """A job-board adapter.

    Attributes:
        name: Unique registry key (matches a value in the SOURCES env list).
        requires_network: When True the pipeline provides a BrowserFetcher and
            enforces robots.txt before the adapter runs.
    """

    name: str
    requires_network: bool

    async def fetch(self, fetcher: BrowserFetcher | None, settings: Settings) -> list[RawPosting]:
        """Return the postings discovered by this adapter."""
        ...
