#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if rg -n "^(<<<<<<<|=======|>>>>>>>)" \
  -g '!frontend/node_modules/**' \
  -g '!frontend/dist/**' \
  -g '!backend/cache/**' \
  -g '!*.db' \
  .; then
  echo "[merge-markers] conflict markers found"
  exit 1
fi

echo "[merge-markers] OK"
