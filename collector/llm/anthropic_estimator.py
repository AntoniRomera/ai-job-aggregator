"""Default salary estimator: Anthropic Claude.

Uses the official ``anthropic`` SDK with ``AsyncAnthropic`` and
``messages.parse(output_format=...)`` for guaranteed-schema structured output,
the ``claude-opus-4-8`` model, and adaptive thinking. Calls are retried with
exponential backoff; on persistent failure (or a missing SDK/key) estimation
delegates to the configured fallback estimator so the pipeline never crashes.
"""

from __future__ import annotations

import logging

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import Settings, get_settings
from ..models import RawPosting, SalaryEstimate
from .base import SYSTEM_PROMPT, SalaryEstimator, build_user_prompt

logger = logging.getLogger("collector.llm.anthropic")


class AnthropicEstimateError(RuntimeError):
    """Raised when the Anthropic call fails (after retries)."""


class AnthropicSalaryEstimator:
    """Salary estimator backed by Claude (claude-opus-4-8)."""

    name = "anthropic"

    def __init__(self, settings: Settings | None = None, fallback: SalaryEstimator | None = None):
        self.settings = settings or get_settings()
        self.fallback = fallback
        self._client = None

    def _get_client(self):  # type: ignore[no-untyped-def]
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError as exc:  # pragma: no cover - optional dep
                raise AnthropicEstimateError("anthropic SDK not installed") from exc
            if not self.settings.anthropic_api_key:
                raise AnthropicEstimateError("ANTHROPIC_API_KEY not set")
            self._client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        return self._client

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(AnthropicEstimateError),
    )
    async def _call(self, posting: RawPosting) -> SalaryEstimate:
        client = self._get_client()
        try:
            response = await client.messages.parse(
                model=self.settings.anthropic_model,
                max_tokens=1024,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_user_prompt(posting)}],
                output_format=SalaryEstimate,
            )
        except Exception as exc:  # network / API errors -> retryable
            raise AnthropicEstimateError(str(exc)) from exc

        parsed = response.parsed_output
        if parsed is None:
            raise AnthropicEstimateError("Anthropic returned no parsed output")
        return parsed

    async def estimate(self, posting: RawPosting) -> SalaryEstimate:
        try:
            return await self._call(posting)
        except Exception as exc:
            logger.warning(
                "Anthropic estimation failed for %s/%s: %s",
                posting.source,
                posting.external_id,
                exc,
            )
            if self.fallback is not None:
                logger.info("Falling back to %s estimator", self.fallback.name)
                return await self.fallback.estimate(posting)
            raise
