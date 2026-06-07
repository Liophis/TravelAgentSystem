# Smart Tour Guide

大型校园 / 景区智能导览平台 MVP。

当前仓库处于 **Stage 3 map data API** 阶段：已建立 FastAPI / Vue / AMap / Docker Compose 骨架，加入 SQLAlchemy 核心表模型、确定性 seed/reset 数据，并把地图浏览 API 接入数据库种子数据。

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
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
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
```

These scripts default to `DEV_DATABASE_URL=sqlite:///./smart_tour_dev.db` and currently seed 10 users, 200 destinations, 80 map nodes, 220 map edges, 20 buildings, 50 facilities, and 10 facility categories.

The local backend reads API data from `API_DATABASE_URL`. For the SQLite demo path, run:

```bash
bash scripts/reset_dev_db.sh
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then check:

```bash
curl http://127.0.0.1:8000/api/v1/map/stats
```

## Docs

- `AGENTS.md`: rules for Codex and future agents.
- `docs/feature_matrix.md`: feature/API/page/table/test status.
- `docs/acceptance_checklist.md`: acceptance requirements.
- `docs/amap_map_plan.md`: AMap frontend rendering plan and OSM backend boundary.
- `docs/stage_1_foundation.md`: project skeleton delivery notes and known gaps.
- `docs/stage_2_data_foundation.md`: data model and seed delivery notes.
- `docs/stage_3_map_data_api.md`: database-backed map API delivery notes.
- `tests/fixtures/README.md`: shared test fixture notes.

## Development Flow

1. Pick a row from `docs/feature_matrix.md`.
2. Implement backend API, frontend page, data model, and tests.
3. Update feature status.
4. Run `bash scripts/check_all.sh`.
5. Update acceptance checklist when criteria change.
