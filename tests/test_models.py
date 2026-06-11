"""Tests for the SQLModel/Pydantic data models."""

from __future__ import annotations

from collector.models import Job, JobRead, RawPosting, SalaryEstimate


def test_job_from_raw_serializes_stack():
    raw = RawPosting(
        external_id="1",
        source="seed",
        title="Dev",
        company="Acme",
        stack=["Python", "AWS"],
    )
    job = Job.from_raw(raw)
    assert job.stack == "Python,AWS"
    assert job.stack_list == ["Python", "AWS"]


def test_job_from_raw_salary_source():
    with_salary = RawPosting(
        external_id="1", source="s", title="t", company="c", salary_min=100_000
    )
    without = RawPosting(external_id="2", source="s", title="t", company="c")
    assert Job.from_raw(with_salary).salary_source == "posting"
    assert Job.from_raw(without).salary_source == "heuristic"


def test_apply_estimate_sets_fields():
    job = Job.from_raw(RawPosting(external_id="1", source="s", title="t", company="c"))
    estimate = SalaryEstimate(
        salary_min=120_000,
        salary_max=160_000,
        currency="EUR",
        period="year",
        confidence=0.8,
        rationale="reasoned",
    )
    job.apply_estimate(estimate, "anthropic")
    assert job.salary_min == 120_000
    assert job.salary_max == 160_000
    assert job.salary_currency == "EUR"
    assert job.salary_source == "anthropic"
    assert job.salary_confidence == 0.8
    assert job.enriched_at is not None


def test_salary_estimate_confidence_bounds():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SalaryEstimate(salary_min=1, salary_max=2, confidence=1.5)


def test_job_read_from_job_mirrors_api_shape():
    job = Job.from_raw(
        RawPosting(
            external_id="1",
            source="seed",
            title="Dev",
            company="Acme",
            stack=["Python"],
        )
    )
    job.id = 7
    read = JobRead.from_job(job)
    assert read.id == 7
    assert read.stack == ["Python"]
    assert read.title == "Dev"


def test_empty_stack_list():
    job = Job.from_raw(RawPosting(external_id="1", source="s", title="t", company="c"))
    assert job.stack_list == []
