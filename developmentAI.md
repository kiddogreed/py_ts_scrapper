# 🧠 developmentAI.md — AI-Agnostic Development Tracker
## Hybrid Python + TypeScript Scraping Infrastructure

> **FOR ANY AI MODEL/AGENT:** This file is your single source of truth. Before doing anything,
> read this entire file top to bottom. Update the `## Progress` section after every completed step.
> Never delete history — only append and mark items. If you are resuming, check `## Current State`
> first. All architectural decisions are documented in `## Architecture Decisions`.

---

## 🔖 Document Version
- **Created:** 2026-05-04
- **Last Updated:** 2026-05-04
- **Project Root:** `c:/projects/2026/py_ts_scrapper`
- **Author:** kiddogreed Full-Stack Developer (Next.js, TS, Postgres, Software Dev Student)

---

## 📌 Current State
> **AI RESUME POINT** — Update this block every session before stopping.

```
STATUS: PHASE 1 COMPLETE — FastAPI microservice built and tested
LAST ACTION: Phase 1 — 14 files committed (commit: 36d8250). All 11 routes verified. Parser smoke test passed.
NEXT ACTION: Phase 2 — Next.js Dashboard (services/dashboard/)
BLOCKING ISSUES: None
```

---

## 🎯 Project Objective

Build a **production-grade, stealth-first, resilient** multi-layered scraping infrastructure
using three architectural patterns that work independently and together:

| Pattern | Stack | Primary Role |
|---|---|---|
| 1. Microservice Approach | Python FastAPI + Next.js TS | REST API scrape-as-a-service |
| 2. Polyglot Workflow | TypeScript (Nav) + Python (Parse) | Pipeline: browse → extract |
| 3. n8n Orchestrator | n8n + Bridge Nodes | Workflow automation & state mgmt |

**Anti-bot Priority:** Every layer must implement stealth and resilience by default.

---

## 🗺️ Master Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      n8n ORCHESTRATOR                        │
│  (Schedules jobs, manages retries, stores state in Postgres) │
└────────────┬──────────────────────────┬───────────────────┘
             │                          │
             ▼                          ▼
┌────────────────────┐      ┌────────────────────────┐
│  PATTERN 1         │      │  PATTERN 2             │
│  FastAPI Service   │      │  Polyglot Pipeline     │
│  (Python)          │      │  TS Navigator          │
│  ┌──────────────┐  │      │  → Python Parser       │
│  │ /scrape      │  │      └────────────────────────┘
│  │ /parse       │  │
│  │ /proxy/rotate│  │
│  └──────────────┘  │
│  Next.js Dashboard │
└────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                     POSTGRES DATABASE                        │
│  Tables: jobs, results, proxies, sessions, fingerprints      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structure (Target)

```
py_ts_scrapper/
│
├── developmentAI.md              ← YOU ARE HERE (AI tracker)
│
├── services/
│   ├── scraper-api/              ← Pattern 1: Python FastAPI
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── scrape.py
│   │   │   ├── parse.py
│   │   │   └── proxy.py
│   │   ├── core/
│   │   │   ├── stealth.py        ← Anti-bot fingerprint config
│   │   │   ├── proxy_manager.py
│   │   │   └── session_pool.py
│   │   ├── parsers/
│   │   │   ├── html_parser.py
│   │   │   └── schema.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── dashboard/                ← Pattern 1: Next.js TS Frontend
│       ├── app/
│       │   ├── page.tsx
│       │   ├── jobs/
│       │   └── api/
│       ├── package.json
│       └── Dockerfile
│
├── pipeline/                     ← Pattern 2: Polyglot Workflow
│   ├── navigator/                ← TypeScript (Playwright)
│   │   ├── index.ts
│   │   ├── stealth.ts
│   │   ├── actions/
│   │   │   ├── navigate.ts
│   │   │   └── intercept.ts
│   │   └── package.json
│   │
│   └── parser/                   ← Python (BeautifulSoup/lxml)
│       ├── main.py
│       ├── extractors/
│       │   ├── base.py
│       │   └── product.py
│       └── requirements.txt
│
├── orchestrator/                 ← Pattern 3: n8n
│   ├── workflows/
│   │   ├── scrape-job.json       ← n8n exported workflow
│   │   └── retry-handler.json
│   ├── custom-nodes/
│   │   ├── PythonBridgeNode/
│   │   └── ProxyRotatorNode/
│   └── docker-compose.yml
│
├── shared/
│   ├── db/
│   │   ├── schema.sql
│   │   └── migrations/
│   ├── types/
│   │   └── scraper.d.ts          ← Shared TS types
│   └── config/
│       └── fingerprints.json     ← Browser fingerprint pool
│
├── docker-compose.yml            ← Full stack compose
└── .env.example
```

