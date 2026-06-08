# Smart Tour Guide

景点/学校推荐 + 校园内部导航平台 MVP。

当前仓库处于 **Stage 32 AIGC Agent preparation** 阶段：已建立 FastAPI / Vue / AMap / Docker Compose 骨架，加入 SQLAlchemy 核心表模型、确定性 seed/reset 数据，并把校园地图浏览、北邮沙河校区内部路线规划、室内导航、附近设施、景点/学校目的地搜索、目的地推荐、OSM/高德数据导入、游记社区、美食推荐、AIGC 占位和后台数据看板接入数据库数据。近期阶段补齐了高德坐标漂移修正、用户兴趣编辑、高德 Web Service 真实 POI 导入、设施数据清洗、地点选择路线输入、游记媒体/索引检索/兴趣推荐、用户注册登录/收藏评分/行为日志闭环、按目的地范围过滤的美食推荐、后台内容管理、真实优先地图图层、北邮沙河参考校园拓扑导入、双 POI 数据集、游记管理/交流的讲义要求对齐、管理员/普通用户角色登录与后台权限保护，并开始把 AIGC 升级为可解释的轻量 Agent 工作流。

Scope clarification:

- 推荐模块面向不同景点和学校，按热度、评分、个人兴趣和行为反馈输出 Top 10 目的地。
- 导航模块当前面向北京邮电大学沙河校区内部地图，处理校门、楼宇、设施和室内外路线。
- 校园建筑和设施用于地图、搜索、场所查询和路线输入，默认不作为旅游推荐候选。

## Target Stack

- Frontend: Vue 3 + Vite + TypeScript + Element Plus
- Map UI: 高德地图 JS API + `@amap/amap-jsapi-loader`
- Map data/routing topology: OpenStreetMap + OSMnx / Overpass
- POI enrichment: 高德 Web Service Place Around API
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
data/reference/   committed reference source data for campus navigation imports
data/external/    downloaded OSM/AMap source payloads before cleaning/import
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

Set the AMap Web Service key only when importing real POIs:

```bash
AMAP_WEB_API_KEY=your_amap_web_service_api_key
```

The frontend `VITE_AMAP_KEY` is used only for browser rendering. Backend map layers now prefer real imported data: OSMnx/OpenStreetMap for roads and building polygons, AMap Web Service for dense POIs, and OSM amenities as an additional POI source. The deterministic seed graph remains hidden by default and is retained for offline tests and local Dijkstra fallback.

Manually supplied campus map source files should be placed under:

```text
data/reference/bupt-shahe/raw_wgs84/
data/reference/bupt-shahe/topology/
```

Use `raw_wgs84/` for original WGS84 JSON/GeoJSON layers and `topology/` for the WGS84 road graph. Do not put these files in `backend/cache/`, `frontend/public/`, or the repository root. Future import scripts should validate and import them into the database before APIs use them.

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
bash scripts/check_map_frontend_optional.sh
```

`check_map_frontend_optional.sh` is intentionally guarded: it skips when `VITE_AMAP_KEY`, a running backend, or local Playwright is unavailable. Use it only when browser screenshot proof of the AMap page is needed.

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
bash scripts/clean_demo_map_layers.sh
```

These scripts default to `DEV_DATABASE_URL=sqlite:///./smart_tour_dev.db` and currently seed 11 users, including `user01` as a normal user and `admin01` as an admin, 207 real China attraction/university destinations, 180 map nodes, 641 map edges, 60 buildings, 120 facilities, 10 facility categories, 19 indoor nodes, 20 indoor edges, 12 restaurants, 72 foods, 20 diaries, and sample user feedback rows.

`bash scripts/seed_all.sh` is incremental once a dev DB already exists: it creates missing tables/columns, upgrades old `北邮沙河导览点` destination rows to real attraction/university rows, assigns existing restaurants to nearby destinations, and backfills sample favorites/ratings/behavior logs without deleting real imported AMap facilities.

The deterministic seed is an offline demo fallback, not a claim of real campus POI density. To enrich facilities from real AMap POI data after seeding:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 3 --request-interval 0.5
```

Use `--reset-facilities` when you want AMap POIs to replace seeded facility points while keeping the existing road graph:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 3000 --max-pages 3 --request-interval 0.8 --reset-facilities
```

