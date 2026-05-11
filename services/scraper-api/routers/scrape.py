# services/scraper-api/routers/scrape.py
"""
POST /scrape — Core scraping endpoint.

Two modes controlled by `javascript` flag:
  - javascript=true  → Playwright headless browser (handles SPAs, JS-rendered pages)
  - javascript=false → curl_cffi (fast, TLS-fingerprint-impersonating HTTP client)

WHY two modes? Browser automation is 10-100x slower than HTTP requests. For
pages that don't need JS execution (static HTML, JSON APIs), curl_cffi is the
right tool. For React/Vue SPAs or sites that fingerprint via JS, Playwright is
required. The caller decides based on the target site.

Phase 5 additions:
  - TLS profile rotation via get_random_tls_profile() (5.1)
  - Dynamic WebGL/canvas init script via build_stealth_init_script() (5.2)
  - human_delay() from core.timing replaces ad-hoc random.gauss() calls (5.3)
  - CAPTCHA detection + webhook alert after every scrape (5.4)
  - Rate limiter acquire() before every request (5.6)
"""
import logging
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from playwright.async_api import async_playwright
from pydantic import BaseModel, HttpUrl
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.stealth import build_stealth_init_script, get_random_fingerprint, get_random_tls_profile
from core.session_pool import SessionPool
from core.timing import human_delay
from core.captcha_detector import is_captcha_page, send_captcha_alert
from core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scraping"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ScrapeRequest(BaseModel):
    url: HttpUrl
    wait_for: Optional[str] = None          # CSS selector to wait for before returning HTML
    intercept_pattern: Optional[str] = None # Capture network responses whose URL contains this
    javascript: bool = True                 # True = Playwright, False = curl_cffi
    timeout_ms: int = 30000
    use_session: bool = True                # Reuse cookies from session pool


class ScrapeResponse(BaseModel):
    url: str
    html: Optional[str] = None
    intercepted: list[dict] = []
    status_code: int
    fingerprint_used: dict


# ---------------------------------------------------------------------------
# Dependency: get session pool and rate limiter from app state
# ---------------------------------------------------------------------------

def get_session_pool(request: Request) -> SessionPool:
    return request.app.state.session_pool


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


# ---------------------------------------------------------------------------
# Route handler
# ---------------------------------------------------------------------------

