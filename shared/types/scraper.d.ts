// shared/types/scraper.d.ts
// Shared TypeScript types used across navigator, dashboard, and n8n custom nodes

export type JobStatus = "pending" | "running" | "done" | "failed" | "dead";
export type PatternType = "microservice" | "polyglot" | "n8n";

export interface Job {
  id: string;
  url: string;
  status: JobStatus;
  pattern: PatternType;
  retries: number;
  maxRetries: number;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown>;
}

export interface ScrapeResult {
  id: string;
  jobId: string;
  url: string;
  data: Record<string, unknown>;
  scrapedAt: string;
  createdAt: string;
}

export interface ProxyConfig {
  host: string;
  port: number;
  username?: string;
  password?: string;
}

export interface StealthConfig {
  userAgent: string;
  viewport: { width: number; height: number };
  locale: string;
  timezoneId: string;
}

export interface NavigateResult {
  url: string;
  html: string;
  interceptedRequests: Array<{ url: string; body: unknown }>;
  statusCode: number;
  timestamp: string;
}

export interface ScrapeRequest {
  url: string;
  waitFor?: string;
  interceptPattern?: string;
  javascript?: boolean;
  timeoutMs?: number;
}

export interface ScrapeResponse {
  url: string;
  html?: string;
  intercepted: Array<{ url: string; data: unknown }>;
  statusCode: number;
  fingerprintUsed: StealthConfig;
}
