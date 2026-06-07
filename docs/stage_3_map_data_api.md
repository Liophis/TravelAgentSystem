# Stage 3 Map Data API

## Scope

This stage connects the public map browsing API to the seeded database. It does not implement real OSMnx import yet.

## Delivered

- Added `API_DATABASE_URL` so local API reads from the dev/demo database.
- `GET /api/v1/map/stats` now returns DB-backed counts.
- `GET /api/v1/map/geojson` now returns seeded roads, buildings, facilities, categories, statistics, and GeoJSON.
- Added layer endpoints:
  - `GET /api/v1/map/nodes`
  - `GET /api/v1/map/edges`
  - `GET /api/v1/map/buildings`
  - `GET /api/v1/map/facilities`
- Docker backend now points `API_DATABASE_URL` at PostgreSQL.
- Added service and API tests for the map data contract.

## API Contract

Coordinates are longitude/latitude arrays.

```text
center: [lng, lat]
roads[].path: [lng, lat][]
buildings[].polygon: [lng, lat][]
facilities[]: lng + lat fields
geojson.features[].geometry.coordinates: GeoJSON longitude/latitude order
```

Current demo source:

```text
source = database-seed-stage-3
```

## Validation

Run from repository root:

```bash
bash scripts/reset_dev_db.sh
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Manual API smoke test:

```bash
bash scripts/reset_dev_db.sh
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/api/v1/map/stats
```

Expected scale:

```text
nodes: 80
roads: 220
buildings: 20
facilities: 50
categories: 10
```

## Known Gaps

- Real OSMnx / Overpass import is not implemented.
- Map data is deterministic seed data for 北京邮电大学沙河校区.
- Routes and nearby facility distance are still scaffolded and not graph-backed.
- Admin map import/status pages are still planned.

## Next Stage

Implement real route graph services on top of `map_nodes` and `map_edges`:

- nearest-node lookup
- Dijkstra shortest path
- route steps, distance, and time
- nearby facilities sorted by graph distance
