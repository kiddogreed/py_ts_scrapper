# Replication & Mastery Guide

> **Goal:** Rebuild this entire project from scratch while *genuinely understanding* every layer.
> Follow the modules in order. Each module has a concept section, hands-on exercises you can run
> standalone, integration steps, and common mistakes to avoid.

---

## What You Will Master

| Technology | What You Learn |
|---|---|
| **Python** | requests → httpx → curl_cffi → Playwright stealth progression |
| **FastAPI** | Async APIs, lifespan events, asyncpg pool, Pydantic, structlog |
| **TypeScript / Node.js** | Playwright network interception, IPC bridge, stealth plugins |
| **Docker / Compose** | Dockerfiles, multi-stage builds, service networking, healthchecks |
| **PostgreSQL** | Schema design, JSONB, triggers, connection pooling |
| **pgBouncer** | Transaction mode pooling, env config, port mapping |
| **n8n** | Custom node development, workflow JSON, Postgres integration |
| **Next.js 15+** | App Router, API routes, TanStack Query, pino logging |
| **Full integration** | How all 8 services wire together and why each design decision was made |

---

## Learning Path Overview

```
Module 1 → Python scraping fundamentals (standalone scripts)
Module 2 → FastAPI async service (standalone, no Docker yet)
Module 3 → TypeScript navigator (standalone, Playwright)
Module 4 → Docker & Docker Compose (containerise what you built)
Module 5 → PostgreSQL & pgBouncer (schema design, pooling)
Module 6 → n8n custom nodes (orchestration layer)
Module 7 → Next.js dashboard (frontend + API routes)
Module 8 → Full integration (wire everything together)
Module 9 → Project scaffold from scratch (reproduce the directory structure)
```

Complete each module fully before moving on. Run every exercise. Break things intentionally and fix them — that is how you internalise the knowledge.

---

## Prerequisites

Install these before starting. Know how to use each one from the terminal.

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | https://python.org |
| Node.js | 22 LTS | https://nodejs.org |
| Docker Desktop | latest | https://docker.com |
| Git | 2.40+ | https://git-scm.com |
| VS Code | latest | https://code.visualstudio.com |

**Recommended VS Code extensions:**
- Python (ms-python.python)
- Pylance
- ESLint
- Docker
- REST Client (for testing APIs without leaving VS Code)

---

## Module 1 — Python Web Scraping (Standalone)

### Concept: The scraping stack ladder

Every scraper has the same problem: websites are built to detect bots. You climb a ladder of tools as detection gets harder:

```
Level 1: requests       — plain HTTP. Blocked by most sites.
Level 2: httpx          — async HTTP, better headers. Still fingerprinted.
Level 3: curl_cffi      — TLS fingerprint impersonation. Bypasses most JS-based detection.
Level 4: Playwright     — real browser. Bypasses everything except advanced fingerprinting.
Level 5: Playwright + stealth — randomised fingerprints, canvas noise, WebGL spoofing.
```

Do not skip straight to Playwright. Understanding each level teaches you *why* bots get blocked and *what* each tool does differently.

---

### 1.1 — Level 1: requests

```python
# practice/01_requests.py
import requests
from bs4 import BeautifulSoup

def scrape(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    return {
        "title": soup.find("title").get_text(strip=True) if soup.find("title") else None,
        "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
        "links": [a["href"] for a in soup.find_all("a", href=True)][:10],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(scrape("https://example.com"), indent=2))
```

Install deps and run:
```bash
pip install requests beautifulsoup4 lxml
python practice/01_requests.py
```

**What to experiment with:**
- Remove the User-Agent header — observe the response change
- Add `print(r.status_code, r.headers)` to see what the server sends back
- Try a URL that redirects — requests follows redirects automatically. Add `allow_redirects=False` to see the raw 301/302

---

### 1.2 — Level 2: httpx (async)

```python
# practice/02_httpx_async.py
import asyncio
import httpx
from bs4 import BeautifulSoup

async def scrape_one(client: httpx.AsyncClient, url: str) -> dict:
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    return {
        "url": url,
        "status": r.status_code,
        "title": soup.find("title").get_text(strip=True) if soup.find("title") else None,
    }

async def scrape_many(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 Chrome/120.0"},
        follow_redirects=True,
        timeout=15,
    ) as client:
        tasks = [scrape_one(client, url) for url in urls]
        return await asyncio.gather(*tasks)

if __name__ == "__main__":
    import json
    urls = [
        "https://example.com",
        "https://httpbin.org/get",
        "https://httpbin.org/headers",
    ]
    results = asyncio.run(scrape_many(urls))
    print(json.dumps(results, indent=2))
```

```bash
pip install httpx
python practice/02_httpx_async.py
```

**Key learning:** `asyncio.gather` fires all requests concurrently. A loop of `await client.get()` would be sequential and 3x slower. Always use `gather` or `asyncio.TaskGroup` for parallel scraping.

---

### 1.3 — Level 3: curl_cffi (TLS impersonation)

`curl_cffi` sends requests with the exact TLS fingerprint of a real Chrome browser. Many enterprise CDNs (Cloudflare, Akamai, Datadome) fingerprint the TLS handshake — `requests` and `httpx` both fail this check.

```python
# practice/03_curl_cffi.py
from curl_cffi import requests as cffi_requests
import json

def scrape(url: str) -> dict:
    # impersonate="chrome120" tells curl_cffi to use Chrome 120's TLS config
    with cffi_requests.Session(impersonate="chrome120") as session:
        r = session.get(url, timeout=15)
        return {
            "status": r.status_code,
            "tls_fingerprint": "chrome120",
            "content_length": len(r.content),
        }

if __name__ == "__main__":
    print(json.dumps(scrape("https://httpbin.org/headers"), indent=2))
```

```bash
pip install curl-cffi
python practice/03_curl_cffi.py
```

**What makes this different:** The JA3 fingerprint of `requests` differs from Chrome. `curl_cffi` mimics Chrome's TLS handshake exactly, passing CDN bot checks that block the other libraries.

---

### 1.4 — Level 4: Playwright basics

```python
# practice/04_playwright_basic.py
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        title = await page.title()
        html = await page.content()
        await browser.close()
    return {"url": url, "title": title, "html_length": len(html)}

if __name__ == "__main__":
    print(json.dumps(asyncio.run(scrape("https://example.com")), indent=2))
```

