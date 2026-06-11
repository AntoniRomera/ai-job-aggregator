// Data access layer. Calls the FastAPI backend; falls back to the static mock
// dataset on failure or when VITE_USE_MOCK=true, so the dashboard renders
// standalone with `npm run dev`.

import type { Job } from "../types";
import { mockJobs } from "./mockJobs";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export interface FetchResult {
  jobs: Job[];
  /** True when the data came from the mock fallback rather than the backend. */
  usingMock: boolean;
}

export async function fetchJobs(signal?: AbortSignal): Promise<FetchResult> {
  if (USE_MOCK) {
    return { jobs: mockJobs, usingMock: true };
  }

  try {
    const res = await fetch(`${API_URL}/api/jobs`, { signal });
    if (!res.ok) {
      throw new Error(`Backend responded ${res.status}`);
    }
    const jobs = (await res.json()) as Job[];
    return { jobs, usingMock: false };
  } catch (err) {
    // Network error / backend down -> graceful mock fallback (not for aborts).
    if (err instanceof DOMException && err.name === "AbortError") {
      throw err;
    }
    console.warn("Backend unreachable, using mock data:", err);
    return { jobs: mockJobs, usingMock: true };
  }
}
