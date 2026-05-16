# py_ts_scrapper

A **production-grade, stealth-first, resilient** multi-layered scraping infrastructure built with Python and TypeScript. Three architectural patterns work independently and together to scrape at scale while evading anti-bot systems.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    n8n ORCHESTRATOR                      │
│   Schedules jobs · manages retries · stores state        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐   ┌──────────────────────┐
│  Pattern 1    │   │  Pattern 2           │
│  FastAPI API  │   │  Polyglot Pipeline   │
│  + Next.js    │   │  TS Navigator        │
│  Dashboard    │   │  → Python Parser     │
└───────┬───────┘   └──────────┬───────────┘
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │   PostgreSQL 16      │
        │  jobs · results      │
        │  proxies · sessions  │
        └──────────────────────┘
```

| Pattern | Stack | Role |
|---|---|---|
| 1 — Microservice | Python FastAPI + Next.js 16 | REST API scrape-as-a-service + dashboard |
| 2 — Polyglot Pipeline | TypeScript (Playwright) + Python (BS4) | Navigate → extract pipeline |
| 3 — Orchestrator | n8n + custom bridge nodes | Workflow automation & retry management |

---

## Stack

| Layer | Technology |
|---|---|
| Scraper API | Python 3.12 · FastAPI 0.111 · Playwright · curl_cffi |
| Dashboard | Next.js 16 · TypeScript · Tailwind v4 · TanStack Query v5 |
| Database | PostgreSQL 16 |
| Navigator | TypeScript · Playwright Extra · stealth plugins |
| Parser | Python · BeautifulSoup4 · lxml |
| Orchestrator | n8n (self-hosted Docker) |
| Container | Docker Compose (full stack) |

---

## Project Structure

```
py_ts_scrapper/
├── services/
│   ├── scraper-api/          # Pattern 1: Python FastAPI
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── scrape.py     # POST /scrape — dual-mode (Playwright + curl_cffi)
│   │   │   ├── parse.py      # POST /parse — rule-based + generic extraction
│   │   │   └── proxy.py      # GET /proxy/rotate · status · validate
│   │   ├── core/
│   │   │   ├── stealth.py    # Fingerprint randomization, UA pool, viewport/TZ
│   │   │   ├── proxy_manager.py  # Rotating pool, circuit-breaker health tracking
│   │   │   └── session_pool.py   # Cookie/session store with TTL
│   │   ├── parsers/
│   │   │   └── html_parser.py    # JSON-LD, Open Graph, CSS-selector, link extraction
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── dashboard/            # Pattern 1: Next.js 16 Frontend
│       ├── app/
│       │   ├── page.tsx              # Jobs list — table, filters, 5s auto-refresh
│       │   ├── jobs/[id]/page.tsx    # Job detail — results, HTML preview, XHR log
│       │   ├── proxy/page.tsx        # Proxy health — stat cards, health bar
│       │   └── api/
│       │       ├── jobs/route.ts     # GET list · POST create + dispatch to FastAPI
│       │       ├── jobs/[id]/route.ts # GET job+results · DELETE
│       │       ├── proxy/route.ts    # GET → FastAPI /proxy/status
│       │       └── health/route.ts   # GET aggregated health
│       ├── lib/
│       │   ├── db.ts                 # pg Pool singleton
│       │   └── scraper-client.ts     # Axios client → FastAPI
│       ├── components/
│       │   └── QueryProvider.tsx     # TanStack Query wrapper
│       └── Dockerfile
│
├── pipeline/                 # Pattern 2: Polyglot Pipeline (Phase 3)
│   ├── navigator/            # TypeScript — Playwright stealth navigation
│   └── parser/               # Python — structured data extraction
│
├── orchestrator/             # Pattern 3: n8n (Phase 4)
│   ├── workflows/
│   └── custom-nodes/
│
├── shared/
│   ├── db/schema.sql         # Postgres schema: jobs, results, proxies, sessions, dead_letter
│   ├── types/scraper.d.ts    # Shared TypeScript interfaces
│   └── config/
│       ├── fingerprints.json # Browser fingerprint pool (WebGL, platform, fonts)
│       └── proxies.json      # Proxy list template
│
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Prerequisites

| Tool | Min Version | Install |
|---|---|---|
| Docker + Docker Compose | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| Git | any | — |

---

## Running Locally

### Option A — Full Docker stack (recommended)

#### Using the launch scripts (easiest)

