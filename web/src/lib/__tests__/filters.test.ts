import { describe, expect, it } from "vitest";
import { allStacks, applyFilters, formatPay, medianPay } from "../filters";
import { EMPTY_FILTERS, type Filters, type Job } from "../../types";

function makeJob(overrides: Partial<Job> = {}): Job {
  return {
    id: 1,
    source: "seed",
    external_id: "x",
    title: "Engineer",
    company: "Acme",
    location: "Remote",
    remote: false,
    description: "",
    url: "",
    stack: [],
    salary_min: null,
    salary_max: null,
    salary_currency: "USD",
    salary_period: "year",
    salary_source: "posting",
    salary_confidence: null,
    salary_rationale: "",
    posted_at: null,
    collected_at: "2026-01-01T00:00:00",
    enriched_at: null,
    ...overrides,
  };
}

function filters(overrides: Partial<Filters> = {}): Filters {
  return { ...EMPTY_FILTERS, ...overrides };
}

describe("applyFilters", () => {
  const jobs = [
    makeJob({ id: 1, remote: true, location: "Remote (US)", stack: ["Python", "AWS"], title: "Backend", salary_min: 150000, salary_max: 180000 }),
    makeJob({ id: 2, remote: false, location: "New York, NY", stack: ["Java"], title: "Platform", salary_min: 120000, salary_max: 140000 }),
    makeJob({ id: 3, remote: true, location: "Berlin, DE", stack: ["Rust", "Go"], title: "Systems" }),
  ];

  it("returns everything with empty filters", () => {
    expect(applyFilters(jobs, filters())).toHaveLength(3);
  });

  it("filters remote-only", () => {
    const result = applyFilters(jobs, filters({ remote: "remote" }));
    expect(result.map((j) => j.id)).toEqual([1, 3]);
  });

  it("filters onsite-only", () => {
    const result = applyFilters(jobs, filters({ remote: "onsite" }));
    expect(result.map((j) => j.id)).toEqual([2]);
  });

  it("filters by location substring (case-insensitive)", () => {
    const result = applyFilters(jobs, filters({ location: "berlin" }));
    expect(result.map((j) => j.id)).toEqual([3]);
  });

  it("requires all selected stack tags (AND, case-insensitive)", () => {
    expect(applyFilters(jobs, filters({ stack: ["python"] })).map((j) => j.id)).toEqual([1]);
    expect(applyFilters(jobs, filters({ stack: ["rust", "go"] })).map((j) => j.id)).toEqual([3]);
    expect(applyFilters(jobs, filters({ stack: ["rust", "python"] }))).toHaveLength(0);
  });

  it("filters by minimum pay against salary_max, dropping jobs without a band", () => {
    const result = applyFilters(jobs, filters({ minPay: 160000 }));
    expect(result.map((j) => j.id)).toEqual([1]);
  });

  it("searches title/company/description", () => {
    expect(applyFilters(jobs, filters({ query: "systems" })).map((j) => j.id)).toEqual([3]);
  });
});

describe("formatPay", () => {
  it("renders a band with the currency symbol in thousands", () => {
    const job = makeJob({ salary_min: 150000, salary_max: 180000, salary_currency: "USD" });
    expect(formatPay(job)).toBe("$150k – $180k");
  });

  it("uses EUR symbol", () => {
    const job = makeJob({ salary_min: 90000, salary_max: 110000, salary_currency: "EUR" });
    expect(formatPay(job)).toBe("€90k – €110k");
  });

  it("falls back to a dash without a band", () => {
    expect(formatPay(makeJob())).toBe("—");
  });
});

describe("allStacks", () => {
  it("returns sorted unique stack tags", () => {
    const jobs = [makeJob({ stack: ["React", "Python"] }), makeJob({ stack: ["Python", "AWS"] })];
    // Deduped (Python appears twice) and locale-sorted.
    expect(allStacks(jobs)).toEqual(["AWS", "Python", "React"]);
  });
});

describe("medianPay", () => {
  it("returns null when no job has a band", () => {
    expect(medianPay([makeJob(), makeJob()])).toBeNull();
  });

  it("computes the median midpoint for an odd count", () => {
    const jobs = [
      makeJob({ salary_min: 100000, salary_max: 100000 }),
      makeJob({ salary_min: 200000, salary_max: 200000 }),
      makeJob({ salary_min: 300000, salary_max: 300000 }),
    ];
    expect(medianPay(jobs)).toBe(200000);
  });

  it("averages the two middle values for an even count", () => {
    const jobs = [
      makeJob({ salary_min: 100000, salary_max: 100000 }),
      makeJob({ salary_min: 200000, salary_max: 200000 }),
    ];
    expect(medianPay(jobs)).toBe(150000);
  });
});