```bash
pip install playwright
playwright install chromium
python practice/04_playwright_basic.py
```

**Run with headless=False first:** Change `headless=True` to `headless=False`, watch the browser open and navigate. This builds intuition for what "goto + wait" really does. Then switch back to headless.

---

### 1.5 — Level 4: Playwright + network interception

Many modern sites load their real data via XHR/fetch calls, not in the initial HTML. Intercepting those gives you clean JSON without parsing HTML.

```python
# practice/05_playwright_intercept.py
import asyncio
import json
from playwright.async_api import async_playwright, Route, Request

intercepted: list[dict] = []

async def handle_route(route: Route, request: Request):
    # Called for every network request the page makes.
    if request.resource_type in ("xhr", "fetch"):
        response = await route.fetch()  # let the request through, capture response
        body = ""
        try:
            body = await response.text()
        except Exception:
            pass
        intercepted.append({
            "url": request.url,
            "method": request.method,
            "status": response.status,
            "body_preview": body[:500],
        })
        await route.fulfill(response=response)
    else:
        await route.continue_()

async def scrape(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.route("**/*", handle_route)
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        title = await page.title()
        await browser.close()
    return {"title": title, "intercepted_count": len(intercepted), "requests": intercepted[:5]}

if __name__ == "__main__":
    print(json.dumps(asyncio.run(scrape("https://httpbin.org/anything")), indent=2))
```

**What to experiment with:** Try this on a site you know loads data via API calls. Filter `intercepted` by URL patterns to find the specific API endpoint. You can often skip all HTML parsing once you know the API URL.

---

### 1.6 — Level 5: Playwright + stealth fingerprinting

Headless Chrome has telltale signs: `navigator.webdriver === true`, missing plugins, predictable screen sizes, no canvas noise. Advanced detection catches these.

```python
# practice/06_playwright_stealth.py
import asyncio
import json
import random
from playwright.async_api import async_playwright

# Minimal stealth script — overrides the most-checked properties
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};
"""

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

async def scrape(url: str) -> dict:
    viewport = random.choice(VIEWPORTS)
    ua = random.choice(USER_AGENTS)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport=viewport,
            user_agent=ua,
            locale="en-US",
            timezone_id="America/New_York",
        )
        await ctx.add_init_script(STEALTH_JS)
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        webdriver_detected = await page.evaluate("navigator.webdriver")
        detected_ua = await page.evaluate("navigator.userAgent")
        await browser.close()

    return {
        "webdriver_detected": webdriver_detected,
        "ua_seen_by_site": detected_ua,
        "viewport": viewport,
    }

if __name__ == "__main__":
    # Try https://bot.sannysoft.com for a real fingerprint test
    print(json.dumps(asyncio.run(scrape("https://httpbin.org/headers")), indent=2))
```

**Practice exercise:** Visit `https://bot.sannysoft.com` with this script. Each row on that page tests a different detection vector. Fail a row = anti-bot identifies you. Your goal is all green.

---

### 1.7 — BeautifulSoup: structured extraction

```python
# practice/07_parsing.py
from bs4 import BeautifulSoup
import json

SAMPLE_HTML = """
<html>
<head>
  <title>Product Page</title>
  <script type="application/ld+json">
  {"@type":"Product","name":"Test Widget","price":{"@type":"PriceSpecification","price":"9.99"}}
  </script>
  <meta property="og:title" content="Test Widget - Best Price">
  <meta property="og:image" content="https://example.com/img.jpg">
</head>
<body>
  <h1 class="product-title">Test Widget</h1>
  <span class="price">$9.99</span>
  <ul class="features">
    <li>Feature A</li>
    <li>Feature B</li>
  </ul>
</body>
</html>
"""

def extract_json_ld(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            results.append(json.loads(script.string))
        except json.JSONDecodeError:
            pass
    return results

def extract_open_graph(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")
    return {
        tag["property"][3:]: tag["content"]
        for tag in soup.find_all("meta", property=lambda v: v and v.startswith("og:"))
        if tag.get("content")
    }

def extract_by_selector(html: str, rules: list[dict]) -> dict:
    soup = BeautifulSoup(html, "lxml")
    out = {}
    for rule in rules:
        el = soup.select_one(rule["selector"])
        out[rule["name"]] = el.get_text(strip=True) if el else None
    return out

if __name__ == "__main__":
    print("JSON-LD:", json.dumps(extract_json_ld(SAMPLE_HTML), indent=2))
    print("OG tags:", json.dumps(extract_open_graph(SAMPLE_HTML), indent=2))
    print("CSS rules:", json.dumps(extract_by_selector(SAMPLE_HTML, [
        {"name": "title", "selector": "h1.product-title"},
        {"name": "price", "selector": "span.price"},
        {"name": "features", "selector": "ul.features"},
    ]), indent=2))
```

**Module 1 complete.** You can now scrape with plain HTTP, async HTTP, TLS impersonation, and a full browser. You can intercept XHR and stealth-patch the browser. You can parse HTML with CSS selectors and extract JSON-LD.

---

## Module 2 — FastAPI Async Service (Standalone)

### Concept: Why async matters for scraping

A synchronous server handles one request at a time. A scraping server spends most of its time waiting for remote servers (I/O). Async lets one process handle hundreds of concurrent scrape requests with `await` — no threads needed.

### Core patterns in this project

| Pattern | Why we use it |
|---|---|
| `lifespan` context manager | Clean startup/shutdown — init DB pool once, close on exit |
| `asyncpg` pool | Thread-safe async Postgres — much faster than `psycopg2` |
| `Pydantic` models | Auto-validates request JSON, generates OpenAPI docs |
| `structlog` JSON logging | Machine-parseable logs for production |
| `tenacity` retries | Automatic retry with exponential back-off on transient errors |

---

### 2.1 — Minimal FastAPI + async practice

