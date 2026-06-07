#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -f backend/scripts/seed_all.py ]; then
  python backend/scripts/seed_all.py
elif [ -f backend/app/seed/seed_all.py ]; then
  python backend/app/seed/seed_all.py
else
  echo "[seed] no backend seed script yet; scaffold pending"
fi

