# Deployment

## Local Demo

```bash
cp .env.example .env.local
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In another shell:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

## Docker Target

```bash
docker compose up --build
```

Expected services:

- frontend on `5173`
- backend on `8000`
- PostgreSQL/PostGIS on `5432`
- Redis on `6379`

## Environment

Required local variables:

- `VITE_AMAP_KEY`
- `VITE_API_BASE_URL`
- `API_DATABASE_URL`
- `DEV_DATABASE_URL`
- `OSM_FALLBACK_LAT`
- `OSM_FALLBACK_LNG`
- `OSM_FALLBACK_DIST`

## Current Gap

Docker Compose is scaffolded, but final deployment validation still needs a real `docker compose up --build` pass in the target environment.