```python
# practice/08_fastapi_basics.py
import asyncio
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
import uvicorn

log = structlog.get_logger()

class FakePool:
    def __init__(self):
        self.connections = 0
    async def connect(self):
        await asyncio.sleep(0.1)
        self.connections += 1
        return self
    async def close(self):
        log.info("pool.closed", connections=self.connections)

pool: FakePool | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    log.info("app.startup")
    pool = await FakePool().connect()
    yield                        # app handles requests here
    await pool.close()
    log.info("app.shutdown")

app = FastAPI(title="Practice API", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "pool_connections": pool.connections if pool else 0}

@app.get("/slow")
async def slow_endpoint():
    await asyncio.sleep(2)
    return {"message": "done after 2s"}

if __name__ == "__main__":
    uvicorn.run("08_fastapi_basics:app", host="0.0.0.0", port=8001, reload=True)
```

```bash
pip install fastapi uvicorn structlog
python practice/08_fastapi_basics.py
```

Open http://localhost:8001/docs — test `/slow` — notice the server is not blocked.

**Experiment:** Open two browser tabs at the same time and hit `/slow` in both. A sync server would queue the second request; async handles both concurrently.

---

### 2.2 — Pydantic request/response models

```python
# practice/09_pydantic_models.py
from pydantic import BaseModel, AnyHttpUrl, Field, model_validator
from typing import Literal

class ScrapeRequest(BaseModel):
    url: AnyHttpUrl
    pattern: Literal["generic", "product", "article", "listing"] = "generic"
    use_proxy: bool = False
    mode: Literal["playwright", "http"] = "http"
    timeout_ms: int = Field(default=30_000, ge=1_000, le=120_000)

    @model_validator(mode="after")
    def playwright_timeout_check(self) -> "ScrapeRequest":
        if self.mode == "playwright" and self.timeout_ms < 5_000:
            raise ValueError("playwright mode requires timeout_ms >= 5000")
        return self

# Test validation
try:
    req = ScrapeRequest(url="not-a-url", pattern="generic")
except Exception as e:
    print("Validation error (expected):", e)

req = ScrapeRequest(url="https://example.com", mode="playwright", timeout_ms=10_000)
print("Valid request:", req.model_dump_json(indent=2))
```

**Key learning:** Pydantic models are the contract between your API and its callers. If `url` is missing or malformed, FastAPI returns a 422 automatically — you do not write any validation code.

---

### 2.3 — asyncpg connection pool

```python
# practice/10_asyncpg_pool.py
# Requires running Postgres: docker run -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16-alpine
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:test@localhost:5432/postgres"

async def main():
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)

    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT version()")
        print("Postgres version:", result)

    # All three run at the same time — pool hands out connections
    await asyncio.gather(
        pool.fetchval("SELECT pg_sleep(0.1)"),
        pool.fetchval("SELECT pg_sleep(0.1)"),
        pool.fetchval("SELECT pg_sleep(0.1)"),
    )
    print("3 concurrent queries done (took ~0.1s, not 0.3s)")
    await pool.close()

asyncio.run(main())
```

**Why pool and not a single connection?** A single connection processes one query at a time. The pool lets multiple `await conn.query()` calls run simultaneously. `min_size=2` keeps 2 connections warm to avoid cold-start latency.

---

### 2.4 — Retry logic with tenacity

```python
# practice/11_tenacity_retry.py
import asyncio
import random
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(ConnectionError),
    before_sleep=before_sleep_log(log, logging.WARNING),
)
async def flaky_network_call(url: str) -> str:
    # Simulates a call that fails 60% of the time.
    if random.random() < 0.6:
        raise ConnectionError(f"Transient network error for {url}")
    return f"Success: {url}"

async def main():
    try:
        result = await flaky_network_call("https://example.com")
        print(result)
    except ConnectionError:
        print("All retries exhausted")

asyncio.run(main())
```

Run it several times — observe the exponential back-off in the logs. This is what wraps every `scraper_client.post()` call in the real scraper-api.

---

**Module 2 complete.** You understand async FastAPI, Pydantic validation, asyncpg pools, and tenacity retries. These are the core patterns used in `services/scraper-api/`.

---

## Module 3 — TypeScript Automation (Standalone)

### Concept: Why TypeScript for the browser layer?

Playwright's Node.js API is more mature than the Python one for the use cases in this project:
- Better CDP (Chrome DevTools Protocol) control
- Easier to build an IPC bridge (stdin/stdout JSON) that Python calls
- TypeScript catches type errors at compile time — important for complex network interception code

---

### 3.1 — TypeScript project setup

```bash
mkdir practice/ts-scraper && cd practice/ts-scraper
npm init -y
npm install typescript @types/node ts-node --save-dev
npm install playwright
npx playwright install chromium
npx tsc --init --target ES2022 --module NodeNext --moduleResolution NodeNext --strict true --outDir dist
```

---

### 3.2 — Basic Playwright navigation in TypeScript

```typescript
// practice/ts-scraper/src/navigate.ts
import { chromium } from "playwright";

interface ScrapeResult {
  url: string;
  title: string;
  htmlLength: number;
  links: string[];
}

async function scrape(url: string): Promise<ScrapeResult> {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.setExtraHTTPHeaders({
    "Accept-Language": "en-US,en;q=0.9",
  });

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
  const title = await page.title();
  const content = await page.content();
  const links = await page.$$eval("a[href]", (els) =>
    els.map((el) => (el as HTMLAnchorElement).href).slice(0, 10)
  );

  await browser.close();
  return { url, title, htmlLength: content.length, links };
}

scrape("https://example.com").then((r) => console.log(JSON.stringify(r, null, 2)));
```

```bash
npx ts-node src/navigate.ts
```

---

### 3.3 — Network interception in TypeScript

```typescript
// practice/ts-scraper/src/intercept.ts
import { chromium, Route, Request } from "playwright";

interface XhrEntry {
  url: string;
  method: string;
  status: number;
  bodyPreview: string;
}

async function scrapeWithIntercept(url: string): Promise<XhrEntry[]> {
  const intercepted: XhrEntry[] = [];
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.route("**/*", async (route: Route, request: Request) => {
    const type = request.resourceType();
    if (type === "xhr" || type === "fetch") {
      const response = await route.fetch();
      let body = "";
      try { body = (await response.text()).slice(0, 500); } catch {}
      intercepted.push({
        url: request.url(),
        method: request.method(),
        status: response.status(),
        bodyPreview: body,
      });
      await route.fulfill({ response });
    } else {
      await route.continue();
    }
  });

  await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
  await browser.close();
  return intercepted;
}

scrapeWithIntercept("https://httpbin.org/anything").then((r) =>
  console.log(JSON.stringify(r, null, 2))
);
```

