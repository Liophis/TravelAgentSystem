# Deployment Readme

## Local Demo Mode

Use SQLite for fast demonstration:

```bash
cp .env.example .env.local
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

## Docker Mode

```bash
docker compose up --build
```

Verify:

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/docs
```

## Required Configuration

- `VITE_AMAP_KEY`: AMap Web JS key.
- `API_DATABASE_URL`: backend API database.
- `DATABASE_URL`: target PostgreSQL database.
- `REDIS_URL`: Redis connection.
- `MEDIA_ROOT`: local uploaded media root.

## Notes

For the current course demo, SQLite local mode is the stable path. Docker/PostgreSQL remains the target deployment profile and should be validated before final submission if required by the instructor.
