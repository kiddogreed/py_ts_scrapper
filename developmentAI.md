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
STATUS: SAAS PLANNING — PHASES 7-12 DEFINED
LAST ACTION: Session 011 — Post-Phase 6 fixes and automation scripts:
             - Switched pgBouncer Docker image: bitnami/pgbouncer (404) → edoburu/pgbouncer:latest
             - Fixed pgBouncer env vars and port mapping (6432:5432)
             - Updated DATABASE_URL in .env from pgbouncer:6432 → pgbouncer:5432
             - Ran npm install in services/dashboard/ to sync package-lock.json
             - Created automation scripts: start.sh, start.bat, stop.sh, stop.bat
             - README.md updated: Quick Start with launch scripts, pgBouncer ports corrected, n8n port corrected (5679)
             - SaaS pivot: Phases 7-12 planned and documented in developmentAI.md
NEXT ACTION: Phase 7.1 — Add users/teams/api_keys tables to shared/db/schema.sql;
             then 7.2 NextAuth.js v5 + API key middleware in dashboard;
             then 7.3 FastAPI X-API-Key header auth
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

> **📅 2026-05-17 SaaS Pivot:** Phases 7–12 extend the core infrastructure into a
> multi-tenant, billable SaaS scraping platform. All Phase 1–6 foundations remain intact.

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

### Phase 2 — Pattern 1: Next.js Dashboard ✅ COMPLETE (commit: 76c9bed)
- [x] `2.1` Initialize Next.js 16 (create-next-app) in `services/dashboard/`
- [x] `2.2` Install dependencies: `axios`, `@tanstack/react-query`, `pg`, `@types/pg`
- [x] `2.3` Build API routes: `/api/jobs` (GET+POST), `/api/jobs/[id]` (GET+DELETE), `/api/proxy` (GET → FastAPI), `/api/health` (GET)
- [x] `2.4` Build jobs list page (`app/page.tsx`) — table, status badges, 5s auto-refresh, new job form, status filter
- [x] `2.5` Build job detail page (`app/jobs/[id]/page.tsx`) — metadata, results viewer, HTML preview, intercepted XHR
- [x] `2.6` Build proxy health page (`app/proxy/page.tsx`) — stat cards, health bar, 10s auto-refresh
- [x] `2.7` Write multi-stage Dockerfile (standalone output, node:22-alpine, healthcheck)

### Phase 3 — Pattern 2: Polyglot Pipeline ✅ COMPLETE (commit: c6d8c50)
- [x] `3.1` Initialize TypeScript project in `pipeline/navigator/`
- [x] `3.2` Install Playwright + stealth plugins (`playwright-extra`, `puppeteer-extra-plugin-stealth`)
- [x] `3.3` Build `stealth.ts` — headless browser stealth config
- [x] `3.4` Build `actions/navigate.ts` — URL navigation with retry logic
- [x] `3.5` Build `actions/intercept.ts` — network request interception (capture XHR/fetch)
- [x] `3.6` Build IPC bridge: TS navigator dumps JSON to stdout/file → Python picks up
- [x] `3.7` Initialize Python project in `pipeline/parser/`
- [x] `3.8` Build `extractors/base.py` — abstract extractor class
- [x] `3.9` Build `extractors/product.py` — concrete product page extractor
- [x] `3.10` Build `main.py` — stdin/file reader → parse → output to Postgres
- [x] `3.11` End-to-end test: TS navigates → Python parses → data in DB

### Phase 4 — Pattern 3: n8n Orchestrator
- [x] `4.1` Set up n8n via Docker in `orchestrator/`
- [x] `4.2` Connect n8n to Postgres for state management
- [x] `4.3` Create `scrape-job.json` workflow (trigger → scrape → parse → store)
- [x] `4.4` Create `retry-handler.json` workflow (failed jobs → exponential backoff)
- [x] `4.5` Build custom n8n node: `PythonBridgeNode` (calls FastAPI)
- [x] `4.6` Build custom n8n node: `ProxyRotatorNode` (fetches next proxy)
- [x] `4.7` Set up n8n credentials for Postgres + FastAPI
- [x] `4.8` Validate custom nodes (tsc clean) + workflow JSONs (9+10 nodes parse OK)
- [x] `4.9` Import workflows into live n8n instance (scrape-job + retry-handler)
- [x] `4.10` Configure Postgres credential in n8n UI (host: postgres, db: scraper_db, user: scraper)
- [x] `4.11` Activate scrape-job workflow (Published); fire test jobs → status DONE in DB
- [x] `4.12` Fix dashboard env: DATABASE_URL → postgres hostname; add SCRAPER_API_URL=http://scraper-api:8000

