"""Tests for the provider-agnostic estimator factory (get_estimator)."""

from __future__ import annotations

from collector.config import Settings
from collector.llm import (
    AnthropicSalaryEstimator,
    GeminiSalaryEstimator,
    HeuristicSalaryEstimator,
    get_estimator,
)


def test_no_keys_defaults_to_heuristic():
    est = get_estimator(Settings(_env_file=None))
    assert isinstance(est, HeuristicSalaryEstimator)
    assert est.name == "heuristic"


def test_forced_heuristic():
    est = get_estimator(Settings(llm_provider="heuristic", anthropic_api_key="x"))
    assert isinstance(est, HeuristicSalaryEstimator)


def test_anthropic_key_prefers_anthropic():
    est = get_estimator(Settings(anthropic_api_key="sk-test", llm_provider="auto"))
    assert isinstance(est, AnthropicSalaryEstimator)
    # Falls back to the heuristic when no Gemini key is configured.
    assert isinstance(est.fallback, HeuristicSalaryEstimator)


def test_anthropic_then_gemini_fallback_chain():
    est = get_estimator(Settings(anthropic_api_key="sk-a", gemini_api_key="g", llm_provider="auto"))
    assert isinstance(est, AnthropicSalaryEstimator)
    assert isinstance(est.fallback, GeminiSalaryEstimator)
    assert isinstance(est.fallback.fallback, HeuristicSalaryEstimator)


def test_gemini_only():
    est = get_estimator(Settings(gemini_api_key="g", llm_provider="auto"))
    assert isinstance(est, GeminiSalaryEstimator)


def test_forced_anthropic():
    est = get_estimator(Settings(llm_provider="anthropic"))
    assert isinstance(est, AnthropicSalaryEstimator)
