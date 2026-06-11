// react-query hook wrapping fetchJobs with caching + retry.

import { useQuery } from "@tanstack/react-query";
import { fetchJobs, type FetchResult } from "../lib/api";

export function useJobs() {
  return useQuery<FetchResult>({
    queryKey: ["jobs"],
    queryFn: ({ signal }) => fetchJobs(signal),
    staleTime: 60_000,
    retry: 1,
  });
}
