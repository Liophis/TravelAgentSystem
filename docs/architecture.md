# Architecture

## Stack

- Frontend: Vue 3, TypeScript, Vite, Element Plus, AMap JS API.
- Backend: FastAPI, SQLAlchemy, Pydantic.
- Demo DB: SQLite through SQLAlchemy.
- Target deploy DB: PostgreSQL/PostGIS.
- Cache target: Redis.
- Map source: OpenStreetMap via OSMnx/Overpass.

## Layers

```text
frontend pages/components
  -> frontend services/api.ts
  -> FastAPI api/v1 routers
  -> service layer
  -> algorithm helpers
  -> SQLAlchemy models/session
```

## Backend Modules

- API routers: request validation and HTTP response contracts.
- Services: business orchestration and database queries.
- Algorithms: Top-K heap, Dijkstra route planning, compression helpers.
- Models: SQLAlchemy table mapping.
- Seed: deterministic demo data reset.

## Frontend Modules

- `AMapView.vue`: map rendering boundary.
- Pages: one route per feature module.
- `services/api.ts`: typed payload contracts and fetch helpers.

## Boundaries

- AMap renders map overlays only.
- OSMnx/OpenStreetMap provides backend map topology and import data.
- Required tests do not depend on remote network services.
