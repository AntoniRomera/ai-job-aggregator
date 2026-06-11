// Responsive grid of JobCards with an empty state.

import type { Job } from "../types";
import { JobCard } from "./JobCard";

export function JobGrid({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return (
      <div className="glass mt-8 rounded-2xl p-12 text-center text-slate-300">
        <p className="text-lg font-medium text-white">No matching jobs</p>
        <p className="mt-1 text-sm">Try clearing some filters or widening the pay range.</p>
      </div>
    );
  }

  return (
    <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {jobs.map((job) => (
        <JobCard key={`${job.source}-${job.external_id}`} job={job} />
      ))}
    </div>
  );
}