**Git Bash / WSL:**
```bash
cp .env.example .env          # configure once
./start.sh                    # starts Docker Desktop if needed, builds, waits for healthy
./stop.sh                     # stop (data preserved)
./stop.sh --clean             # stop + wipe all volumes
```

**Windows CMD / double-click:**
```bat
copy .env.example .env
start.bat
stop.bat
stop.bat --clean
```

The scripts handle everything automatically:
- Launch Docker Desktop if it isn't running and wait for the daemon
- Sync `package-lock.json` if new npm packages were added
- Run `docker compose up --build -d`
- Poll health endpoints until all services respond
- Print all service URLs when ready

#### Manual
```bash
cp .env.example .env
# Edit .env — at minimum set POSTGRES_PASSWORD and SCRAPER_API_SECRET
docker compose up --build -d
docker compose ps             # all services should show "healthy"
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| Scraper API (FastAPI) | http://localhost:8000 |
| Swagger / API Docs | http://localhost:8000/docs |
| n8n Orchestrator | http://localhost:5679 |
| pgBouncer | localhost:6432 |
| PostgreSQL | localhost:5432 |

---

### Option B — Local dev (without Docker)

> Run each service in a separate terminal. You still need Postgres running — use `docker compose up postgres` to start only that.

#### 1. Start Postgres only

```bash
docker compose up postgres -d
```

#### 2. FastAPI Scraper API

```bash
# From project root
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash / bash
# .venv\Scripts\activate         # Windows PowerShell
# source .venv/bin/activate      # macOS / Linux

cd services/scraper-api
pip install -r requirements.txt
playwright install chromium

# Copy and configure env
cp ../../.env.example ../../.env
# Edit .env — set DATABASE_URL=postgresql://scraper:changeme@localhost:5432/scraper_db

uvicorn main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

#### 3. Next.js Dashboard

```bash
# In a new terminal (from project root)
cd services/dashboard
npm install
npm run dev
# → http://localhost:3000
```

#### 4. TypeScript Pipeline Navigator

```bash
# In a new terminal
cd pipeline/navigator
npm install
npx playwright install chromium

# Run a one-off navigation (outputs intercepted XHR + parsed HTML to stdout)
npm run navigate -- --url https://books.toscrape.com

# Or compile and run
npm run build
npm start -- --url https://books.toscrape.com
```

#### 5. Python Pipeline Parser

```bash
# In a new terminal (re-use the .venv from step 2)
source .venv/Scripts/activate
cd pipeline/parser
pip install -r requirements.txt

# Parse a local HTML file
python main.py --file /path/to/page.html

# Or pipe HTML from stdin
curl -s https://books.toscrape.com | python main.py
```

#### 6. n8n Orchestrator (local)

```bash
docker compose up n8n -d
# → http://localhost:5678
# Login: admin / <N8N_BASIC_AUTH_PASSWORD from .env>
```

Import workflows after first login:
1. Open n8n → **Settings → Import** (or **Workflows → Import**)
2. Import `orchestrator/workflows/scrape-job.json`
3. Import `orchestrator/workflows/retry-handler.json`
4. Activate both workflows

---

## Testing

### Scraper API — smoke tests (no Docker needed)

These tests verify all Phase 5 stealth & resilience modules without a live browser or network:

```bash
source .venv/Scripts/activate         # or .venv\Scripts\activate on PowerShell
cd services/scraper-api

python -c "
import asyncio, sys
sys.path.insert(0, '.')

# 5.1 + 5.2 — TLS rotation + dynamic fingerprint
from core.stealth import get_random_tls_profile, TLS_PROFILES, get_random_fingerprint, build_stealth_init_script
profile = get_random_tls_profile()
assert profile in TLS_PROFILES
fp = get_random_fingerprint()
script = build_stealth_init_script(fp)
assert 'WebGLRenderingContext' in script
print(f'5.1+5.2 OK: profile={profile}, vendor={fp[\"hardware\"][\"webgl_vendor\"]}')

async def run():
    # 5.3 — Gaussian delays
    from core.timing import human_delay, random_scroll_pauses
    ms = await human_delay(mean_ms=100, std_ms=10, min_ms=50)
    print(f'5.3 OK: delay={ms:.0f}ms pauses={[round(p,2) for p in random_scroll_pauses(3)]}')

    # 5.4 — CAPTCHA detection
    from core.captcha_detector import is_captcha_page
    assert is_captcha_page('<title>Just a moment...</title>__cf_chl_opt', 'https://x.com')
    assert not is_captcha_page('<title>Books to Scrape</title>', 'https://books.toscrape.com')
    assert is_captcha_page('', 'https://x.com', status_code=403)
    assert is_captcha_page('ok', 'https://x.com', status_code=429)
    print('5.4 OK: Cloudflare + clean page + 403 + 429')

    # 5.5 — IP reputation
    from core.proxy_manager import ProxyManager, Proxy
    assert hasattr(ProxyManager([Proxy('1.2.3.4', 8080)]), 'check_ip_reputation')
    print('5.5 OK: check_ip_reputation present')

    # 5.6 — Rate limiter
    from core.rate_limiter import RateLimiter
    rl = RateLimiter(default_rpm=6000, burst=10)
    waited = await rl.acquire('test.com')
    assert waited == 0.0
    rl.throttle_domain('test.com')
    print('5.6 OK: acquire + throttle work')

    # 5.7 — Session persistence
    from core.session_pool import SessionPool
    sp = SessionPool()
    assert hasattr(sp, 'load_from_db') and hasattr(sp, '_persist_session')
    print('5.7 OK: Postgres persistence methods present')

asyncio.run(run())
print('=== ALL SMOKE TESTS PASSED ===')
"
```