### Phase 5 — Stealth & Resilience Hardening ✅ COMPLETE (Session 009)
- [x] `5.1` Implement TLS fingerprint rotation (curl_cffi: chrome110/116/120/124/firefox120/edge101)
- [x] `5.2` Implement browser fingerprint pool (canvas noise, WebGL vendor/renderer, platform, colorDepth) — build_stealth_init_script() injects per-request values from fingerprints.json pool
- [x] `5.3` Implement human-like timing delays (Gaussian Box-Muller) — core/timing.py: human_delay(), read_delay(), random_scroll_pauses(), jittered_interval()
- [x] `5.4` Implement CAPTCHA detection + webhook alert — core/captcha_detector.py: multi-signal (title/body/DOM/status) + async n8n webhook via CAPTCHA_WEBHOOK_URL env var
- [x] `5.5` Implement IP reputation check before proxy use — ProxyManager.check_ip_reputation() via proxycheck.io; PROXYCHECK_API_KEY env var; fails open
- [x] `5.6` Add rate limiting per domain (token bucket algorithm) — core/rate_limiter.py: per-domain bucket, throttle_domain() on CAPTCHA, RATE_LIMIT_RPM env var
- [x] `5.7` Implement session cookie persistence across requests — SessionPool.load_from_db() on startup, fire-and-forget _persist_session() to Postgres sessions table

### Phase 6 — Production Hardening
- [x] `6.1` Full Docker Compose stack (all services)
- [x] `6.2` Centralized logging (structlog Python + pino TS → stdout)
- [x] `6.3` Health check endpoints for all services
- [x] `6.4` Postgres connection pooling (pgBouncer or asyncpg pool)
- [x] `6.5` Secrets management via `.env` (never hardcode)
- [x] `6.6` Write README.md with full setup instructions

---

### Phase 7 — Multi-Tenancy & Authentication _(SaaS Foundation)_
- [ ] `7.1` **DB schema** — Add `users`, `teams`, `api_keys`, `subscriptions`, `usage_events` tables to `shared/db/schema.sql`; Row-Level Security policies on `jobs`, `results` scoped to `tenant_id`
- [ ] `7.2` **NextAuth.js v5** — Install in dashboard; Credentials + Google/GitHub OAuth providers; JWT session strategy; protect all `/app` routes via middleware
- [ ] `7.3` **API key system** — Generate SHA-256 hashed keys; `POST /api/keys` to create, `DELETE /api/keys/[id]` to revoke; store prefix + hash (never plaintext)
- [ ] `7.4` **FastAPI auth middleware** — `X-API-Key` header validation against DB hash; inject `tenant_id` into request state; 401 on missing/invalid key
- [ ] `7.5` **RBAC** — Three roles: `admin` (all), `developer` (create/view own jobs), `viewer` (read-only); enforced at API route level
- [ ] `7.6` **Tenant isolation** — All scrape/job queries include `WHERE tenant_id = $1`; RLS as second layer; no cross-tenant data leakage
- [ ] `7.7` **Dashboard auth UI** — Login page, sign-up, profile page, API key management page, team invite (email)
- [ ] `7.8` **Test** — Register two tenants; verify jobs of tenant A are invisible to tenant B via API and dashboard

### Phase 8 — Usage Metering & Billing
- [ ] `8.1` **Credit model** — 1 credit = 1 HTTP scrape, 5 credits = 1 browser scrape, 0.5 credits = 1 parse; configurable per pricing tier in DB
- [ ] `8.2` **Metering middleware** — FastAPI dependency checks `credits_remaining > 0` before executing scrape; atomically deducts credits; writes `usage_events` row
- [ ] `8.3` **Stripe integration** — Products: Free (100 credits/mo), Pro (5 000 credits/mo), Enterprise (custom); `stripe.checkout.Session` for upgrades
- [ ] `8.4` **Stripe webhooks** — Handle `invoice.paid` (top-up credits), `customer.subscription.deleted` (downgrade to free), `customer.subscription.updated`
- [ ] `8.5` **Customer portal** — Stripe hosted portal link at `/billing`; invoice history, cancel, upgrade/downgrade
- [ ] `8.6` **Usage dashboard** — Credits used today/this month, live burn rate chart (TanStack Query polling), per-endpoint breakdown, export CSV
- [ ] `8.7` **Over-limit handling** — Return `HTTP 402 Payment Required` with `{"error": "credit_exhausted", "upgrade_url": ...}` instead of scraping
- [ ] `8.8` **Test** — Exhaust credits on a free account; verify 402 response; simulate `invoice.paid` webhook; verify credits restored

