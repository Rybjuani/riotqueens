#!/usr/bin/env bash
set -e

echo "Deploying RiotQueens..."

if [ ! -f .env ]; then
  echo "Error: .env file missing. Please copy .env.example to .env and configure secrets."
  exit 1
fi

docker compose up -d --build

echo "Waiting for postgres to become healthy..."
while ! docker compose ps | grep postgres | grep -q "healthy"; do
  sleep 2
done

echo "Applying migrations..."
cat ops/migrations/*.sql | docker compose exec -T postgres psql -U riotqueens -d riotqueens

echo "Deployment complete."
