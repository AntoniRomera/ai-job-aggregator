"""Tests for the Anthropic estimator's graceful-degradation behavior.

These never hit the network: with no API key, the client construction raises
and the estimator must fall back to the configured fallback estimator.
"""

from __future__ import annotations

import pytest
from collector.config import Settings
from collector.llm.anthropic_estimator import (
    AnthropicEstimateError,
    AnthropicSalaryEstimator,
)
from collector.llm.heuristic_estimator import HeuristicSalaryEstimator
from collector.models import RawPosting

POSTING = RawPosting(
    external_id="1", source="seed", title="Senior Go Engineer", company="Acme", stack=["go"]
)


async def test_missing_key_falls_back_to_heuristic():
    est = AnthropicSalaryEstimator(
        settings=Settings(anthropic_api_key=None),
        fallback=HeuristicSalaryEstimator(),
    )
    result = await est.estimate(POSTING)
    # The heuristic produced a real band rather than the pipeline crashing.
    assert result.salary_min > 0
    assert result.salary_min < result.salary_max


async def test_missing_key_no_fallback_raises():
    est = AnthropicSalaryEstimator(settings=Settings(anthropic_api_key=None), fallback=None)
    with pytest.raises(AnthropicEstimateError):
        await est.estimate(POSTING)


async def test_model_id_is_opus_4_8():
    """The default model is the configured Claude Opus 4.8 id."""
    est = AnthropicSalaryEstimator(settings=Settings(_env_file=None))
    assert est.settings.anthropic_model == "claude-opus-4-8"
