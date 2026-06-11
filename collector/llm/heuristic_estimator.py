"""Deterministic, no-network salary estimator.

This is the offline backstop: it always produces a plausible range so the seed
dataset enriches without any API key. The model is a transparent base-by-stack
estimate scaled by inferred seniority, location, and remote signals.
"""

from __future__ import annotations

from ..models import RawPosting, SalaryEstimate

# Rough USD annual base midpoints by primary stack signal.
_STACK_BASE: dict[str, float] = {
    "rust": 165_000,
    "go": 160_000,
    "golang": 160_000,
    "kubernetes": 160_000,
    "scala": 158_000,
    "elixir": 150_000,
    "swift": 150_000,
    "kotlin": 148_000,
    "machine learning": 170_000,
    "ml": 170_000,
    "ai": 172_000,
    "data": 150_000,
    "python": 150_000,
    "java": 148_000,
    "typescript": 145_000,
    "javascript": 140_000,
    "react": 142_000,
    "node": 142_000,
    "node.js": 142_000,
    "vue": 138_000,
    "php": 125_000,
    "ruby": 140_000,
    "c#": 140_000,
    "c++": 155_000,
    "devops": 155_000,
    "terraform": 155_000,
    "aws": 152_000,
    "sql": 130_000,
}

_DEFAULT_BASE = 135_000.0

_SENIORITY_MULTIPLIER: list[tuple[tuple[str, ...], float]] = [
    (("principal", "staff", "distinguished"), 1.55),
    (("lead", "head", "architect"), 1.40),
    (("senior", "sr.", "sr "), 1.25),
    (("mid", "intermediate"), 1.0),
    (("junior", "jr.", "jr ", "entry", "graduate", "intern"), 0.72),
]

# Cost-of-living style adjustment by location keyword.
_LOCATION_MULTIPLIER: list[tuple[tuple[str, ...], float]] = [
    (("san francisco", "bay area", "new york", "nyc", "seattle"), 1.20),
    (("london", "zurich", "geneva"), 1.10),
    (("boston", "los angeles", "austin", "washington"), 1.08),
    (("berlin", "amsterdam", "dublin", "paris"), 0.95),
    (("madrid", "barcelona", "lisbon", "warsaw", "remote"), 0.85),
    (("india", "bangalore", "manila", "lagos"), 0.55),
]


def _base_for_stack(stack: list[str], title: str) -> float:
    haystack = [s.lower() for s in stack] + [title.lower()]
    best = _DEFAULT_BASE
    matched = False
    for token, base in _STACK_BASE.items():
        if any(token in h for h in haystack) and (not matched or base > best):
            best = base
            matched = True
    return best


def _seniority_multiplier(title: str) -> float:
    t = title.lower()
    for keywords, mult in _SENIORITY_MULTIPLIER:
        if any(k in t for k in keywords):
            return mult
    return 1.0


def _location_multiplier(location: str, remote: bool) -> float:
    loc = location.lower()
    for keywords, mult in _LOCATION_MULTIPLIER:
        if any(k in loc for k in keywords):
            return mult
    return 0.9 if remote else 1.0


class HeuristicSalaryEstimator:
    """Deterministic salary estimator — requires no network or API key."""

    name = "heuristic"

    async def estimate(self, posting: RawPosting) -> SalaryEstimate:
        base = _base_for_stack(posting.stack, posting.title)
        base *= _seniority_multiplier(posting.title)
        base *= _location_multiplier(posting.location, posting.remote)

        # Build a +/- 12% band around the midpoint, rounded to the nearest 1k.
        salary_min = round(base * 0.88, -3)
        salary_max = round(base * 1.12, -3)

        return SalaryEstimate(
            salary_min=float(salary_min),
            salary_max=float(salary_max),
            currency="USD",
            period="year",
            confidence=0.35,
            rationale=(
                "Heuristic estimate from stack, seniority, and location signals "
                "(no LLM provider configured)."
            ),
        )