---

## ✅ Progress Tracker

> **AI RULE:** Check off items as `[x]` when completed. Never delete rows. Add sub-items as needed.

### Phase 0 — Project Scaffolding ✅ COMPLETE (commit: 6300f19)
- [x] `0.1` Create directory structure
- [x] `0.2` Initialize git repository
- [x] `0.3` Create root `docker-compose.yml`
- [x] `0.4` Create `.env.example` with all required variables
- [x] `0.5` Create `shared/db/schema.sql` (Postgres tables)
- [x] `0.6` Create `shared/config/fingerprints.json` (WebGL/platform pool)
- [x] `0.7` Create `shared/config/proxies.json` (proxy list template)
- [x] `0.8` Create `shared/types/scraper.d.ts` (shared TS interfaces)

### Phase 1 — Pattern 1: Python FastAPI Scraper Microservice ✅ COMPLETE (commit: 36d8250)
- [x] `1.1` Initialize FastAPI project in `services/scraper-api/`
- [x] `1.2` Install dependencies (`playwright`, `httpx`, `beautifulsoup4`, `fake-useragent`, `tenacity`)
- [x] `1.3` Build `core/stealth.py` — browser fingerprint randomization
- [x] `1.4` Build `core/proxy_manager.py` — rotating proxy pool
- [x] `1.5` Build `core/session_pool.py` — persistent session/cookie management
- [x] `1.6` Build `routers/scrape.py` — POST `/scrape` endpoint
- [x] `1.7` Build `routers/parse.py` — POST `/parse` endpoint
- [x] `1.8` Build `routers/proxy.py` — GET `/proxy/rotate` endpoint
- [x] `1.9` Build `parsers/html_parser.py` with schema extraction
- [x] `1.10` Write Dockerfile for scraper-api
- [x] `1.11` Integration test: parser smoke test ✅, all 11 routes verified ✅

### Phase 2 — Pattern 1: Next.js Dashboard
- [ ] `2.1` Initialize Next.js 14+ project in `services/dashboard/`
- [ ] `2.2` Install dependencies (`axios`, `@tanstack/react-query`, `shadcn/ui`)
- [ ] `2.3` Build `/api/jobs` Next.js API route → proxies to FastAPI
- [ ] `2.4` Build jobs list page with real-time status
- [ ] `2.5` Build job detail / results viewer
- [ ] `2.6` Build proxy health dashboard
- [ ] `2.7` Write Dockerfile for dashboard

### Phase 3 — Pattern 2: Polyglot Pipeline
- [ ] `3.1` Initialize TypeScript project in `pipeline/navigator/`
- [ ] `3.2` Install Playwright + stealth plugins (`playwright-extra`, `puppeteer-extra-plugin-stealth`)
- [ ] `3.3` Build `stealth.ts` — headless browser stealth config
- [ ] `3.4` Build `actions/navigate.ts` — URL navigation with retry logic
- [ ] `3.5` Build `actions/intercept.ts` — network request interception (capture XHR/fetch)
- [ ] `3.6` Build IPC bridge: TS navigator dumps JSON to stdout/file → Python picks up
- [ ] `3.7` Initialize Python project in `pipeline/parser/`
- [ ] `3.8` Build `extractors/base.py` — abstract extractor class
- [ ] `3.9` Build `extractors/product.py` — concrete product page extractor
- [ ] `3.10` Build `main.py` — stdin/file reader → parse → output to Postgres
- [ ] `3.11` End-to-end test: TS navigates → Python parses → data in DB

