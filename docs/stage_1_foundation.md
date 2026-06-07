# Stage 1 Foundation

## Delivered

- FastAPI app scaffold with `/api/v1` router.
- Backend mock contracts:
  - `GET /api/v1/health`
  - `GET /api/v1/map/stats`
  - `GET /api/v1/map/geojson`
  - `POST /api/v1/routes/plan`
  - `GET /api/v1/facilities/nearby`
- Backend contract tests for health, map payload, route payload, and facility filtering.
- Vue 3 + Vite + TypeScript frontend scaffold.
- AMap loading wrapper plan implemented in frontend structure.
- `AMapView` page/component scaffold for roads, buildings, facilities, and route drawing.
- Docker Compose scaffold for PostGIS, Redis, backend, and frontend.

## Not Yet Delivered

- Real OSMnx data import.
- Real PostgreSQL/PostGIS models and migrations.
- Real graph shortest-path routing.
- Real road-distance sorting for nearby facilities.
- Frontend typecheck/build verification, because npm dependency installation was not allowed in this session.

## Verification

```bash
bash scripts/check_all.sh
```

Current expected result:

- Backend tests pass.
- Frontend check skips typecheck/build if `frontend/node_modules` is missing.

After dependencies are installed:

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