### Phase 9 — Public API & Developer Experience
- [ ] `9.1` **Versioned API** — Mount all public routes under `/api/v1/`; include `API-Version` response header; deprecation notices in OpenAPI tags
- [ ] `9.2` **OpenAPI 3.1 spec** — Auto-generated from FastAPI; add `securitySchemes: apiKey`; publish at `api.domain.com/docs`
- [ ] `9.3` **TypeScript SDK** — `@scraper/client` npm package: typed methods for `scrape()`, `parse()`, `getJob()`, `listJobs()`; auto-generated from OpenAPI spec
- [ ] `9.4` **Python SDK** — `scraper-client` PyPI package: same methods, async-first (`httpx`); auto-generated from OpenAPI spec
- [ ] `9.5` **Webhook delivery** — User registers `webhook_url` per job or globally; on job completion FastAPI POSTs signed payload (`X-Scraper-Signature: hmac-sha256`); retry 3×
- [ ] `9.6` **Playground UI** — Dashboard page to test scrape configs live: URL input, mode selector (http/browser), custom headers, response viewer with raw/parsed tabs
- [ ] `9.7` **API reference docs** — Mintlify or Fumadocs static site at `docs.domain.com`; code samples in Python, TypeScript, curl; generated from OpenAPI spec
- [ ] `9.8` **Test** — Call every v1 endpoint from both SDKs; verify webhook delivery + signature; confirm playground returns same result as direct API call

### Phase 10 — Async Job Queue & Scheduling
- [ ] `10.1` **BullMQ** — Add Redis service to `docker-compose.yml`; replace n8n as primary job queue; queues: `scrape-http`, `scrape-browser`, `parse`, `webhook-delivery`
- [ ] `10.2` **Job priorities** — Four levels: `critical` (0), `high` (1), `normal` (5), `low` (10); enterprise tenants get elevated default priority
- [ ] `10.3` **Scheduled / cron scrapes** — User-defined `cron` expression stored in DB; BullMQ repeatable jobs; pause/resume/delete via API
- [ ] `10.4` **Real-time status** — SSE endpoint `GET /api/v1/jobs/[id]/stream`; dashboard job detail page subscribes; eliminates polling
- [ ] `10.5` **Concurrency limits** — Per-tenant max concurrent jobs configurable (Free: 2, Pro: 10, Enterprise: 50); enforced at queue worker level
- [ ] `10.6` **Dead letter queue** — Failed jobs after max retries moved to `dead_letter` queue; dashboard DLQ page; manual requeue button
- [ ] `10.7` **Worker service** — New `services/worker/` Node.js service with BullMQ workers; containerised with its own Dockerfile; added to `docker-compose.yml`
- [ ] `10.8` **Test** — Submit 20 concurrent jobs; verify concurrency limits enforced; verify cron fires at correct time; verify SSE delivers updates in <1s

### Phase 11 — Observability & SLA Monitoring
- [ ] `11.1` **Prometheus** — Add `prometheus-fastapi-instrumentator` to scraper-api; expose `/metrics`; add Prometheus container to `docker-compose.yml`
- [ ] `11.2` **Grafana** — Add Grafana container; provision datasource (Prometheus + Postgres); pre-built dashboards: scrape success rate, latency p50/p95/p99, credits burned/hr, active sessions, proxy health
- [ ] `11.3` **AlertManager** — Rules: error rate >5% for 5min → Slack; queue depth >1000 → PagerDuty; credit exhaustion spike → email; add AlertManager container
- [ ] `11.4` **OpenTelemetry** — Instrument FastAPI + Next.js API routes with `opentelemetry-sdk`; export traces to Jaeger (or Grafana Tempo); trace ID propagated in headers
- [ ] `11.5` **SLA tracking** — Per-tenant uptime % and p95 latency stored in Postgres (5-min rollups); visible in dashboard account page; breach triggers email alert
- [ ] `11.6` **Synthetic monitoring** — n8n workflow fires a canary scrape every 5 min against a known stable URL; records success/latency; feeds Grafana
- [ ] `11.7` **Test** — Trigger a 5-min error storm; verify AlertManager fires Slack message; confirm p95 latency visible in Grafana within 2 scraping cycles

