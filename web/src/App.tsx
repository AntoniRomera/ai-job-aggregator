// Dashboard shell: header, filters panel, stat bar, job grid, and
// loading/empty/error/mock states.

import { useMemo, useState } from "react";
import { EMPTY_FILTERS, type Filters } from "./types";
import { useJobs } from "./hooks/useJobs";
import { applyFilters, allStacks } from "./lib/filters";
import { FiltersPanel } from "./components/Filters";
import { JobGrid } from "./components/JobGrid";
import { StatBar } from "./components/StatBar";
import { Spinner } from "./components/Spinner";

export default function App() {
  const { data, isLoading, isError, refetch } = useJobs();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);

  const jobs = data?.jobs ?? [];
  const stacks = useMemo(() => allStacks(jobs), [jobs]);
  const filtered = useMemo(() => applyFilters(jobs, filters), [jobs, filters]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              AI Job Aggregator
            </h1>
            <p className="mt-1 text-sm text-slate-300">
              Job postings with LLM-estimated salary bands. Filter by stack, location,
              remote, and pay.
            </p>
          </div>
          {data?.usingMock ? (
            <span className="glass rounded-full px-3 py-1 text-xs text-amber-200">
              Mock data — backend offline
            </span>
          ) : (
            <span className="glass rounded-full px-3 py-1 text-xs text-emerald-200">
              Live · {jobs.length} postings
            </span>
          )}
        </div>
      </header>

      {isLoading ? (
        <Spinner />
      ) : isError ? (
        <div className="glass rounded-2xl p-12 text-center">
          <p className="text-lg font-medium text-white">Couldn’t load jobs</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-4 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm text-white"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
          <div className="lg:sticky lg:top-8 lg:self-start">
            <FiltersPanel
              filters={filters}
              stacks={stacks}
              onChange={setFilters}
              onReset={() => setFilters(EMPTY_FILTERS)}
            />
          </div>
          <div>
            <StatBar jobs={filtered} />
            <p className="mt-4 text-sm text-slate-400">
              Showing {filtered.length} of {jobs.length} postings
            </p>
            <JobGrid jobs={filtered} />
          </div>
        </div>
      )}

      <footer className="mt-12 text-center text-xs text-slate-500">
        Built with React 18 · Vite · Tailwind v4 · FastAPI · MIT licensed
      </footer>
    </div>
  );
}
