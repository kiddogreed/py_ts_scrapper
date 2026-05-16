# services/scraper-api/core/session_pool.py
"""
Persistent browser session / cookie management.

WHY: Many sites track login state, consent banners, and "seen before" cookies.
Starting cold each request looks robotic. A session pool maintains cookies
and local storage state across requests per domain — like a real browser
that hasn't been cleared. Sessions are rotated before they expire or after
a configurable number of uses to avoid over-association.

Phase 5 addition (5.7):
  Sessions are now persisted to the Postgres `sessions` table
  (shared/db/schema.sql) via asyncpg. On startup, existing sessions are
  loaded from DB so they survive service restarts. In-memory cache is still
  used for hot path; Postgres is the source of truth.

  Set DATABASE_URL in .env to enable persistence. If DATABASE_URL is absent
  or the connection fails, the pool degrades gracefully to in-memory only.
"""
import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
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
    Session pool with in-memory hot cache + optional Postgres persistence.

    On startup call await pool.load_from_db() to restore previous sessions.
    Writes are fire-and-forget (non-blocking) — DB failures never crash a scrape.
    """

    def __init__(self, db_pool: Optional[Any] = None) -> None:
        self._sessions: dict[str, list[Session]] = {}
        self._lock = asyncio.Lock()
        self._db_url: Optional[str] = os.getenv("DATABASE_URL", "").strip() or None
        # Prefer a shared asyncpg.Pool (injected at startup) for efficiency.
        # Falls back to creating a direct connection when pool is absent.
        self._pool: Optional[Any] = db_pool

    # ------------------------------------------------------------------
    # Postgres helpers
    # ------------------------------------------------------------------

    async def load_from_db(self) -> int:
        """
        Load valid (non-expired) sessions from the Postgres `sessions` table
        into the in-memory cache. Call once at application startup.

        Returns the number of sessions loaded, or 0 if DB is unavailable.
        """
        if not self._pool and not self._db_url:
            return 0
        try:
            import asyncpg  # optional dep — only used when DATABASE_URL is set

            async def _fetch(conn: Any) -> list:
                return await conn.fetch(
                    """
                    SELECT id, domain, cookies, user_agent, created_at
                    FROM sessions
                    WHERE expires_at > NOW()
                    ORDER BY created_at DESC
                    LIMIT 500
                    """
                )

            if self._pool:
                async with self._pool.acquire() as conn:
                    rows = await _fetch(conn)
            else:
                conn = await asyncpg.connect(self._db_url)
                try:
                    rows = await _fetch(conn)
                finally:
                    await conn.close()

            loaded = 0
            for row in rows:
                session = Session(
                    id=str(row["id"]),
                    domain=row["domain"],
                    cookies=json.loads(row["cookies"]),
                    user_agent=row["user_agent"] or "",
                    created_at=row["created_at"].replace(tzinfo=timezone.utc)
                    if row["created_at"].tzinfo is None
                    else row["created_at"],
                )
                if session.is_valid:
                    if session.domain not in self._sessions:
                        self._sessions[session.domain] = []
                    self._sessions[session.domain].append(session)
                    loaded += 1
            logger.info("Loaded %d sessions from Postgres", loaded)
            return loaded
        except Exception as exc:
            logger.warning("Session DB load failed (in-memory only): %s", exc)
            return 0

    async def _persist_session(self, session: Session) -> None:
        """Write a single session to Postgres. Fire-and-forget (exceptions are swallowed)."""
        if not self._pool and not self._db_url:
            return
        try:
            import asyncpg
            expires_at = session.created_at + timedelta(minutes=_SESSION_TTL_MINUTES)
            sql = """
                    INSERT INTO sessions (id, domain, cookies, user_agent, created_at, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE
                        SET cookies = EXCLUDED.cookies,
                            expires_at = EXCLUDED.expires_at
                    """
            args = (
                session.id,
                session.domain,
                json.dumps(session.cookies),
                session.user_agent,
                session.created_at,
                expires_at,
            )
            if self._pool:
                async with self._pool.acquire() as conn:
                    await conn.execute(sql, *args)
            else:
                conn = await asyncpg.connect(self._db_url)
                try:
                    await conn.execute(sql, *args)
                finally:
                    await conn.close()
        except Exception as exc:
            logger.debug("Session persist failed (non-fatal): %s", exc)

    async def _delete_from_db(self, domain: str) -> None:
        """Remove all sessions for *domain* from Postgres when invalidated."""
        if not self._pool and not self._db_url:
            return
        try:
            import asyncpg
            sql = "DELETE FROM sessions WHERE domain = $1"
            if self._pool:
                async with self._pool.acquire() as conn:
                    await conn.execute(sql, domain)
            else:
                conn = await asyncpg.connect(self._db_url)
                try:
                    await conn.execute(sql, domain)
                finally:
                    await conn.close()
        except Exception as exc:
            logger.debug("Session delete failed (non-fatal): %s", exc)

    # ------------------------------------------------------------------
    # Public interface (unchanged API from Phase 4)
    # ------------------------------------------------------------------

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

        # Persist to DB asynchronously — don't await so it doesn't slow the scrape
        asyncio.create_task(self._persist_session(session))
        return session

    async def invalidate_domain(self, domain: str) -> None:
        """Wipe all sessions for a domain (e.g. after a fingerprint ban)."""
        async with self._lock:
            count = len(self._sessions.pop(domain, []))
            logger.warning("Invalidated %d session(s) for %s", count, domain)
        asyncio.create_task(self._delete_from_db(domain))

    @property
    def stats(self) -> dict:
        return {
            domain: len(sessions)
            for domain, sessions in self._sessions.items()
        }
