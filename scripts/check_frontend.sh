#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "[frontend] checking project structure"
test -d frontend

if [ -f frontend/package.json ]; then
  cd frontend
  if [ ! -d node_modules ]; then
    echo "[frontend] node_modules missing; run npm install"
    echo "[frontend] skipping typecheck/build until dependencies are installed"
    exit 0
  fi
  if npm run | grep -q "typecheck"; then
    npm run typecheck
  fi
  if npm run | grep -q "build"; then
    npm run build
  fi
else
  echo "[frontend] package.json not present yet; scaffold pending"
fi

echo "[frontend] OK"
