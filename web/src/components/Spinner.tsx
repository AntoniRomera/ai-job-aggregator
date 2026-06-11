// Loading indicator for the data-fetching state.

export function Spinner({ label = "Loading jobs…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-slate-300">
      <div
        className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-[var(--color-accent)]"
        role="status"
        aria-label="Loading"
      />
      <p className="text-sm">{label}</p>
    </div>
  );
}
