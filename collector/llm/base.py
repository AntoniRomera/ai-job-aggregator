"""SalaryEstimator protocol + shared prompt builder.

The structured-output schema is ``SalaryEstimate`` from ``collector.models`` so
the same Pydantic model flows from the LLM call all the way to the API layer.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import RawPosting, SalaryEstimate

SYSTEM_PROMPT = (
    "You are a compensation analyst. Given a software job posting, estimate a "
    "realistic GROSS ANNUAL salary range for the role. Base your estimate on the "
    "title, seniority, tech stack, location, and whether it is remote. Return a "
    "tight, defensible range in the posting's most likely currency (default USD). "
    "Be concrete: salary_min and salary_max must be positive numbers with "
    "salary_min <= salary_max. Provide a confidence in [0,1] and a one-sentence "
    "rationale."
)


def build_user_prompt(posting: RawPosting) -> str:
    """Render a posting into the user message for the estimator."""
    stack = ", ".join(posting.stack) if posting.stack else "unspecified"
    remote = "yes" if posting.remote else "no"
    location = posting.location or "unspecified"
    description = posting.description.strip()
    if len(description) > 2000:
        description = description[:2000] + "…"
    return (
        f"Title: {posting.title}\n"
        f"Company: {posting.company}\n"
        f"Location: {location}\n"
        f"Remote: {remote}\n"
        f"Tech stack: {stack}\n"
        f"Description:\n{description or '(no description provided)'}"
    )


@runtime_checkable
class SalaryEstimator(Protocol):
    """Provider-agnostic salary estimator contract."""

    name: str

    async def estimate(self, posting: RawPosting) -> SalaryEstimate:
        """Return a salary estimate for a single posting."""
        ...
