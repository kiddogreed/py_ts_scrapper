# services/scraper-api/main.py
"""
FastAPI application entry point.

Startup: loads proxy list, initializes shared state (ProxyManager, SessionPool).
All routers are mounted here. Shared state is stored on app.state so routers
can access it via FastAPI's Depends() injection.
"""
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
import structlog
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.proxy_manager import ProxyManager
from core.session_pool import SessionPool
from core.rate_limiter import RateLimiter
from routers import scrape, parse, proxy

load_dotenv()

# ---------------------------------------------------------------------------
# Structured logging setup
# WHY structlog? JSON logs are machine-readable — essential when logs flow to
# a collector (Loki, Datadog, CloudWatch). structlog adds context per request.
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: runs on startup and shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    proxy_list_path = os.getenv("PROXY_LIST_PATH", "shared/config/proxies.json")
    try:
        raw_proxies = json.loads(Path(proxy_list_path).read_text())
    except FileNotFoundError:
        logger.warning("proxy_list_not_found", path=proxy_list_path)
        raw_proxies = []

    # ---------------------------------------------------------------------------
    # Asyncpg connection pool (6.4 Production Hardening)
    # WHY: asyncpg.create_pool() pre-warms a fixed number of Postgres connections.
    # All DB operations reuse these connections instead of opening/closing per
    # request — reduces latency by ~5ms and prevents connection exhaustion.
    # The pool connects to pgBouncer (port 6432) in Docker, which further
    # multiplexes connections to Postgres in transaction mode.
    # ---------------------------------------------------------------------------
    db_url = os.getenv("DATABASE_URL")
    db_pool = None
    if db_url:
        try:
            db_pool = await asyncpg.create_pool(
                dsn=db_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            app.state.db_pool = db_pool
            logger.info("db_pool_ready", min=2, max=10)
        except Exception as exc:
            logger.warning("db_pool_failed", error=str(exc))
            app.state.db_pool = None
    else:
        app.state.db_pool = None

    app.state.proxy_manager = ProxyManager.from_list(raw_proxies)
    app.state.session_pool = SessionPool(db_pool=db_pool)
    app.state.rate_limiter = RateLimiter()

    # 5.7 — restore persisted sessions from Postgres on startup
    loaded = await app.state.session_pool.load_from_db()

    logger.info(
        "startup_complete",
        proxy_pool=app.state.proxy_manager.pool_status,
        sessions_loaded=loaded,
    )

    yield

    # ---- Shutdown ----
    if db_pool:
        await db_pool.close()
        logger.info("db_pool_closed")
    logger.info("shutdown")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Scraper API",
    description="Stealth-first scraping microservice — Pattern 1 of the hybrid stack.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: only the dashboard origin in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("NEXT_PUBLIC_ORIGIN", "http://localhost:3000")],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Mount routers
app.include_router(scrape.router)
app.include_router(parse.router)
app.include_router(proxy.router)


# ---------------------------------------------------------------------------
# Health check — required by Docker healthcheck and n8n readiness probe
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {
        "status": "ok",
        "proxy_pool": app.state.proxy_manager.pool_status,
        "session_domains": len(app.state.session_pool.stats),
    }
