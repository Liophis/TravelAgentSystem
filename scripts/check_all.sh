#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

bash scripts/check_merge_markers.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh

echo "[all] OK"
