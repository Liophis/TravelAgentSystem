# Stage 19 Real Data Enrichment

## Problem

The previous campus density work improved demo stability with deterministic seed data, but it did not solve real campus POI scarcity. Seed data must be treated as an offline fallback, not as newly collected campus data.

## Scope

This stage adds a real POI enrichment path:

- OSMnx/OpenStreetMap remains the backend road topology source.
- AMap Web Service Place Around imports real facilities around 北京邮电大学沙河校区.
- Imported AMap POIs are converted from GCJ-02 to WGS84 before storage.
- Imported facilities are de-duplicated and attached to the nearest local graph node.
- Required tests stay network-free by mocking AMap responses.

## Commands

Set a backend Web Service key:

```bash
AMAP_WEB_API_KEY=your_amap_web_service_key
```

Import real POIs into the dev database:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 3 --request-interval 0.5
```

Replace fallback facility points but keep the road graph:

```bash
PYTHONPATH=backend python backend/scripts/import_amap_pois.py --radius 1800 --max-pages 5 --request-interval 0.5 --reset-facilities
```

Admin API equivalent:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/admin/map/import \
  -H 'Content-Type: application/json' \
  -d '{"source":"amap_poi","dist":1800,"max_pages":3,"request_interval":0.5,"reset_existing":false}'
```

## Data Contract

- Backend DB stores WGS84 `[lng, lat]`.
- AMap Web Service returns GCJ-02 POI coordinates.
- Frontend `AMapView` converts backend WGS84 overlays to GCJ-02 for rendering.
- Backend Dijkstra still runs on local `map_nodes` and `map_edges`.

## Validation

```bash
PYTHONPATH=backend pytest backend/tests/test_stage19_real_data_enrichment.py
bash scripts/reset_dev_db.sh
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

Expected:

- coordinate conversion round-trip is covered by tests
- mocked AMap POIs import into `facilities`
- duplicate keyword hits are skipped
- AMap QPS limit code `10021` backs off and retries
- no tests require a live AMap key

## Clean Live Import Result

Executed locally with a real `AMAP_WEB_API_KEY`:

```bash
python backend/scripts/import_amap_pois.py --radius 3000 --max-pages 3 --request-interval 0.8 --reset-facilities
```

Result:

- raw AMap POIs: 544
- imported facility rows: 516
- skipped duplicate/invalid/out-of-radius rows: 28
- total local facilities after cleanup: 516
- offline fallback facility seed rows removed from the local dev DB

Category distribution after import:

| Category | Count |
| --- | ---: |
| shop | 182 |
| transport | 128 |
| clinic | 53 |
| sport | 45 |
| canteen | 41 |
| gate | 22 |
| library | 14 |
| water | 13 |
| toilet | 9 |
| atm | 9 |

The generated SQLite database remains ignored and is not committed.

## Remaining Limits

- AMap POI import improves facility points, not building polygons.
- If campus road topology from OSM is sparse, we still need better walkable graph data or manually verified campus paths.
- Live import depends on `AMAP_WEB_API_KEY`, network access, quota, and AMap terms.
