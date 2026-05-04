-- ============================================================
-- shared/db/schema.sql
-- Auto-applied by Docker on first Postgres startup
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---- Jobs ----
CREATE TABLE IF NOT EXISTS jobs (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    url         TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'running', 'done', 'failed', 'dead')),
    pattern     TEXT,                          -- 'microservice' | 'polyglot' | 'n8n'
    retries     INT         NOT NULL DEFAULT 0,
    max_retries INT         NOT NULL DEFAULT 3,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata    JSONB       NOT NULL DEFAULT '{}'
);

-- ---- Results ----
CREATE TABLE IF NOT EXISTS results (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID        REFERENCES jobs(id) ON DELETE CASCADE,
    url         TEXT        NOT NULL,
    data        JSONB       NOT NULL,
    scraped_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---- Proxy Pool ----
CREATE TABLE IF NOT EXISTS proxies (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    host        TEXT        NOT NULL,
    port        INT         NOT NULL,
    username    TEXT,
    password    TEXT,
    failures    INT         NOT NULL DEFAULT 0,
    last_used   TIMESTAMPTZ,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    UNIQUE(host, port)
);

-- ---- Session / Cookie Store ----
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain      TEXT        NOT NULL,
    cookies     JSONB       NOT NULL,
    user_agent  TEXT,
    fingerprint JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

-- ---- Dead Letter Queue (failed jobs) ----
CREATE TABLE IF NOT EXISTS dead_letter (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID        REFERENCES jobs(id) ON DELETE SET NULL,
    url         TEXT        NOT NULL,
    error       TEXT,
    payload     JSONB       NOT NULL DEFAULT '{}',
    failed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---- Indexes ----
CREATE INDEX IF NOT EXISTS jobs_status_idx     ON jobs(status);
CREATE INDEX IF NOT EXISTS jobs_url_idx        ON jobs(url);
CREATE INDEX IF NOT EXISTS jobs_created_idx    ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS results_job_idx     ON results(job_id);
CREATE INDEX IF NOT EXISTS results_url_idx     ON results(url);
CREATE INDEX IF NOT EXISTS proxies_active_idx  ON proxies(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS sessions_domain_idx ON sessions(domain);

-- ---- Auto-update updated_at trigger ----
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS jobs_updated_at ON jobs;
CREATE TRIGGER jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
