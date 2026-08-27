#!/usr/bin/env bash
# RiotQueens deploy — compose up + idempotent SQL migrations.
# Prefer shared runtime.env (mode 600) over a committed .env.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Deploying RiotQueens from $ROOT ..."

if [[ -f runtime.env && ! -f .env ]]; then
  ln -sfn runtime.env .env
  echo "Linked runtime.env -> .env"
fi

if [[ ! -f .env ]]; then
  echo "Error: missing .env (or runtime.env). Copy shared/runtime.env or .env.example."
  exit 1
fi

# Never print secret values. Resolve symlink target for mode check.
ENV_TARGET=".env"
if [[ -L .env ]]; then
  ENV_TARGET="$(readlink -f .env || readlink .env)"
fi
ENV_MODE="$(stat -c '%a' "$ENV_TARGET" 2>/dev/null || stat -f '%OLp' "$ENV_TARGET")"
if [[ "$ENV_MODE" != "600" && "$ENV_MODE" != "400" ]]; then
  echo "Warning: env file mode is $ENV_MODE (prefer 600 on $ENV_TARGET)."
fi

DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  if sudo -n docker info >/dev/null 2>&1; then
    DOCKER=(sudo docker)
  else
    echo "Error: cannot talk to Docker daemon (try: sudo usermod -aG docker \$USER)."
    exit 1
  fi
fi

COMPOSE=("${DOCKER[@]}" compose)

echo "Building and starting stack..."
"${COMPOSE[@]}" up -d --build

echo "Waiting for postgres healthy (timeout 180s)..."
deadline=$((SECONDS + 180))
while true; do
  status="$("${COMPOSE[@]}" ps postgres --format '{{.Status}}' 2>/dev/null || true)"
  if echo "$status" | grep -qi healthy; then
    echo "postgres: $status"
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "Error: postgres not healthy within 180s (status=$status)"
    "${COMPOSE[@]}" ps
    exit 1
  fi
  sleep 2
done

echo "Waiting for api healthy (timeout 180s)..."
deadline=$((SECONDS + 180))
while true; do
  status="$("${COMPOSE[@]}" ps api --format '{{.Status}}' 2>/dev/null || true)"
  if echo "$status" | grep -qi healthy; then
    echo "api: $status"
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "Error: api not healthy within 180s (status=$status)"
    "${COMPOSE[@]}" ps
    exit 1
  fi
  sleep 2
done

PG_USER="$(grep -E '^POSTGRES_USER=' .env | head -1 | cut -d= -f2-)"
PG_DB="$(grep -E '^POSTGRES_DB=' .env | head -1 | cut -d= -f2-)"
PG_USER="${PG_USER:-riotqueens}"
PG_DB="${PG_DB:-riotqueens}"

echo "Applying migrations (ON_ERROR_STOP)..."
# shellcheck disable=SC2016
cat ops/migrations/*.sql | "${COMPOSE[@]}" exec -T postgres \
  psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d "$PG_DB"

echo "Deployment complete."
"${COMPOSE[@]}" ps
