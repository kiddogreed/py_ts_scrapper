# Replication Guide — py_ts_scrapper

Complete step-by-step instructions to rebuild this project from scratch on a fresh machine.

---

## Prerequisites

Install these before starting:

| Tool | Version | Install |
|---|---|---|
| Git | any | https://git-scm.com |
| Docker Desktop | latest | https://www.docker.com/products/docker-desktop |
| Node.js | 22.x | https://nodejs.org (or `nvm install 22`) |
| Python | 3.12.x | https://www.python.org/downloads |
| npm | 11.x | bundled with Node 22 |

Verify:
```bash
git --version
docker --version
node --version    # v22.x.x
python --version  # Python 3.12.x
npm --version     # 11.x.x
```

---

## Step 1 — Create the project root

```bash
mkdir py_ts_scrapper
cd py_ts_scrapper
git init
```

---

## Step 2 — Create the directory structure

```bash
mkdir -p services/scraper-api/core
mkdir -p services/scraper-api/routers
mkdir -p services/scraper-api/parsers
mkdir -p services/dashboard
mkdir -p pipeline/navigator
mkdir -p pipeline/parser
mkdir -p orchestrator/workflows
mkdir -p orchestrator/custom-nodes
mkdir -p shared/db
mkdir -p shared/config
mkdir -p shared/types
```

---

## Step 3 — Create `.gitignore`

Create `.gitignore` at the project root:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
*.egg-info/
dist/
.pytest_cache/
.mypy_cache/

# TypeScript / Node
node_modules/
.next/
out/
dist/
*.js.map
*.d.ts.map

# Environment
.env
*.env.local

# Docker
*.log

# OS
.DS_Store
Thumbs.db
```

---

## Step 4 — Create `.env.example`

Create `.env.example` at the project root:

```env
# ============================================================
# .env.example — Copy to .env and fill in real values
# NEVER commit .env to git
# ============================================================

# --- Postgres ---
POSTGRES_DB=scraper_db
POSTGRES_USER=scraper
POSTGRES_PASSWORD=change_me_in_production
DATABASE_URL=postgresql://scraper:change_me_in_production@localhost:5432/scraper_db

# --- FastAPI Scraper Service ---
SCRAPER_API_HOST=0.0.0.0
SCRAPER_API_PORT=8000
SCRAPER_API_SECRET=change_me_in_production

# --- Next.js Dashboard ---
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=change_me_in_production
NEXTAUTH_URL=http://localhost:3000

# --- n8n Orchestrator ---
N8N_PORT=5678
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change_me_in_production
N8N_DB_NAME=n8n_db

# --- Proxy Configuration ---
PROXY_LIST_PATH=./shared/config/proxies.json
PROXY_VALIDATION_ENABLED=true

# --- Rate Limiting ---
RATE_LIMIT_PER_DOMAIN=30

# --- Stealth ---
CURL_IMPERSONATE=chrome120
```

Then copy it:
```bash
cp .env.example .env
# Edit .env with real values (POSTGRES_PASSWORD at minimum)
```

---

## Step 5 — Create `docker-compose.yml`

Create `docker-compose.yml` at the project root:

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
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
    build:
      context: ./services/scraper-api
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./shared:/app/shared:ro
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3

  dashboard:
    build:
      context: ./services/dashboard
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    ports:
      - "3000:3000"
    depends_on:
      scraper-api:
        condition: service_healthy

  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    env_file: .env
    ports:
      - "${N8N_PORT:-5678}:5678"
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
      - WEBHOOK_URL=http://localhost:${N8N_PORT:-5678}/
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

## Step 6 — Create `shared/db/schema.sql`

```sql
-- shared/db/schema.sql
-- Auto-applied by Docker on first Postgres startup

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    url         TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'running', 'done', 'failed', 'dead')),
    pattern     TEXT,
    retries     INT         NOT NULL DEFAULT 0,
    max_retries INT         NOT NULL DEFAULT 3,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata    JSONB       NOT NULL DEFAULT '{}'
);