### Phase 4 — Pattern 3: n8n Orchestrator
- [ ] `4.1` Set up n8n via Docker in `orchestrator/`
- [ ] `4.2` Connect n8n to Postgres for state management
- [ ] `4.3` Create `scrape-job.json` workflow (trigger → scrape → parse → store)
- [ ] `4.4` Create `retry-handler.json` workflow (failed jobs → exponential backoff)
- [ ] `4.5` Build custom n8n node: `PythonBridgeNode` (calls FastAPI)
- [ ] `4.6` Build custom n8n node: `ProxyRotatorNode` (fetches next proxy)
- [ ] `4.7` Set up n8n credentials for Postgres + FastAPI
- [ ] `4.8` Test full orchestrated workflow end-to-end

### Phase 5 — Stealth & Resilience Hardening
- [ ] `5.1` Implement TLS fingerprint rotation (using `curl_cffi` in Python)
- [ ] `5.2` Implement browser fingerprint pool (canvas, WebGL, fonts)
- [ ] `5.3` Implement human-like timing delays (Gaussian distribution)
- [ ] `5.4` Implement CAPTCHA detection + webhook alert
- [ ] `5.5` Implement IP reputation check before proxy use
- [ ] `5.6` Add rate limiting per domain (token bucket algorithm)
- [ ] `5.7` Implement session cookie persistence across requests

### Phase 6 — Production Hardening
- [ ] `6.1` Full Docker Compose stack (all services)
- [ ] `6.2` Centralized logging (structlog Python + pino TS → stdout)
- [ ] `6.3` Health check endpoints for all services
- [ ] `6.4` Postgres connection pooling (pgBouncer or asyncpg pool)
- [ ] `6.5` Secrets management via `.env` (never hardcode)
- [ ] `6.6` Write README.md with full setup instructions

---

## 🏗️ Architecture Decisions (ADRs)

> Every "Why" is documented here so any AI or developer can understand the reasoning.

### ADR-001: Why Python for Parsing, TypeScript for Navigation?

**Decision:** Use TypeScript/Playwright for browser navigation; Python for HTML/data parsing.

**Reasoning:**
- **TypeScript Strengths:** Playwright is TypeScript-native, has the best browser automation API,
  and async/await patterns map perfectly to sequential page interactions (click, wait, scroll).
