# n8n Credentials Setup

After starting n8n via `docker compose up -d`, configure the following credentials
in the n8n UI (Settings → Credentials → New):

---

## 1. Scraper Postgres

**Type:** PostgreSQL

| Field    | Value                                  |
|----------|----------------------------------------|
| Host     | `postgres`                             |
| Port     | `5432`                                 |
| Database | `scraper_db` (value of `POSTGRES_DB`)  |
| User     | value of `POSTGRES_USER`               |
| Password | value of `POSTGRES_PASSWORD`           |
| SSL      | disabled (internal Docker network)     |

**Credential name (must match workflows):** `Scraper Postgres`

---

## 2. Scraper API (Custom)

**Type:** Scraper API  *(registered by PythonBridgeNode / ProxyRotatorNode)*

| Field      | Value                                        |
|------------|----------------------------------------------|
| Base URL   | `http://scraper-api:8000`                    |
| API Secret | value of `SCRAPER_API_SECRET` from `.env`    |

**Credential name:** `Scraper API`

---

## 3. Importing Workflows

1. Open n8n UI → **Workflows → Import**
2. Import `orchestrator/workflows/scrape-job.json`
3. Import `orchestrator/workflows/retry-handler.json`
4. Open each workflow → assign the credentials above to the matching nodes
5. **Activate** both workflows (toggle top-right)

### Webhook URL (after activation)

The `scrape-job` workflow will be reachable at:

```
POST http://localhost:5678/webhook/scrape-job
Content-Type: application/json

{
  "url": "https://example.com/product",
  "javascript": true,
  "wait_for": ".price",
  "intercept_pattern": "/api/product"
}
```

---

## 4. Custom Nodes

The custom nodes (`PythonBridgeNode`, `ProxyRotatorNode`) are mounted into the n8n
container via the Docker volume:

```
./orchestrator/custom-nodes → /home/node/.n8n/custom
```

Build them before starting the stack:

```bash
cd orchestrator/custom-nodes/PythonBridgeNode && npm install && npm run build
cd ../ProxyRotatorNode && npm install && npm run build
```

Then restart n8n:

```bash
docker compose restart n8n
```
