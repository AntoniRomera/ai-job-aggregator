// Shared TS types mirroring the backend JobRead JSON shape (collector/models.py).

export type PayPeriod = "year" | "month" | "day" | "hour";
export type SalarySource = "posting" | "anthropic" | "gemini" | "heuristic";

export interface Job {
  id: number;
  source: string;
  external_id: string;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  description: string;
  url: string;
  stack: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_period: string;
  salary_source: string;
  salary_confidence: number | null;
  salary_rationale: string;
  posted_at: string | null;
  collected_at: string;
  enriched_at: string | null;
}

export interface Filters {
  stack: string[];
  location: string;
  remote: "all" | "remote" | "onsite";
  minPay: number;
  query: string;
}

export const EMPTY_FILTERS: Filters = {
  stack: [],
  location: "",
  remote: "all",
  minPay: 0,
  query: "",
};
