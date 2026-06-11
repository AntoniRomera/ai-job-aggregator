"""Tests for robots.txt allow/deny enforcement (offline, via respx mocks)."""

from __future__ import annotations

import httpx
import pytest
import respx
from collector import robots


@pytest.fixture(autouse=True)
def _clear_cache():
    robots.clear_cache()
    yield
    robots.clear_cache()


@respx.mock
async def test_allows_when_robots_permits():
    respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nAllow: /\n")
    )
    assert await robots.is_allowed("https://example.com/api", "test-agent") is True


@respx.mock
async def test_disallows_blocked_path():
    respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /private\n")
    )
    assert await robots.is_allowed("https://example.com/private/x", "test-agent") is False
    assert await robots.is_allowed("https://example.com/public", "test-agent") is True


@respx.mock
async def test_403_treated_as_disallowed():
    respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(403))
    assert await robots.is_allowed("https://example.com/anything", "test-agent") is False


@respx.mock
async def test_404_treated_as_allowed():
    respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
    assert await robots.is_allowed("https://example.com/anything", "test-agent") is True


@respx.mock
async def test_network_error_allows():
    respx.get("https://example.com/robots.txt").mock(side_effect=httpx.ConnectError("boom"))
    assert await robots.is_allowed("https://example.com/anything", "test-agent") is True


@respx.mock
async def test_result_is_cached_per_origin():
    route = respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nAllow: /\n")
    )
    await robots.is_allowed("https://example.com/a", "agent")
    await robots.is_allowed("https://example.com/b", "agent")
    assert route.call_count == 1
