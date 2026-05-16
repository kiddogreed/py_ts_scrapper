#!/usr/bin/env bash
# =============================================================================
# stop.sh — Stop and optionally remove the py_ts_scrapper stack
# Usage: ./stop.sh          # stop containers (volumes preserved)
#        ./stop.sh --clean  # stop + remove volumes (full reset)
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEAN=false

for arg in "$@"; do
  [[ "$arg" == "--clean" ]] && CLEAN=true
done

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[stop]${NC} $*"; }
warn() { echo -e "${YELLOW}[stop]${NC} $*"; }

if $CLEAN; then
  warn "Stopping containers and removing volumes (all data will be lost)..."
  docker compose -f "$ROOT/docker-compose.yml" down -v
  info "Stack stopped and volumes removed."
else
  info "Stopping containers (volumes preserved)..."
  docker compose -f "$ROOT/docker-compose.yml" down
  info "Stack stopped. Run ./start.sh to restart."
fi
