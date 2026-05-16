#!/usr/bin/env bash
# =============================================================================
# start.sh — Launch the full py_ts_scrapper stack
# Usage: ./start.sh [--no-build]
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$ROOT/services/dashboard"
NO_BUILD=false

for arg in "$@"; do
  [[ "$arg" == "--no-build" ]] && NO_BUILD=true
done

# Colours
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[start]${NC} $*"; }
warn()  { echo -e "${YELLOW}[start]${NC} $*"; }
error() { echo -e "${RED}[start]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# 1. Ensure Docker daemon is running
# ---------------------------------------------------------------------------
if ! docker info &>/dev/null; then
  warn "Docker not running — launching Docker Desktop..."
  # Windows (Git Bash)
  DOCKER_APP="/c/Program Files/Docker/Docker/Docker Desktop.exe"
  if [[ -f "$DOCKER_APP" ]]; then
    start "" "$DOCKER_APP" &>/dev/null || true
  else
    error "Docker Desktop not found at '$DOCKER_APP'. Start Docker manually and re-run."
    exit 1
  fi

  echo -n "    Waiting for Docker daemon"
  for i in $(seq 1 24); do
    sleep 5
    if docker info &>/dev/null; then
      echo -e " ${GREEN}ready${NC}"
      break
    fi
    echo -n "."
    if [[ $i -eq 24 ]]; then
      echo ""
      error "Docker did not become ready within 2 minutes."
      exit 1
    fi
  done
fi

info "Docker daemon is running."

# ---------------------------------------------------------------------------
# 2. Sync dashboard package-lock.json if pino is missing (added in Phase 6)
# ---------------------------------------------------------------------------
LOCKFILE="$DASHBOARD_DIR/package-lock.json"
if ! grep -q '"pino"' "$LOCKFILE" 2>/dev/null; then
  warn "package-lock.json out of sync — running npm install in services/dashboard..."
  (cd "$DASHBOARD_DIR" && npm install --silent)
  info "package-lock.json updated."
fi

# ---------------------------------------------------------------------------
# 3. Start all services
# ---------------------------------------------------------------------------
BUILD_FLAG=""
$NO_BUILD || BUILD_FLAG="--build"

info "Starting all services (this may take a few minutes on first run)..."
docker compose -f "$ROOT/docker-compose.yml" up $BUILD_FLAG -d

# ---------------------------------------------------------------------------
# 4. Wait for health endpoints to respond
# ---------------------------------------------------------------------------
info "Waiting for services to become healthy..."

wait_for() {
  local name="$1" url="$2" retries="${3:-20}" delay="${4:-5}"
  for i in $(seq 1 "$retries"); do
    if curl -sf "$url" &>/dev/null; then
      echo -e "  ${GREEN}✔${NC} $name"
      return 0
    fi
    sleep "$delay"
  done
  echo -e "  ${RED}✘${NC} $name did not respond at $url"
  return 1
}

wait_for "Scraper API" "http://localhost:8000/health"     20 5
wait_for "Dashboard"   "http://localhost:3000/api/health" 24 5

# ---------------------------------------------------------------------------
# 5. Final status
# ---------------------------------------------------------------------------
echo ""
docker compose -f "$ROOT/docker-compose.yml" ps
echo ""
echo -e "${GREEN}All services are up!${NC}"
echo ""
echo -e "  Dashboard   → ${GREEN}http://localhost:3000${NC}"
echo -e "  Scraper API → ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs    → ${GREEN}http://localhost:8000/docs${NC}"

# Read N8N_HOST_PORT from .env if present
N8N_PORT=$(grep -E '^N8N_HOST_PORT=' "$ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || echo "5679")
echo -e "  n8n         → ${GREEN}http://localhost:${N8N_PORT}${NC}"
echo -e "  pgBouncer   → localhost:6432"
echo -e "  Postgres    → localhost:5432"
echo ""