@router.post("/", response_model=ScrapeResponse)
async def scrape_url(
    req: ScrapeRequest,
    session_pool: SessionPool = Depends(get_session_pool),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ScrapeResponse:
    domain = urlparse(str(req.url)).netloc
    try:
        # 5.6 — enforce per-domain rate limit before sending any request
        waited = await rate_limiter.acquire(domain)
        if waited > 0.5:
            logger.info("Rate limit: waited %.2fs for %s", waited, domain)

        if req.javascript:
            return await _browser_scrape(req, session_pool, rate_limiter, domain)
        return await _http_scrape(req, rate_limiter, domain)
    except Exception as exc:
        logger.exception("Scrape failed for %s", req.url)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Browser scrape (Playwright)
# ---------------------------------------------------------------------------

async def _browser_scrape(
    req: ScrapeRequest,
    session_pool: SessionPool,
    rate_limiter: RateLimiter,
    domain: str,
) -> ScrapeResponse:
    fingerprint = get_random_fingerprint()
    # 5.2 — per-request init script with baked-in WebGL/canvas/platform values
    init_script = build_stealth_init_script(fingerprint)
    intercepted: list[dict] = []

    # Attempt to reuse an existing session for this domain
    existing_session = None
    if req.use_session:
        existing_session = await session_pool.get_session(domain)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        context_options = dict(
            user_agent=fingerprint["user_agent"],
            viewport=fingerprint["viewport"],
            locale=fingerprint["locale"],
            timezone_id=fingerprint["timezone"],
            extra_http_headers=fingerprint["extra_headers"],
        )

        # Restore cookies from session pool if available
        if existing_session and existing_session.cookies:
            context_options["storage_state"] = {
                "cookies": existing_session.cookies,
                "origins": [],
            }

        context = await browser.new_context(**context_options)
        # 5.2 — dynamic init script replaces static STEALTH_INIT_SCRIPT
        await context.add_init_script(init_script)
        page = await context.new_page()

        # Network interception — capture matching XHR/fetch responses
        if req.intercept_pattern:
            async def handle_response(response):
                if req.intercept_pattern in response.url:
                    try:
                        body = await response.json()
                        intercepted.append({"url": response.url, "data": body})
                    except Exception:
                        pass

            page.on("response", handle_response)

        # 5.3 — human-like Gaussian delay before navigating
        await human_delay(mean_ms=1200, std_ms=400)

        response = await page.goto(
            str(req.url),
            timeout=req.timeout_ms,
            wait_until="networkidle",
            referer=fingerprint["referrer"] or None,
        )
        status = response.status if response else 0

        if req.wait_for:
            await page.wait_for_selector(req.wait_for, timeout=req.timeout_ms)

        html = await page.content()

        # Persist cookies back to session pool for next request
        if req.use_session:
            cookies = await context.cookies()
            await session_pool.store_session(
                domain=domain,
                cookies=cookies,
                user_agent=fingerprint["user_agent"],
                fingerprint=fingerprint,
            )

        await browser.close()

    # 5.4 — CAPTCHA detection + optional webhook alert
    if is_captcha_page(html, url=str(req.url), status_code=status):
        await send_captcha_alert(str(req.url), status_code=status)
        # 5.6 — back off this domain after a CAPTCHA hit
        rate_limiter.throttle_domain(domain)
        # Invalidate session — cookies may be tainted
        await session_pool.invalidate_domain(domain)
        raise HTTPException(
            status_code=503,
            detail=f"CAPTCHA/challenge page detected at {req.url}",
        )

    return ScrapeResponse(
        url=str(req.url),
        html=html,
        intercepted=intercepted,
        status_code=status,
        fingerprint_used=fingerprint,
    )


# ---------------------------------------------------------------------------
# HTTP scrape (curl_cffi — TLS fingerprint impersonation)
# WHY curl_cffi: Python's httpx/requests use a Python TLS stack with a
# distinct JA3 fingerprint that Cloudflare/Akamai detect immediately.
# curl_cffi wraps libcurl and can impersonate Chrome/Firefox TLS handshakes.
# Phase 5.1: rotate TLS profile instead of always using chrome120.
# ---------------------------------------------------------------------------

async def _http_scrape(
    req: ScrapeRequest,
    rate_limiter: RateLimiter,
    domain: str,
) -> ScrapeResponse:
    try:
        from curl_cffi.requests import AsyncSession
    except ImportError as exc:
        raise HTTPException(
            status_code=500, detail="curl_cffi not installed"
        ) from exc

    fingerprint = get_random_fingerprint()
    # 5.1 — rotate TLS profile per request
    tls_profile = get_random_tls_profile()

    # 5.3 — human-like delay before HTTP request too
    await human_delay(mean_ms=800, std_ms=300)

    async with AsyncSession(impersonate=tls_profile) as session:
        response = await session.get(
            str(req.url),
            headers={
                **fingerprint["extra_headers"],
                "User-Agent": fingerprint["user_agent"],
            },
            timeout=req.timeout_ms / 1000,
            allow_redirects=True,
        )

    html = response.text
    status = response.status_code

    # 5.4 — CAPTCHA detection
    if is_captcha_page(html, url=str(req.url), status_code=status):
        await send_captcha_alert(str(req.url), status_code=status)
        rate_limiter.throttle_domain(domain)
        raise HTTPException(
            status_code=503,
            detail=f"CAPTCHA/challenge page detected at {req.url}",
        )

    return ScrapeResponse(
        url=str(req.url),
        html=html,
        intercepted=[],
        status_code=status,
        fingerprint_used={**fingerprint, "tls_profile": tls_profile},
    )
