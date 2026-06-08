#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

if [ -f backend/scripts/reset_dev_db.py ]; then
  PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/reset_dev_db.py
elif [ -f backend/app/seed/reset_dev_db.py ]; then
  PYTHONPATH=backend ${PYTHON_CMD} backend/app/seed/reset_dev_db.py
else
  echo "[db] no reset script yet; scaffold pending"
  echo "[db] when Docker is introduced, this script should drop/recreate dev schema and rerun seed_all"
  exit 0
fi

bash scripts/restore_campus_map.sh

if [ -f data/external/summer-palace/osm/osmnx_summer_palace_payload.json ]; then
  bash scripts/restore_summer_palace_map.sh
else
  echo "[db] skipping Summer Palace restore; offline payload not found"
fi
