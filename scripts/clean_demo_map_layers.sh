#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/clean_demo_map_layers.py "$@"