---

### 3.4 — IPC bridge (Python calls TypeScript via stdin/stdout)

This is the pattern `pipeline/navigator/` uses. Python spawns the Node.js process, sends a JSON command to stdin, and reads the JSON result from stdout.

**TypeScript bridge** (`practice/ts-scraper/src/bridge.ts`):

```typescript
import { chromium } from "playwright";

interface Command {
  url: string;
  mode: "navigate" | "intercept";
}

async function main() {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const command: Command = JSON.parse(Buffer.concat(chunks).toString());

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(command.url, { waitUntil: "domcontentloaded" });
  const result = { url: command.url, title: await page.title() };
  await browser.close();

  process.stdout.write(JSON.stringify(result) + "\n");
}

main().catch((e) => {
  process.stderr.write(JSON.stringify({ error: String(e) }) + "\n");
  process.exit(1);
});
```

**Python IPC client** (`practice/ipc_client.py`):

```python
import subprocess, json

def call_navigator(url: str) -> dict:
    command = json.dumps({"url": url, "mode": "navigate"})
    proc = subprocess.run(
        ["npx", "ts-node", "practice/ts-scraper/src/bridge.ts"],
        input=command.encode(),
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())
    return json.loads(proc.stdout.decode())

print(call_navigator("https://example.com"))
```

**Key learning:** The navigator runs in its own process. Python does not need to know anything about Playwright. The JSON protocol is the contract. This makes the Python scraper-api agnostic to the browser implementation.

---

**Module 3 complete.** You can build a TypeScript Playwright scraper with network interception and connect it to Python via an IPC bridge.

---

## Module 4 — Docker & Docker Compose

### Concept: What Docker actually does

Docker packages your app + all its dependencies into an image. The image runs in a container — an isolated process that thinks it's a separate machine but shares the host kernel.

The critical mental model:
```
Image     = recipe (immutable snapshot built from a Dockerfile)
Container = running instance of an image
Volume    = persistent directory that survives container restarts
Network   = how containers find each other (by service name, not IP)
```

---

### 4.1 — Write a Dockerfile for the scraper API

```dockerfile
# syntax=docker/dockerfile:1

# Base image
FROM python:3.12-slim

# System dependencies
# gcc + libxml2 are needed to compile lxml
# curl is needed for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements FIRST, before code.
# Docker caches layers. If requirements.txt hasn't changed, this layer
# is reused even if your .py files changed — huge build speedup.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium --with-deps

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Build and run it:
```bash
cd services/scraper-api
docker build -t scraper-api:dev .
docker run -p 8000:8000 scraper-api:dev
```

---

### 4.2 — Multi-stage build (dashboard)

Multi-stage builds produce smaller production images by discarding build tools:

```dockerfile
# Stage 1: install deps (node_modules only needed during build)
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: build the Next.js app
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: run — no node_modules, no source code, only compiled output
FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

**What to compare:** Build single-stage and multi-stage. Run `docker images` and compare sizes. Multi-stage is typically 60–80% smaller.

---

### 4.3 — Docker Compose: service networking

When services are in the same Compose file, they communicate by **service name**, not `localhost`:

```yaml
services:
  postgres:
    image: postgres:16-alpine

  scraper-api:
    build: ./services/scraper-api
    environment:
      # "postgres" = the service name, not localhost
      DATABASE_URL: postgresql://scraper:change_me@postgres:5432/scraper_db

  dashboard:
    build: ./services/dashboard
    environment:
      # "scraper-api" = the service name
      SCRAPER_API_URL: http://scraper-api:8000
```

**Common mistake:** Using `localhost` in Docker. `localhost` inside a container refers to that container itself, not other containers. Always use the service name.

---

### 4.4 — depends_on with healthchecks

```yaml
  dashboard:
    depends_on:
      scraper-api:
        condition: service_healthy
      postgres:
        condition: service_healthy
```

Without `condition: service_healthy`, Compose only waits for the container to *start*, not for the service inside to be *ready*. Postgres takes ~2 seconds to initialise — without the condition, dashboard crashes on startup with "connection refused".

**Experiment:** Remove `condition: service_healthy`, run `docker compose up`, watch dashboard fail, then add it back.

---

### 4.5 — pgBouncer in Docker

pgBouncer sits between your app and Postgres, reusing connections:

```
App → pgBouncer:5432 → PostgreSQL:5432
      (external: 6432)  (internal: 5432)
```

Key config points:
- Port mapping `6432:5432` means external port 6432 maps to the container's internal port 5432
- Apps inside Docker Compose connect to `pgbouncer:5432` (the **internal** port)
- The `edoburu/pgbouncer` image reads config from environment variables (not a config file)
- `POOL_MODE=transaction` — connections are released after each transaction, not after the session ends

```yaml
  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_USER: scraper
      DB_PASSWORD: change_me
      DB_NAME: scraper_db
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 100
      DEFAULT_POOL_SIZE: 20
    ports:
      - "6432:5432"
    depends_on:
      postgres:
        condition: service_healthy
```

**Why transaction mode?** Session mode keeps a Postgres connection open for the entire session lifetime. Transaction mode returns the connection to the pool after each `COMMIT`. Much more efficient for async apps that have hundreds of concurrent connections but only brief bursts of actual DB work.

---

**Module 4 complete.** You can write Dockerfiles, use multi-stage builds, configure Compose networking, and understand healthchecks and pgBouncer.

---

## Module 5 — PostgreSQL Schema Design

### Concept: Design for the access patterns, not the entities

The schema in this project is designed around how data is *queried*, not just what data exists.

---

### 5.1 — Schema walkthrough

