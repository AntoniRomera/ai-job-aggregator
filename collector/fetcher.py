"""Async Playwright browser manager with retry/backoff + per-domain rate limiting.

Live source adapters use ``BrowserFetcher.get_text`` to render a page with
headless Chromium. Navigation is retried with exponential backoff via tenacity,
and requests to the same domain are spaced out by ``rate_limit_seconds``.

Playwright is imported lazily so the package (and the offline seed flow) works
without Chromium installed.
"""

from __future__ import annotations

import asyncio
import logging
import time
from types import TracebackType
from urllib.parse import urlsplit

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Settings, get_settings

logger = logging.getLogger("collector.fetcher")


class FetchError(RuntimeError):
    """Raised when a page could not be fetched after retries."""


class BrowserFetcher:
    """Manages a single headless Chromium instance for the collection run."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._playwright = None
        self._browser = None
        self._last_request: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> BrowserFetcher:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def start(self) -> None:
        """Launch the browser. Imports Playwright lazily."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise FetchError(
                "Playwright is not installed. Run `pip install -r requirements.txt` "
                "and `python -m playwright install chromium` to use live sources."
            ) from exc

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        logger.info("Launched headless Chromium")

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def _respect_rate_limit(self, url: str) -> None:
        """Block until ``rate_limit_seconds`` have elapsed since the last hit
        on this domain."""
        domain = urlsplit(url).netloc
        async with self._lock:
            last = self._last_request.get(domain)
            now = time.monotonic()
            if last is not None:
                wait = self.settings.rate_limit_seconds - (now - last)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._last_request[domain] = time.monotonic()

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(FetchError),
    )
    async def get_text(self, url: str, *, wait_selector: str | None = None) -> str:
        """Render ``url`` and return its text content. Retries on failure."""
        if self._browser is None:
            raise FetchError("Browser not started; use `async with BrowserFetcher() as f`.")

        await self._respect_rate_limit(url)
        context = await self._browser.new_context(user_agent=self.settings.user_agent)
        page = await context.new_page()
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            if response is None or not response.ok:
                status = response.status if response else "no response"
                raise FetchError(f"Navigation to {url} failed: {status}")
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=15_000)
            return await page.content()
        except FetchError:
            raise
        except Exception as exc:  # Playwright timeouts etc.
            raise FetchError(f"Error fetching {url}: {exc}") from exc
        finally:
            await context.close()
