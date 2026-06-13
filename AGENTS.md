# AGENTS.md

## Project

Smart Tour Guide: 景点/学校推荐 + 多场景内部导航 MVP。

## Target Stack

- Frontend: Vue 3 + Vite + TypeScript + Element Plus
- Map UI: 高德地图 JS API via `@amap/amap-jsapi-loader`
- Backend: FastAPI
- Database: PostgreSQL + PostGIS in Docker; SQLite only allowed for isolated tests
- Cache: Redis
- Search: PostgreSQL full-text / pg_trgm first
- Map data and routing topology: OpenStreetMap via OSMnx / Overpass
- Real POI enrichment: AMap Web Service Place Around API imported into local DB
- Storage: local `media/`, replaceable by MinIO later
- Deploy: Docker Compose + Nginx

## Directory Contract

```text
backend/            FastAPI application, services, db models, tests
frontend/           Vue 3 application
docs/               product, API, acceptance, and design docs
infra/nginx/        Nginx config
media/              local uploaded media, gitignored except placeholders
scripts/            project-level bash helpers
tests/fixtures/     small shared fixtures for backend/frontend tests
data/reference/     committed reference source data for real campus navigation imports
data/external/      downloaded third-party OSM/AMap source payloads before cleaning/import
```

## Do Not

- Do not reintroduce Streamlit as the main app.
- Do not add new business features before updating `docs/feature_matrix.md`.
- Do not hard-code secrets or API keys.
- Do not hard-code the AMap Web JS API key; read it from `VITE_AMAP_KEY`.
- Do not hard-code the AMap Web Service key; read it from `AMAP_WEB_API_KEY`.
- Do not use AMap as the backend routing topology source; AMap may enrich POIs, but backend routes must use OSMnx/OSM or local graph data.
- Do not present deterministic seed points as real campus data. Label them as offline fallback/demo data.
- Do not put real campus source files in `backend/cache/`, `frontend/public/`, or root-level scratch paths.
- Do not read raw reference files directly in request handlers; import them through a validation/cleaning script first.
- Do not rely on remote services in required tests.
- Do not commit generated databases, uploads, caches, `node_modules`, or build outputs.
- Do not silently change public API paths without updating docs and checks.

## Map Contract

- Destination recommendation covers attractions and schools/campuses.
- Destination search/recommendation uses `destinations` rows and `GET /api/v1/search/places?scope=destinations` when place-search autocomplete is needed.
- Campus buildings/facilities/user-facing named topology nodes are route and map entities, not tourism recommendation candidates unless also modeled in `destinations`.
- Internal navigation is scene-scoped. Default scene is `bupt_shahe`; Stage 35 adds `summer_palace`.
- Valid current scene keys are `bupt_shahe` for 北京邮电大学沙河校区 and `summer_palace` for 北京颐和园.
- RoutePlannerPage endpoint autocomplete must use `GET /api/v1/search/places?scope=campus`, may expose `building-{id}`, `facility-{id}`, and semantic `node-{id}` endpoints, and must not expose `destination-{id}` or generic road/intersection nodes as route endpoints.
- Maintain two POI datasets: `nearby_facilities` for school-surrounding facility recommendation, and `campus_navigation` for BUPT Shahe internal navigation POIs.
- Scene-scoped tables are `map_nodes.scene_key`, `map_edges.scene_key`, `buildings.scene_key`, and `facilities.scene_key`.
- All map/search/route/nearby-facility APIs must default to `scene_key=bupt_shahe` and must not mix rows across scenes.
- Backend stores and plans routes using OSM/PostGIS data.
- Manually supplied campus source files live under `data/reference/bupt-shahe/`.
- `data/reference/bupt-shahe/raw_wgs84/` stores original WGS84 JSON/GeoJSON source layers.
- `data/reference/bupt-shahe/topology/` stores original WGS84 road graph topology files.
- `data/reference/bupt-shahe/processed/` stores cleaned intermediate outputs, not API runtime state.
- Frontend renders maps with AMap JS API.
- Optional backend POI enrichment imports AMap GCJ-02 POIs, converts them to WGS84, and stores them as local facilities.
- AMap raw GCJ-02 payloads belong under `data/external/bupt-shahe/amap_gcj02/`, not `data/reference/bupt-shahe/raw_wgs84/`.
- Summer Palace raw OSM/AMap payloads belong under `data/external/summer-palace/`.
- API coordinates are WGS84 longitude/latitude.
- AMap overlays must receive `[lng, lat]`.
- Default map center: `[116.28333, 40.15608]` for 北京邮电大学沙河校区.

## Nearby Facility Contract

- Nearby facility search must be centered on an explicit user-selected origin.
- Preferred origin input is `origin_place_id` from `GET /api/v1/search/places?scope=campus`.
- Coordinate input is allowed only as map-click or debug fallback.
- Results must be ranked by Dijkstra graph distance plus snap distance, never by straight-line distance.
- Category lookup must support dropdown category codes and Chinese text aliases.
- Frontend should show the origin, resolved category, Top-K route distance, and selected route polyline.

## AIGC Contract

- AIGC animation remains a deterministic local simulation unless a real external model provider is explicitly configured.
- Do not present mock video links as real generated videos.
- LLM user profile extraction may call an OpenAI-compatible provider only when `LLM_API_KEY` is configured.
- Missing or failed LLM calls must fall back to deterministic local tag aggregation and must not break tests or demo startup.
- LLM-extracted tags are allowed to update `user_interests`; deterministic course algorithms remain the source of recommendation/routing/search behavior.
- The AIGC Agent is exposed as `POST /api/v1/aigc/agent/run`.
- Agent responses must include `agent_trace.steps[]` with tool name, status, timing, input summary, and output summary.
- Keep `POST /api/v1/aigc/diary-draft` and `POST /api/v1/aigc/storyboard` backward-compatible.
- Agent tools should be small deterministic functions first: media analyzer, diary writer, storyboard planner, prompt builder, mock video generator, and compression summary.

## Required Harness Commands

Run from repository root:

```bash
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_data_requirements.sh
bash scripts/check_merge_markers.sh
bash scripts/check_all.sh
bash scripts/seed_all.sh
bash scripts/reset_dev_db.sh
bash scripts/restore_campus_map.sh
bash scripts/restore_summer_palace_map.sh
bash scripts/smoke_features.sh
```

Optional campus reference import:

```bash
bash scripts/restore_campus_map.sh
bash scripts/restore_summer_palace_map.sh
```

Optional conda backend check:

```bash
BACKEND_PYTHON_CMD="conda run -n travel-agent python" \
BACKEND_PYTEST_CMD="conda run -n travel-agent pytest" \
bash scripts/check_backend.sh
```

## Development Rule

For every feature:

1. Update `docs/feature_matrix.md`.
2. Add or update API tests.
3. Add or update page-level acceptance notes.
4. Run `bash scripts/check_all.sh`.
5. Update `docs/acceptance_checklist.md` if acceptance criteria changed.
6. Run `bash scripts/reset_dev_db.sh && bash scripts/smoke_features.sh` before claiming local demo usability.
