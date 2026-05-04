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

- Docker + Docker Compose
- Node.js 22+
- Python 3.12+

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, SCRAPER_API_URL, N8N_PORT, etc.
```

### 2. Start full stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| Scraper API (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| n8n Orchestrator | http://localhost:${N8N_PORT} |

### 3. Local development (without Docker)

**FastAPI scraper:**
```bash
cd services/scraper-api
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000
```

**Next.js dashboard:**
```bash
cd services/dashboard
npm install
npm run dev     # http://localhost:3000
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

- **Fingerprint randomization** — WebGL renderer, platform, fonts, canvas noise per request
- **User-agent pool** — realistic browser UA strings rotated per session
- **Proxy rotation** — circuit-breaker health tracking, automatic failover
- **Session reuse** — persistent cookies/headers across requests to same domain
- **Network interception** — capture XHR/fetch responses during navigation
- **Dual-mode scraping** — Playwright (JS-heavy sites) or curl_cffi (TLS fingerprint impersonation for lightweight)

---

## Build Status

| Phase | Status | Commit |
|---|---|---|
| Phase 0 — Scaffolding | ✅ Complete | `6300f19` |
| Phase 1 — FastAPI Microservice | ✅ Complete | `36d8250` |
| Phase 2 — Next.js Dashboard | ✅ Complete | `76c9bed` |
| Phase 3 — Polyglot Pipeline | ⬜ Planned | — |
| Phase 4 — n8n Orchestrator | ⬜ Planned | — |
| Phase 5 — Stealth Hardening | ⬜ Planned | — |
| Phase 6 — Production Hardening | ⬜ Planned | — |

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

See [`developmentAI.md`](developmentAI.md) for the full AI-agnostic development tracker and session logs.