### Scraper API — live HTTP tests (stack must be running)

```bash
# Health check
curl http://localhost:8000/health

# Scrape a public test site (browser mode)
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://books.toscrape.com", "mode": "playwright", "use_proxy": false}'

# Scrape with curl_cffi (HTTP mode, faster)
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://quotes.toscrape.com", "mode": "http", "use_proxy": false}'

# Parse HTML
curl -X POST http://localhost:8000/parse/ \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Hello</h1><p>World</p>", "pattern": "generic"}'

# Proxy pool status
curl http://localhost:8000/proxy/status
```

### Dashboard — via browser

```
http://localhost:3000           # Jobs table (auto-refreshes every 5s)
http://localhost:3000/proxy     # Proxy health cards
http://localhost:3000/jobs/<id> # Job detail + results + XHR log
```

### TypeScript — type-check (no build needed)

```bash
# Navigator
cd pipeline/navigator && npm run typecheck

# Dashboard
cd services/dashboard && npx tsc --noEmit

# Custom n8n nodes
cd orchestrator/custom-nodes/PythonBridgeNode && npx tsc --noEmit
cd orchestrator/custom-nodes/ProxyRotatorNode  && npx tsc --noEmit
```

### Dashboard — lint

```bash
cd services/dashboard
npm run lint
```

---

## API Reference

### Scraper API — `http://localhost:8000`

| Method | Route | Description |
|---|---|---|
| `POST` | `/scrape/` | Scrape a URL (Playwright or curl_cffi mode) |
| `POST` | `/parse/` | Extract structured data from HTML |
| `GET` | `/proxy/rotate` | Get next healthy proxy |
| `GET` | `/proxy/status` | List all proxies + health stats |
| `POST` | `/proxy/validate/{host}/{port}` | Test a proxy |
| `DELETE` | `/proxy/{host}/{port}` | Remove a proxy |
| `GET` | `/health` | Service health check |

**Scrape request body:**
```json
{
  "url": "https://example.com",
  "pattern": "generic",
  "use_proxy": true,
  "mode": "playwright"
}
```

