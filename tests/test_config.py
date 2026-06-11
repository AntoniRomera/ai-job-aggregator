"""Tests for typed settings."""

from __future__ import annotations

from collector.config import Settings


def test_defaults_are_offline():
    s = Settings(_env_file=None)
    assert s.anthropic_api_key is None
    assert s.gemini_api_key is None
    assert s.llm_provider == "auto"
    assert s.sources == "seed"
    assert s.anthropic_model == "claude-opus-4-8"


def test_source_list_normalizes():
    s = Settings(sources=" Seed , RemoteOK ,, ")
    assert s.source_list == ["seed", "remoteok"]


def test_cors_origin_list():
    s = Settings(cors_origins="http://a.com, http://b.com ,")
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]


def test_env_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "heuristic")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-8")
    s = Settings(_env_file=None)
    assert s.llm_provider == "heuristic"
    assert s.anthropic_model == "claude-opus-4-8"
