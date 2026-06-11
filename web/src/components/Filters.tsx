// Filter controls: search, stack multiselect, location input, remote toggle,
// and a minimum-pay range slider. Controlled by the parent via Filters state.

import type { Filters } from "../types";

interface Props {
  filters: Filters;
  stacks: string[];
  onChange: (next: Filters) => void;
  onReset: () => void;
}

const remoteOptions: { value: Filters["remote"]; label: string }[] = [
  { value: "all", label: "All" },
  { value: "remote", label: "Remote" },
  { value: "onsite", label: "On-site" },
];

export function FiltersPanel({ filters, stacks, onChange, onReset }: Props) {
  const toggleStack = (tag: string) => {
    const next = filters.stack.includes(tag)
      ? filters.stack.filter((t) => t !== tag)
      : [...filters.stack, tag];
    onChange({ ...filters, stack: next });
  };

  return (
    <aside className="glass flex flex-col gap-5 rounded-2xl p-5">
      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
          Search
        </label>
        <input
          type="text"
          value={filters.query}
          placeholder="title, company, keyword…"
          onChange={(e) => onChange({ ...filters, query: e.target.value })}
          className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-[var(--color-accent)] focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
          Location
        </label>
        <input
          type="text"
          value={filters.location}
          placeholder="e.g. Berlin, Remote"
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-[var(--color-accent)] focus:outline-none"
        />
      </div>

      <div>
        <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
          Remote
        </span>
        <div className="flex gap-2">
          {remoteOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange({ ...filters, remote: opt.value })}
              className={`flex-1 rounded-lg px-3 py-1.5 text-sm transition ${
                filters.remote === opt.value
                  ? "bg-[var(--color-accent)] text-white"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
          Min estimated pay: ${Math.round(filters.minPay / 1000)}k
        </label>
        <input
          type="range"
          min={0}
          max={300000}
          step={10000}
          value={filters.minPay}
          onChange={(e) => onChange({ ...filters, minPay: Number(e.target.value) })}
          className="w-full accent-[var(--color-accent)]"
        />
      </div>

      <div>
        <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-400">
          Stack
        </span>
        <div className="flex max-h-48 flex-wrap gap-1.5 overflow-y-auto">
          {stacks.map((tag) => {
            const active = filters.stack.includes(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => toggleStack(tag)}
                className={`rounded-md px-2 py-1 text-xs transition ${
                  active
                    ? "bg-[var(--color-accent)] text-white"
                    : "bg-white/10 text-indigo-100 hover:bg-white/20"
                }`}
              >
                {tag}
              </button>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={onReset}
        className="rounded-lg border border-white/15 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10"
      >
        Reset filters
      </button>
    </aside>
  );
}
