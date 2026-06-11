// Glassmorphism job card: title, company, stack tags, location/remote badge,
// and the estimated pay band (with a marker showing how the band was derived).

import type { Job } from "../types";
import { formatPay } from "../lib/filters";

const sourceLabel: Record<string, string> = {
  posting: "from posting",
  anthropic: "AI est. (Claude)",
  gemini: "AI est. (Gemini)",
  heuristic: "heuristic est.",
};

const sourceColor: Record<string, string> = {
  posting: "text-emerald-300",
  anthropic: "text-indigo-300",
  gemini: "text-sky-300",
  heuristic: "text-amber-300",
};

export function JobCard({ job }: { job: Job }) {
  const pay = formatPay(job);
  const label = sourceLabel[job.salary_source] ?? job.salary_source;
  const color = sourceColor[job.salary_source] ?? "text-slate-300";

  return (
    <article className="glass group flex flex-col gap-4 rounded-2xl p-5 transition-transform duration-200 hover:-translate-y-1 hover:border-white/30">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold leading-tight text-white">{job.title}</h3>
          <p className="text-sm text-slate-300">{job.company}</p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
            job.remote
              ? "bg-emerald-400/15 text-emerald-200"
              : "bg-slate-400/15 text-slate-200"
          }`}
        >
          {job.remote ? "Remote" : "On-site"}
        </span>
      </header>

      <div className="flex flex-wrap gap-1.5">
        {job.stack.slice(0, 6).map((tag) => (
          <span
            key={tag}
            className="rounded-md bg-white/10 px-2 py-0.5 text-xs text-indigo-100"
          >
            {tag}
          </span>
        ))}
      </div>

      <p className="line-clamp-2 text-sm text-slate-400">{job.description}</p>

      <footer className="mt-auto flex items-end justify-between gap-3 pt-2">
        <div>
          <p className="text-xl font-bold text-white">{pay}</p>
          <p className={`text-xs ${color}`}>
            {label}
            {job.salary_confidence != null && job.salary_source !== "posting"
              ? ` · ${Math.round(job.salary_confidence * 100)}% conf.`
              : ""}
          </p>
        </div>
        <div className="text-right text-xs text-slate-400">
          <p>{job.location || "—"}</p>
          {job.url ? (
            <a
              href={job.url}
              target="_blank"
              rel="noreferrer"
              className="text-[var(--color-accent-soft)] hover:underline"
            >
              View posting →
            </a>
          ) : null}
        </div>
      </footer>
    </article>
  );
}
