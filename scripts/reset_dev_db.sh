#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ -f backend/scripts/reset_dev_db.py ]; then
  python backend/scripts/reset_dev_db.py
elif [ -f backend/app/seed/reset_dev_db.py ]; then
  python backend/app/seed/reset_dev_db.py
else
  echo "[db] no reset script yet; scaffold pending"
  echo "[db] when Docker is introduced, this script should drop/recreate dev schema and rerun seed_all"
fi