### Phase 12 — Kubernetes & CI/CD
- [ ] `12.1` **K8s manifests** — `k8s/` directory: Deployments (scraper-api, dashboard, worker), Services, Ingress (nginx), ConfigMaps, Secrets (sealed)
- [ ] `12.2` **Horizontal Pod Autoscaler** — HPA on scraper-api (CPU >70% → scale up to 10 pods) and worker (queue depth metric via KEDA)
- [ ] `12.3` **Helm chart** — Package all K8s manifests as `charts/scraper-platform`; `values.yaml` with image tags, replica counts, resource limits
- [ ] `12.4` **GitHub Actions CI** — On PR: lint (ruff + eslint), unit tests, Docker build, `trivy` image scan; on merge to main: push images to GHCR with SHA tag
- [ ] `12.5` **ArgoCD CD** — GitOps: ArgoCD watches `k8s/` directory; auto-sync on main push; manual gate for production namespace
- [ ] `12.6` **Secrets management** — External Secrets Operator pulling from AWS SSM Parameter Store (or HashiCorp Vault); no secrets in Git
- [ ] `12.7` **Multi-region proxy affinity** — Proxy pool tagged by region; jobs with `region` hint routed to matching worker pods in that region
- [ ] `12.8` **Test** — Deploy to staging K8s cluster; run load test (k6, 500 RPS for 60s); verify HPA scales; ArgoCD shows synced; rollback works

> Every “Why” is documented here so any AI or developer can understand the reasoning.

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

### ADR-007: Why NextAuth.js v5 for Multi-Tenant Auth? _(Phase 7)_

**Decision:** NextAuth.js v5 (Auth.js) as the authentication layer for the SaaS dashboard.

**Reasoning:**
- Already in the Next.js ecosystem; zero additional infrastructure.
- v5 supports the App Router (`auth()` server components, `middleware.ts` matcher).
- Supports both OAuth (Google/GitHub for quick sign-up) and Credentials (email/password for B2B).
- API key auth runs separately in FastAPI — dashboard auth (sessions) and API auth (keys) serve
  different client types (humans vs. machines) and must not be conflated.
- Alternative (Clerk) adds a paid third-party dependency; NextAuth keeps auth self-hosted.

### ADR-008: Why Credit-Based Metering Over Seat-Based Billing? _(Phase 8)_

**Decision:** Credit system (per-request) rather than seat or time-based billing.

**Reasoning:**
- Scraping costs correlate with usage, not headcount — credits map directly to compute cost.
- Different request types have different costs (browser = 5× HTTP) — credits express this
  naturally; seat/time models cannot.
- Credits enable pay-as-you-go top-ups without a subscription change, reducing churn.
- Stripe Metered Billing achieves the same but adds latency to usage tracking; a local
  Postgres counter is instant and can enforce limits synchronously mid-request.

### ADR-009: Why BullMQ Over Celery/n8n as Primary Queue? _(Phase 10)_

**Decision:** BullMQ (Node.js, Redis-backed) replaces n8n as the primary job queue for Phase 10+.

**Reasoning:**
- n8n is excellent for visual workflow authoring and ad-hoc automation but is not designed as
  a high-throughput job queue. It cannot handle 100s of concurrent jobs efficiently.
- BullMQ is purpose-built for job queues: concurrency limits, priorities, rate limiting, delayed
  jobs, and repeatable (cron) jobs are first-class features.
- Redis is already the natural store for ephemeral queue state; Postgres retains durable
  job records. The two complement each other — Redis for speed, Postgres for history.
- n8n is retained for alert workflows, webhook triggers, and human-facing automation
  (non-throughput use cases).
- Alternative (Celery) requires Python workers; our worker code is Node.js to match the
  existing TypeScript pipeline — BullMQ keeps the stack consistent.

### ADR-010: Why Helm + ArgoCD Over Raw Manifests for K8s? _(Phase 12)_

**Decision:** Helm chart packaged in `charts/` + ArgoCD for GitOps CD.

**Reasoning:**
- Helm parameterises per-environment differences (image tags, replicas, resource limits) without
  duplicating manifest files.
- ArgoCD provides a reconciliation loop — drift between Git and cluster state is detected and
  auto-corrected, preventing configuration decay across environments.