-- Results
CREATE TABLE IF NOT EXISTS results (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID        REFERENCES jobs(id) ON DELETE CASCADE,
    url         TEXT        NOT NULL,
    data        JSONB       NOT NULL,
    scraped_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Proxy Pool
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

-- Session / Cookie Store
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain      TEXT        NOT NULL,
    cookies     JSONB       NOT NULL,
    user_agent  TEXT,
    fingerprint JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

-- Dead Letter Queue
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

## Step 7 — Create `shared/types/scraper.d.ts`

```typescript
// shared/types/scraper.d.ts

export interface ScrapeRequest {
  url: string;
  pattern?: "generic" | "product" | "article" | "listing";
  use_proxy?: boolean;
  mode?: "playwright" | "http";
}

export interface ScrapeResult {
  url: string;
  status_code: number;
  html: string;
  json_ld?: Record<string, unknown>[];
  open_graph?: Record<string, string>;
  intercepted_xhr?: XhrEntry[];
  fingerprint?: BrowserFingerprint;
  scraped_at: string;
}

export interface XhrEntry {
  url: string;
  method: string;
  status: number;
  body?: string;
}

export interface BrowserFingerprint {
  user_agent: string;
  viewport: { width: number; height: number };
  timezone: string;
  locale: string;
  webgl_renderer: string;
  platform: string;
}

export interface ProxyConfig {
  host: string;
  port: number;
  username?: string;
  password?: string;
  protocol?: "http" | "socks5";
}

export interface Job {
  id: string;
  url: string;
  status: "pending" | "running" | "done" | "failed" | "dead";
  pattern?: string;
  retries: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}
```

---

## Step 8 — Create `shared/config/fingerprints.json`

```json
{
  "webgl_renderers": [
    "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "Apple GPU",
    "Mesa Intel(R) UHD Graphics 620 (KBL GT2)"
  ],
  "platforms": ["Win32", "MacIntel", "Linux x86_64"],
  "viewports": [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 2560, "height": 1440}
  ],
  "timezones": [
    "America/New_York", "America/Chicago", "America/Los_Angeles",
    "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Singapore"
  ],
  "locales": ["en-US", "en-GB", "en-CA", "fr-FR", "de-DE", "ja-JP"]
}
```

---

## Step 9 — Create `shared/config/proxies.json`

```json
[
  {
    "_comment": "Replace with real proxies. Leave empty array [] if not using proxies.",
    "host": "proxy1.example.com",
    "port": 1080,
    "username": "user",
    "password": "pass",
    "protocol": "socks5"
  }
]
```

---

## Step 10 — Build Phase 1: FastAPI Scraper API

### 10.1 — `services/scraper-api/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
httpx==0.27.0
playwright==1.44.0
beautifulsoup4==4.12.3
lxml==5.2.1
curl-cffi==0.7.1
fake-useragent==1.5.1
tenacity==8.3.0
asyncpg==0.29.0
python-dotenv==1.0.1
structlog==24.1.0
```

### 10.2 — `services/scraper-api/__init__.py`

Empty file:
```python
```

### 10.3 — `services/scraper-api/core/__init__.py`

Empty file.

### 10.4 — `services/scraper-api/routers/__init__.py`

Empty file.

### 10.5 — `services/scraper-api/parsers/__init__.py`

Empty file.

### 10.6 — `services/scraper-api/core/stealth.py`

Copy the full file from `services/scraper-api/core/stealth.py`.

Key responsibilities:
- `BrowserFingerprint` dataclass — viewport, timezone, locale, WebGL renderer, UA, platform
- `FingerprintFactory.random()` — picks random values from `fingerprints.json` pool
- `STEALTH_INIT_SCRIPT` — JS injected into every page to override `navigator`, `screen`, canvas noise
- `build_stealth_context_options(fingerprint)` — returns Playwright `new_context()` kwargs

### 10.7 — `services/scraper-api/core/proxy_manager.py`

Key responsibilities:
- `ProxyManager` — loads from `proxies.json`, tracks failure counts per proxy
- `get_proxy()` — returns lowest-failure active proxy, raises if all exhausted
- `mark_failure(host, port)` / `mark_success(host, port)` — circuit-breaker updates
- `get_status()` — returns list of all proxies with health stats

### 10.8 — `services/scraper-api/core/session_pool.py`

Key responsibilities:
- `SessionPool` — in-memory dict keyed by domain
- `get_session(domain)` — returns existing if not expired/overused
- `store_session(domain, cookies, ua, fingerprint)` — saves with TTL
- Expiry: `max_age=3600` seconds, `max_uses=50` per session

### 10.9 — `services/scraper-api/parsers/html_parser.py`

Key responsibilities:
- `extract_json_ld(html)` — parses `<script type="application/ld+json">` blocks
- `extract_open_graph(html)` — parses all `<meta property="og:*">` tags
- `extract_by_rules(html, rules)` — applies CSS selector rules `[{"name": "title", "selector": "h1"}]`
- `extract_links(html, base_url)` — returns all `<a href>` normalized to absolute URLs
- `generic_extract(html)` — runs all extractors, returns combined dict

### 10.10 — `services/scraper-api/routers/scrape.py`

Key responsibilities:
- `POST /scrape/` — accepts `ScrapeRequest`, dispatches to Playwright or curl_cffi
- Playwright path: stealth context → navigate → intercept XHR → return HTML + intercepted requests
- curl_cffi path: `requests.Session(impersonate="chrome120")` → GET → return HTML
- Session reuse via `SessionPool`; proxy injection via `ProxyManager`
- Returns `ScrapeResponse` with `html`, `status_code`, `intercepted_xhr`, `fingerprint`, `scraped_at`

### 10.11 — `services/scraper-api/routers/parse.py`

Key responsibilities:
- `POST /parse/` — accepts `{"html": "...", "rules": [...], "pattern": "generic"}`
- Returns extracted `json_ld`, `open_graph`, `rule_results`, `links`

### 10.12 — `services/scraper-api/routers/proxy.py`

Key responsibilities:
- `GET /proxy/rotate` — returns next healthy proxy
- `GET /proxy/status` — returns all proxies with health info
- `POST /proxy/validate/{host}/{port}` — tests proxy against a known URL
- `DELETE /proxy/{host}/{port}` — removes proxy from pool

### 10.13 — `services/scraper-api/main.py`

```python
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import scrape, parse, proxy

log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("scraper_api.startup")
    yield
    log.info("scraper_api.shutdown")

app = FastAPI(title="Scraper API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape.router)
app.include_router(parse.router)
app.include_router(proxy.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "scraper-api"}
```

### 10.14 — `services/scraper-api/Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .

VOLUME ["/app/shared"]
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 10.15 — Verify the scraper API locally

```bash
cd services/scraper-api
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs — all routes should appear.

---

## Step 11 — Build Phase 2: Next.js Dashboard

### 11.1 — Scaffold Next.js

Run from the project root:

```bash
cd services
npx create-next-app@16.2.4 dashboard \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
cd dashboard
```

When prompted `Ok to proceed? (y)` → type `y` and press Enter.

### 11.2 — Install additional dependencies

```bash
npm install axios @tanstack/react-query pg
npm install --save-dev @types/pg
```

### 11.3 — Update `next.config.ts`

Replace the contents of `next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

### 11.4 — Create `lib/db.ts`

```typescript
// services/dashboard/lib/db.ts
import { Pool } from "pg";

declare global {
  // eslint-disable-next-line no-var
  var __pgPool: Pool | undefined;
}

function createPool(): Pool {
  return new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 5,
    idleTimeoutMillis: 30_000,
  });
}

const db: Pool = global.__pgPool ?? createPool();
if (process.env.NODE_ENV !== "production") global.__pgPool = db;

export default db;
```

### 11.5 — Create `lib/scraper-client.ts`

```typescript
// services/dashboard/lib/scraper-client.ts
import axios from "axios";

const scraperClient = axios.create({
  baseURL: process.env.SCRAPER_API_URL ?? "http://localhost:8000",
  timeout: 35_000,
});

export default scraperClient;
```

### 11.6 — Create `components/QueryProvider.tsx`

```typescript
// services/dashboard/components/QueryProvider.tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

### 11.7 — Create `app/layout.tsx`

```typescript
// services/dashboard/app/layout.tsx
import type { Metadata } from "next";
import Link from "next/link";
import QueryProvider from "@/components/QueryProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scraper Dashboard",
  description: "Stealth scraping infrastructure dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex gap-6 items-center">
          <span className="font-bold text-white">🕷 Scraper</span>
          <Link href="/" className="text-gray-300 hover:text-white text-sm">Jobs</Link>
          <Link href="/proxy" className="text-gray-300 hover:text-white text-sm">Proxies</Link>
        </nav>
        <QueryProvider>
          <main className="p-6">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
```

### 11.8 — Create `app/globals.css`

Replace the default content:

```css
@import "tailwindcss";
```

### 11.9 — Create `app/api/jobs/route.ts`

```typescript
// services/dashboard/app/api/jobs/route.ts
import { NextRequest, NextResponse } from "next/server";
import db from "@/lib/db";
import scraperClient from "@/lib/scraper-client";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const status = searchParams.get("status");
  const limit = Number(searchParams.get("limit") ?? 20);
  const offset = Number(searchParams.get("offset") ?? 0);

  const conditions: string[] = [];
  const values: unknown[] = [];
  if (status) {
    conditions.push(`status = $${values.length + 1}`);
    values.push(status);
  }
  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
  values.push(limit, offset);

  const { rows } = await db.query(
    `SELECT * FROM jobs ${where} ORDER BY created_at DESC LIMIT $${values.length - 1} OFFSET $${values.length}`,
    values
  );
  return NextResponse.json(rows);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { url, pattern = "generic" } = body;

  if (!url || typeof url !== "string") {
    return NextResponse.json({ error: "url is required" }, { status: 400 });
  }
  try { new URL(url); } catch {
    return NextResponse.json({ error: "invalid url" }, { status: 400 });
  }

  const { rows } = await db.query(
    `INSERT INTO jobs (url, status, pattern) VALUES ($1, 'pending', $2) RETURNING *`,
    [url, pattern]
  );
  const job = rows[0];

  // Fire-and-forget scrape
  (async () => {
    try {
      await db.query(`UPDATE jobs SET status='running', updated_at=NOW() WHERE id=$1`, [job.id]);
      const { data } = await scraperClient.post("/scrape/", { url, pattern });
      await db.query(
        `INSERT INTO results (job_id, url, data, scraped_at) VALUES ($1, $2, $3, NOW())`,
        [job.id, url, JSON.stringify(data)]
      );
      await db.query(`UPDATE jobs SET status='done', updated_at=NOW() WHERE id=$1`, [job.id]);
    } catch (err) {
      await db.query(`UPDATE jobs SET status='failed', updated_at=NOW() WHERE id=$1`, [job.id]);
    }
  })();

  return NextResponse.json(job, { status: 201 });
}
```

### 11.10 — Create `app/api/jobs/[id]/route.ts`

```typescript
// services/dashboard/app/api/jobs/[id]/route.ts
import { NextRequest, NextResponse } from "next/server";
import db from "@/lib/db";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!UUID_RE.test(id)) return NextResponse.json({ error: "invalid id" }, { status: 400 });

  const { rows: jobs } = await db.query(`SELECT * FROM jobs WHERE id = $1`, [id]);
  if (!jobs.length) return NextResponse.json({ error: "not found" }, { status: 404 });

  const { rows: results } = await db.query(
    `SELECT * FROM results WHERE job_id = $1 ORDER BY created_at DESC`,
    [id]
  );
  return NextResponse.json({ ...jobs[0], results });
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!UUID_RE.test(id)) return NextResponse.json({ error: "invalid id" }, { status: 400 });
  await db.query(`DELETE FROM jobs WHERE id = $1`, [id]);
  return NextResponse.json({ ok: true });
}
```

### 11.11 — Create `app/api/proxy/route.ts`

```typescript
// services/dashboard/app/api/proxy/route.ts
import { NextResponse } from "next/server";
import scraperClient from "@/lib/scraper-client";

