#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}
RAW_PAYLOAD="data/external/summer-palace/amap_gcj02/food_pois_raw.json"
SUMMER_PALACE_DESTINATION_ID=${SUMMER_PALACE_DESTINATION_ID:-103}
export SUMMER_PALACE_DESTINATION_ID

if [ ! -f "$RAW_PAYLOAD" ]; then
  echo "[summer-palace-foods] missing AMap food raw payload: $RAW_PAYLOAD"
  exit 1
fi

echo "[summer-palace-foods] restoring Summer Palace real AMap restaurant POIs"
PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_amap_foods.py \
  --destination-id "$SUMMER_PALACE_DESTINATION_ID" \
  --radius 3000 \
  --reset-destination \
  --load-raw "$RAW_PAYLOAD"

PYTHONPATH=backend ${PYTHON_CMD} - <<'PY'
import os

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import create_app_engine
from app.models import Food, Restaurant

engine = create_app_engine(settings.api_database_url)
destination_id = int(os.environ["SUMMER_PALACE_DESTINATION_ID"])
with Session(engine) as session:
    restaurant_count = session.scalar(
        select(func.count(Restaurant.id))
        .where(Restaurant.destination_id == destination_id, Restaurant.source == "amap")
    )
    food_count = session.scalar(
        select(func.count(Food.id))
        .join(Restaurant)
        .where(Restaurant.destination_id == destination_id, Restaurant.source == "amap")
    )

print(f"[summer-palace-foods] restaurants={restaurant_count} foods={food_count}")

if not restaurant_count or restaurant_count < 50:
    raise SystemExit("[summer-palace-foods] restore failed: real restaurant count is below 50")
if not food_count or food_count < 50:
    raise SystemExit("[summer-palace-foods] restore failed: real food recommendation count is below 50")
PY
