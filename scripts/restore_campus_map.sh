#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}
OSM_PAYLOAD="data/external/bupt-shahe/osm/osmnx_campus_payload.json"
REFERENCE_TOPOLOGY="data/reference/bupt-shahe/topology/scene_bupt_campus.geojson"

if [ ! -f "$REFERENCE_TOPOLOGY" ]; then
  echo "[campus-map] missing reference topology: $REFERENCE_TOPOLOGY"
  exit 1
fi

if [ ! -f "$OSM_PAYLOAD" ]; then
  echo "[campus-map] missing offline OSM payload: $OSM_PAYLOAD"
  exit 1
fi

echo "[campus-map] restoring BUPT Shahe reference topology"
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_reference_campus.py \
  --scene-key bupt_shahe \
  --replace-campus-layers

echo "[campus-map] restoring offline OSM building/facility layers"
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_osm_campus.py \
  --source osmnx \
  --scene-key bupt_shahe \
  --features-only \
  --load-payload "$OSM_PAYLOAD"

echo "[campus-map] cleaning BUPT navigation data"
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/clean_navigation_data.py --scene-key bupt_shahe

PYTHONPATH=backend ${PYTHON_CMD} - <<'PY'
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import create_app_engine
from app.services.map_data_service import get_map_stats_from_db

engine = create_app_engine(settings.api_database_url)
with Session(engine) as session:
    stats = get_map_stats_from_db(session)

print(f"[campus-map] visible map stats: {stats}")

if stats["roads"] <= 0:
    raise SystemExit("[campus-map] restore failed: visible roads are empty")
if stats["buildings"] <= 0:
    raise SystemExit("[campus-map] restore failed: visible buildings are empty")
if stats["facilities"] <= 0:
    raise SystemExit("[campus-map] restore failed: visible facilities are empty")
PY