- GitHub Actions handles CI (lint, test, build, push) up to GHCR; ArgoCD handles CD from there.
  This separation keeps the CI pipeline stateless and the CD process auditable via Git history.

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

### Session 004 — 2026-05-04
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Executed Phase 2 in full:
  - Scaffolded Next.js 16.2.4 (create-next-app, TypeScript, Tailwind v4, App Router)
  - Installed: `axios`, `@tanstack/react-query`, `pg`, `@types/pg`
  - `lib/db.ts` — pg Pool singleton with hot-reload guard
  - `lib/scraper-client.ts` — axios client pointing to FastAPI (SCRAPER_API_URL)
  - `components/QueryProvider.tsx` — ReactQueryProvider wrapper (client component)
  - `app/api/jobs/route.ts` — GET (list jobs from Postgres) + POST (create job + dispatch to FastAPI)
  - `app/api/jobs/[id]/route.ts` — GET (job + results) + DELETE
  - `app/api/proxy/route.ts` — GET proxy status from FastAPI
  - `app/api/health/route.ts` — GET aggregated health check
  - `app/page.tsx` — jobs list: table, status badges, 5s auto-refresh, create job form, status filter
  - `app/jobs/[id]/page.tsx` — job detail: metadata, HTML preview, intercepted XHR, fingerprint viewer
  - `app/proxy/page.tsx` — proxy health: stat cards, color health bar, 10s refresh
  - `app/layout.tsx` — dark theme, nav (Jobs / Proxies), QueryProvider wrapper
  - `next.config.ts` — `output: 'standalone'` for Docker
  - `Dockerfile` — 3-stage (deps/builder/runner), node:22-alpine, HEALTHCHECK
  - TypeScript check: clean ✅, `npm run build` clean ✅, 8 routes registered ✅
  - Git commit: `76c9bed`
- **Completed Phases:** Phase 2 ✅
- **Next Session Should:** Phase 3 — Polyglot Pipeline (pipeline/navigator/ TS + pipeline/parser/ Python)

### Session 005 — 2026-05-05
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Executed Phase 3 in full:
  - `pipeline/navigator/package.json` — TypeScript project, playwright + playwright-extra + puppeteer-extra-plugin-stealth
  - `pipeline/navigator/tsconfig.json` — ES2022 + DOM lib, CommonJS output
  - `pipeline/navigator/stealth.ts` — randomStealthConfig(), applyStealthPatches() (webdriver/chrome/permissions/plugins patches), humanDelay() (Gaussian Box-Muller)
  - `pipeline/navigator/actions/navigate.ts` — navigateAndExtract() with stealth context, XHR interception, stdout/file IPC output, CLI entry point
  - `pipeline/navigator/actions/intercept.ts` — attachInterceptor() reusable capture layer, waitForCaptures() helper
  - `pipeline/navigator/index.ts` — CLI entry point with --output/--wait-for/--intercept/--timeout flags
  - `pipeline/parser/requirements.txt` — beautifulsoup4, lxml, asyncpg
  - `pipeline/parser/extractors/__init__.py` — package exports
  - `pipeline/parser/extractors/base.py` — abstract BaseExtractor (strategy pattern)
  - `pipeline/parser/extractors/product.py` — ProductExtractor: 4-strategy cascade (XHR → JSON-LD → OG meta → CSS heuristics)
  - `pipeline/parser/main.py` — stdin/file reader, extractor dispatch, asyncpg Postgres write, stdout output
  - tsc --noEmit: clean ✅
  - ProductExtractor smoke test: title/price/sku/rating/availability all extracted correctly ✅
  - main.py imports clean ✅
- **Completed Phases:** Phase 3 ✅
- **Next Session Should:** Phase 4 — n8n Orchestrator (orchestrator/)

### Session 006 — 2026-05-10
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Full verification audit of Phases 0–3:
  - Phase 0: All 8 shared files confirmed (schema.sql, fingerprints.json, proxies.json, scraper.d.ts, .env.example, docker-compose.yml). All 4 DB tables (jobs, results, proxies, sessions) verified in schema.sql. 4 fingerprint profiles. 9 type definitions. ✅
  - Phase 1: All 5 core modules import cleanly (stealth, proxy_manager, session_pool, html_parser, main). All 3 routers (scrape, parse, proxy) verified. HtmlParser `generic_extract()` + `extract_meta()` + `extract_links()` confirmed working. All 9 pip packages confirmed installed. **BUG FIXED:** `curl-cffi==0.7.1` was in requirements.txt but not installed in venv — installed it; `AsyncSession` now importable. `_http_scrape` TLS impersonation confirmed. ✅
  - Phase 2: All 13 dashboard source files present. `tsc --noEmit` clean. `next.config.ts` standalone output confirmed. All 5 npm deps (axios, @tanstack/react-query, pg, @types/pg, typescript) present. ✅
  - Phase 3: `tsc --noEmit` clean on navigator. BaseExtractor + ProductExtractor smoke test: JSON-LD cascade extracted title="Blue Widget", price=19.99, sku="BW-001", rating="4.5", availability="InStock". main.py syntax OK. All 3 navigator npm deps present. ✅
