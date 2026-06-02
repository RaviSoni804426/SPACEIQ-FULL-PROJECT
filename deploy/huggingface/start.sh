#!/usr/bin/env bash
set -euo pipefail

export APP_ENV="${APP_ENV:-production}"
export DEBUG="${DEBUG:-false}"
export DATABASE_URL="${DATABASE_URL:-sqlite:////data/spaceiq.db}"
export FRONTEND_URL="${FRONTEND_URL:-http://localhost:7860}"
export ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost:7860}"
export PORT="${PORT:-7860}"
export SEED_DEMO_DATA="${SEED_DEMO_DATA:-true}"

db_was_missing=false
if [[ "$DATABASE_URL" == sqlite:* && ! -f /data/spaceiq.db ]]; then
    db_was_missing=true
fi

cd /app/backend
alembic upgrade head

if [[ "$SEED_DEMO_DATA" == "true" ]]; then
    python -m app.scripts.seed_demo_users
    python -m app.scripts.seed_demo_inventory

    if [[ "$db_was_missing" == "true" || "${FORCE_SEED_ANALYTICS:-false}" == "true" ]]; then
        python -m app.scripts.seed_demo_analytics --days "${SEED_ANALYTICS_DAYS:-210}"
    fi
fi

uvicorn app.main:app --host 127.0.0.1 --port 8000 &
backend_pid=$!

cd /app/frontend
npm run start -- --hostname 127.0.0.1 --port 3000 &
frontend_pid=$!

cleanup() {
    kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

nginx -g "daemon off;"
