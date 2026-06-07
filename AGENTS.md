# AGENTS.md

## Project

Smart Tour Guide: 大型校园 / 景区智能导览平台 MVP。

## Target Stack

- Frontend: Vue 3 + Vite + TypeScript + Element Plus
- Map UI: 高德地图 JS API via `@amap/amap-jsapi-loader`
- Backend: FastAPI
- Database: PostgreSQL + PostGIS in Docker; SQLite only allowed for isolated tests
- Cache: Redis
- Search: PostgreSQL full-text / pg_trgm first
- Map data and routing topology: OpenStreetMap via OSMnx / Overpass
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
```

## Do Not

- Do not reintroduce Streamlit as the main app.
- Do not add new business features before updating `docs/feature_matrix.md`.
- Do not hard-code secrets or API keys.
- Do not hard-code the AMap Web JS API key; read it from `VITE_AMAP_KEY`.
- Do not use AMap as the backend routing topology source; backend routes must use OSMnx/OSM graph data.
- Do not rely on remote services in required tests.
- Do not commit generated databases, uploads, caches, `node_modules`, or build outputs.
- Do not silently change public API paths without updating docs and checks.

## Map Contract

- Backend stores and plans routes using OSM/PostGIS data.
- Frontend renders maps with AMap JS API.
- API coordinates are WGS84 longitude/latitude.
- AMap overlays must receive `[lng, lat]`.
- Default map center: `[116.28333, 40.15608]` for 北京邮电大学沙河校区.

## Required Harness Commands

Run from repository root:

```bash
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
bash scripts/seed_all.sh
bash scripts/reset_dev_db.sh
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
