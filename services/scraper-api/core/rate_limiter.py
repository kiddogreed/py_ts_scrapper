# services/scraper-api/core/rate_limiter.py
"""
Per-domain token bucket rate limiter.

WHY: Sending too many requests per minute to a single domain is the most
common trigger for IP bans. A token bucket enforces a configurable cap per
domain. Tokens refill at a steady rate; each request consumes one token.
If the bucket is empty, the caller awaits until a token is available —
the scraper self-throttles instead of crashing with a 429.

Implementation notes:
  - In-process (asyncio) state — single FastAPI worker only.
    For multi-worker deployments, move bucket state to Redis.
  - Configurable default via RATE_LIMIT_RPM env var (default: 10 req/min).
  - Per-domain override via set_domain_rate() — useful after receiving a 429
    to back off a specific site without affecting the rest of the pool.
  - Token bucket allows bursts (capacity > 1 token) to handle page-load
    sequences (HTML + XHR) without artificial throttling.

Usage:
    limiter = RateLimiter(default_rpm=10, burst=5)
    await limiter.acquire("books.toscrape.com")   # waits if over limit
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_RPM = 10.0   # requests per minute per domain
_DEFAULT_BURST = 5    # max tokens that can accumulate in one bucket


# ---------------------------------------------------------------------------
# Internal bucket
# ---------------------------------------------------------------------------

@dataclass
class _Bucket:
    rate_per_sec: float          # tokens added per second
    capacity: int                # max storable tokens
    tokens: float                # current token count
    last_refill: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def _refill(self) -> None:
        """Add tokens proportional to elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.rate_per_sec)
        self.last_refill = now


# ---------------------------------------------------------------------------
# Public rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """
    Per-domain token bucket rate limiter.

    One bucket is created per domain on first use and lives for the
    lifetime of the FastAPI process.
    """

    def __init__(
        self,
        default_rpm: Optional[float] = None,
        burst: Optional[int] = None,
    ) -> None:
        env_rpm = float(os.getenv("RATE_LIMIT_RPM", str(_DEFAULT_RPM)))
        self._default_rate_per_sec = (default_rpm or env_rpm) / 60.0
        self._burst = burst or _DEFAULT_BURST
        self._buckets: dict[str, _Bucket] = {}
        self._global_lock = asyncio.Lock()

    async def _get_bucket(self, domain: str) -> _Bucket:
        async with self._global_lock:
            if domain not in self._buckets:
                self._buckets[domain] = _Bucket(
                    rate_per_sec=self._default_rate_per_sec,
                    capacity=self._burst,
                    tokens=float(self._burst),  # start full — first burst is free
                )
            return self._buckets[domain]

    async def acquire(self, domain: str) -> float:
        """
        Consume one token for *domain*. Suspends the caller if no tokens
        are currently available.

        Returns:
            Number of seconds waited (0.0 if token was immediately available).
        """
        bucket = await self._get_bucket(domain)
        waited = 0.0

        async with bucket.lock:
            bucket._refill()
            if bucket.tokens < 1.0:
                # Time until next token is available
                wait_secs = (1.0 - bucket.tokens) / bucket.rate_per_sec
                logger.debug(
                    "Rate limit hit: sleeping %.2fs for domain=%s", wait_secs, domain
                )
                await asyncio.sleep(wait_secs)
                bucket._refill()
                waited = wait_secs

            bucket.tokens -= 1.0

        return waited

    def set_domain_rate(
        self,
        domain: str,
        rpm: float,
        burst: Optional[int] = None,
    ) -> None:
        """
        Override the rate for a specific domain at runtime.

        Call this after receiving a 429 from *domain* to back off
        without affecting other domains in the pool.
        """
        if domain in self._buckets:
            self._buckets[domain].rate_per_sec = rpm / 60.0
            if burst is not None:
                self._buckets[domain].capacity = burst
            logger.info(
                "Rate override applied: domain=%s rpm=%.1f burst=%s",
                domain,
                rpm,
                burst,
            )
        # Bucket doesn't exist yet — will be created at first acquire() with default

    def throttle_domain(self, domain: str) -> None:
        """
        Halve the rate for *domain* — convenience wrapper for 429 handling.
        """
        if domain in self._buckets:
            current_rpm = self._buckets[domain].rate_per_sec * 60.0
            new_rpm = max(1.0, current_rpm / 2.0)
            self.set_domain_rate(domain, new_rpm)
            logger.warning(
                "Domain %s throttled: %.1f → %.1f rpm", domain, current_rpm, new_rpm
            )

    @property
    def stats(self) -> dict:
        """Snapshot of current token counts per domain (for /health endpoint)."""
        return {
            domain: {
                "tokens": round(bucket.tokens, 2),
                "capacity": bucket.capacity,
                "rpm": round(bucket.rate_per_sec * 60.0, 1),
            }
            for domain, bucket in self._buckets.items()
        }
