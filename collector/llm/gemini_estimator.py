"""Fallback salary estimator: Google Gemini.

Uses the current unified ``google-genai`` SDK (NOT the deprecated
``google-generativeai``) with ``gemini-2.0-flash`` and structured output via a
response JSON schema. Retried with backoff; delegates to a fallback estimator
on persistent failure.
"""

from __future__ import annotations

import json
import logging

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import Settings, get_settings
from ..models import RawPosting, SalaryEstimate
from .base import SYSTEM_PROMPT, SalaryEstimator, build_user_prompt

logger = logging.getLogger("collector.llm.gemini")


class GeminiEstimateError(RuntimeError):
    """Raised when the Gemini call fails (after retries)."""


class GeminiSalaryEstimator:
    """Salary estimator backed by Gemini (gemini-2.0-flash)."""

    name = "gemini"

    def __init__(self, settings: Settings | None = None, fallback: SalaryEstimator | None = None):
        self.settings = settings or get_settings()
        self.fallback = fallback
        self._client = None

    def _get_client(self):  # type: ignore[no-untyped-def]
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:  # pragma: no cover - optional dep
                raise GeminiEstimateError("google-genai SDK not installed") from exc
            if not self.settings.gemini_api_key:
                raise GeminiEstimateError("GEMINI_API_KEY not set")
            self._client = genai.Client(api_key=self.settings.gemini_api_key)
        return self._client

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(GeminiEstimateError),
    )
    async def _call(self, posting: RawPosting) -> SalaryEstimate:
        client = self._get_client()
        prompt = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(posting)}"
        try:
            response = await client.aio.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": SalaryEstimate,
                },
            )
        except Exception as exc:
            raise GeminiEstimateError(str(exc)) from exc

        # google-genai returns a parsed instance when response_schema is a
        # Pydantic model; fall back to manual JSON parsing if not.
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, SalaryEstimate):
            return parsed
        text = getattr(response, "text", None)
        if not text:
            raise GeminiEstimateError("Gemini returned no content")
        try:
            return SalaryEstimate.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValueError) as exc:
            raise GeminiEstimateError(f"Could not parse Gemini output: {exc}") from exc

    async def estimate(self, posting: RawPosting) -> SalaryEstimate:
        try:
            return await self._call(posting)
        except Exception as exc:
            logger.warning(
                "Gemini estimation failed for %s/%s: %s",
                posting.source,
                posting.external_id,
                exc,
            )
            if self.fallback is not None:
                logger.info("Falling back to %s estimator", self.fallback.name)
                return await self.fallback.estimate(posting)
            raise
