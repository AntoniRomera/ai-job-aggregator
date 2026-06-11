import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchJobs } from "../api";
import { mockJobs } from "../mockJobs";

describe("fetchJobs", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns backend jobs when the request succeeds", async () => {
    const backendJobs = [{ ...mockJobs[0], id: 42, title: "From Backend" }];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(backendJobs), { status: 200 }),
      ),
    );

    const result = await fetchJobs();
    expect(result.usingMock).toBe(false);
    expect(result.jobs).toHaveLength(1);
    expect(result.jobs[0].title).toBe("From Backend");
  });

  it("falls back to mock data when the backend errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("nope", { status: 500 })),
    );

    const result = await fetchJobs();
    expect(result.usingMock).toBe(true);
    expect(result.jobs).toEqual(mockJobs);
  });

  it("falls back to mock data on a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network down")));

    const result = await fetchJobs();
    expect(result.usingMock).toBe(true);
    expect(result.jobs).toEqual(mockJobs);
  });

  it("re-throws AbortError instead of falling back", async () => {
    const abort = new DOMException("aborted", "AbortError");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(abort));

    await expect(fetchJobs()).rejects.toThrow("aborted");
  });
});
