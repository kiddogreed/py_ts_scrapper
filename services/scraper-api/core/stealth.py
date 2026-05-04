# services/scraper-api/core/stealth.py
"""
Browser fingerprint randomization.

WHY: Anti-bot systems (Cloudflare, PerimeterX, Akamai) build a fingerprint from
dozens of browser signals — user-agent, viewport, timezone, WebGL, canvas noise,
accepted headers. Returning a consistent fingerprint across requests is a red flag.
This module randomizes every signal per-request so each scrape looks like a
different real user on a different machine.
"""
import json
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Fingerprint pool (WebGL vendor/renderer, platform, screen depth)
# Loaded once at import time — file is shared/config/fingerprints.json
# ---------------------------------------------------------------------------
_FINGERPRINT_POOL_PATH = (
    Path(__file__).resolve().parents[3] / "shared" / "config" / "fingerprints.json"
)

try:
    _FINGERPRINT_POOL: list[dict] = json.loads(_FINGERPRINT_POOL_PATH.read_text())
except FileNotFoundError:
    _FINGERPRINT_POOL = [
        {
            "webgl_vendor": "Google Inc. (NVIDIA)",
            "webgl_renderer": "ANGLE (NVIDIA GeForce RTX 3070, D3D11)",
            "platform": "Win32",
            "screen_depth": 24,
        }
    ]

# ---------------------------------------------------------------------------
# Static pools
# ---------------------------------------------------------------------------
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

VIEWPORTS: list[dict] = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
    {"width": 1536, "height": 864},
]

TIMEZONES: list[str] = [
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "America/Denver",
    "Europe/London",
    "Europe/Paris",
]

LOCALES: list[str] = ["en-US", "en-GB", "en-CA", "en-AU"]

REFERRERS: list[str] = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "",  # direct navigation
]


def get_random_fingerprint() -> dict:
    """
    Returns a fully randomized browser fingerprint config for one scrape request.
    Every field is independently randomized so fingerprints don't cluster.
    """
    locale = random.choice(LOCALES)
    hw_fingerprint = random.choice(_FINGERPRINT_POOL)

    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": random.choice(VIEWPORTS),
        "timezone": random.choice(TIMEZONES),
        "locale": locale,
        "referrer": random.choice(REFERRERS),
        "hardware": hw_fingerprint,
        "extra_headers": {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": f"{locale},en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        },
    }


# Init script injected into every Playwright browser context.
# Patches the most commonly checked navigator/window properties.
STEALTH_INIT_SCRIPT = """
() => {
    // 1. Hide webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // 2. Restore chrome runtime (headless Chrome removes it)
    window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {} };

    // 3. Fix permissions API (returns 'denied' for notifications in headless)
    const origQuery = window.navigator.permissions.query.bind(navigator.permissions);
    window.navigator.permissions.query = (p) =>
        p.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origQuery(p);

    // 4. Fake a realistic plugin list length
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });

    // 5. Fake languages
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
}
"""