### Dashboard API — `http://localhost:3000/api`

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/jobs` | List jobs (`?status=pending&limit=20&offset=0`) |
| `POST` | `/api/jobs` | Create + dispatch a new scrape job |
| `GET` | `/api/jobs/:id` | Get job + results by UUID |
| `DELETE` | `/api/jobs/:id` | Delete a job |
| `GET` | `/api/proxy` | Proxy pool status |
| `GET` | `/api/health` | Aggregated health (API + DB) |

---

## Database Schema

```sql
-- Core tables
jobs        (id, url, status, pattern, retries, max_retries, metadata, created_at, updated_at)
results     (id, job_id, url, data JSONB, scraped_at, created_at)
proxies     (host, port, protocol, username, password, healthy, fail_count, last_checked)
sessions    (id, cookies JSONB, headers JSONB, fingerprint JSONB, used_count, expires_at)
dead_letter (id, job_id, error, payload JSONB, created_at)
```

Job status flow: `pending → running → done | failed | dead`

---

## Stealth Features

- **TLS fingerprint rotation** — curl_cffi cycles through 6 real browser TLS profiles (chrome110/116/120/124, firefox120, edge101) per request
- **Dynamic browser fingerprint** — WebGL vendor/renderer, `navigator.platform`, `screen.colorDepth`, and canvas noise (1–15 px random delta) injected fresh per request from a pool
- **Human-like timing** — Gaussian-distributed delays (Box-Muller) between actions; proportional read delays; random scroll pauses
- **CAPTCHA detection + alerting** — multi-signal detection (HTTP status, `<title>`, DOM markers, body patterns) covering Cloudflare, hCaptcha, reCAPTCHA, DataDome, PerimeterX, Imperva; triggers n8n webhook alert and auto-throttles the domain
- **IP reputation screening** — proxies checked via proxycheck.io before use; risk > 75 blocks proxy; fails open
- **Per-domain rate limiting** — token bucket algorithm; auto-halves rate on CAPTCHA hit; runtime override via `set_domain_rate()`
- **User-agent pool** — realistic browser UA strings rotated per session
- **Proxy rotation** — circuit-breaker health tracking, automatic failover
- **Session reuse** — persistent cookies/headers across requests to same domain, backed by Postgres
- **Network interception** — capture XHR/fetch responses during Playwright navigation
- **Dual-mode scraping** — Playwright (JS-heavy sites) or curl_cffi (lightweight, TLS impersonation)

---

## Build Status

| Phase | Status | Commit |
|---|---|---|
| Phase 0 — Scaffolding | ✅ Complete | `6300f19` |
| Phase 1 — FastAPI Microservice | ✅ Complete | `36d8250` |
| Phase 2 — Next.js Dashboard | ✅ Complete | `76c9bed` |
| Phase 3 — Polyglot Pipeline | ✅ Complete | `c6d8c50` |
| Phase 4 — n8n Orchestrator | ✅ Complete | verified live |
| Phase 5 — Stealth Hardening | ✅ Complete | `5d19062` |
| Phase 6 — Production Hardening | ✅ Complete | `a13d75e` |
| Phase 7 — Multi-Tenancy & Auth | 🟡 Planned | — |
| Phase 8 — Usage Metering & Billing | 🟡 Planned | — |
| Phase 9 — Public API & SDKs | 🟡 Planned | — |
| Phase 10 — Async Queue & Scheduling | 🟡 Planned | — |
| Phase 11 — Observability & SLA | 🟡 Planned | — |
| Phase 12 — Kubernetes & CI/CD | 🟡 Planned | — |

---

## Production Hardening (Phase 6)

### pgBouncer — connection pooling

The stack includes a [pgBouncer](https://www.pgbouncer.org/) service that multiplexes application connections to Postgres. In `transaction` pool mode a connection is released back to the pool after each SQL transaction, allowing far more concurrent application connections than Postgres could handle directly.

```
Scraper API / Dashboard ──▶ pgBouncer :5432 (container) ──▶ Postgres :5432
         host port 6432 ──▶│  max 100 client conns          │
                            │  20 server connections          │
```

The image used is `edoburu/pgbouncer` (port 5432 inside the container, mapped to host port 6432). The FastAPI service also creates an `asyncpg.create_pool()` on startup (min 2, max 10) so connections within the process are reused rather than opened per request.

When using Docker Compose set `DATABASE_URL` to point at pgBouncer:

```env
DATABASE_URL=postgresql://scraper:changeme@pgbouncer:5432/scraper_db
```

### Centralized structured logging

| Service | Library | Format |
|---|---|---|
| Scraper API (Python) | `structlog` 24 | JSON to stdout |
| Dashboard (TypeScript) | `pino` 9 | JSON to stdout |

All services use the `json-file` Docker log driver with rotation (`max-size: 10m`, `max-file: 5`). Logs can be collected by any aggregator (Loki, Datadog, CloudWatch) without additional parsing.

Set `LOG_LEVEL` in `.env` to control dashboard verbosity (`trace|debug|info|warn|error`).

### Health checks

Every service exposes a health endpoint and is monitored by Docker's healthcheck:

| Service | Endpoint | Interval |
|---|---|---|
| Postgres | `pg_isready` | 10s |
| pgBouncer | `pg_isready :5432` (container) | 10s |
| Scraper API | `GET /health` | 15s |
| Dashboard | `GET /api/health` | 30s |

The `scraper-api` and `dashboard` services use `depends_on: condition: service_healthy` so they only start after their dependencies are confirmed healthy.

### Secrets management

- All secrets are loaded from `.env` via `python-dotenv` (Python) and `process.env` (Node.js)
- `.env` is listed in `.gitignore` — only `.env.example` (with placeholder values) is committed
- No passwords, API keys, or tokens are hardcoded anywhere in the source
- Rotate secrets by updating `.env` and restarting the affected service container

---

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

```env
# Database
POSTGRES_USER=scraper
POSTGRES_PASSWORD=changeme
POSTGRES_DB=scraper_db
DATABASE_URL=postgresql://scraper:changeme@postgres:5432/scraper_db

