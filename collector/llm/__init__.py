"""LLM salary-estimator factory.

Provider selection:
  * ``LLM_PROVIDER`` forces a concrete provider when set to a name.
  * In ``auto`` mode: prefer Anthropic when ANTHROPIC_API_KEY is set, fall back
    to Gemini when GEMINI_API_KEY is set, and finally to a deterministic
    heuristic so the seed dataset always enriches offline.

Anthropic is wrapped so that a runtime failure during estimation transparently
falls back to Gemini (if available) and then the heuristic — the pipeline never
crashes because an API key is missing or a call fails.
"""

from __future__ import annotations

import logging

from ..config import Settings, get_settings
from .anthropic_estimator import AnthropicSalaryEstimator
from .base import SalaryEstimator
from .gemini_estimator import GeminiSalaryEstimator
from .heuristic_estimator import HeuristicSalaryEstimator

logger = logging.getLogger("collector.llm")


def get_estimator(settings: Settings | None = None) -> SalaryEstimator:
    """Return the configured salary estimator (with graceful fallbacks)."""
    settings = settings or get_settings()
    provider = settings.llm_provider

    heuristic = HeuristicSalaryEstimator()

    if provider == "heuristic":
        logger.info("Salary estimator: heuristic (forced)")
        return heuristic

    if provider == "anthropic":
        logger.info("Salary estimator: anthropic (forced)")
        return AnthropicSalaryEstimator(settings, fallback=heuristic)

    if provider == "gemini":
        logger.info("Salary estimator: gemini (forced)")
        return GeminiSalaryEstimator(settings, fallback=heuristic)

    # auto
    if settings.anthropic_api_key:
        gemini_fallback: SalaryEstimator = heuristic
        if settings.gemini_api_key:
            gemini_fallback = GeminiSalaryEstimator(settings, fallback=heuristic)
        logger.info("Salary estimator: anthropic (auto)")
        return AnthropicSalaryEstimator(settings, fallback=gemini_fallback)

    if settings.gemini_api_key:
        logger.info("Salary estimator: gemini (auto)")
        return GeminiSalaryEstimator(settings, fallback=heuristic)

    logger.info("Salary estimator: heuristic (no API keys configured — offline)")
    return heuristic


__all__ = [
    "SalaryEstimator",
    "AnthropicSalaryEstimator",
    "GeminiSalaryEstimator",
    "HeuristicSalaryEstimator",
    "get_estimator",
]
