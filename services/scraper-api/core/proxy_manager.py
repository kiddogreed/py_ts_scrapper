# services/scraper-api/core/proxy_manager.py
"""
Rotating proxy pool with health tracking.

WHY: A single IP making hundreds of requests triggers rate-limiting and bans.
Rotating through a pool of residential/datacenter proxies distributes the load
across many IPs. We track per-proxy failures so bad proxies are automatically
retired without breaking the whole pool.
"""
import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Validation endpoint — neutral, always returns IP as JSON
_VALIDATION_URL = "https://api.ipify.org?format=json"
_VALIDATION_TIMEOUT = 10.0


@dataclass
class Proxy:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    failures: int = field(default=0, compare=False)
    max_failures: int = field(default=3, compare=False)

    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"

    @property
    def is_healthy(self) -> bool:
        return self.failures < self.max_failures

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"


class ProxyManager:
    """
    Thread-safe rotating proxy pool.

    Usage:
        manager = ProxyManager.from_list([{"host": ..., "port": ...}])
        proxy = await manager.get_proxy()
        # use proxy.url
        await manager.mark_success(proxy)  # or mark_failure(proxy)
    """

    def __init__(self, proxies: list[Proxy]) -> None:
        self._pool: deque[Proxy] = deque(proxies)
        self._lock = asyncio.Lock()

    @classmethod
    def from_list(cls, raw: list[dict]) -> "ProxyManager":
        proxies = [
            Proxy(
                host=p["host"],
                port=int(p["port"]),
                username=p.get("username"),
                password=p.get("password"),
            )
            for p in raw
            if "host" in p and "port" in p and not p.get("comment")
        ]
        return cls(proxies)

    async def get_proxy(self) -> Optional[Proxy]:
        """Returns the next healthy proxy via round-robin, or None if all are dead."""
        async with self._lock:
            for _ in range(len(self._pool)):
                proxy = self._pool[0]
                self._pool.rotate(-1)
                if proxy.is_healthy:
                    return proxy
            logger.error("All proxies in pool are unhealthy")
            return None

    async def mark_failure(self, proxy: Proxy) -> None:
        proxy.failures += 1
        if not proxy.is_healthy:
            logger.warning("Proxy %s retired after %d failures", proxy, proxy.failures)

    async def mark_success(self, proxy: Proxy) -> None:
        # Slowly recover failure count on success (circuit breaker pattern)
        proxy.failures = max(0, proxy.failures - 1)

    async def validate_proxy(self, proxy: Proxy) -> bool:
        """Hits a neutral endpoint through the proxy to confirm it works."""
        try:
            async with httpx.AsyncClient(
                proxy=proxy.url, timeout=_VALIDATION_TIMEOUT
            ) as client:
                r = await client.get(_VALIDATION_URL)
                return r.status_code == 200
        except Exception as exc:
            logger.debug("Proxy %s validation failed: %s", proxy, exc)
            return False

    @property
    def pool_status(self) -> dict:
        total = len(self._pool)
        healthy = sum(1 for p in self._pool if p.is_healthy)
        return {"total": total, "healthy": healthy, "dead": total - healthy}