# Services
SCRAPER_API_URL=http://scraper-api:8000
N8N_PORT=5678

# Proxies (optional)
PROXY_LIST=socks5://user:pass@host:port
```

---

## Architecture Decisions

| ADR | Decision |
|---|---|
| ADR-001 | TypeScript for navigation, Python for parsing |
| ADR-002 | FastAPI async for scraper service |
| ADR-003 | n8n over Airflow/Celery for orchestration |
| ADR-004 | Playwright over Puppeteer/Selenium |
| ADR-005 | curl_cffi for HTTP-only scraping (TLS fingerprint impersonation) |
| ADR-007 | NextAuth.js v5 for multi-tenant auth (Phase 7) |
| ADR-008 | Credit-based metering over seat/time billing (Phase 8) |
| ADR-009 | BullMQ + Redis replaces n8n as primary job queue (Phase 10) |
| ADR-010 | Helm + ArgoCD for K8s GitOps CD (Phase 12) |

See [`developmentAI.md`](developmentAI.md) for the full AI-agnostic development tracker and session logs.

---

## SaaS Roadmap (Phases 7–12)

> The core infrastructure (Phases 0–6) is production-ready. Phases 7–12 evolve it into a
> multi-tenant, billable SaaS scraping platform. Each phase is independently deployable.

### Phase 7 — Multi-Tenancy & Authentication
Add user accounts, teams, and API key management so multiple customers can use the platform without seeing each other’s data.
- NextAuth.js v5 (Credentials + Google/GitHub OAuth) protecting all dashboard routes
- API keys (SHA-256 hashed) verified in FastAPI via `X-API-Key` header
- Postgres Row-Level Security scoping `jobs` and `results` to `tenant_id`
- RBAC: `admin`, `developer`, `viewer` roles

### Phase 8 — Usage Metering & Billing
Charge customers per scrape request with a credit system; integrate Stripe for subscriptions and top-ups.
- Credit model: 1 credit = HTTP scrape, 5 = browser scrape, 0.5 = parse
- Metering middleware deducts atomically before executing; returns `HTTP 402` when exhausted
- Stripe Products: Free (100 cr/mo), Pro (5 000 cr/mo), Enterprise (custom)
- Stripe webhooks restore credits on `invoice.paid`; hosted customer portal at `/billing`

### Phase 9 — Public API & Developer Experience
Publish a versioned REST API, typed SDKs, webhook delivery, and a documentation site so developers can integrate without touching the dashboard.
- Versioned routes under `/api/v1/`; OpenAPI 3.1 spec at `api.domain.com/docs`
- `@scraper/client` npm package and `scraper-client` PyPI package (auto-generated from spec)
- Webhook delivery with HMAC-SHA256 signatures and 3× retry
- In-dashboard playground for no-code scrape testing

### Phase 10 — Async Job Queue & Scheduling
Replace n8n as the throughput layer with BullMQ for high-concurrency, prioritised, and scheduled scraping.
- BullMQ (Redis-backed) queues: `scrape-http`, `scrape-browser`, `parse`, `webhook-delivery`
- Job priorities (critical/high/normal/low); per-tenant concurrency limits
- Cron/scheduled scrapes with pause/resume/delete
- SSE stream endpoint replaces polling for real-time job status in dashboard

### Phase 11 — Observability & SLA Monitoring
Give operators full visibility into platform health and SLA compliance.
- Prometheus metrics from FastAPI; Grafana dashboards (success rate, p50/p95/p99, credits/hr)
- AlertManager rules → Slack/PagerDuty for error rate >5%, queue depth >1000
- OpenTelemetry distributed tracing (FastAPI + Next.js); trace IDs in all logs
- Per-tenant SLA tracking (uptime %, p95 latency) visible in their dashboard account page

### Phase 12 — Kubernetes & CI/CD
Containerise the platform for cloud deployment with full GitOps automation.
- Helm chart `charts/scraper-platform` for all services
- HPA on scraper-api (CPU) and worker (KEDA queue-depth metric)
- GitHub Actions CI: lint, test, Docker build, Trivy image scan, push to GHCR
- ArgoCD GitOps CD watching `k8s/`; manual gate for production namespace
- External Secrets Operator pulling secrets from AWS SSM / HashiCorp Vault
