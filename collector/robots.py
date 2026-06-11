"""robots.txt fetching and allow/deny checks — responsible-use enforcement.

Live source adapters MUST call ``is_allowed`` before fetching a URL. Fetched
robots.txt files are cached per-origin for the lifetime of the process.
"""

from __future__ import annotations

import logging
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger("collector.robots")

# origin -> parser (or None if robots.txt was unreachable)
_cache: dict[str, RobotFileParser | None] = {}


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


async def _load_parser(origin: str, user_agent: str, timeout: float) -> RobotFileParser | None:
    """Fetch and parse robots.txt for an origin. Cached. None on failure."""
    if origin in _cache:
        return _cache[origin]

    robots_url = f"{origin}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": user_agent}) as client:
            resp = await client.get(robots_url)
        if resp.status_code == 200:
            parser.parse(resp.text.splitlines())
        elif resp.status_code in (401, 403):
            # Access to robots.txt itself is forbidden -> treat as fully disallowed.
            parser.disallow_all = True
        else:
            # 404 / 5xx -> no restrictions published, allow.
            parser.allow_all = True
    except httpx.HTTPError as exc:
        logger.warning("robots.txt fetch failed for %s: %s (allowing)", origin, exc)
        parser.allow_all = True

    _cache[origin] = parser
    return parser


async def is_allowed(
    url: str,
    user_agent: str,
    *,
    timeout: float = 10.0,
) -> bool:
    """Return True if ``user_agent`` may fetch ``url`` per the site's robots.txt."""
    origin = _origin(url)
    parser = await _load_parser(origin, user_agent, timeout)
    if parser is None:
        return False
    allowed = parser.can_fetch(user_agent, url)
    if not allowed:
        logger.info("robots.txt disallows %s for %s", url, user_agent)
    return allowed


def clear_cache() -> None:
    """Clear the per-origin robots.txt cache (used in tests)."""
    _cache.clear()