export async function GET() {
  const { data } = await scraperClient.get("/proxy/status");
  return NextResponse.json(data);
}
```

### 11.12 — Create `app/api/health/route.ts`

```typescript
// services/dashboard/app/api/health/route.ts
import { NextResponse } from "next/server";
import scraperClient from "@/lib/scraper-client";

export async function GET() {
  try {
    const { data } = await scraperClient.get("/health");
    return NextResponse.json({ dashboard: "ok", scraper: data });
  } catch {
    return NextResponse.json({ dashboard: "ok", scraper: "unreachable" }, { status: 200 });
  }
}
```

### 11.13 — Create `app/page.tsx`

Copy the full file from `services/dashboard/app/page.tsx`.

Key features:
- `"use client"` — TanStack Query `useQuery` polling every 5 seconds
- Status filter buttons: all / pending / running / done / failed / dead
- Job creation form: URL input + pattern select + Submit (`useMutation` → `POST /api/jobs`)
- Table columns: ID (truncated link), URL, StatusBadge, Pattern, Retries, Created (relative time)

### 11.14 — Create `app/jobs/[id]/page.tsx`

Copy the full file from `services/dashboard/app/jobs/[id]/page.tsx`.

Key features:
- `"use client"` — `useParams<{ id: string }>()` for the job UUID
- Conditional `refetchInterval`: 3000 while `pending|running`, `false` when `done|failed|dead`
- Job metadata card + results list
- Each result: collapsible fingerprint, intercepted XHR, HTML preview (first 8000 chars)

### 11.15 — Create `app/proxy/page.tsx`

Copy the full file from `services/dashboard/app/proxy/page.tsx`.

Key features:
- `"use client"` — polls `/api/proxy` every 10 seconds
- Stat cards: total / healthy / dead proxy counts
- Health percentage bar: green ≥80%, yellow ≥40%, red <40%
- Warning banner when no proxies configured

### 11.16 — Create `Dockerfile` for dashboard

```dockerfile
# syntax=docker/dockerfile:1

