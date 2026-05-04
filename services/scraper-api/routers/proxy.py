# services/scraper-api/routers/proxy.py
"""
GET  /proxy/rotate  — Return the next healthy proxy from the pool
GET  /proxy/status  — Pool health summary
POST /proxy/validate — Validate a specific proxy
DELETE /proxy/{host}/{port} — Mark a proxy dead manually

WHY expose proxy management as endpoints?
  n8n's ProxyRotatorNode calls GET /proxy/rotate before each scrape job.
  The Next.js dashboard polls GET /proxy/status to show pool health.
  This keeps proxy state centralized in the FastAPI process rather than
  duplicated across callers.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.proxy_manager import Proxy, ProxyManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proxy", tags=["proxy"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ProxyOut(BaseModel):
    host: str
    port: int
    url: str
    failures: int


class PoolStatusOut(BaseModel):
    total: int
    healthy: int
    dead: int


# ---------------------------------------------------------------------------
# Dependency: get proxy manager from app state
# ---------------------------------------------------------------------------

def get_proxy_manager(request: Request) -> ProxyManager:
    return request.app.state.proxy_manager


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/rotate", response_model=ProxyOut)
async def rotate_proxy(
    manager: ProxyManager = Depends(get_proxy_manager),
) -> ProxyOut:
    """Returns the next healthy proxy. Used by n8n nodes before each request."""
    proxy = await manager.get_proxy()
    if proxy is None:
        raise HTTPException(status_code=503, detail="No healthy proxies available")
    return ProxyOut(host=proxy.host, port=proxy.port, url=proxy.url, failures=proxy.failures)


@router.get("/status", response_model=PoolStatusOut)
async def proxy_status(
    manager: ProxyManager = Depends(get_proxy_manager),
) -> PoolStatusOut:
    """Pool health summary for the dashboard."""
    status = manager.pool_status
    return PoolStatusOut(**status)


@router.post("/validate/{host}/{port}")
async def validate_proxy(
    host: str,
    port: int,
    manager: ProxyManager = Depends(get_proxy_manager),
) -> dict:
    """Validate a specific proxy against the external IP check endpoint."""
    proxy = Proxy(host=host, port=port)
    is_valid = await manager.validate_proxy(proxy)
    return {"host": host, "port": port, "valid": is_valid}


@router.delete("/{host}/{port}")
async def retire_proxy(
    host: str,
    port: int,
    manager: ProxyManager = Depends(get_proxy_manager),
) -> dict:
    """Manually mark a proxy as dead (max_failures exceeded)."""
    for proxy in manager._pool:
        if proxy.host == host and proxy.port == port:
            proxy.failures = proxy.max_failures
            logger.warning("Manually retired proxy %s:%d", host, port)
            return {"retired": True, "host": host, "port": port}
    raise HTTPException(status_code=404, detail="Proxy not found in pool")