Two POI datasets are supported:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --dataset nearby_facilities --radius 3000 --max-pages 3 --request-interval 0.8 --reset-facilities
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --dataset campus_navigation --radius 1500 --max-pages 3 --request-interval 0.8 --campus-only --reset-dataset
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --dataset campus_navigation --radius 1500 --campus-only --reset-dataset --load-raw data/external/bupt-shahe/amap_gcj02/campus_navigation_raw.json
```

To capture external source payloads without changing the database:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py --source osmnx --dist 900 --download-only --save-payload data/external/bupt-shahe/osm/osmnx_campus_payload.json
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --dataset campus_navigation --campus-only --download-only --save-raw data/external/bupt-shahe/amap_gcj02/campus_navigation_raw.json
```

To remove old offline square building/facility layers:

```bash
bash scripts/clean_demo_map_layers.sh
```

To merge real OSM road graph, OSM building polygons, and OSM amenities while preserving AMap POIs:

```bash
python backend/scripts/import_osm_campus.py --source osmnx --graph-only --dist 1800
python backend/scripts/import_osm_campus.py --source osmnx --features-only --dist 1800
```

To import the manually supplied BUPT Shahe WGS84 campus topology:

```bash
PYTHONPATH=backend python backend/scripts/import_reference_campus.py --replace-campus-layers
```

This replaces visible OSM road nodes/edges with the reference campus graph, keeps the deterministic seed graph hidden as fallback, preserves existing building polygons and POIs, and imports reference campus facilities.

The public map API hides seed/fallback layers by default. Use `include_demo=true` only for fallback inspection:

```bash
curl 'http://127.0.0.1:8000/api/v1/map/geojson'
curl 'http://127.0.0.1:8000/api/v1/map/geojson?include_demo=true'
```

The local backend reads API data from `API_DATABASE_URL`. For the SQLite demo path, run the backend from the repository root so the SQLite relative path matches `scripts/reset_dev_db.sh`:

```bash
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

For a cleaned real-facility demo, replace the fallback facility seed after reset:

```bash
bash scripts/reset_dev_db.sh
python backend/scripts/import_amap_pois.py --radius 3000 --max-pages 3 --request-interval 0.8 --reset-facilities
bash scripts/smoke_features.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then check:

```bash
curl http://127.0.0.1:8000/api/v1/map/stats
curl -X POST http://127.0.0.1:8000/api/v1/routes/plan \
  -H 'Content-Type: application/json' \
  -d '{"start_lng":116.28333,"start_lat":40.15608,"end_lng":116.2862,"end_lat":40.1582,"route_source":"local_graph"}'
curl -X POST http://127.0.0.1:8000/api/v1/routes/plan \
  -H 'Content-Type: application/json' \
  -d '{"start_place_id":"facility-1","end_place_id":"facility-2","strategy":"shortest_distance","mode":"walk","route_source":"local_graph"}'
curl -X POST http://127.0.0.1:8000/api/v1/routes/multi-point \
  -H 'Content-Type: application/json' \
  -d '{"start_lng":116.28333,"start_lat":40.15608,"points":[{"name":"教学楼","lng":116.2842,"lat":40.1567},{"name":"图书馆","lng":116.2862,"lat":40.1582}],"return_to_start":true}'
curl 'http://127.0.0.1:8000/api/v1/facilities/nearby?current_lng=116.28333&current_lat=40.15608&category=water&radius=5000&limit=3'
curl 'http://127.0.0.1:8000/api/v1/destinations?category=school&q=大学&limit=5'
curl 'http://127.0.0.1:8000/api/v1/search/places?keyword=厕所&scope=campus&limit=5'
curl 'http://127.0.0.1:8000/api/v1/search/places?keyword=大学&scope=destinations&limit=5'
curl 'http://127.0.0.1:8000/api/v1/recommendations?user_id=1&strategy=composite&limit=10'
curl -X POST http://127.0.0.1:8000/api/v1/users/login \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"user01","password":"demo123456"}'
ADMIN_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/users/login \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"admin01","password":"admin123456"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -X POST http://127.0.0.1:8000/api/v1/users/1/favorites \
  -H 'Content-Type: application/json' \
  -d '{"target_type":"destination","target_id":120,"note":"demo favorite"}'
curl -X POST http://127.0.0.1:8000/api/v1/users/1/ratings \
  -H 'Content-Type: application/json' \
  -d '{"target_type":"destination","target_id":120,"rating":5}'
curl -X POST http://127.0.0.1:8000/api/v1/users/1/behavior \
  -H 'Content-Type: application/json' \
  -d '{"target_type":"destination","target_id":120,"action":"view","metadata_text":"demo browse"}'
curl 'http://127.0.0.1:8000/api/v1/recommendations?user_id=1&strategy=behavior&limit=10'
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"source":"fixture","reset_existing":true}'
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"source":"amap_poi","dist":1800,"max_pages":3,"request_interval":0.5,"reset_existing":false}'
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"source":"reference_campus","reset_existing":true}'
curl 'http://127.0.0.1:8000/api/v1/diaries?limit=5'
curl 'http://127.0.0.1:8000/api/v1/foods/recommend?destination_id=1&limit=5'
curl -X POST http://127.0.0.1:8000/api/v1/aigc/diary-draft \
  -H 'Content-Type: application/json' \
  -d '{"topic":"沙河校区路线","keywords":["食堂","图书馆"],"tone":"自然"}'
curl -H "Authorization: Bearer $ADMIN_TOKEN" 'http://127.0.0.1:8000/api/v1/admin/stats'
curl -X PATCH http://127.0.0.1:8000/api/v1/admin/destinations/1 \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name":"后台更新目的地","popularity":999,"tags":["food","study"]}'
curl -H "Authorization: Bearer $ADMIN_TOKEN" 'http://127.0.0.1:8000/api/v1/admin/diaries?limit=5'
```

