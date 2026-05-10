-- orchestrator/init/02_n8n_db.sql
-- Creates the n8n database alongside the scraper database.
-- Runs automatically via Docker entrypoint on first Postgres init.

SELECT 'CREATE DATABASE n8n_db'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'n8n_db'
)\gexec
