#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -z "${VITE_AMAP_KEY:-}" ]; then
  echo "[map-e2e] SKIP: VITE_AMAP_KEY is not set"
  exit 0
fi

if [ ! -x frontend/node_modules/.bin/playwright ]; then
  echo "[map-e2e] SKIP: frontend/node_modules/.bin/playwright is not installed"
  echo "[map-e2e] install @playwright/test locally if browser screenshot proof is needed"
  exit 0
fi

if ! curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null; then
  echo "[map-e2e] SKIP: backend is not reachable at http://127.0.0.1:8000"
  exit 0
fi

cd frontend
VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8000}" \
  ./node_modules/.bin/playwright test tests/amap-smoke.spec.ts