```sql
-- UUID primary keys: no integer sequences to coordinate across distributed services
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- jobs: the unit of work
CREATE TABLE IF NOT EXISTS jobs (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    url         TEXT        NOT NULL,
    -- status is constrained by a CHECK — invalid transitions are caught at DB level
    status      TEXT        NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','running','done','failed','dead')),
    pattern     TEXT,
    retries     INT         NOT NULL DEFAULT 0,
    max_retries INT         NOT NULL DEFAULT 3,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- JSONB: flexible bag for anything that doesn't have a fixed schema
    metadata    JSONB       NOT NULL DEFAULT '{}'
);

-- results: one-to-many from jobs (a retry produces another result row)
CREATE TABLE IF NOT EXISTS results (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID        REFERENCES jobs(id) ON DELETE CASCADE,
    url         TEXT        NOT NULL,
    data        JSONB       NOT NULL,
    scraped_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- proxies: health-tracked proxy pool
CREATE TABLE IF NOT EXISTS proxies (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    host        TEXT        NOT NULL,
    port        INT         NOT NULL,
    username    TEXT,
    password    TEXT,
    failures    INT         NOT NULL DEFAULT 0,
    last_used   TIMESTAMPTZ,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    UNIQUE(host, port)
);

-- sessions: cookie/fingerprint cache per domain
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain      TEXT        NOT NULL,
    cookies     JSONB       NOT NULL,
    user_agent  TEXT,
    fingerprint JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

-- dead_letter: jobs that exhausted all retries — for inspection/replay
CREATE TABLE IF NOT EXISTS dead_letter (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID        REFERENCES jobs(id) ON DELETE SET NULL,
    url         TEXT        NOT NULL,
    error       TEXT,
    payload     JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 5.2 — Useful queries to know

```sql
-- All failed jobs in the last hour
SELECT id, url, retries, updated_at
FROM jobs
WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '1 hour'
ORDER BY updated_at DESC;

-- Get job + all its results in one query (no N+1 problem)
SELECT j.*, jsonb_agg(r.*) AS results
FROM jobs j
LEFT JOIN results r ON r.job_id = j.id
WHERE j.id = '<uuid>'
GROUP BY j.id;

-- Query inside JSONB: find jobs where metadata has a specific value
SELECT * FROM jobs WHERE metadata @> '{"source": "n8n"}';

-- JSONB index (add this for production)
CREATE INDEX idx_jobs_metadata ON jobs USING gin(metadata);

-- Update and return in one statement — avoids a second SELECT
-- Also acts as an optimistic lock: only updates if status is still 'pending'
UPDATE jobs SET status = 'running', updated_at = NOW()
WHERE id = $1 AND status = 'pending'
RETURNING *;
```

---

### 5.3 — Why JSONB instead of extra columns

`metadata JSONB` stores anything that doesn't have a fixed schema: n8n workflow IDs, Stripe customer IDs, experiment flags, webhook payloads. Adding a column requires a migration; updating JSONB does not.

Rule of thumb: **structured, always-present, queried fields → columns. Variable, optional, infrequently-queried data → JSONB**.

---

### 5.4 — Auto-initialise Postgres in Docker

Postgres runs any `.sql` files placed in `/docker-entrypoint-initdb.d/` on first startup:

```yaml
  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./shared/db/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
      - ./orchestrator/init/02_n8n_db.sql:/docker-entrypoint-initdb.d/02_n8n_db.sql
```

Files run in alphabetical order. `01_schema.sql` creates the app tables. `02_n8n_db.sql` creates the n8n database.

**Important:** These init scripts only run when the data volume is empty (first-ever startup). If you change the schema, either drop the volume (`docker compose down -v`) or write a migration.

---

**Module 5 complete.** You understand the schema design choices, JSONB, and how Postgres initialises in Docker.

---

## Module 6 — n8n Custom Node Development

### Concept: What n8n actually is

n8n is a self-hosted workflow automation tool — like Zapier but open-source. You connect nodes in a visual editor. Each node is a TypeScript class that defines inputs, outputs, and an `execute()` method.

This project uses n8n as the **orchestration layer**: it triggers scrape jobs on a schedule, handles retries, and routes failures to the dead letter queue.

---

### 6.1 — Custom node structure

Every n8n custom node is a TypeScript package that exports a class implementing `INodeType`:

```typescript
import {
  INodeType, INodeTypeDescription,
  IExecuteFunctions, INodeExecutionData
} from "n8n-workflow";