OSMnx import CLI:

```bash
PYTHONPATH=backend python backend/scripts/import_osm_campus.py --source osmnx
```

If the configured `OSM_DEFAULT_PLACE` is not found by Nominatim, the importer falls back to `OSM_FALLBACK_LAT` / `OSM_FALLBACK_LNG` / `OSM_FALLBACK_DIST`.

AMap POI import CLI:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 3 --request-interval 0.5
```

AMap POI import uses the official Place Around Web Service endpoint, converts returned GCJ-02 coordinates back to WGS84 for storage, classifies campus facilities, de-duplicates repeated keyword hits, binds each POI to the nearest local graph node, and backs off when AMap returns QPS limit code `10021`.

AMap walking route smoke:

```bash
python backend/scripts/smoke_amap_route.py
```

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
- `docs/stage_18_query_polish.md`: facility category lookup and food search sorting notes.
- `docs/stage_19_real_data_enrichment.md`: AMap POI real-data enrichment notes.
- `docs/stage_20_data_cleaning_route_inputs.md`: data cleaning and route place-input notes.
- `docs/stage_21_real_route_planning.md`: AMap walking route and local Dijkstra fallback notes.
- `docs/stage_22_diary_media_search.md`: diary media, exact title index, inverted index, and interest recommendation notes.
- `docs/stage_23_user_feedback_loop.md`: registration/login, token auth, favorites, ratings, behavior logs, and recommendation feedback notes.
- `docs/stage_24_destination_food_scope.md`: restaurant destination linkage and scoped food API notes.
- `docs/stage_25_admin_moderation.md`: admin edit endpoints and diary moderation notes.
- `docs/stage_26_optional_map_smoke.md`: optional AMap browser screenshot smoke notes.
- `docs/stage_27_real_map_layers.md`: real-priority OSM + AMap POI map layer cleanup and import notes.
- `docs/campus_navigation_data_plan.md`: reference campus data placement, validation, and import plan.
- `docs/stage_28_reference_campus_navigation.md`: supplied BUPT reference topology import and verification notes.
- `docs/stage_29_dual_poi_sources.md`: separate nearby-facility and campus-navigation POI source workflows.
- `docs/stage_30_diary_requirement_alignment.md`: diary management/community requirement mapping and next implementation focus.
- `docs/stage_31_admin_user_auth.md`: role-aware user/admin login-state implementation notes and acceptance criteria.
- `docs/stage_32_aigc_agent_preparation.md`: AIGC Agent workflow target, API contract, trace schema, and acceptance criteria.
- `README_DEPLOY.md`: local and Docker deployment commands.
- `tests/fixtures/README.md`: shared test fixture notes.

## Development Flow

1. Pick a row from `docs/feature_matrix.md`.
2. Implement backend API, frontend page, data model, and tests.
3. Update feature status.
4. Run `bash scripts/check_all.sh`.
5. Update acceptance checklist when criteria change.
