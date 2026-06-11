// Top summary stats: total count, remote percentage, median estimated pay.

import type { Job } from "../types";
import { medianPay } from "../lib/filters";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass flex-1 rounded-xl px-5 py-4">
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
    </div>
  );
}

export function StatBar({ jobs }: { jobs: Job[] }) {
  const total = jobs.length;
  const remote = jobs.filter((j) => j.remote).length;
  const remotePct = total > 0 ? Math.round((remote / total) * 100) : 0;
  const median = medianPay(jobs);
  const medianLabel = median != null ? `$${Math.round(median / 1000)}k` : "—";

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <Stat label="Jobs" value={String(total)} />
      <Stat label="Remote" value={`${remotePct}%`} />
      <Stat label="Median est. pay" value={medianLabel} />
    </div>
  );
}
