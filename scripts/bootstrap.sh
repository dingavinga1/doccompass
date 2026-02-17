#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true
(
  cd backend
  uv sync
)

echo "Bootstrap complete. Start services with: docker compose up --build"
