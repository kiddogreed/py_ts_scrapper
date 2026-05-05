// pipeline/navigator/stealth.ts
import { BrowserContext, Page } from "playwright";

export interface StealthConfig {
  userAgent: string;
  viewport: { width: number; height: number };
  locale: string;
  timezoneId: string;
}

const USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
];

const VIEWPORTS = [
  { width: 1920, height: 1080 },
  { width: 1440, height: 900 },
  { width: 1366, height: 768 },
  { width: 1280, height: 800 },
];

const LOCALES = ["en-US", "en-GB", "en-CA"];
const TIMEZONES = ["America/New_York", "America/Chicago", "Europe/London"];

export function randomStealthConfig(): StealthConfig {
  return {
    userAgent: USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)],
    viewport: VIEWPORTS[Math.floor(Math.random() * VIEWPORTS.length)],
    locale: LOCALES[Math.floor(Math.random() * LOCALES.length)],
    timezoneId: TIMEZONES[Math.floor(Math.random() * TIMEZONES.length)],
  };
}

export async function applyStealthPatches(page: Page): Promise<void> {
  await page.addInitScript(() => {
    // Patch webdriver detection
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });

    // Patch chrome runtime (present in real browsers)
    (window as any).chrome = {
      runtime: {},
      loadTimes: () => {},
      csi: () => {},
    };

    // Patch permissions API to avoid notification permission fingerprint
    const originalQuery = window.navigator.permissions.query.bind(
      window.navigator.permissions
    );
    (window.navigator.permissions as any).query = (parameters: any) =>
      parameters.name === "notifications"
        ? Promise.resolve({ state: Notification.permission } as PermissionStatus)
        : originalQuery(parameters);

    // Patch plugin length to look like a real browser
    Object.defineProperty(navigator, "plugins", {
      get: () => [1, 2, 3, 4, 5],
    });

    // Patch language arrays
    Object.defineProperty(navigator, "languages", {
      get: () => ["en-US", "en"],
    });
  });
}

/** Gaussian random delay — mimics human think time (Box-Muller transform) */
export async function humanDelay(meanMs = 1500, stdMs = 500): Promise<void> {
  const u1 = Math.random();
  const u2 = Math.random();
  const z = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  const delay = Math.max(200, meanMs + z * stdMs);
  await new Promise((r) => setTimeout(r, delay));
}