export class MyCustomNode implements INodeType {
  description: INodeTypeDescription = {
    displayName: "My Custom Node",
    name: "myCustomNode",
    group: ["transform"],
    version: 1,
    description: "Does something useful",
    defaults: { name: "My Custom Node" },
    inputs: ["main"],
    outputs: ["main"],
    properties: [
      {
        displayName: "URL",
        name: "url",
        type: "string",
        default: "",
        required: true,
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const results: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const url = this.getNodeParameter("url", i) as string;
      results.push({ json: { url, processed: true } });
    }
    return [results];  // array of arrays: one per output connector
  }
}
```

---

### 6.2 — PythonBridgeNode

The `PythonBridgeNode` in this project calls the FastAPI scraper-api. It:
1. Reads the `url` and `pattern` parameters from the n8n UI
2. Makes an HTTP POST to `http://scraper-api:8000/scrape/`
3. Returns the scraped data as output JSON

Key things to understand in `orchestrator/custom-nodes/PythonBridgeNode/src/PythonBridgeNode.node.ts`:
- Uses `this.helpers.httpRequest()` — n8n's built-in HTTP helper (handles retries, auth)
- `credentials` field connects to `ScraperApiCredentials` — stores the API base URL securely
- Output format must match `INodeExecutionData` (`{ json: {...} }`)

---

### 6.3 — ProxyRotatorNode

The `ProxyRotatorNode` calls `GET /proxy/rotate` on the scraper-api and outputs the next healthy proxy config. Downstream nodes can use that proxy for their requests.

Key design: it is a **stateless** node — it does not track state itself. State lives in the scraper-api's `ProxyManager`, which reads from `proxies.json` and tracks failures.

---

### 6.4 — Deploy custom nodes to n8n in Docker

```yaml
  n8n:
    volumes:
      - n8n_data:/home/node/.n8n
      - ./orchestrator/custom-nodes:/home/node/.n8n/custom
```

n8n discovers any package in `/home/node/.n8n/custom/` that exports `INodeType` classes in its `package.json`'s `n8n.nodes` field.

After changing a custom node:
```bash
docker compose restart n8n
```

---

### 6.5 — Build custom nodes before Docker starts

The `.ts` files must be compiled to `.js` before n8n can load them:

```bash
cd orchestrator/custom-nodes/PythonBridgeNode
npm install
npm run build   # tsc compiles .ts -> .js (dist/ folder)
```

The compiled `.js` files are what n8n actually loads. The `index.ts` declares which node classes to export.

---

**Module 6 complete.** You can build, compile, and deploy custom n8n nodes. You understand the IPC between n8n and scraper-api.

---

## Module 7 — Next.js 15 App Router Dashboard

### Concept: App Router vs Pages Router

Next.js 13+ introduced the App Router. Key differences:

| Feature | Pages Router | App Router |
|---|---|---|
| Default component type | Client | Server |
| Layout | `_app.tsx` | `layout.tsx` (nested) |
| API routes | `pages/api/` | `app/api/.../route.ts` |
| Data fetching | `getServerSideProps` | `async` server components |
| Client state | anywhere | only `"use client"` components |

This project uses App Router. All `page.tsx` files that use `useState`/`useQuery` need `"use client"` at the top.

---

### 7.1 — API route structure

```typescript
// app/api/jobs/route.ts — handles GET /api/jobs and POST /api/jobs
export async function GET(req: NextRequest) { /* ... */ }
export async function POST(req: NextRequest) { /* ... */ }

// app/api/jobs/[id]/route.ts — handles /api/jobs/:id
// Next.js 15: params is a Promise, must be awaited
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  // ...
}
```

---

### 7.2 — TanStack Query v5 in App Router

```typescript
"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// Fetch with automatic polling
const { data: jobs, isLoading } = useQuery({
  queryKey: ["jobs", statusFilter],
  queryFn: async () => {
    const r = await fetch(`/api/jobs?status=${statusFilter}`);
    return r.json();
  },
  refetchInterval: 5_000,  // poll every 5s
});

// Mutate (POST) and invalidate cache on success
const qc = useQueryClient();
const submitJob = useMutation({
  mutationFn: (body: { url: string; pattern: string }) =>
    fetch("/api/jobs", {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    }).then(r => r.json()),
  onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
});
```

**Key learning:** `invalidateQueries` after a mutation causes the job list to refetch immediately. Without it, the UI won't show the new job until the next 5-second poll.

---

### 7.3 — Database access from API routes

API routes run on the server (Node.js). They can directly query Postgres using `pg`:

```typescript
// lib/db.ts — singleton pool (global prevents re-creation on hot reload)
import { Pool } from "pg";
declare global { var __pgPool: Pool | undefined; }

const db: Pool = global.__pgPool ?? new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 5,
});
if (process.env.NODE_ENV !== "production") global.__pgPool = db;
export default db;
```

**Why the global pattern?** Next.js hot reload re-executes module code on each file change. Without the `global` check, you'd create a new pool on every reload, eventually exhausting Postgres connections.

---

### 7.4 — Tailwind v4

Tailwind v4 no longer needs a `tailwind.config.ts` file. The entire config is CSS-first:

```css
/* app/globals.css */
@import "tailwindcss";

/* Custom tokens (optional) */
@theme {
  --color-brand: #7c3aed;
}
```

Classes like `bg-gray-950`, `text-white`, `hover:text-gray-300` work exactly as before.

---

**Module 7 complete.** You understand App Router, API routes with dynamic params, TanStack Query polling + mutations, and Tailwind v4.

---

## Module 8 — Full Integration

### How all layers connect

```
User (browser)
  |
  v
Next.js Dashboard (port 3000)
  |  POST /api/jobs --> fire-and-forget async scrape
  |  GET /api/proxy --> proxy status
  |
  v
scraper-api (port 8000)
  |  POST /scrape/ (mode=playwright or http)
  |  curl_cffi or Playwright stealth browser
  |  BeautifulSoup parsing
  |
  v
pgBouncer (port 6432 external / 5432 internal)
  |
  v
PostgreSQL (port 5432)
  |  jobs, results, proxies, sessions, dead_letter

n8n (port 5679)
  |  cron trigger --> PythonBridgeNode --> POST /scrape/
  |  retry-handler --> re-submits failed jobs
  |
  v
PostgreSQL (separate n8n_db database)
```

---

### 8.1 — End-to-end flow: submit a scrape job

1. User fills the form in the dashboard and clicks Submit
2. `POST /api/jobs` inserts a row in `jobs` with status `pending`
3. Fire-and-forget async function:
   - Updates status to `running`
   - Calls `scraperClient.post("/scrape/", { url, pattern })`
   - On success: inserts row in `results`, updates `jobs.status = 'done'`
   - On failure: updates `jobs.status = 'failed'`
4. Dashboard polls `GET /api/jobs` every 5 seconds
5. Job transitions: `pending → running → done`
6. User clicks the job ID to see the scraped result JSON

---

### 8.2 — End-to-end flow: n8n triggers a scrape

1. n8n cron trigger fires (e.g. every 5 minutes)
2. PythonBridgeNode: `POST http://scraper-api:8000/scrape/` with `{ url, pattern }`
3. scraper-api processes the request (same code path as dashboard-submitted jobs)
4. n8n receives the result JSON as node output
5. Next node: parse the result, store it, or trigger a webhook

---

### 8.3 — Integration debug checklist

```bash
# 1. Are all containers running?
docker compose ps

# 2. Check logs for errors
docker compose logs scraper-api --tail 50
docker compose logs dashboard --tail 50
docker compose logs postgres --tail 20

# 3. Can dashboard reach scraper-api?
docker compose exec dashboard wget -qO- http://scraper-api:8000/health

# 4. Can scraper-api reach postgres?
docker compose exec scraper-api python -c \
  "import asyncio, asyncpg; asyncio.run(asyncpg.connect('postgresql://scraper:change_me@pgbouncer:5432/scraper_db'))"

# 5. Test scrape endpoint directly
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","mode":"http"}'
```

---

## Module 9 — Project Scaffold from Scratch

Now reproduce the entire project. Try doing this without looking at this guide.

### Step 1 — Create the project root

```bash
mkdir py_ts_scrapper && cd py_ts_scrapper
git init
git remote add origin https://github.com/<your-username>/py_ts_scrapper.git
```

---

### Step 2 — Create the directory structure

```bash
mkdir -p \
  services/scraper-api/core \
  services/scraper-api/parsers \
  services/scraper-api/routers \
  "services/dashboard/app/api/jobs" \
  "services/dashboard/app/api/proxy" \
  "services/dashboard/app/api/health" \
  "services/dashboard/app/jobs/[id]" \
  "services/dashboard/app/proxy" \
  services/dashboard/components \
  services/dashboard/lib \
  pipeline/navigator/actions \
  pipeline/parser/extractors \
  orchestrator/custom-nodes/PythonBridgeNode/src \
  orchestrator/custom-nodes/PythonBridgeNode/credentials \
  orchestrator/custom-nodes/ProxyRotatorNode/src \
  orchestrator/custom-nodes/ProxyRotatorNode/credentials \
  orchestrator/init \
  orchestrator/workflows \
  shared/db/migrations \
  shared/config \
  shared/types
```

---

### Step 3 — `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
dist/
.next/
.turbo/

# Docker / secrets
*.env
.env
!.env.example
shared/config/proxies.json

# macOS / editors
.DS_Store
.idea/
*.swp

# Personal / private docs
earnStart.md
```

---

### Step 4 — `.env.example`

```env
# PostgreSQL
POSTGRES_USER=scraper
POSTGRES_PASSWORD=change_me
POSTGRES_DB=scraper_db
DATABASE_URL=postgresql://scraper:change_me@pgbouncer:5432/scraper_db

# n8n
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change_me
N8N_DB_NAME=n8n_db
N8N_HOST_PORT=5679

# Scraper API
SCRAPER_API_URL=http://scraper-api:8000
LOG_LEVEL=info
RATE_LIMIT_RPM=10

# Optional
CAPTCHA_WEBHOOK_URL=
PROXYCHECK_API_KEY=
```

Copy to `.env`:
```bash
cp .env.example .env
```

---

### Step 5 — Root `docker-compose.yml`

```yaml
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    env_file: .env
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./shared/db/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
      - ./orchestrator/init/02_n8n_db.sql:/docker-entrypoint-initdb.d/02_n8n_db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging: *default-logging

