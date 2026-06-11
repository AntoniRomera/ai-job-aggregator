"""Tests for the deterministic offline salary estimator."""

from __future__ import annotations

import pytest
from collector.llm.heuristic_estimator import HeuristicSalaryEstimator
from collector.models import RawPosting


def _posting(**kwargs) -> RawPosting:
    base = {
        "external_id": "x",
        "source": "seed",
        "title": "Engineer",
        "company": "Acme",
        "stack": ["python"],
    }
    base.update(kwargs)
    return RawPosting(**base)


@pytest.fixture
def estimator() -> HeuristicSalaryEstimator:
    return HeuristicSalaryEstimator()


async def test_returns_valid_band(estimator):
    est = await estimator.estimate(_posting())
    assert est.salary_min > 0
    assert est.salary_min < est.salary_max
    assert est.currency == "USD"
    assert est.period == "year"
    assert 0.0 <= est.confidence <= 1.0


async def test_deterministic(estimator):
    """Same input -> same output (it is the offline backstop)."""
    p = _posting()
    a = await estimator.estimate(p)
    b = await estimator.estimate(p)
    assert (a.salary_min, a.salary_max) == (b.salary_min, b.salary_max)


async def test_seniority_increases_pay(estimator):
    junior = await estimator.estimate(_posting(title="Junior Python Engineer"))
    senior = await estimator.estimate(_posting(title="Senior Python Engineer"))
    staff = await estimator.estimate(_posting(title="Staff Python Engineer"))
    assert junior.salary_max < senior.salary_max < staff.salary_max


async def test_high_cost_location_pays_more(estimator):
    sf = await estimator.estimate(_posting(location="San Francisco, CA"))
    india = await estimator.estimate(_posting(location="Bangalore, India"))
    assert sf.salary_max > india.salary_max


async def test_stack_signal_changes_base(estimator):
    """A higher-paying stack signal lifts the band."""
    rust = await estimator.estimate(_posting(title="Engineer", stack=["rust"]))
    php = await estimator.estimate(_posting(title="Engineer", stack=["php"]))
    assert rust.salary_max > php.salary_max


async def test_unknown_stack_uses_default(estimator):
    est = await estimator.estimate(_posting(stack=["cobol"], title="Developer"))
    # default base is 135k, +/-12% band, rounded to nearest 1k
    assert est.salary_min == pytest.approx(119_000, abs=2_000)
    assert est.salary_max == pytest.approx(151_000, abs=2_000)
