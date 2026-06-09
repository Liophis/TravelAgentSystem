#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/import_amap_pois.py \
  --scene-key summer_palace \
  --center-lng 116.2755 \
  --center-lat 39.9996 \
  --radius 2500 \
  --dataset scenic_navigation \
  --max-pages 4 \
  --request-interval 0.35 \
  --keyword 景点 \
  --keyword 出入口 \
  --keyword 售票处 \
  --keyword 游客中心 \
  --keyword 厕所 \
  --keyword 卫生间 \
  --keyword 餐厅 \
  --keyword 商店 \
  --keyword 便利店 \
  --keyword 停车场 \
  --save-raw data/external/summer-palace/amap_gcj02/summer_palace_pois_raw.json \
  --download-only
