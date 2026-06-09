#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}
OSM_PAYLOAD="data/external/summer-palace/osm/osmnx_summer_palace_payload.json"
AMAP_POI_RAW="data/external/summer-palace/amap_gcj02/summer_palace_pois_raw.json"
AMAP_FOOD_RAW="data/external/summer-palace/amap_gcj02/food_pois_raw.json"

if [ ! -f "$OSM_PAYLOAD" ]; then
  echo "[summer-palace-map] missing offline OSM payload: $OSM_PAYLOAD"
  exit 1
fi

echo "[summer-palace-map] restoring Summer Palace OSM graph, buildings, and facilities"
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_osm_campus.py \
  --source osmnx \
  --scene-key summer_palace \
  --load-payload "$OSM_PAYLOAD"

echo "[summer-palace-map] cleaning Summer Palace navigation data"
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/clean_navigation_data.py --scene-key summer_palace

if [ -f "$AMAP_POI_RAW" ]; then
  echo "[summer-palace-map] importing Summer Palace AMap scenic POIs"
  PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_amap_pois.py \
    --scene-key summer_palace \
    --center-lng 116.2755 \
    --center-lat 39.9996 \
    --radius 2500 \
    --dataset scenic_navigation \
    --reset-dataset \
    --load-raw "$AMAP_POI_RAW"

  echo "[summer-palace-map] cleaning merged Summer Palace POIs"
  PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/clean_navigation_data.py --scene-key summer_palace
elif [ -f "$AMAP_FOOD_RAW" ]; then
  echo "[summer-palace-map] importing Summer Palace AMap restaurant POIs as scenic service facilities"
  PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_amap_pois.py \
    --scene-key summer_palace \
    --center-lng 116.2755 \
    --center-lat 39.9996 \
    --radius 3000 \
    --dataset scenic_navigation \
    --reset-dataset \
    --load-raw "$AMAP_FOOD_RAW"

  echo "[summer-palace-map] cleaning merged Summer Palace POIs"
  PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/clean_navigation_data.py --scene-key summer_palace
else
  echo "[summer-palace-map] skipping AMap scenic POI import; raw payload not found: $AMAP_POI_RAW or $AMAP_FOOD_RAW"
fi

PYTHONPATH=backend ${PYTHON_CMD} - <<'PY'
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import create_app_engine
from app.services.map_data_service import get_map_stats_from_db

engine = create_app_engine(settings.api_database_url)
with Session(engine) as session:
    stats = get_map_stats_from_db(session, scene_key="summer_palace")

print(f"[summer-palace-map] visible map stats: {stats}")

if stats["roads"] < 200:
    raise SystemExit("[summer-palace-map] restore failed: roads are below requirement")
if stats["buildings"] < 20:
    raise SystemExit("[summer-palace-map] restore failed: buildings are below requirement")
if stats["facilities"] < 50:
    raise SystemExit("[summer-palace-map] restore failed: facilities are below requirement")
PY
