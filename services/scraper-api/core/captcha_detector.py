# services/scraper-api/core/captcha_detector.py
"""
CAPTCHA detection and webhook alerting.

WHY: When a scrape returns a CAPTCHA page, continuing to hammer the same
endpoint wastes proxies and risks permabanning the IP. We detect common
CAPTCHA patterns in the HTML response and fire a webhook to n8n so the
workflow can pause, swap proxies, and optionally trigger a CAPTCHA-solving
service (manual or automated).

Detection approach — multi-signal cascade:
  1. Page <title> keywords (fastest, no full parse needed)
  2. Body text / script src patterns
  3. Known CAPTCHA provider DOM markers (hCaptcha, reCAPTCHA, Cloudflare
     Turnstile, DataDome, PerimeterX, Shape Security)

Webhook integration:
  Set CAPTCHA_WEBHOOK_URL in .env to receive alerts in n8n:
    CAPTCHA_WEBHOOK_URL=http://n8n:5678/webhook/captcha-alert
"""
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# <title> content that strongly indicates a challenge/block page
_TITLE_PATTERNS = re.compile(
    r"(captcha|robot|human verification|access denied|security check|"
    r"ddos-guard|just a moment|checking your browser|challenge|"
    r"are you a bot|bot detection|attention required|verify you are human)",
    re.IGNORECASE,
)

# Strings found in the <body> / <script src> that indicate CAPTCHA providers
_BODY_PATTERNS = re.compile(
    r"(hcaptcha\.com|recaptcha\.net|www\.recaptcha\.net|"
    r"cf-challenge|cf-turnstile|__cf_chl_opt|"
    r"datadome\.co|js\.datadome\.co|"
    r"px-captcha|px\.perfdns\.com|_pxParam|"
    r"please enable javascript and cookies|"
    r"unusual traffic from your computer|"
    r"automated access to this page has been denied)",
    re.IGNORECASE,
)

# Raw substrings to search in the full HTML (avoids regex overhead for simple checks)
_DOM_MARKERS: list[str] = [
    'id="challenge-form"',          # Cloudflare challenge form
    'id="challenge-stage"',         # Cloudflare 2024+ layout
    'class="g-recaptcha"',          # Google reCAPTCHA v2
    'class="h-captcha"',            # hCaptcha
    'data-sitekey',                  # Generic CAPTCHA SDK marker
    '__cf_chl_opt',                  # Cloudflare JS challenge variable
    'px-captcha',                    # PerimeterX
    'datadome',                      # DataDome script tag
    'shape-sec.com',                 # Shape Security / F5
    'incapsula.com',                 # Imperva Incapsula
    'akamai-bot-manager',            # Akamai Bot Manager
]

# HTTP status codes that almost always mean we're blocked
BLOCKED_STATUS_CODES: set[int] = {403, 429, 503}


# ---------------------------------------------------------------------------
# Detection function
# ---------------------------------------------------------------------------

def is_captcha_page(html: str, url: str = "", status_code: int = 200) -> bool:
    """
    Returns True if the HTML looks like a CAPTCHA / challenge / block page.

    Checks (in order of cost):
      1. HTTP status code (instant)
      2. <title> keywords (regex on ~100 chars)
      3. DOM marker substrings (one pass over full HTML)
      4. Body regex patterns (compiled, single pass)

    Args:
        html:        Raw HTML string from the scraper.
        url:         Source URL — only used for logging context.
        status_code: HTTP response status; 403/429/503 are strong signals.
    """
    # 1. Status code fast-path (checked before html guard — empty body + 403 is a block)
    if status_code in BLOCKED_STATUS_CODES:
        logger.warning("CAPTCHA/block detected via status %d — %s", status_code, url)
        return True

    if not html:
        return False

    # 2. Title check — extract up to 300 chars inside <title>…</title>
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", html[:2000], re.IGNORECASE | re.DOTALL
    )
    if title_match:
        title = title_match.group(1).strip()[:300]
        if _TITLE_PATTERNS.search(title):
            logger.warning("CAPTCHA detected via title %r — %s", title, url)
            return True

    # 3. DOM markers — fast substring scan
    for marker in _DOM_MARKERS:
        if marker in html:
            logger.warning("CAPTCHA detected via DOM marker %r — %s", marker, url)
            return True

    # 4. Body pattern regex — covers script src URLs and inline text
    if _BODY_PATTERNS.search(html):
        logger.warning("CAPTCHA detected via body pattern — %s", url)
        return True

    return False


# ---------------------------------------------------------------------------
# Webhook alert
# ---------------------------------------------------------------------------

async def send_captcha_alert(
    url: str,
    proxy_used: Optional[str] = None,
    status_code: int = 0,
) -> None:
    """
    Fires a POST to the n8n CAPTCHA alert webhook (if CAPTCHA_WEBHOOK_URL is set).

    Non-blocking: network failures are logged but do not raise exceptions.
    The scraper should still handle the CAPTCHA page (skip / retry with
    different proxy) regardless of whether the webhook succeeds.

    Payload sent to n8n:
        {
            "event": "captcha_detected",
            "target_url": "<url>",
            "proxy_used": "<ip:port or null>",
            "status_code": 403
        }
    """
    webhook_url = os.getenv("CAPTCHA_WEBHOOK_URL", "").strip()
    if not webhook_url:
        logger.debug("CAPTCHA_WEBHOOK_URL not configured — skipping alert for %s", url)
        return

    payload = {
        "event": "captcha_detected",
        "target_url": url,
        "proxy_used": proxy_used,
        "status_code": status_code,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(webhook_url, json=payload)
            logger.info(
                "CAPTCHA webhook fired: http=%d target=%s", resp.status_code, url
            )
    except Exception as exc:
        # Webhook failure must never crash the scraper
        logger.warning("CAPTCHA webhook failed (%s) — %s", exc, url)
