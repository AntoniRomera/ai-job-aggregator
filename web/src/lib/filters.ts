// Client-side filtering + small formatting helpers used across components.

import type { Filters, Job } from "../types";

export function applyFilters(jobs: Job[], filters: Filters): Job[] {
  const query = filters.query.trim().toLowerCase();
  const location = filters.location.trim().toLowerCase();

  return jobs.filter((job) => {
    if (filters.remote === "remote" && !job.remote) return false;
    if (filters.remote === "onsite" && job.remote) return false;

    if (location && !job.location.toLowerCase().includes(location)) return false;

    if (filters.stack.length > 0) {
      const jobStack = new Set(job.stack.map((s) => s.toLowerCase()));
      const hasAll = filters.stack.every((tag) => jobStack.has(tag.toLowerCase()));
      if (!hasAll) return false;
    }

    if (filters.minPay > 0) {
      // Keep jobs whose estimated top of band clears the minimum.
      if (job.salary_max === null || job.salary_max < filters.minPay) return false;
    }

    if (query) {
      const blob = `${job.title} ${job.company} ${job.description}`.toLowerCase();
      if (!blob.includes(query)) return false;
    }

    return true;
  });
}

/** All unique stack tags present in the dataset, sorted. */
export function allStacks(jobs: Job[]): string[] {
  const set = new Set<string>();
  jobs.forEach((j) => j.stack.forEach((s) => set.add(s)));
  return Array.from(set).sort((a, b) => a.localeCompare(b));
}

const currencySymbols: Record<string, string> = {
  USD: "$",
  EUR: "€",
  GBP: "£",
  CHF: "CHF ",
};

export function formatPay(job: Job): string {
  if (job.salary_min === null || job.salary_max === null) return "—";
  const sym = currencySymbols[job.salary_currency] ?? `${job.salary_currency} `;
  const fmt = (n: number) => `${sym}${Math.round(n / 1000)}k`;
  return `${fmt(job.salary_min)} – ${fmt(job.salary_max)}`;
}

/** Median midpoint salary across jobs that have a band (in USD-ish terms). */
export function medianPay(jobs: Job[]): number | null {
  const mids = jobs
    .filter((j) => j.salary_min !== null && j.salary_max !== null)
    .map((j) => ((j.salary_min as number) + (j.salary_max as number)) / 2)
    .sort((a, b) => a - b);
  if (mids.length === 0) return null;
  const mid = Math.floor(mids.length / 2);
  return mids.length % 2 === 0 ? (mids[mid - 1] + mids[mid]) / 2 : mids[mid];
}
