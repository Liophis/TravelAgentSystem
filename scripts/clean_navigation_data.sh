#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}
SCENE_KEY=${1:-all}

PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/clean_navigation_data.py --scene-key "$SCENE_KEY"
