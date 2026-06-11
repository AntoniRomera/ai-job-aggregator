import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { JobCard } from "../JobCard";
import type { Job } from "../../types";

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: 1,
    source: "seed",
    external_id: "x",
    title: "Senior Backend Engineer",
    company: "Northwind Labs",
    location: "San Francisco, CA",
    remote: false,
    description: "Own the payments API.",
    url: "https://example.com/job",
    stack: ["Python", "FastAPI"],
    salary_min: 175000,
    salary_max: 210000,
    salary_currency: "USD",
    salary_period: "year",
    salary_source: "anthropic",
    salary_confidence: 0.82,
    salary_rationale: "Senior role",
    posted_at: null,
    collected_at: "2026-01-01T00:00:00",
    enriched_at: null,
    ...overrides,
  };
}

describe("JobCard", () => {
  it("renders title, company, and pay band", () => {
    render(<JobCard job={makeJob()} />);
    expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
    expect(screen.getByText("Northwind Labs")).toBeInTheDocument();
    expect(screen.getByText("$175k – $210k")).toBeInTheDocument();
  });

  it("shows the on-site / remote badge", () => {
    render(<JobCard job={makeJob({ remote: true })} />);
    expect(screen.getByText("Remote")).toBeInTheDocument();
  });

  it("labels an AI estimate from Claude with confidence", () => {
    render(<JobCard job={makeJob({ salary_source: "anthropic", salary_confidence: 0.82 })} />);
    expect(screen.getByText(/AI est\. \(Claude\)/)).toBeInTheDocument();
    expect(screen.getByText(/82% conf\./)).toBeInTheDocument();
  });

  it("renders the stack tags and posting link", () => {
    render(<JobCard job={makeJob()} />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View posting/ })).toHaveAttribute(
      "href",
      "https://example.com/job",
    );
  });
});
