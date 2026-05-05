// pipeline/navigator/actions/navigate.ts
import { chromium, BrowserContext, Page } from "playwright";
import { randomStealthConfig, applyStealthPatches, humanDelay } from "../stealth";
import * as fs from "fs";

export interface NavigateResult {
  url: string;
  html: string;
  interceptedRequests: Array<{ url: string; body: unknown }>;
  statusCode: number;
  timestamp: string;
}

export interface NavigateOptions {
  waitForSelector?: string;
  interceptPattern?: string;
  outputFile?: string;
  timeoutMs?: number;
}

export async function navigateAndExtract(
  targetUrl: string,
  options: NavigateOptions = {}
): Promise<NavigateResult> {
  const config = randomStealthConfig();
  const intercepted: Array<{ url: string; body: unknown }> = [];
  const timeoutMs = options.timeoutMs ?? 30000;

  const browser = await chromium.launch({
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-blink-features=AutomationControlled",
      "--disable-web-security",
      "--disable-dev-shm-usage",
    ],
  });

  try {
    const context: BrowserContext = await browser.newContext({
      userAgent: config.userAgent,
      viewport: config.viewport,
      locale: config.locale,
      timezoneId: config.timezoneId,
      extraHTTPHeaders: {
        "Accept-Language": `${config.locale},en;q=0.9`,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
      },
    });

    const page: Page = await context.newPage();
    await applyStealthPatches(page);

    // Intercept matching network responses
    if (options.interceptPattern) {
      page.on("response", async (response) => {
        if (response.url().includes(options.interceptPattern!)) {
          try {
            const body = await response.json();
            intercepted.push({ url: response.url(), body });
          } catch {
            // Not JSON — skip
          }
        }
      });
    }

    // Human-like delay before navigation
    await humanDelay(800, 300);

    const response = await page.goto(targetUrl, {
      waitUntil: "networkidle",
      timeout: timeoutMs,
    });

    if (options.waitForSelector) {
      await page.waitForSelector(options.waitForSelector, { timeout: 10000 });
    }

    const html = await page.content();

    const result: NavigateResult = {
      url: targetUrl,
      html,
      interceptedRequests: intercepted,
      statusCode: response?.status() ?? 0,
      timestamp: new Date().toISOString(),
    };

    // Write to file for Python parser to consume
    if (options.outputFile) {
      fs.writeFileSync(options.outputFile, JSON.stringify(result, null, 2));
    } else {
      // Default: write to stdout for pipeline piping
      process.stdout.write(JSON.stringify(result));
    }

    return result;
  } finally {
    await browser.close();
  }
}

// CLI entry point
if (require.main === module) {
  const url = process.argv[2];
  if (!url) {
    process.stderr.write("Usage: ts-node navigate.ts <url> [output.json]\n");
    process.exit(1);
  }
  navigateAndExtract(url, { outputFile: process.argv[3] }).catch((e) => {
    process.stderr.write(String(e) + "\n");
    process.exit(1);
  });
}