  pgbouncer:
    image: edoburu/pgbouncer:latest
    restart: unless-stopped
    env_file: .env
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=${POSTGRES_USER}
      - DB_PASSWORD=${POSTGRES_PASSWORD}
      - DB_NAME=${POSTGRES_DB}
      - POOL_MODE=transaction
      - MAX_CLIENT_CONN=100
      - DEFAULT_POOL_SIZE=20
    ports:
      - "6432:5432"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h localhost -p 5432 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging: *default-logging

  scraper-api:
    build:
      context: ./services/scraper-api
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - RATE_LIMIT_RPM=${RATE_LIMIT_RPM:-10}
    volumes:
      - ./shared:/app/shared:ro
    ports:
      - "8000:8000"
    depends_on:
      pgbouncer:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 5s
      start_period: 30s
      retries: 3
    logging: *default-logging

  dashboard:
    build:
      context: ./services/dashboard
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SCRAPER_API_URL=${SCRAPER_API_URL:-http://scraper-api:8000}
      - NODE_ENV=production
    ports:
      - "3000:3000"
    depends_on:
      scraper-api:
        condition: service_healthy
      pgbouncer:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
    logging: *default-logging

  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    env_file: .env
    ports:
      - "${N8N_HOST_PORT:-5679}:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=${N8N_BASIC_AUTH_ACTIVE}
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - N8N_DB_TYPE=postgresdb
      - N8N_DB_POSTGRESDB_HOST=postgres
      - N8N_DB_POSTGRESDB_PORT=5432
      - N8N_DB_POSTGRESDB_DATABASE=${N8N_DB_NAME:-n8n_db}
      - N8N_DB_POSTGRESDB_USER=${POSTGRES_USER}
      - N8N_DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - WEBHOOK_URL=http://localhost:${N8N_HOST_PORT:-5679}/
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - n8n_data:/home/node/.n8n
      - ./orchestrator/custom-nodes:/home/node/.n8n/custom
    logging: *default-logging

volumes:
  postgres_data:
  n8n_data:
```

---

### Step 6 — `shared/db/schema.sql`

Copy the full schema from Module 5. Auto-applied by Postgres on first startup.

---

### Step 7 — `orchestrator/init/02_n8n_db.sql`

```sql
CREATE DATABASE n8n_db;
```

---

### Step 8 — Build the scraper API

Refer to Module 2 for all concepts. Create these files:

```
services/scraper-api/
├── requirements.txt
├── __init__.py
├── main.py                   # FastAPI app with lifespan + asyncpg pool
├── core/
│   ├── __init__.py
│   ├── stealth.py            # BrowserFingerprint + stealth JS injection
│   ├── proxy_manager.py      # ProxyManager circuit-breaker
│   ├── session_pool.py       # SessionPool with TTL
│   ├── rate_limiter.py       # TokenBucket
│   ├── timing.py             # random human-like delays
│   └── captcha_detector.py   # detect CAPTCHA in HTML
├── parsers/
│   ├── __init__.py
│   └── html_parser.py        # extract_json_ld, extract_open_graph, extract_by_rules
└── routers/
    ├── __init__.py
    ├── scrape.py             # POST /scrape/
    ├── parse.py              # POST /parse/
    └── proxy.py              # GET /proxy/rotate, GET /proxy/status
```

Run locally to verify before Docker:
```bash
cd services/scraper-api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000
# Open http://localhost:8000/docs
```

---

### Step 9 — Build the Next.js dashboard

```bash
cd services
npx create-next-app@latest dashboard \
  --typescript --tailwind --eslint --app --no-src-dir \
  --import-alias "@/*"
cd dashboard
npm install @tanstack/react-query pg pino pino-pretty
npm install --save-dev @types/pg
```

Create in order:
```
services/dashboard/
├── next.config.ts            # output: "standalone"
├── Dockerfile                # multi-stage build (see Module 4)
├── lib/
│   ├── db.ts                 # singleton pg Pool with global cache
│   └── scraper-client.ts     # axios instance pointing to scraper-api
├── components/
│   └── QueryProvider.tsx     # TanStack Query client wrapper ("use client")
└── app/
    ├── globals.css           # @import "tailwindcss"
    ├── layout.tsx            # nav + QueryProvider
    ├── page.tsx              # jobs list + create form ("use client")
    ├── jobs/[id]/page.tsx    # job detail + results ("use client")
    ├── proxy/page.tsx        # proxy pool status ("use client")
    └── api/
        ├── health/route.ts
        ├── jobs/route.ts
        ├── jobs/[id]/route.ts
        └── proxy/route.ts
```

Build to verify:
```bash
npm run build
# Should show 8 routes with no TypeScript errors
```

---

### Step 10 — Build the TypeScript pipeline

```bash
cd pipeline/navigator
npm init -y
npm install typescript @types/node ts-node --save-dev
npm install playwright playwright-extra playwright-extra-plugin-stealth
npx tsc --init
```

Create:
```
pipeline/navigator/
├── index.ts          # reads JSON command from stdin, writes result to stdout
├── stealth.ts        # playwright-extra stealth plugin init
├── tsconfig.json
└── actions/
    ├── navigate.ts   # goto + wait + return HTML
    └── intercept.ts  # route interception + XHR capture
```

---

### Step 11 — Build n8n custom nodes

```bash
cd orchestrator/custom-nodes/PythonBridgeNode
npm install n8n-workflow typescript @types/node --save-dev
npm run build   # must compile before docker compose up
```

Repeat for ProxyRotatorNode.

---

### Step 12 — First launch

```bash
cd <project-root>
docker compose up --build
```

First build takes 3–5 minutes (Playwright chromium download is ~500 MB).

| Service | URL | Auth |
|---|---|---|
| Dashboard | http://localhost:3000 | none |
| Scraper API Swagger | http://localhost:8000/docs | none |
| n8n | http://localhost:5679 | admin / your password |
| pgBouncer | localhost:6432 | (internal only) |

---

### Step 13 — Verify end-to-end

```bash
# Health check
curl http://localhost:8000/health
curl http://localhost:3000/api/health

# Scrape via API (HTTP mode — fast)
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","pattern":"generic","mode":"http"}'

# Scrape via API (Playwright mode — full browser)
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","pattern":"generic","mode":"playwright"}'

# Submit a job from the dashboard:
# Open http://localhost:3000, enter a URL, click Submit
# Watch: pending -> running -> done

# Check proxy pool
curl http://localhost:8000/proxy/status
```

---

## Common Mistakes & How to Fix Them

| Mistake | Symptom | Fix |
|---|---|---|
| `localhost` in Docker Compose env vars | Connection refused | Use service name: `postgres`, `scraper-api`, `pgbouncer` |
| Forgot `await params` in Next.js 15 | `params.id` is undefined, TS error | `const { id } = await params;` — params is a Promise in Next.js 15 |
| `DATABASE_URL` uses wrong port | asyncpg connect error | Inside Docker use `pgbouncer:5432` (internal port), not `6432` |
| `bitnami/pgbouncer` image | Docker pull 404 | Use `edoburu/pgbouncer:latest` |
| Tailwind not applying styles | Page renders unstyled | Ensure `globals.css` has `@import "tailwindcss"` (Tailwind v4 syntax) |
| n8n custom node not appearing | Node missing from palette | `npm run build` in the custom node folder, then `docker compose restart n8n` |
| `npm ci` fails in dashboard | lockfile mismatch | Run `npm install` locally first, commit updated `package-lock.json` |
| Playwright `goto` timeout | TimeoutError: Navigation timeout | Increase timeout or use `waitUntil: "domcontentloaded"` instead of `"networkidle"` |
| CAPTCHA on scraped site | 403 or challenge HTML | Switch to Playwright mode; add stealth; use a proxy |
| Postgres init script doesn't run | Tables don't exist | Init scripts only run on empty volume — `docker compose down -v` to reset |
| Sequential `await` in loops | Scraping 10x slower than expected | Use `asyncio.gather(*tasks)` instead of `for url in urls: await scrape(url)` |
| Multiple DB pools in dev | "too many connections" error | Use the `global.__pgPool` singleton pattern in `lib/db.ts` |

---

## Practice Projects

Build these to reinforce each module independently.

| Project | Technologies | What you practise |
|---|---|---|
| Price tracker | Python + PostgreSQL | curl_cffi scraping, JSONB storage, change detection |
| Job board scraper | Python + Playwright | Pagination, stealth, structured extraction |
| Proxy health checker | Python + asyncio | Async testing of 100 proxies concurrently |
| Scrape dashboard API | FastAPI + asyncpg | Full CRUD, connection pooling, lifespan |
| TypeScript navigator CLI | TypeScript + Playwright | IPC bridge, network interception, fingerprinting |
| Docker microservices | Docker Compose | Multi-container networking, healthchecks, volumes |
| n8n ETL workflow | n8n + custom nodes | Trigger → scrape → transform → store pipeline |
| Real-time job UI | Next.js + TanStack Query | Polling, mutations, optimistic updates |

---

## What's Built in This Project

| Phase | What was built | Status |
|---|---|---|
| 0 | Project scaffold, Docker Compose, shared schema | ✅ Done |
| 1 | FastAPI scraper-api (stealth, proxy, session, rate limit) | ✅ Done |
| 2 | Next.js dashboard (jobs, proxy, API routes) | ✅ Done |
| 3 | TypeScript pipeline navigator + Python parser | ✅ Done |
| 4 | n8n custom nodes (PythonBridgeNode, ProxyRotatorNode) | ✅ Done |
| 5 | Stealth hardening (canvas noise, fingerprint rotation) | ✅ Done |
| 6 | Production hardening (pgBouncer, pino logging, health) | ✅ Done |
| 7 | Multi-tenancy & auth (NextAuth.js v5, API keys, RLS) | 🟡 Planned |
| 8 | Billing & metering (Stripe, credits, 402) | 🟡 Planned |
| 9 | Public API & DX (v1 versioning, SDKs, webhooks) | 🟡 Planned |
| 10 | Async queue (BullMQ + Redis, priorities, SSE) | 🟡 Planned |
| 11 | Observability (Prometheus, Grafana, OpenTelemetry) | 🟡 Planned |
| 12 | Kubernetes & CI/CD (Helm, HPA, GitHub Actions, ArgoCD) | 🟡 Planned |

See `developmentAI.md` for the full phase task lists.