# ---- Stage 1: Install dependencies ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- Stage 2: Build ----
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---- Stage 3: Production runner ----
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
```

### 11.17 — Verify the dashboard build

```bash
cd services/dashboard
npm run build
```

Expected output — all 8 routes registered with no TypeScript errors:
```
Route (app)
┌ ○ /
├ ○ /_not-found
├ ƒ /api/health
├ ƒ /api/jobs
├ ƒ /api/jobs/[id]
├ ƒ /api/proxy
├ ƒ /jobs/[id]
└ ○ /proxy
```

---

## Step 12 — First commit

```bash
cd <project-root>
git add .
git commit -m "Phase 0+1+2: full scaffold, FastAPI scraper, Next.js dashboard"
```

---

## Step 13 — Run the full stack with Docker

```bash
# From project root
docker compose up --build
```

Wait for all services to become healthy (~2–3 minutes on first run — Playwright chromium download is large).

Check logs:
```bash
docker compose logs -f scraper-api
docker compose logs -f dashboard
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| Scraper API Swagger | http://localhost:8000/docs |
| n8n | http://localhost:5678 |
| Postgres | localhost:5432 |

---

## Step 14 — Verify end-to-end

### Test the scraper API directly:
```bash
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "pattern": "generic", "mode": "http"}'
```

