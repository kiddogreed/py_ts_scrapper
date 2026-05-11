# services/scraper-api/core/stealth.py
"""
Browser fingerprint randomization + TLS profile rotation.

WHY: Anti-bot systems (Cloudflare, PerimeterX, Akamai) build a fingerprint from
dozens of browser signals — user-agent, viewport, timezone, WebGL, canvas noise,
accepted headers. Returning a consistent fingerprint across requests is a red flag.
This module randomizes every signal per-request so each scrape looks like a
different real user on a different machine.

Phase 5 additions:
  - TLS_PROFILES pool for curl_cffi impersonation rotation (5.1)
  - build_stealth_init_script(): per-request dynamic WebGL/canvas/platform injection (5.2)
"""
import json
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Fingerprint pool (WebGL vendor/renderer, platform, screen depth)
# Loaded once at import time — file is shared/config/fingerprints.json
# ---------------------------------------------------------------------------
_FINGERPRINT_POOL_PATH = (
    Path(__file__).resolve().parents[1] / "shared" / "config" / "fingerprints.json"
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

# ---------------------------------------------------------------------------
# TLS impersonation profiles (5.1)
# curl_cffi supports these Chrome/Firefox/Edge TLS profiles.
# Rotating prevents JA3/JA4 fingerprint clustering — same impersonation
# on every request is still a detectable pattern.
# ---------------------------------------------------------------------------
TLS_PROFILES: list[str] = [
    "chrome110",
    "chrome116",
    "chrome120",
    "chrome124",
    "firefox120",
    "edge101",
]


def get_random_tls_profile() -> str:
    """Returns a random curl_cffi impersonation profile string."""
    return random.choice(TLS_PROFILES)


# ---------------------------------------------------------------------------
# Dynamic stealth init script (5.2)
# Injects per-request WebGL/canvas/platform values from the fingerprint pool.
# ---------------------------------------------------------------------------

def build_stealth_init_script(fingerprint: dict) -> str:
    """
    Returns a JavaScript IIFE string with fingerprint values baked in.
    Covers: webdriver flag, chrome runtime, permissions API, plugins,
    languages, navigator.platform, WebGL vendor/renderer, canvas noise,
    screen.colorDepth.

    WHY dynamic (not static)? Static init scripts produce the same
    WebGL renderer string on every page load. Anti-bot ML models learn
    that this renderer → bot. Rotating from a pool of real hardware
    fingerprints breaks that signal.
    """
    hw: dict = fingerprint.get("hardware", {})
    webgl_vendor = hw.get("webgl_vendor", "Google Inc. (NVIDIA)").replace("'", "\\'")
    webgl_renderer = hw.get("webgl_renderer", "ANGLE (NVIDIA)").replace("'", "\\'")
    platform = hw.get("platform", "Win32").replace("'", "\\'")
    screen_depth = int(hw.get("screen_depth", 24))
    # Small random canvas noise value — different per request
    canvas_noise = random.randint(1, 15)

    return f"""
() => {{
    // 1. Hide webdriver flag
    Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});

    // 2. Restore chrome runtime (absent in headless Chrome)
    window.chrome = {{ runtime: {{}}, loadTimes: () => {{}}, csi: () => {{}} }};

    // 3. Fix permissions API — returns 'denied' for notifications in headless
    const origQuery = window.navigator.permissions.query.bind(navigator.permissions);
    window.navigator.permissions.query = (p) =>
        p.name === 'notifications'
            ? Promise.resolve({{ state: Notification.permission }})
            : origQuery(p);

    // 4. Realistic plugin list
    Object.defineProperty(navigator, 'plugins', {{ get: () => [1, 2, 3, 4, 5] }});

    // 5. Language array
    Object.defineProperty(navigator, 'languages', {{ get: () => ['en-US', 'en'] }});

    // 6. Platform spoofing (Win32 / MacIntel matches the selected fingerprint)
    Object.defineProperty(navigator, 'platform', {{ get: () => '{platform}' }});

    // 7. WebGL vendor / renderer spoofing
    const _getParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(p) {{
        if (p === 37445) return '{webgl_vendor}';   // UNMASKED_VENDOR_WEBGL
        if (p === 37446) return '{webgl_renderer}'; // UNMASKED_RENDERER_WEBGL
        return _getParam.call(this, p);
    }};
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const _getParam2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(p) {{
            if (p === 37445) return '{webgl_vendor}';
            if (p === 37446) return '{webgl_renderer}';
            return _getParam2.call(this, p);
        }};
    }}

    // 8. Canvas fingerprint noise — tiny pixel delta breaks hash-based detection
    const _toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {{
        const ctx = this.getContext('2d');
        if (ctx && this.width > 0 && this.height > 0) {{
            const img = ctx.getImageData(0, 0, 1, 1);
            img.data[0] = (img.data[0] + {canvas_noise}) & 0xFF;
            ctx.putImageData(img, 0, 0);
        }}
        return _toDataURL.apply(this, [type, ...args]);
    }};

    // 9. Screen color depth
    Object.defineProperty(screen, 'colorDepth', {{ get: () => {screen_depth} }});
    Object.defineProperty(screen, 'pixelDepth', {{ get: () => {screen_depth} }});
}}
"""


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


# Backward-compatible alias — new code should call build_stealth_init_script(fingerprint)
STEALTH_INIT_SCRIPT: str = build_stealth_init_script(get_random_fingerprint())
