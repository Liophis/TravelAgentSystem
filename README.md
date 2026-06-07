# Smart Tour Guide

大型校园 / 景区智能导览平台 MVP。

当前仓库处于 **Stage 1 foundation** 阶段：已建立 FastAPI / Vue / AMap / Docker Compose 骨架，并用 mock API 验证地图、路线、附近设施三个页面的接口闭环。

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

At the harness stage there is no runnable business app yet. After backend/frontend scaffolds are added, use:
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

At this harness stage these scripts are intentionally safe if seed/reset implementation is not created yet.

## Docs

- `AGENTS.md`: rules for Codex and future agents.
- `docs/feature_matrix.md`: feature/API/page/table/test status.
- `docs/acceptance_checklist.md`: acceptance requirements.
- `docs/amap_map_plan.md`: AMap frontend rendering plan and OSM backend boundary.
- `docs/stage_1_foundation.md`: current stage delivery notes and known gaps.
- `tests/fixtures/README.md`: shared test fixture notes.

## Development Flow

1. Pick a row from `docs/feature_matrix.md`.
2. Implement backend API, frontend page, data model, and tests.
3. Update feature status.
4. Run `bash scripts/check_all.sh`.
5. Update acceptance checklist when criteria change.