- **Fixes Applied:** Installed `curl-cffi==0.7.1` into venv (was listed in requirements.txt but missing from environment)
- **Completed Phases:** Phases 0–3 verified ✅
- **Next Session Should:** Phase 4 — n8n Orchestrator (orchestrator/)

### Session 007 — 2026-05-10
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Implemented all Phase 4 tasks:
  - `4.1` `orchestrator/docker-compose.yml` — Postgres + n8n standalone dev stack, custom-nodes volume mounted ro
  - `4.2` `orchestrator/init/02_n8n_db.sql` — conditional CREATE DATABASE n8n_db via \gexec
  - `4.3` `orchestrator/workflows/scrape-job.json` — 9-node workflow: Webhook → Validate → Scrape → Parse → Store Job → Store Result → Respond (200); error path → Log Dead Letter → 500
  - `4.4` `orchestrator/workflows/retry-handler.json` — 10-node workflow: Schedule (5min) → Fetch Failed → IF any → SplitBatches → Prepare → Mark Running → Retry → Mark Done; error path → Mark Failed/Dead
  - `4.5` `orchestrator/custom-nodes/PythonBridgeNode/` — 5 files, operations: scrape + parse, n8n-workflow INodeType, tsc clean ✅
  - `4.6` `orchestrator/custom-nodes/ProxyRotatorNode/` — 6 files, operations: rotate + status + validate + retire, tsc clean ✅
  - `4.7` `orchestrator/CREDENTIALS.md` — setup guide for Scraper Postgres + Scraper API credentials in n8n UI
  - `4.8` Workflow JSON validation: scrape-job.json (9 nodes) ✅, retry-handler.json (10 nodes) ✅; tsc clean both nodes ✅
- **Bug Fixed:** `Record<string, unknown>` not assignable to `IDataObject` — replaced all occurrences in both node files
- **Bug Fixed:** Cross-package re-export violated TypeScript `rootDir` — inlined credential class in ProxyRotatorNode
- **Completed Phases:** Phase 4 ✅
- **Next Session Should:** Phase 5 — Stealth & Resilience Hardening

### Session 008 — 2026-05-11
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** End-to-end stack verification and live test run:
  - Confirmed custom nodes mounted: `docker exec n8n ls /home/node/.n8n/custom/` → PythonBridgeNode + ProxyRotatorNode ✅
  - Imported `scrape-job.json` and `retry-handler.json` into live n8n instance via UI
  - Created Postgres credential in n8n UI: host=`postgres`, db=`scraper_db`, user=`scraper`, password=`change_me_in_production`
  - Activated scrape-job workflow (Published green badge ✅)
  - Submitted test jobs from dashboard: `https://books.toscrape.com/` + `https://quotes.toscrape.com/` → both STATUS=`done` in DB ✅
  - Confirmed results stored in `results` table (JSONB `data` column with raw HTML)
- **Bug Fixed:** Dashboard showed "Failed to create job" — `DATABASE_URL` in `.env` used `localhost` instead of Docker service name. Fixed: `localhost:5432` → `postgres:5432`
- **Bug Fixed:** Added `SCRAPER_API_URL=http://scraper-api:8000` to `.env` — dashboard container couldn't reach scraper-api via `localhost`
- **DB Schema Confirmed:** Tables: `jobs`, `results`, `proxies`, `sessions`, `dead_letter`. Results stored as `{html: "<raw HTML>"}` in JSONB `data` column.
- **Note:** Parse HTML node in workflow stores raw HTML only — structured extraction (title, links) is a Phase 5 improvement
- **Completed:** Phase 4 fully verified in production Docker stack ✅
- **Next Session Should:** Phase 5 — Stealth & Resilience Hardening (5.1 TLS fingerprint rotation first)

