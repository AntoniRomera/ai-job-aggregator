"""Tests for source adapters and the registry."""

from __future__ import annotations

from collector.config import Settings
from collector.sources import available_sources, resolve_sources
from collector.sources.seed import SeedSource


def test_registry_lists_known_sources():
    names = available_sources()
    assert "seed" in names
    assert "remoteok" in names


def test_resolve_known_source():
    sources = resolve_sources(["seed"])
    assert len(sources) == 1
    assert sources[0].name == "seed"


def test_resolve_unknown_falls_back_to_seed():
    sources = resolve_sources(["does-not-exist"])
    assert len(sources) == 1
    assert sources[0].name == "seed"


def test_seed_source_is_offline():
    assert SeedSource().requires_network is False


async def test_seed_source_loads_bundled_dataset():
    postings = await SeedSource().fetch(None, Settings(_env_file=None))
    assert len(postings) > 0
    first = postings[0]
    assert first.source == "seed"
    assert first.external_id
    assert first.title
    assert first.company


async def test_seed_source_handles_optional_fields(tmp_path):
    import json

    payload = {
        "jobs": [
            {"external_id": "a1", "title": "Dev", "company": "Acme"},
        ]
    }
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    postings = await SeedSource(path=path).fetch(None, Settings(_env_file=None))
    assert len(postings) == 1
    p = postings[0]
    assert p.location == ""
    assert p.remote is False
    assert p.stack == []
    assert p.salary_currency == "USD"
