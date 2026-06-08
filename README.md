# Smart Tour Guide

大型校园 / 景区智能导览平台 MVP。

当前仓库处于 **Stage 13 campus data density and AMap drift hardening** 阶段：已建立 FastAPI / Vue / AMap / Docker Compose 骨架，加入 SQLAlchemy 核心表模型、确定性 seed/reset 数据，并把地图浏览、路线规划、附近设施、目的地搜索、推荐、OSM 导入、游记社区、美食推荐、AIGC 占位和后台数据看板接入数据库数据。本阶段进一步增密北京邮电大学沙河校区演示地图，并在前端渲染前完成 WGS84 到 GCJ-02 坐标转换，解决高德底图上的覆盖物漂移问题。

## Target Stack

- Frontend: Vue 3 + Vite + TypeScript + Element Plus
- Map UI: 高德地图 JS API + `@amap/amap-jsapi-loader`
- Map data/routing topology: OpenStreetMap + OSMnx / Overpass
- Backend: FastAPI
- Database: PostgreSQL + PostGIS
- Cache: Redis
- Deploy: Docker Compose + Nginx

## Directory

```text
backend/          FastAPI backend
frontend/         Vue frontend
docs/             planning, matrix, acceptance docs
infra/nginx/      reverse proxy config
media/            local uploaded files
scripts/          bash check/seed/reset scripts
tests/fixtures/   deterministic small test fixtures
```

## Environment

```bash
cp .env.example .env.local
```

Do not commit `.env.local`.

Set the AMap Web JS API key in `.env.local`:

```bash
VITE_AMAP_KEY=your_amap_web_js_api_key
```

The frontend uses AMap only for rendering. Backend map import, graph topology, route planning, and nearby-facility distance calculation still use OSMnx/OpenStreetMap data.

Default campus:

```text
北京邮电大学沙河校区
Center: [116.28333, 40.15608]
```

Optional backend conda workflow:

```bash
conda activate travel-agent
pip install -r backend/requirements.txt
BACKEND_PYTHON_CMD="conda run -n travel-agent python" \
BACKEND_PYTEST_CMD="conda run -n travel-agent pytest" \
bash scripts/check_backend.sh
```

## Checks

```bash
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

## Startup

Backend:

```bash
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

When Docker infrastructure is introduced:

```bash
docker compose up --build
```

## Data Helpers

```bash
bash scripts/seed_all.sh
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
```

These scripts default to `DEV_DATABASE_URL=sqlite:///./smart_tour_dev.db` and currently seed 10 users, 200 destinations, 180 map nodes, 641 map edges, 60 buildings, 120 facilities, 10 facility categories, 19 indoor nodes, 20 indoor edges, 12 restaurants, 72 foods, and 20 diaries.

The local backend reads API data from `API_DATABASE_URL`. For the SQLite demo path, run the backend from the repository root so the SQLite relative path matches `scripts/reset_dev_db.sh`:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then check:

```bash
curl http://127.0.0.1:8000/api/v1/map/stats
curl -X POST http://127.0.0.1:8000/api/v1/routes/plan \
  -H 'Content-Type: application/json' \
  -d '{"start_lng":116.28333,"start_lat":40.15608,"end_lng":116.2862,"end_lat":40.1582}'
curl -X POST http://127.0.0.1:8000/api/v1/routes/multi-point \
  -H 'Content-Type: application/json' \
  -d '{"start_lng":116.28333,"start_lat":40.15608,"points":[{"name":"教学楼","lng":116.2842,"lat":40.1567},{"name":"图书馆","lng":116.2862,"lat":40.1582}],"return_to_start":true}'
curl 'http://127.0.0.1:8000/api/v1/facilities/nearby?current_lng=116.28333&current_lat=40.15608&category=water&radius=5000&limit=3'
curl 'http://127.0.0.1:8000/api/v1/destinations?category=campus&q=导览点&limit=5'
curl 'http://127.0.0.1:8000/api/v1/search/places?keyword=厕所&limit=5'
curl 'http://127.0.0.1:8000/api/v1/recommendations?user_id=1&strategy=composite&limit=10'
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -d '{"source":"fixture","reset_existing":true}'
curl 'http://127.0.0.1:8000/api/v1/diaries?limit=5'
curl 'http://127.0.0.1:8000/api/v1/foods/recommend?limit=5'
curl -X POST http://127.0.0.1:8000/api/v1/aigc/diary-draft \
  -H 'Content-Type: application/json' \
  -d '{"topic":"沙河校区路线","keywords":["食堂","图书馆"],"tone":"自然"}'
curl 'http://127.0.0.1:8000/api/v1/admin/stats'
```

OSMnx import CLI:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py --source osmnx
```

If the configured `OSM_DEFAULT_PLACE` is not found by Nominatim, the importer falls back to `OSM_FALLBACK_LAT` / `OSM_FALLBACK_LNG` / `OSM_FALLBACK_DIST`.

## Docs

- `AGENTS.md`: rules for Codex and future agents.
- `docs/feature_matrix.md`: feature/API/page/table/test status.
- `docs/course_requirement_gap_analysis.md`: current gaps against `要求.md`.
- `docs/acceptance_checklist.md`: acceptance requirements.
- `docs/amap_map_plan.md`: AMap frontend rendering plan and OSM backend boundary.
- `docs/stage_1_foundation.md`: project skeleton delivery notes and known gaps.
- `docs/stage_2_data_foundation.md`: data model and seed delivery notes.
- `docs/stage_3_map_data_api.md`: database-backed map API delivery notes.
- `docs/stage_4_route_planning.md`: database-backed Dijkstra route planning notes.
- `docs/stage_5_nearby_facilities.md`: graph-distance nearby facility query notes.
- `docs/stage_6_destinations_search_recommend.md`: destination list, search, and recommendation notes.
- `docs/stage_7_osm_import.md`: OSMnx import pipeline and admin import notes.
- `docs/stage_8_diaries.md`: diary community, search, rating, comments, and compression notes.
- `docs/stage_9_food_aigc_admin.md`: food recommendation, AIGC placeholders, and admin dashboard notes.
- `docs/stage_10_final_docs.md`: final documentation and demo-readiness notes.
- `docs/stage_11_mainline_hardening.md`: smoke, merge-marker, and frontend error-handling hardening notes.
- `docs/stage_12_multi_point_routes.md`: multi-point route planning notes.
- `docs/stage_13_campus_data_density.md`: campus data density and AMap coordinate drift notes.
- `docs/stage_14_route_strategies.md`: congestion and transport-mode route strategy notes.
- `docs/stage_15_indoor_navigation.md`: indoor graph and cross-floor route notes.
- `docs/stage_16_user_preferences.md`: editable interests and recommendation refresh notes.
- `README_DEPLOY.md`: local and Docker deployment commands.
- `tests/fixtures/README.md`: shared test fixture notes.

## Development Flow

1. Pick a row from `docs/feature_matrix.md`.
2. Implement backend API, frontend page, data model, and tests.
3. Update feature status.
4. Run `bash scripts/check_all.sh`.
5. Update acceptance checklist when criteria change.