### Session 009 — 2026-05-11
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Implemented all Phase 5 tasks:
  - `5.1` `core/stealth.py` — Added `TLS_PROFILES` list (chrome110/116/120/124/firefox120/edge101) and `get_random_tls_profile()`. `_http_scrape` now rotates profile per request.
  - `5.2` `core/stealth.py` — Added `build_stealth_init_script(fingerprint)`: per-request JavaScript IIFE that injects WebGL vendor/renderer, navigator.platform, screen.colorDepth/pixelDepth from the fingerprint pool, plus canvas noise (random 1–15 pixel delta). Replaced static `STEALTH_INIT_SCRIPT` in browser scrape path with dynamic call.
  - `5.3` `core/timing.py` (new file) — `human_delay()` (Gaussian, Box-Muller, min/max clamped), `read_delay()` (proportional to content length ±20% jitter), `random_scroll_pauses()`, `jittered_interval()`. Replaced `random.gauss()` in scrape.py.
  - `5.4` `core/captcha_detector.py` (new file) — `is_captcha_page()`: multi-signal detection (status 403/429/503 fast-path, `<title>` regex, DOM marker substring scan, body pattern regex covering Cloudflare/hCaptcha/reCAPTCHA/DataDome/PerimeterX/Incapsula). `send_captcha_alert()`: async httpx POST to CAPTCHA_WEBHOOK_URL. Wired into both `_browser_scrape` and `_http_scrape`; on CAPTCHA: fires webhook + throttles domain + invalidates session + raises HTTP 503.
  - `5.5` `core/proxy_manager.py` — Added `check_ip_reputation()`: calls proxycheck.io v2 API (vpn+risk flags); blocks proxy only if risk>75 AND flagged as proxy; fails open. PROXYCHECK_API_KEY env var for higher limits.
  - `5.6` `core/rate_limiter.py` (new file) — `RateLimiter`: per-domain `_Bucket` (token bucket, asyncio.Lock), `acquire()` suspends caller if empty, `throttle_domain()` halves rate on CAPTCHA, `set_domain_rate()` for manual override, RATE_LIMIT_RPM env var. Wired as `app.state.rate_limiter` in main.py, Depends() in scrape router.
  - `5.7` `core/session_pool.py` — Added Postgres persistence: `load_from_db()` (loads valid sessions at startup via asyncpg), `_persist_session()` (fire-and-forget INSERT/upsert to sessions table), `_delete_from_db()` (on domain invalidation). All DB failures are non-fatal — graceful in-memory fallback.
  - `main.py` — Imports RateLimiter, initialises `app.state.rate_limiter`, calls `session_pool.load_from_db()` on startup.
  - `Bug Fixed:` `is_captcha_page()` status code check was after empty-HTML guard — moved before so `is_captcha_page('', status_code=403)` correctly returns True.
- **Tests:** All 7 smoke tests PASSED (py_compile clean + functional assertions)
- **New env vars:** `CAPTCHA_WEBHOOK_URL`, `PROXYCHECK_API_KEY`, `RATE_LIMIT_RPM`
- **Completed Phases:** Phase 5 ✅
- **Next Session Should:** Phase 6 — Production Hardening (centralized logging, health checks, pgBouncer, README)

### Session 010 — 2026-05-11
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:** Implemented all Phase 6 Production Hardening tasks:
  - `6.1` `docker-compose.yml` — Added `x-logging` YAML anchor (json-file driver, max-size 10m, max-file 5) applied to all services. Added `pgbouncer` service (bitnami/pgbouncer, port 6432, transaction mode, max_client_conn=100, default_pool_size=20, healthcheck). Added `healthcheck:` to `dashboard` service (wget on `/api/health`, 30s interval/start_period). `scraper-api` now `depends_on: pgbouncer: condition: service_healthy`. Added `start_period: 20s` to scraper-api healthcheck.
  - `6.2` `services/dashboard/package.json` — Added `"pino": "^9.5.0"` to dependencies. `services/dashboard/lib/logger.ts` (new file) — pino logger with `LOG_LEVEL` env, `pino-pretty` transport in dev, `base: { service, env }`, `serializers: { err }`. Wired `logger.error(...)` into all 4 API routes (`jobs/route.ts`, `jobs/[id]/route.ts`, `proxy/route.ts`, `health/route.ts`) replacing `console.error`.
  - `6.3` Health checks already existed on FastAPI `/health` and dashboard `/api/health`. Added docker-compose service-level `healthcheck:` to `dashboard` (task 6.1). Verified all services covered.
  - `6.4` `services/scraper-api/main.py` — Added `asyncpg.create_pool(dsn=db_url, min_size=2, max_size=10, command_timeout=30)` in lifespan startup; stores as `app.state.db_pool`; passes `db_pool` to `SessionPool`; closes pool on teardown. `core/session_pool.py` — `__init__` accepts `db_pool: Optional[Any]`; all three DB methods use `async with self._pool.acquire() as conn` when pool available, fallback to `asyncpg.connect()`.
  - `6.5` `.env.example` — Added pgBouncer connection comment, `PGBOUNCER_MAX_CLIENT_CONN=100`, `PGBOUNCER_DEFAULT_POOL_SIZE=20`, `LOG_LEVEL=info`.
  - `6.6` `README.md` — Phase 6 row updated to ✅ Complete. Added "## Production Hardening (Phase 6)" section covering pgBouncer architecture, asyncpg pool, structured logging table, health check table, and secrets management notes.
