# Stage 28 Reference Campus Navigation

## Delivered

- Added offline import service for manually supplied BUPT Shahe campus files:
  - `data/reference/bupt-shahe/raw_wgs84/scenes.json`
  - `data/reference/bupt-shahe/topology/scene_bupt_campus.geojson`
- Added CLI:
  - `backend/scripts/import_reference_campus.py`
- Added admin import source:
  - `POST /api/v1/admin/map/import` with `source=reference_campus`
- Imported reference campus data into local dev DB:
  - nodes: 106
  - road edges: 246
  - reference facilities: 35
- Visible road layer now uses the reference campus graph after `--replace-campus-layers`.
- Old deterministic seed graph remains hidden as offline fallback.
- RoutePlannerPage is now scoped to 北京邮电大学沙河校区内部导航:
  - endpoint search calls `GET /api/v1/search/places?scope=campus`
  - nationwide attraction/school destinations are excluded from route endpoint candidates
  - user-facing route source defaults to `local_graph` over the imported campus topology
  - map overlays on the route page filter facilities/buildings to the BUPT Shahe campus boundary

## Coordinate Contract

- Source files are WGS84.
- Backend stores WGS84 `[lng, lat]`.
- Frontend AMap overlays still convert WGS84 to GCJ-02 before rendering.

## Import Command

```bash
PYTHONPATH=backend python backend/scripts/import_reference_campus.py --replace-campus-layers
```

## Verification

```bash
PYTHONPATH=backend pytest backend/tests/test_stage28_reference_campus_import.py -q
bash scripts/smoke_features.sh
bash scripts/check_all.sh
```

## Remaining Work

- Add edge-projection snapping with temporary virtual nodes.
- Add data-quality report for disconnected components and large snap distances.
- Add browser screenshot verification after starting frontend/backend with `VITE_AMAP_KEY`.
