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
  if [ ! -x node_modules/.bin/vue-tsc ] || [ ! -x node_modules/.bin/vite ]; then
    echo "[frontend] dependencies incomplete; run npm install"
    echo "[frontend] skipping typecheck/build until required binaries are installed"
    exit 0
  fi
  if node -e "const scripts=require('./package.json').scripts||{}; process.exit(scripts.typecheck ? 0 : 1)"; then
    npm run typecheck
  fi
  if node -e "const scripts=require('./package.json').scripts||{}; process.exit(scripts.build ? 0 : 1)"; then
    npm run build
  fi
else
  echo "[frontend] package.json not present yet; scaffold pending"
fi

echo "[frontend] OK"