- **Bug Fixed:** `session_pool.py` — `load_from_db()` row-processing loop was missing after earlier partial edit; added `loaded = 0; for row in rows: ...` block to correctly hydrate sessions from DB.
- **New env vars:** `PGBOUNCER_MAX_CLIENT_CONN`, `PGBOUNCER_DEFAULT_POOL_SIZE`, `LOG_LEVEL`
- **Completed Phases:** Phase 6 ✅ — All 6 phases complete. Project is production-ready.
- **Next Session Should:** No further phases planned. Potential follow-ups: Kubernetes manifests, CI/CD pipeline, Prometheus metrics, or structured product extraction in the parser.

---

### Session 011 — 2026-05-17
- **Agent:** GitHub Copilot (Claude Sonnet 4.6)
- **Actions:**
  - **pgBouncer image swap:** `bitnami/pgbouncer:latest` no longer resolves on Docker Hub. Replaced with `edoburu/pgbouncer:latest`. Updated env var names (`POSTGRESQL_HOST` → `DB_HOST`, `POSTGRESQL_PORT` → `DB_PORT`, `POSTGRESQL_USER` → `DB_USER`, `POSTGRESQL_PASSWORD` → `DB_PASSWORD`, `POSTGRESQL_DATABASE` → `DB_NAME`). Updated port mapping from `6432:6432` → `6432:5432` because edoburu listens on port 5432 inside the container.
  - **`DATABASE_URL` fix:** `.env` and `.env.example` updated from `pgbouncer:6432` → `pgbouncer:5432` to match edoburu's internal port.
  - **`package-lock.json` sync:** `pino` was added to `services/dashboard/package.json` in Session 010 but `npm install` was never run. Docker build failed with `npm ci` lockfile mismatch. Fixed by running `npm install` in `services/dashboard/`.
  - **Full stack verified running:** `docker compose up --build -d` succeeded. All 5 services (postgres, pgbouncer, scraper-api, dashboard, n8n) reached healthy state. `http://localhost:8000/health` and `http://localhost:3000/api/health` both return `{"status":"ok"}`.
  - **Automation scripts created:**
    - `start.sh` — Git Bash: checks/starts Docker Desktop, syncs lockfile, `docker compose up --build -d`, polls health endpoints, prints URLs. Supports `--no-build` flag.
    - `start.bat` — Windows CMD equivalent of `start.sh`.
    - `stop.sh` — Git Bash: `docker compose down` (volumes preserved); `--clean` flag also removes volumes.
    - `stop.bat` — Windows CMD equivalent of `stop.sh`.
  - **README.md updated:** Quick Start section now documents `./start.sh` / `start.bat` as primary method; manual `docker compose` steps kept as fallback. n8n URL corrected from port 5678 → 5679. pgBouncer port diagram and `DATABASE_URL` example corrected to use internal port 5432. Health check table corrected to `pg_isready :5432 (container)`.
- **Bugs Fixed:** bitnami/pgbouncer image (404), DATABASE_URL wrong port, npm ci lockfile mismatch.
- **New files:** `start.sh`, `start.bat`, `stop.sh`, `stop.bat`
- **Git:** Committed and pushed to `origin/main` — commit `a13d75e` "feat: Phase 6 — Production Hardening complete" (16 files changed, 762 insertions, 107 deletions)
- **Completed Phases:** No new phases — all 6 remain complete. Post-release stabilisation.

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