- **Python Strengths:** `lxml`, `BeautifulSoup`, `parsel` (Scrapy's CSS/XPath engine) are the
  gold standard for HTML parsing. `pandas` for data transformation. The ML/NLP ecosystem
  (for intelligent extraction) lives in Python.
- **Result:** Each language does what it's best at. The handoff is a simple JSON blob.

### ADR-002: Why FastAPI Over Flask/Django for the Scraper Service?

**Decision:** FastAPI as the Python microservice framework.

**Reasoning:**
- Async-first: scraping is I/O bound. FastAPI + `asyncio` handles 100s of concurrent scrape
  requests without threading complexity.
- Auto-generates OpenAPI docs (critical for the Next.js frontend to consume correctly).
- Pydantic models enforce request/response schemas — prevents malformed scrape configs.
- `httpx` (async HTTP client) integrates natively into FastAPI's async context.

### ADR-003: Why n8n Over Airflow/Celery for Orchestration?

**Decision:** n8n as the workflow orchestrator (not Airflow, not Celery).

**Reasoning:**
- **vs Airflow:** Airflow is overkill for scraping workflows and requires significant DevOps.
  n8n runs in a single Docker container and has a visual editor for fast iteration.
- **vs Celery:** Celery needs Redis/RabbitMQ and has no visual state management. n8n stores
  execution history in Postgres (which we already have).
- **Custom Nodes:** n8n allows TypeScript custom nodes — we can write a `PythonBridgeNode`
  that calls our FastAPI service, keeping the orchestration layer thin.
- **Webhooks:** n8n's webhook triggers let external systems (a Next.js frontend button) kick
  off scrape jobs without building a separate job queue.

### ADR-004: Why Playwright Over Puppeteer/Selenium?

**Decision:** Playwright (via `playwright-extra` for stealth) over alternatives.

**Reasoning:**
- Playwright supports Chromium, Firefox, AND WebKit — rotating browsers is a stealth tactic.
- `playwright-extra` + `puppeteer-extra-plugin-stealth` patches 30+ bot-detection vectors
  (navigator.webdriver, chrome runtime, permissions API, etc.).
- Built-in network interception (`page.route()`) lets us capture XHR/fetch responses without
  full page rendering — critical for SPAs that load data via API.
- Better async support than Selenium.

### ADR-005: Why curl_cffi for HTTP-Only Scraping?

**Decision:** Use `curl_cffi` instead of `requests` or `httpx` for direct HTTP scraping.

**Reasoning:**
- `requests` and `httpx` use Python's TLS stack which has a unique fingerprint that
  anti-bot systems (Cloudflare, Akamai, Datadome) detect immediately.
- `curl_cffi` wraps libcurl and can **impersonate** Chrome/Firefox TLS fingerprints (JA3/JA4).
- For sites that don't need JavaScript rendering, `curl_cffi` is 10-100x faster than
  a headless browser AND bypasses TLS-based bot detection.

### ADR-006: Why Postgres Over MongoDB/Redis for Scrape State?

**Decision:** PostgreSQL as the primary state store.

**Reasoning:**
- The developer already uses Postgres (stated background) — no new infrastructure.
- Scrape jobs have relational structure: job → results → proxy_used → session.
- JSONB columns handle flexible result schemas without losing SQL query power.
- n8n natively integrates with Postgres for workflow execution history.

---

## 🛡️ Stealth & Resilience Reference

> Quick reference for all anti-bot countermeasures implemented.

### Browser-Level Stealth
```
- navigator.webdriver = false          (playwright-extra-stealth)
- Chrome runtime object patched        (stealth plugin)
- Randomized viewport: 1280-1920px     (core/stealth.py)
- Randomized user-agent per session    (fake-useragent library)
- Random accept-language headers       (en-US, en-GB, etc.)
- Timezone spoofing per proxy region   (match IP geolocation)
- WebGL renderer/vendor randomization  (fingerprint pool)
- Canvas fingerprint noise injection   (stealth plugin)
```

### Network-Level Stealth
```
- TLS fingerprint impersonation       (curl_cffi: chrome110, chrome120)
- Rotating residential proxies        (proxy_manager.py)
- Proxy validation before use         (IP reputation check)
- Per-domain rate limiting            (token bucket: max req/min)
- Random delays between requests      (Gaussian μ=2s, σ=0.8s)
- Referrer header spoofing            (Google/Bing/Direct)
- Cookie persistence across sessions  (session_pool.py)
```

### Resilience Patterns
```
- Retry with exponential backoff      (tenacity library, max 3 retries)
- Circuit breaker per domain          (fail fast if >5 consecutive errors)
- CAPTCHA detection → skip + alert    (webhook to n8n)
- Proxy failover (auto-swap on 403)   (proxy_manager.py)
- Job dead-letter queue in Postgres   (failed jobs table)
- Session rotation on fingerprint ban (session_pool.py)
```

---

## 💻 Core Code Reference

> Production-ready snippets. These are the canonical implementations. Do not deviate.

### 🐍 Python: `core/stealth.py`
```python
# services/scraper-api/core/stealth.py
import random
import json
from pathlib import Path

FINGERPRINT_POOL = json.loads(
    (Path(__file__).parent.parent.parent.parent / "shared/config/fingerprints.json").read_text()
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
]

TIMEZONES = ["America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London"]
LOCALES = ["en-US", "en-GB", "en-CA", "en-AU"]


def get_random_fingerprint() -> dict:
    """Returns a randomized browser fingerprint config."""
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": random.choice(VIEWPORTS),
        "timezone": random.choice(TIMEZONES),
        "locale": random.choice(LOCALES),
        "extra_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": f"{random.choice(LOCALES)},en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        },
    }
```

### 🐍 Python: `core/proxy_manager.py`
```python
# services/scraper-api/core/proxy_manager.py
import asyncio
import httpx
from typing import Optional
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    failures: int = 0
    max_failures: int = 3

    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"

    @property
    def is_healthy(self) -> bool:
        return self.failures < self.max_failures


class ProxyManager:
    def __init__(self, proxies: list[dict]):
        self._pool: deque[Proxy] = deque(
            Proxy(**p) for p in proxies
        )
        self._lock = asyncio.Lock()

    async def get_proxy(self) -> Optional[Proxy]:
        async with self._lock:
            # Rotate to next healthy proxy
            for _ in range(len(self._pool)):
                proxy = self._pool[0]
                self._pool.rotate(-1)
                if proxy.is_healthy:
                    return proxy
            return None  # All proxies exhausted

    async def mark_failure(self, proxy: Proxy) -> None:
        proxy.failures += 1
        if not proxy.is_healthy:
            logger.warning(f"Proxy {proxy.host}:{proxy.port} marked dead after {proxy.failures} failures")

    async def mark_success(self, proxy: Proxy) -> None:
        proxy.failures = max(0, proxy.failures - 1)

    async def validate_proxy(self, proxy: Proxy) -> bool:
        """Test proxy against a neutral endpoint."""
        try:
            async with httpx.AsyncClient(proxy=proxy.url, timeout=10.0) as client:
                r = await client.get("https://api.ipify.org?format=json")
                return r.status_code == 200
        except Exception:
            return False
```

### 🐍 Python: `routers/scrape.py`
```python
# services/scraper-api/routers/scrape.py
import asyncio
import random
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.stealth import get_random_fingerprint
from ..core.proxy_manager import ProxyManager

router = APIRouter(prefix="/scrape", tags=["scraping"])


class ScrapeRequest(BaseModel):
    url: HttpUrl
    wait_for: Optional[str] = None          # CSS selector to wait for
    intercept_pattern: Optional[str] = None # Capture matching network requests
    javascript: bool = True                 # Use browser vs curl_cffi
    timeout_ms: int = 30000


class ScrapeResponse(BaseModel):
    url: str
    html: Optional[str] = None
    intercepted: list[dict] = []
    status_code: int
    fingerprint_used: dict


@router.post("/", response_model=ScrapeResponse)
async def scrape_url(req: ScrapeRequest):
    if req.javascript:
        return await _browser_scrape(req)
    return await _http_scrape(req)


async def _browser_scrape(req: ScrapeRequest) -> ScrapeResponse:
    fingerprint = get_random_fingerprint()
    intercepted = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            user_agent=fingerprint["user_agent"],
            viewport=fingerprint["viewport"],
            locale=fingerprint["locale"],
            timezone_id=fingerprint["timezone"],
            extra_http_headers=fingerprint["extra_headers"],
        )

        # Patch navigator.webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = await context.new_page()

        # Network interception
        if req.intercept_pattern:
            async def handle_response(response):
                if req.intercept_pattern in response.url:
                    try:
                        data = await response.json()
                        intercepted.append({"url": response.url, "data": data})
                    except Exception:
                        pass
            page.on("response", handle_response)

        # Human-like random delay before navigation
        await asyncio.sleep(random.gauss(1.0, 0.3))

        response = await page.goto(str(req.url), timeout=req.timeout_ms, wait_until="networkidle")

        if req.wait_for:
            await page.wait_for_selector(req.wait_for, timeout=req.timeout_ms)

        html = await page.content()
        status = response.status if response else 0

        await browser.close()

    return ScrapeResponse(
        url=str(req.url),
        html=html,
        intercepted=intercepted,
        status_code=status,
        fingerprint_used=fingerprint,
    )


async def _http_scrape(req: ScrapeRequest) -> ScrapeResponse:
    """Fast HTTP-only scraping using curl_cffi for TLS fingerprint impersonation."""
    from curl_cffi.requests import AsyncSession

    fingerprint = get_random_fingerprint()

    async with AsyncSession(impersonate="chrome120") as session:
        response = await session.get(
            str(req.url),
            headers=fingerprint["extra_headers"],
            timeout=req.timeout_ms / 1000,
        )

    return ScrapeResponse(
        url=str(req.url),
        html=response.text,
        intercepted=[],
        status_code=response.status_code,
        fingerprint_used=fingerprint,
    )
```

### 🟦 TypeScript: `pipeline/navigator/stealth.ts`
```typescript
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

export function randomStealthConfig(): StealthConfig {
  return {
    userAgent: USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)],
    viewport: {
      width: 1280 + Math.floor(Math.random() * 640),
      height: 768 + Math.floor(Math.random() * 312),
    },
    locale: ["en-US", "en-GB", "en-CA"][Math.floor(Math.random() * 3)],
    timezoneId: ["America/New_York", "America/Chicago", "Europe/London"][
      Math.floor(Math.random() * 3)
    ],
  };
}

export async function applyStealthPatches(page: Page): Promise<void> {
  await page.addInitScript(() => {
    // Patch webdriver
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });

    // Patch chrome runtime
    (window as any).chrome = {
      runtime: {},
      loadTimes: () => {},
      csi: () => {},
    };

    // Patch permissions API
    const originalQuery = window.navigator.permissions.query.bind(
      window.navigator.permissions
    );
    window.navigator.permissions.query = (parameters: any) =>
      parameters.name === "notifications"
        ? Promise.resolve({ state: Notification.permission } as PermissionStatus)
        : originalQuery(parameters);

    // Patch plugin length
    Object.defineProperty(navigator, "plugins", {
      get: () => [1, 2, 3, 4, 5],
    });
  });
}

/** Gaussian random delay — mimics human think time */
export async function humanDelay(meanMs = 1500, stdMs = 500): Promise<void> {
  // Box-Muller transform for Gaussian distribution
  const u1 = Math.random();
  const u2 = Math.random();
  const z = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  const delay = Math.max(200, meanMs + z * stdMs);
  await new Promise((r) => setTimeout(r, delay));
}
```

### 🟦 TypeScript: `pipeline/navigator/actions/navigate.ts`
```typescript
// pipeline/navigator/actions/navigate.ts
import { chromium, BrowserContext, Page } from "playwright";
import { randomStealthConfig, applyStealthPatches, humanDelay } from "../stealth";
import * as fs from "fs";
import * as path from "path";

export interface NavigateResult {
  url: string;
  html: string;
  interceptedRequests: Array<{ url: string; body: unknown }>;
  statusCode: number;
  timestamp: string;
}

export async function navigateAndExtract(
  targetUrl: string,
  options: {
    waitForSelector?: string;
    interceptPattern?: string;
    outputFile?: string;
  } = {}
): Promise<NavigateResult> {
  const config = randomStealthConfig();
  const intercepted: Array<{ url: string; body: unknown }> = [];

  const browser = await chromium.launch({
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-blink-features=AutomationControlled",
      "--disable-web-security",
    ],
  });

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

  await humanDelay(800, 300);

  const response = await page.goto(targetUrl, {
    waitUntil: "networkidle",
    timeout: 30000,
  });

  if (options.waitForSelector) {
    await page.waitForSelector(options.waitForSelector, { timeout: 10000 });
  }

  const html = await page.content();
  await browser.close();

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
}

// CLI entry point
if (require.main === module) {
  const url = process.argv[2];
  if (!url) {
    console.error("Usage: ts-node navigate.ts <url> [output.json]");
    process.exit(1);
  }
  navigateAndExtract(url, { outputFile: process.argv[3] }).catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
```

### 🐍 Python: `pipeline/parser/main.py`
```python
# pipeline/parser/main.py
"""
Reads NavigateResult JSON from stdin or a file, parses the HTML,
and outputs structured data. Designed to be the second stage
of the Polyglot Pipeline (after TypeScript navigator).
"""
import sys
import json
import asyncio
import asyncpg
import os
from extractors.product import ProductExtractor


async def run(navigate_result: dict) -> None:
    extractor = ProductExtractor()
    structured_data = extractor.extract(
        html=navigate_result["html"],
        source_url=navigate_result["url"],
        intercepted=navigate_result.get("interceptedRequests", []),
    )

    # Write to Postgres
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        await conn.execute(
            """
            INSERT INTO results (job_id, url, data, scraped_at)
            VALUES ($1, $2, $3, $4)
            """,
            structured_data.get("job_id"),
            navigate_result["url"],
            json.dumps(structured_data),
            navigate_result["timestamp"],
        )
    finally:
        await conn.close()

    # Also write to stdout for debugging / n8n consumption
    print(json.dumps(structured_data, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        # Read from stdin (pipe from TypeScript navigator)
        data = json.loads(sys.stdin.read())

    asyncio.run(run(data))
```

### 🐍 Python: `pipeline/parser/extractors/base.py`
```python
# pipeline/parser/extractors/base.py
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Any


class BaseExtractor(ABC):
    """Abstract base for all page-specific extractors."""

    def extract(self, html: str, source_url: str, intercepted: list[dict]) -> dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        result = self._extract(soup, source_url, intercepted)
        result["source_url"] = source_url
        return result

    @abstractmethod
    def _extract(
        self,
        soup: BeautifulSoup,
        source_url: str,
        intercepted: list[dict],
    ) -> dict[str, Any]:
        """Implement extraction logic per page type."""
        ...
```

### 🗄️ SQL: `shared/db/schema.sql`
```sql
-- shared/db/schema.sql
-- Postgres schema for the scraping infrastructure

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scrape jobs
CREATE TABLE IF NOT EXISTS jobs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url         TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'done', 'failed', 'dead')),
    pattern     TEXT,             -- Pattern 1, 2, or 3
    retries     INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    metadata    JSONB DEFAULT '{}'
);

-- Scrape results
CREATE TABLE IF NOT EXISTS results (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID REFERENCES jobs(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    data        JSONB NOT NULL,
    scraped_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Proxy pool
CREATE TABLE IF NOT EXISTS proxies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    host        TEXT NOT NULL,
    port        INT NOT NULL,
    username    TEXT,
    password    TEXT,
    failures    INT DEFAULT 0,
    last_used   TIMESTAMPTZ,
    is_active   BOOLEAN DEFAULT TRUE
);

-- Session/cookie store
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain      TEXT NOT NULL,
    cookies     JSONB NOT NULL,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status);
CREATE INDEX IF NOT EXISTS jobs_url_idx ON jobs(url);
CREATE INDEX IF NOT EXISTS results_job_idx ON results(job_id);
```

---

## 🔧 Environment Variables Reference

```env
# .env.example

# Database
DATABASE_URL=postgresql://scraper:password@localhost:5432/scraper_db
POSTGRES_DB=scraper_db
POSTGRES_USER=scraper
POSTGRES_PASSWORD=change_me_in_production

# FastAPI Scraper Service
SCRAPER_API_HOST=0.0.0.0
SCRAPER_API_PORT=8000
SCRAPER_API_SECRET=change_me_in_production

# Next.js Dashboard
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=change_me_in_production

# n8n Orchestrator
N8N_PORT=5678
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change_me_in_production
N8N_DB_TYPE=postgresdb
N8N_DB_POSTGRESDB_HOST=postgres
N8N_DB_POSTGRESDB_PORT=5432
N8N_DB_POSTGRESDB_DATABASE=n8n_db
N8N_DB_POSTGRESDB_USER=scraper
N8N_DB_POSTGRESDB_PASSWORD=change_me_in_production

# Proxy Configuration
PROXY_LIST_PATH=./shared/config/proxies.json
PROXY_VALIDATION_ENABLED=true
```

---

## 🐳 Docker Compose (Root)

```yaml
# docker-compose.yml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./shared/db/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  scraper-api:
    build: ./services/scraper-api
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./shared:/app/shared:ro

  dashboard:
    build: ./services/dashboard
    env_file: .env
    ports:
      - "3000:3000"
    depends_on:
      - scraper-api

  n8n:
    image: n8nio/n8n:latest
    env_file: .env
    ports:
      - "${N8N_PORT}:5678"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - n8n_data:/home/node/.n8n
      - ./orchestrator/custom-nodes:/home/node/.n8n/custom

volumes:
  postgres_data:
  n8n_data:
```

---

## 📝 Session Log

> AI agents append to this section after each work session.

### Session 001 — 2026-05-04
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Created `developmentAI.md` with full architecture, ADRs, code reference,
  progress tracker, directory structure, and Docker configuration.
- **Completed Phases:** None (scaffold only)
- **Next Session Should:** Run Phase 0 — create directory structure, init git, write schema.sql

### Session 002 — 2026-05-04
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Executed Phase 0 in full:
  - Created all project directories (services/, pipeline/, orchestrator/, shared/)
  - Initialized git repo, set branch to `main`
  - Created `docker-compose.yml` (postgres, scraper-api, dashboard, n8n with healthchecks)
  - Created `.env.example` with all variables documented
  - Created `shared/db/schema.sql` (jobs, results, proxies, sessions, dead_letter + indexes + trigger)
  - Created `shared/config/fingerprints.json` (4 WebGL fingerprint profiles)
  - Created `shared/config/proxies.json` (proxy list template)
  - Created `shared/types/scraper.d.ts` (all shared TS interfaces)
  - Git commit: `6300f19`
- **Completed Phases:** Phase 0 ✅
- **Next Session Should:** Phase 1 — FastAPI scraper service (stealth.py, proxy_manager.py, session_pool.py, routers)

### Session 003 — 2026-05-04
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Executed Phase 1 in full:
  - `core/stealth.py` — fingerprint randomization, UA pool, viewport/timezone/locale pools, STEALTH_INIT_SCRIPT
  - `core/proxy_manager.py` — rotating pool, health tracking, circuit-breaker pattern
  - `core/session_pool.py` — in-memory cookie/session store, TTL + use-count expiry
  - `routers/scrape.py` — dual-mode (Playwright + curl_cffi), session reuse, network interception
  - `routers/parse.py` — rule-based + generic extraction endpoint
  - `routers/proxy.py` — rotate/status/validate/retire endpoints
  - `parsers/html_parser.py` — JSON-LD, Open Graph, CSS-selector rules, link extraction
  - `main.py` — lifespan startup, CORS, structlog, health endpoint
  - `Dockerfile` — python:3.12-slim + Playwright chromium
  - Fixed: absolute imports for uvicorn compatibility
  - Tests: parser smoke test ✅, all 11 routes import-verified ✅
  - Git commit: `36d8250`
- **Completed Phases:** Phase 1 ✅
- **Next Session Should:** Phase 2 — Next.js Dashboard (services/dashboard/)

---

## 🚨 AI Agent Rules (READ BEFORE EVERY ACTION)

1. **ALWAYS** read this entire file before starting any work
2. **ALWAYS** update `## Current State` at the end of your session
3. **ALWAYS** append to `## Session Log` — never delete history
4. **NEVER** deviate from the architecture in `## Architecture Decisions` without adding a new ADR
5. **NEVER** hardcode secrets — always use `.env` references
6. **NEVER** skip stealth/resilience requirements — they are non-negotiable
7. **COMMIT INCREMENTALLY** — one phase at a time, never bulk commits
8. **IF BLOCKED** — document the blocker in `## Current State` and stop
9. **CODE STYLE:** Python = Black formatter, 4 spaces. TypeScript = Prettier, 2 spaces.
10. **TEST BEFORE MARKING DONE** — a phase is not `[x]` until it has been tested

---

*This document is the single source of truth. All AI agents, developers, and tools must treat it as authoritative.*