### Submit a job from the dashboard:
1. Open http://localhost:3000
2. Enter a URL in the form → Submit
3. Job appears as `pending` → transitions to `running` → `done`
4. Click the job ID to see the scraped results

### Check proxy status:
```bash
curl http://localhost:8000/proxy/status
```

---

## Step 15 — Optional: Add real proxies

Edit `shared/config/proxies.json` with your proxy list, then restart:
```bash
docker compose restart scraper-api
```

---

## Environment Variable Reference for Docker

When running in Docker Compose, set these in `.env`:

```env
DATABASE_URL=postgresql://scraper:your_password@postgres:5432/scraper_db
SCRAPER_API_URL=http://scraper-api:8000
```

Note: `@postgres` (not `@localhost`) — Docker internal hostname.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `dashboard` can't reach `scraper-api` | Set `SCRAPER_API_URL=http://scraper-api:8000` in `.env` (not localhost) |
| `DATABASE_URL` connection refused | Use `@postgres:5432` in Docker, `@localhost:5432` for local dev |
| Playwright install hangs | Normal — chromium + deps is ~500 MB. Wait or use `mode: "http"` |
| `npm run build` fails with Tailwind error | Ensure `app/globals.css` contains `@import "tailwindcss"` (Tailwind v4 syntax, no config file needed) |
| `params` type error in Next.js API routes | Next.js 15+ — `params` is `Promise<{id:string}>`, must `await params` |
| Port already in use | Change ports in `docker-compose.yml` or stop conflicting services |

---

## What's Not Yet Built (Phases 3–6)

| Phase | What to build |
|---|---|
| Phase 3 | `pipeline/navigator/` — TypeScript Playwright stealth navigator; `pipeline/parser/` — Python BS4 structured extractor; IPC bridge (stdout JSON) |
| Phase 4 | `orchestrator/` — n8n custom nodes (`PythonBridgeNode`, `ProxyRotatorNode`), exported workflow JSONs |
| Phase 5 | Stealth hardening — canvas noise, WebRTC leak prevention, residential proxy rotation, rate limiting |
| Phase 6 | Production hardening — auth, HTTPS, monitoring (Prometheus/Grafana), log aggregation |

See `developmentAI.md` for the full phase-by-phase task list.
