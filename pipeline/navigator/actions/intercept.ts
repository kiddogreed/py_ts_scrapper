// pipeline/navigator/actions/intercept.ts
/**
 * Dedicated network request interception module.
 * Attaches response listeners to a Playwright page and collects
 * JSON payloads matching a URL pattern or content-type.
 *
 * Designed as a reusable capture layer — compose with navigate.ts
 * or use standalone when the page is already open.
 */
import { Page, Response } from "playwright";

export interface InterceptedResponse {
  url: string;
  method: string;
  status: number;
  contentType: string;
  body: unknown;
  timestamp: string;
}

export interface InterceptOptions {
  /** URL substring to match — intercept only matching responses */
  urlPattern?: string;
  /** Capture only responses with these HTTP status codes (default: all 2xx) */
  statusCodes?: number[];
  /** Maximum number of responses to capture (default: unlimited) */
  maxCaptures?: number;
}

/**
 * Attaches a response interceptor to an already-open Playwright page.
 * Returns a teardown function and the captured responses array.
 *
 * Usage:
 *   const { captures, teardown } = attachInterceptor(page, { urlPattern: '/api/' });
 *   await page.goto(...);
 *   await teardown();
 *   console.log(captures);
 */
export function attachInterceptor(
  page: Page,
  options: InterceptOptions = {}
): { captures: InterceptedResponse[]; teardown: () => void } {
  const captures: InterceptedResponse[] = [];
  const { urlPattern, statusCodes, maxCaptures } = options;

  const handler = async (response: Response) => {
    // Respect capture limit
    if (maxCaptures !== undefined && captures.length >= maxCaptures) return;

    // Filter by URL pattern
    if (urlPattern && !response.url().includes(urlPattern)) return;

    // Filter by status code
    const status = response.status();
    if (statusCodes) {
      if (!statusCodes.includes(status)) return;
    } else {
      // Default: only 2xx responses
      if (status < 200 || status >= 300) return;
    }

    const contentType = response.headers()["content-type"] ?? "";

    // Only attempt JSON parsing for JSON responses
    if (!contentType.includes("application/json")) return;

    try {
      const body = await response.json();
      captures.push({
        url: response.url(),
        method: response.request().method(),
        status,
        contentType,
        body,
        timestamp: new Date().toISOString(),
      });
    } catch {
      // Not parseable JSON — skip silently
    }
  };

  page.on("response", handler);

  return {
    captures,
    teardown: () => page.off("response", handler),
  };
}

/**
 * Waits until at least `count` responses have been captured, or timeout elapses.
 * Useful for SPAs that fire XHR requests shortly after DOMContentLoaded.
 */
export async function waitForCaptures(
  captures: InterceptedResponse[],
  count = 1,
  timeoutMs = 10000
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (captures.length < count) {
    if (Date.now() >= deadline) {
      throw new Error(
        `Timeout waiting for ${count} intercept(s). Only captured ${captures.length}.`
      );
    }
    await new Promise((r) => setTimeout(r, 100));
  }
}
