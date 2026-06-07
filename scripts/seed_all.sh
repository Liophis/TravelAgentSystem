#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

if [ -f backend/scripts/seed_all.py ]; then
  PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/seed_all.py
elif [ -f backend/app/seed/seed_all.py ]; then
  PYTHONPATH=backend ${PYTHON_CMD} backend/app/seed/seed_all.py
else
  echo "[seed] no backend seed script yet; scaffold pending"
fi
