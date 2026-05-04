# services/scraper-api/core/session_pool.py
"""
Persistent browser session / cookie management.

WHY: Many sites track login state, consent banners, and "seen before" cookies.
Starting cold each request looks robotic. A session pool maintains cookies
and local storage state across requests per domain — like a real browser
that hasn't been cleared. Sessions are rotated before they expire or after
a configurable number of uses to avoid over-association.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

_SESSION_TTL_MINUTES = 30
_SESSION_MAX_USES = 50


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid4()))
    domain: str = ""
    cookies: list[dict] = field(default_factory=list)
    user_agent: str = ""
    fingerprint: dict = field(default_factory=dict)
    uses: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        age = datetime.now(timezone.utc) - self.created_at
        return age > timedelta(minutes=_SESSION_TTL_MINUTES)

    @property
    def is_exhausted(self) -> bool:
        return self.uses >= _SESSION_MAX_USES

    @property
    def is_valid(self) -> bool:
        return not self.is_expired and not self.is_exhausted


class SessionPool:
    """
    In-memory session pool keyed by domain.

    In production this should be backed by the Postgres `sessions` table
    (see shared/db/schema.sql). For now sessions live in memory and survive
    as long as the FastAPI process is running.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, list[Session]] = {}
        self._lock = asyncio.Lock()

    async def get_session(self, domain: str) -> Optional[Session]:
        """Return a valid existing session for the domain, or None."""
        async with self._lock:
            sessions = self._sessions.get(domain, [])
            # Evict stale sessions first
            sessions = [s for s in sessions if s.is_valid]
            self._sessions[domain] = sessions

            if sessions:
                session = sessions[0]
                session.uses += 1
                logger.debug(
                    "Reusing session %s for %s (use %d/%d)",
                    session.id[:8],
                    domain,
                    session.uses,
                    _SESSION_MAX_USES,
                )
                return session
            return None

    async def store_session(
        self,
        domain: str,
        cookies: list[dict],
        user_agent: str,
        fingerprint: dict,
    ) -> Session:
        """Persist a new session after a successful scrape."""
        session = Session(
            domain=domain,
            cookies=cookies,
            user_agent=user_agent,
            fingerprint=fingerprint,
            uses=1,
        )
        async with self._lock:
            if domain not in self._sessions:
                self._sessions[domain] = []
            self._sessions[domain].append(session)
            logger.info("Stored new session %s for %s", session.id[:8], domain)
        return session

    async def invalidate_domain(self, domain: str) -> None:
        """Wipe all sessions for a domain (e.g. after a fingerprint ban)."""
        async with self._lock:
            count = len(self._sessions.pop(domain, []))
            logger.warning("Invalidated %d session(s) for %s", count, domain)

    @property
    def stats(self) -> dict:
        return {
            domain: len(sessions)
            for domain, sessions in self._sessions.items()
        }
